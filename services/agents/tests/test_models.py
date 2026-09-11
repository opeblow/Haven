"""Tests for Haven domain models."""

from __future__ import annotations

from datetime import UTC, datetime

from haven.models import (
    AgentEvent,
    DonationStatus,
    DonorOffer,
    RecipientRequest,
    Shift,
    ShiftStatus,
    UrgencyLevel,
    Volunteer,
    VolunteerStatus,
)


class TestDonationStatus:
    def test_enum_values(self):
        assert DonationStatus.OFFERED.value == "offered"
        assert DonationStatus.ACCEPTED.value == "accepted"
        assert DonationStatus.IN_TRANSIT.value == "in_transit"
        assert DonationStatus.RECEIVED.value == "received"
        assert DonationStatus.DISTRIBUTED.value == "distributed"
        assert DonationStatus.REJECTED.value == "rejected"

    def test_all_statuses_are_strings(self):
        for status in DonationStatus:
            assert isinstance(status.value, str)


class TestDonorOffer:
    def test_create_offer(self):
        offer = DonorOffer(
            donor_name="Green Farms",
            donor_phone="555-0100",
            description="Fresh vegetables",
            quantity="200 lbs",
            category="produce",
        )
        assert offer.donor_name == "Green Farms"
        assert offer.status == DonationStatus.OFFERED
        assert offer.requires_refrigeration is False
        assert isinstance(offer.id, str)
        assert len(offer.id) > 0

    def test_offer_defaults(self):
        offer = DonorOffer(
            donor_name="Test",
            donor_phone="555-0000",
            description="Test",
            quantity="10 lbs",
            category="other",
        )
        assert offer.donor_email == ""
        assert offer.address == ""
        assert offer.latitude is None
        assert offer.longitude is None
        assert offer.notes == ""

    def test_offer_with_refrigeration(self):
        offer = DonorOffer(
            donor_name="Dairy Farm",
            donor_phone="555-0200",
            description="Milk",
            quantity="50 gallons",
            category="dairy",
            requires_refrigeration=True,
        )
        assert offer.requires_refrigeration is True
        assert offer.category == "dairy"

    def test_offer_timestamps_are_utc(self):
        offer = DonorOffer(
            donor_name="Test",
            donor_phone="555-0000",
            description="Test",
            quantity="1 lb",
            category="other",
        )
        assert offer.created_at.tzinfo == UTC
        assert offer.updated_at.tzinfo == UTC


class TestVolunteer:
    def test_create_volunteer(self):
        vol = Volunteer(
            name="Maria Rodriguez",
            phone="555-0123",
            email="maria@test.com",
            skills=["food_distribution", "spanish_speaker"],
        )
        assert vol.name == "Maria Rodriguez"
        assert vol.status == VolunteerStatus.AVAILABLE
        assert vol.rating == 5.0
        assert vol.no_shows == 0
        assert vol.has_vehicle is False

    def test_volunteer_with_vehicle(self):
        vol = Volunteer(
            name="James T",
            phone="555-0456",
            email="james@test.com",
            skills=["driving"],
            has_vehicle=True,
        )
        assert vol.has_vehicle is True

    def test_volunteer_languages_default(self):
        vol = Volunteer(
            name="Test",
            phone="555-0000",
            email="test@test.com",
        )
        assert vol.languages == ["en"]


class TestRecipientRequest:
    def test_create_request(self):
        req = RecipientRequest(
            phone="555-0789",
            request_text="Need food for family of 4",
            language="en",
            household_size=4,
        )
        assert req.phone == "555-0789"
        assert req.resolved is False
        assert req.household_size == 4
        assert req.language == "en"

    def test_request_with_dietary_restrictions(self):
        req = RecipientRequest(
            phone="555-0000",
            request_text="Need gluten-free options",
            dietary_restrictions=["gluten-free", "nut-free"],
        )
        assert len(req.dietary_restrictions) == 2
        assert "gluten-free" in req.dietary_restrictions


class TestShift:
    def test_create_shift(self):
        shift = Shift(
            pantry_id="pantry-001",
            pantry_name="Downtown Pantry",
            role="food_distribution",
            start_time=datetime(2026, 9, 12, 9, 0, tzinfo=UTC),
            end_time=datetime(2026, 9, 12, 13, 0, tzinfo=UTC),
            volunteers_needed=3,
        )
        assert shift.pantry_name == "Downtown Pantry"
        assert shift.status == ShiftStatus.OPEN
        assert shift.volunteers_needed == 3
        assert shift.volunteers_assigned == []


class TestAgentEvent:
    def test_create_event(self):
        event = AgentEvent(
            event_type="donation_offer",
            source="donor_agent",
            payload={"donation_id": "abc-123"},
        )
        assert event.event_type == "donation_offer"
        assert event.urgency == UrgencyLevel.MEDIUM
        assert event.requires_human is False
        assert event.processed_by == []

    def test_critical_urgency(self):
        event = AgentEvent(
            event_type="food_safety_incident",
            source="compliance_agent",
            payload={},
            urgency=UrgencyLevel.CRITICAL,
            requires_human=True,
        )
        assert event.urgency == UrgencyLevel.CRITICAL
        assert event.requires_human is True
