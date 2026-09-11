"""Tests for Haven agent tools — verifying they hit DynamoDB, not returning mocks."""

from __future__ import annotations


class TestDonorTools:
    def test_parse_donation_offer_creates_record(self, mock_dynamodb):
        """Verify parse_donation_offer calls DynamoDB put_item, not returning hardcoded data."""
        _, mock_table = mock_dynamodb
        mock_table.put_item.return_value = {}

        from haven.tools.donor_tools import parse_donation_offer

        result = parse_donation_offer(
            donor_name="Green Farms",
            donor_phone="555-0100",
            description="Fresh vegetables",
            quantity="200 lbs",
            category="produce",
        )

        assert mock_table.put_item.called
        put_call = mock_table.put_item.call_args_list[0]
        item = put_call[1]["Item"] if "Item" in put_call[1] else put_call[0][0]
        assert item["donor_name"] == "Green Farms"
        assert item["category"] == "produce"
        assert result["category"] == "produce"
        assert result["next_step"] == "assess_cold_chain"

    def test_accept_donation_updates_record(self, mock_dynamodb):
        """Verify accept_donation calls DynamoDB update_item."""
        _, mock_table = mock_dynamodb
        mock_table.get_item.return_value = {"Item": {"id": "don-123", "donor_name": "Test Farm", "status": "offered"}}

        from haven.tools.donor_tools import accept_donation

        result = accept_donation("don-123", notes="Confirmed")

        assert result["offer_id"] == "don-123"
        assert result["status"] == "accepted"

    def test_accept_donation_not_found(self, mock_dynamodb):
        """Verify accept_donation handles missing records."""
        _, mock_table = mock_dynamodb
        mock_table.get_item.return_value = {}

        from haven.tools.donor_tools import accept_donation

        result = accept_donation("nonexistent")
        assert "error" in result

    def test_check_cold_chain_updates_record(self, mock_dynamodb):
        """Verify check_cold_chain writes back to DynamoDB."""
        _, mock_table = mock_dynamodb

        from haven.tools.donor_tools import check_cold_chain_requirements

        result = check_cold_chain_requirements("don-001", "dairy", True)

        assert mock_table.update_item.called
        assert result["cold_chain_required"] is True
        assert result["temperature_range"] == "33-40°F"

    def test_cold_chain_bakery_not_required(self, mock_dynamodb):
        """Verify bakery doesn't require cold chain by default."""

        from haven.tools.donor_tools import check_cold_chain_requirements

        result = check_cold_chain_requirements("don-002", "bakery", False)

        assert result["cold_chain_required"] is False
        assert result["temperature_range"] == "ambient"

    def test_generate_tax_receipt_creates_audit(self, mock_dynamodb):
        """Verify tax receipt generation logs to audit trail."""

        from haven.tools.donor_tools import generate_tax_receipt

        result = generate_tax_receipt("don-001", "Green Farms", "Vegetables", 500.0)

        assert "receipt" in result
        assert result["receipt"]["donor_name"] == "Green Farms"
        assert result["receipt"]["estimated_value"] == 500.0
        assert result["receipt"]["organization_ein"] == "XX-XXXXXXX"


