from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from asset_management.data_collection.contracts.v1 import (
    ABCDailyTradableUniverseSnapshotV1,
    AccountImportEnvelopeV1,
    DataQualityAlertV1,
    InvestmentPlanSnapshotV1,
    MonthlyAccountAnchorV1,
    ValidatedMarketObservationV1,
)
from asset_management.data_collection.domain.enums import (
    FreshnessStatus,
    PlanStatus,
    QualityStatus,
    ReconciliationStatus,
    ScheduleType,
)


def test_monthly_anchor_serializes_stable_identity_and_decimal_values() -> None:
    anchor = MonthlyAccountAnchorV1(
        anchor_id="anchor-1",
        instrument_code="019172",
        snapshot_as_of_date=date(2026, 8, 31),
        confirmed_at=datetime(2026, 9, 5, 9, 0, tzinfo=UTC),
        confirmed_units=Decimal("12.3400000000"),
        account_value=Decimal("1234.5600000000"),
        pending_amount=Decimal("10.0000000000"),
        pending_units=None,
        quality_status=QualityStatus.VALID,
        reconciliation_status=ReconciliationStatus.RECONCILED,
    )

    payload = anchor.model_dump(mode="json")

    assert payload["contract_name"] == "MonthlyAccountAnchor"
    assert payload["contract_version"] == "v1"
    assert anchor.confirmed_units == Decimal("12.3400000000")
    assert payload["pending_units"] is None


def test_v1_contracts_require_their_identity_fields() -> None:
    with pytest.raises(ValidationError):
        MonthlyAccountAnchorV1(
            instrument_code="019172",
            snapshot_as_of_date=date(2026, 8, 31),
            confirmed_at=datetime(2026, 9, 5, tzinfo=UTC),
            confirmed_units=Decimal(1),
            account_value=Decimal(1),
            quality_status=QualityStatus.VALID,
            reconciliation_status=ReconciliationStatus.RECONCILED,
        )


def test_invalid_enum_value_is_rejected() -> None:
    with pytest.raises(ValidationError):
        InvestmentPlanSnapshotV1(
            snapshot_id="plan-1",
            instrument_code="019172",
            schedule_type="NOT_A_SCHEDULE",
            amount=Decimal(10),
            status=PlanStatus.ENABLED,
            effective_from=date(2026, 9, 1),
        )


def test_estimated_and_confirmed_units_are_distinct_fields() -> None:
    observation = ValidatedMarketObservationV1(
        observation_id="obs-1",
        instrument_code="019172",
        observation_type="OFFICIAL_NAV",
        value=Decimal("1.2345"),
        as_of_date=date(2026, 9, 1),
        collected_at=datetime(2026, 9, 2, tzinfo=UTC),
        quality_status=QualityStatus.VALID,
        freshness_status=FreshnessStatus.FRESH,
    )

    assert observation.value == Decimal("1.2345")
    assert "estimated_units" not in ValidatedMarketObservationV1.model_fields
    assert "confirmed_units" not in ValidatedMarketObservationV1.model_fields


def test_all_approved_v1_contracts_have_fixed_identity() -> None:
    assert AccountImportEnvelopeV1.model_fields["contract_version"].default == "v1"
    assert ABCDailyTradableUniverseSnapshotV1.model_fields["contract_name"].default == (
        "ABCDailyTradableUniverseSnapshot"
    )
    assert DataQualityAlertV1.model_fields["contract_name"].default == "DataQualityAlert"
    assert ScheduleType.DAILY.value == "DAILY"
