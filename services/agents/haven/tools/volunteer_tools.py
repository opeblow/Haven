"""Tools for the VolunteerAgent — manages volunteer matching."""

from __future__ import annotations

import uuid

from strands import tool

from haven.db import (
    create_audit_entry,
    create_event,
    get_shift,
    get_volunteer,
    list_shifts,
    update_shift,
    update_volunteer,
)


@tool
def get_open_shifts(pantry_id: str = "", role: str = "") -> dict:
    """Retrieve open volunteer shifts from DynamoDB.

    Returns a list of shifts that need volunteers, optionally
    filtered by pantry and role.
    """
    shifts = list_shifts(status="open")
    if pantry_id:
        shifts = [s for s in shifts if s.get("pantry_id") == pantry_id]
    if role:
        shifts = [s for s in shifts if s.get("role") == role]
    return {
        "shifts": shifts,
        "total_open": len(shifts),
        "filter_applied": {"pantry_id": pantry_id, "role": role},
    }


@tool
def match_volunteer(
    shift_id: str,
    volunteer_id: str,
    volunteer_skills: list[str],
    volunteer_location: str,
    shift_requirements: list[str],
) -> dict:
    """Match a volunteer to a shift based on the provided skills/requirements.

    The score uses the skills and requirements passed in this call, not
    stored profiles, because the stored records do not yet carry skill data.
    An SMS offer is NOT sent from this tool; it only stages the match.
    """
    skill_overlap = len(set(volunteer_skills) & set(shift_requirements))
    total_requirements = max(len(shift_requirements), 1)
    score = (skill_overlap / total_requirements) * 100

    offer_staged = score >= 50
    if offer_staged:
        volunteer = get_volunteer(volunteer_id)
        if volunteer:
            update_volunteer(volunteer_id, {"status": "matched"})
        shift = get_shift(shift_id)
        if shift:
            assigned = shift.get("volunteers_assigned", [])
            if volunteer_id not in assigned:
                assigned.append(volunteer_id)
            new_status = "filled" if len(assigned) >= shift.get("volunteers_needed", 1) else "open"
            update_shift(shift_id, {"volunteers_assigned": assigned, "status": new_status})

    create_audit_entry(
        {
            "action": "volunteer_match",
            "agent": "volunteer",
            "entity_type": "shift",
            "entity_id": shift_id,
            "details": {"volunteer_id": volunteer_id, "match_score": round(score), "offer_staged": offer_staged},
        }
    )

    return {
        "shift_id": shift_id,
        "volunteer_id": volunteer_id,
        "match_score": round(score),
        "skill_match": skill_overlap,
        "offer_staged": offer_staged,
        "offer_sent": False,
        "message": (
            f"Match staged for volunteer {volunteer_id} on shift {shift_id}. "
            "Send an SMS offer via send_shift_offer_sms before considering it accepted."
            if offer_staged
            else f"Match score {score}% too low. Looking for better candidates."
        ),
    }


@tool
def send_shift_offer_sms(
    volunteer_phone: str,
    volunteer_name: str,
    shift_details: str,
    pantry_name: str,
    response_deadline: str,
) -> dict:
    """Send an SMS shift offer to a volunteer via Twilio.

    Only reports 'sent' when Twilio confirms delivery. There is no durable
    outbound queue, so an unconfigured or failed send is reported honestly.
    """
    from haven.config import get_settings

    settings = get_settings()
    message = (
        f"Hi {volunteer_name}! A new shift is available at {pantry_name}.\n\n"
        f"{shift_details}\n\n"
        f"Reply YES to confirm or NO to decline by {response_deadline}."
    )

    twilio_sid = None
    twilio_error = None
    if settings.twilio_account_sid and settings.twilio_auth_token:
        try:
            from twilio.base.exceptions import TwilioRestException
            from twilio.rest import Client

            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            sms = client.messages.create(
                body=message,
                from_=settings.twilio_phone_number,
                to=volunteer_phone,
            )
            twilio_sid = sms.sid
        except (ImportError, TwilioRestException) as e:
            twilio_error = f"{type(e).__name__}: {e}"

    if twilio_sid:
        status = "sent"
    elif twilio_error:
        status = "failed"
    else:
        status = "not_configured"

    create_event(
        {
            "id": str(uuid.uuid4()),
            "event_type": "shift_offer_sms",
            "source": "volunteer_agent",
            "payload": {"phone": volunteer_phone, "pantry_name": pantry_name, "status": status},
            "urgency": "low",
        }
    )

    return {
        "phone": volunteer_phone,
        "message": message,
        "status": status,
        "twilio_sid": twilio_sid or "",
        "error": twilio_error or "",
        "durable_queue": False,
        "next_step": "Retry via the outbound channel once Twilio is configured." if status != "sent" else "",
    }


@tool
def handle_no_show(volunteer_id: str, shift_id: str) -> dict:
    """Handle a volunteer no-show. Updates records and triggers backfill."""
    volunteer = get_volunteer(volunteer_id)
    shift = get_shift(shift_id)

    new_no_shows = (volunteer.get("no_shows", 0) + 1) if volunteer else 1
    update_volunteer(volunteer_id, {"no_shows": new_no_shows, "status": "available"})

    if shift:
        assigned = shift.get("volunteers_assigned", [])
        if volunteer_id in assigned:
            assigned.remove(volunteer_id)
        update_shift(shift_id, {"volunteers_assigned": assigned, "status": "open"})

    create_audit_entry(
        {
            "action": "volunteer_no_show",
            "agent": "volunteer",
            "entity_type": "volunteer",
            "entity_id": volunteer_id,
            "details": {"shift_id": shift_id, "total_no_shows": new_no_shows},
        }
    )

    return {
        "volunteer_id": volunteer_id,
        "shift_id": shift_id,
        "action": "no_show_logged",
        "volunteer_warned": new_no_shows >= 2,
        "backfill_triggered": False,
        "message": "No-show logged. Shift reopened; a replacement volunteer is not yet selected.",
    }


@tool
def calculate_volunteer_stats(volunteer_id: str) -> dict:
    """Calculate performance statistics for a volunteer from DynamoDB data."""
    volunteer = get_volunteer(volunteer_id)
    if not volunteer:
        return {"error": f"Volunteer {volunteer_id} not found"}

    total = volunteer.get("total_shifts_completed", 0)
    no_shows = volunteer.get("no_shows", 0)
    completed = total
    completion_rate = (completed / max(total + no_shows, 1)) * 100
    reliability = min(100, max(0, 100 - (no_shows * 10)))

    return {
        "volunteer_id": volunteer_id,
        "name": volunteer.get("name", ""),
        "total_shifts": total,
        "completed_shifts": completed,
        "no_shows": no_shows,
        "completion_rate": round(completion_rate, 1),
        "reliability_score": round(reliability),
        "skills": volunteer.get("skills", []),
        "rating": volunteer.get("rating", 5.0),
        "recommendation": (
            "Reliable volunteer. Consider for shift lead role."
            if reliability >= 80
            else "Needs improvement. Monitor attendance."
        ),
    }