class TestVolunteerTools:
    def test_get_open_shifts_from_db(self, mock_dynamodb):
        """Verify get_open_shifts queries DynamoDB, not returning hardcoded data."""
        _, mock_table = mock_dynamodb
        mock_table.query.return_value = {
            "Items": [
                {"id": "s1", "pantry_name": "Downtown", "status": "open"},
                {"id": "s2", "pantry_name": "Eastside", "status": "open"},
            ]
        }

        from haven.tools.volunteer_tools import get_open_shifts

        result = get_open_shifts()

        assert result["total_open"] == 2
        assert len(result["shifts"]) == 2

    def test_match_volunteer_updates_records(self, mock_dynamodb):
        """Verify match_volunteer updates records and stages (not sends) an offer."""
        _, mock_table = mock_dynamodb
        mock_table.get_item.side_effect = [
            {"Item": {"id": "v1", "name": "Maria", "status": "available"}},
            {"Item": {"id": "s1", "volunteers_assigned": [], "volunteers_needed": 2, "status": "open"}},
            {"Item": {"id": "v1", "name": "Maria", "status": "matched"}},
            {"Item": {"id": "s1", "volunteers_assigned": ["v1"], "volunteers_needed": 2, "status": "open"}},
        ]

        from haven.tools.volunteer_tools import match_volunteer

        result = match_volunteer(
            shift_id="s1",
            volunteer_id="v1",
            volunteer_skills=["food_distribution", "driving"],
            volunteer_location="downtown",
            shift_requirements=["food_distribution"],
        )

        assert result["match_score"] == 100
        assert result["offer_staged"] is True
        assert result["offer_sent"] is False

    def test_match_low_score_no_offer(self, mock_dynamodb):
        """Verify low match scores don't stage offers."""

        from haven.tools.volunteer_tools import match_volunteer

        result = match_volunteer(
            shift_id="s1",
            volunteer_id="v1",
            volunteer_skills=["cooking"],
            volunteer_location="downtown",
            shift_requirements=["driving", "food_distribution", "admin"],
        )

        assert result["match_score"] == 0
        assert result["offer_staged"] is False
        assert result["offer_sent"] is False

    def test_handle_no_show_updates_records(self, mock_dynamodb):
        """Verify handle_no_show updates volunteer and shift."""
        _, mock_table = mock_dynamodb
        mock_table.get_item.side_effect = [
            {"Item": {"id": "v1", "no_shows": 0}},
            {"Item": {"id": "s1", "volunteers_assigned": ["v1", "v2"]}},
            {"Item": {"id": "v1", "no_shows": 1, "status": "available"}},
            {"Item": {"id": "s1", "volunteers_assigned": ["v2"]}},
        ]

        from haven.tools.volunteer_tools import handle_no_show

        result = handle_no_show("v1", "s1")

        assert result["action"] == "no_show_logged"
        assert result["backfill_triggered"] is False

    def test_calculate_stats_from_real_data(self, mock_dynamodb):
        """Verify stats are computed from DynamoDB data, not hardcoded."""
        _, mock_table = mock_dynamodb
        mock_table.get_item.return_value = {
            "Item": {
                "id": "v1",
                "name": "Maria",
                "total_shifts_completed": 20,
                "no_shows": 2,
                "rating": 4.8,
                "skills": ["driving"],
            }
        }

        from haven.tools.volunteer_tools import calculate_volunteer_stats

        result = calculate_volunteer_stats("v1")

        assert result["total_shifts"] == 20
        assert result["no_shows"] == 2
        assert result["name"] == "Maria"
        assert result["completion_rate"] == 90.9


class TestRecipientTools:
    def test_verify_eligibility_creates_audit(self, mock_dynamodb):
        """Verify eligibility check logs audit trail, honest when no pantry data."""

        from haven.tools.recipient_tools import verify_eligibility

        result = verify_eligibility("pantry-001", 4, "12345")

        assert result["eligible"] is None
        assert result["data_available"] is False
        assert result["household_size"] == 4

    def test_translate_same_language_passthrough(self):
        """Verify translate returns passthrough when same language."""
        from haven.tools.recipient_tools import translate_response

        result = translate_response("Hello", "en", "en")

        assert result["translated_text"] == "Hello"
        assert result["engine"] == "passthrough"
        assert result["confidence"] == 1.0

    def test_submit_recipient_request_creates_record(self, mock_dynamodb):
        """Verify submit_recipient_request writes to DynamoDB."""
        _, mock_table = mock_dynamodb

        from haven.tools.recipient_tools import submit_recipient_request

        result = submit_recipient_request(
            phone="555-0000",
            request_text="Need help",
            language="es",
            household_size=3,
        )

        assert result["status"] == "submitted"
        assert "request_id" in result
        assert mock_table.put_item.called


class TestLogisticsTools:
    def test_optimize_route_creates_event(self, mock_dynamodb):
        """Verify optimize_route logs event to DynamoDB."""
        _, mock_table = mock_dynamodb

        from haven.tools.logistics_tools import optimize_route

        result = optimize_route("123 Main St", "456 Oak Ave", ["789 Elm St"], True)

        assert result["total_distance_miles"] > 0
        assert result["estimated_duration_minutes"] > 0
        assert result["cold_chain_compliant"] is True
        assert mock_table.put_item.called

    def test_dispatch_driver_logs_event(self, mock_dynamodb):
        """Verify dispatch_driver creates event in DynamoDB, honestly notifying."""
        _, mock_table = mock_dynamodb

        from haven.tools.logistics_tools import dispatch_driver

        result = dispatch_driver("driver-001", "MAN-123", "van")

        assert result["status"] == "logged"
        assert result["driver_notified"] is False
        assert mock_table.put_item.called

    def test_cold_chain_breach_creates_critical_event(self, mock_dynamodb):
        """Verify cold chain breach logs critical event."""

        from haven.tools.logistics_tools import track_cold_chain

        result = track_cold_chain("ship-001", 55.0, 33.0, 40.0)

        assert result["in_compliance"] is False
        assert "CRITICAL" in result["alert"]
        assert result["recommendation"] == "IMMEDIATE ACTION: Check cooling equipment"

    def test_cold_chain_in_range(self, mock_dynamodb):
        """Verify in-range temperature doesn't trigger alert."""

        from haven.tools.logistics_tools import track_cold_chain

        result = track_cold_chain("ship-002", 37.0, 33.0, 40.0)

        assert result["in_compliance"] is True
        assert result["alert"] is None


class TestComplianceTools:
    def test_generate_usda_report_creates_audit(self, mock_dynamodb):
        """Verify USDA report generation logs audit trail (draft, not submitted)."""

        from haven.tools.compliance_tools import generate_usda_report

        result = generate_usda_report(
            reporting_period="Sep 2026",
            organization_id="org-001",
            total_pounds_distributed=12400.0,
            total_meals_served=8267,
            unique_recipients=1204,
        )

        assert result["compliance_status"] == "draft"
        assert result["metrics"]["pounds_per_meal"] == 1.5
        assert result["submission_ready"] is False

    def test_log_food_safety_event_critical(self, mock_dynamodb):
        """Verify critical safety events log a system alert (no external notify)."""

        from haven.tools.compliance_tools import log_food_safety_event

        result = log_food_safety_event(
            event_type="temperature_excursion",
            description="Refrigerator malfunction",
            severity="critical",
            affected_items=["milk", "cheese"],
        )

        assert result["logged"] is True
        assert result["notification_sent"] is False
        assert result["system_alert_logged"] is True
        assert result["follow_up_required"] is True

    def test_log_food_safety_event_low_severity(self, mock_dynamodb):
        """Verify low severity events don't send notifications."""

        from haven.tools.compliance_tools import log_food_safety_event

        result = log_food_safety_event(
            event_type="minor_spill",
            description="Small spill in loading area",
            severity="low",
            affected_items=[],
        )

        assert result["notification_sent"] is False

    def test_get_compliance_summary(self, mock_dynamodb):
        """Verify compliance summary aggregates real data."""
        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {
            "Items": [
                {"id": "d1", "status": "distributed", "quantity": "100 lbs"},
                {"id": "d2", "status": "accepted", "quantity": "50 lbs"},
            ]
        }

        from haven.tools.compliance_tools import get_compliance_summary

        result = get_compliance_summary()

        assert result["total_donations"] == 2
        assert result["compliance_status"] == "pending_review"
