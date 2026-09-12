from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from asset_management.data_collection.domain.enums import (
    FreshnessStatus,
    PlanStatus,
    QualityStatus,
    ReconciliationStatus,
    ScheduleType,
)


def _reject_binary_float(value: object) -> object:
    if isinstance(value, float):
        raise TypeError("binary float is not allowed for financial values")
    return value


DecimalValue = Annotated[Decimal, BeforeValidator(_reject_binary_float)]
NonNegativeDecimal = Annotated[DecimalValue, Field(ge=0)]


class ContractBase(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ValidatedMarketObservationV1(ContractBase):
    contract_name: Literal["ValidatedMarketObservation"] = "ValidatedMarketObservation"
    contract_version: Literal["v1"] = "v1"
    observation_id: str
    instrument_code: str
    observation_type: str
    value: DecimalValue
    as_of_date: date
    collected_at: datetime
    quality_status: QualityStatus
    freshness_status: FreshnessStatus


class AccountImportEnvelopeV1(ContractBase):
    contract_name: Literal["AccountImportEnvelope"] = "AccountImportEnvelope"
    contract_version: Literal["v1"] = "v1"
    envelope_id: str
    source: str
    imported_at: datetime
    records: list[dict[str, object]] = Field(default_factory=list)


class InvestmentPlanSnapshotV1(ContractBase):
    contract_name: Literal["InvestmentPlanSnapshot"] = "InvestmentPlanSnapshot"
    contract_version: Literal["v1"] = "v1"
    snapshot_id: str
    instrument_code: str
    schedule_type: ScheduleType
    amount: NonNegativeDecimal
    status: PlanStatus
    effective_from: date
    effective_to: date | None = None


class MonthlyAccountAnchorV1(ContractBase):
    contract_name: Literal["MonthlyAccountAnchor"] = "MonthlyAccountAnchor"
    contract_version: Literal["v1"] = "v1"
    anchor_id: str
    instrument_code: str
    snapshot_as_of_date: date
    confirmed_at: datetime
    confirmed_units: NonNegativeDecimal
    account_value: NonNegativeDecimal
    pending_amount: NonNegativeDecimal | None = None
    pending_units: NonNegativeDecimal | None = None
    source: Literal["MANUAL_MONTHLY_CONFIRMATION"] = "MANUAL_MONTHLY_CONFIRMATION"
    quality_status: QualityStatus
    reconciliation_status: ReconciliationStatus


class ABCDailyTradableUniverseSnapshotV1(ContractBase):
    contract_name: Literal["ABCDailyTradableUniverseSnapshot"] = "ABCDailyTradableUniverseSnapshot"
    contract_version: Literal["v1"] = "v1"
    snapshot_id: str
    as_of_date: date
    entries: list[dict[str, object]] = Field(default_factory=list)


class CollectionRunStatusV1(ContractBase):
    contract_name: Literal["CollectionRunStatus"] = "CollectionRunStatus"
    contract_version: Literal["v1"] = "v1"
    run_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None


class DataQualityAlertV1(ContractBase):
    contract_name: Literal["DataQualityAlert"] = "DataQualityAlert"
    contract_version: Literal["v1"] = "v1"
    alert_id: str
    instrument_code: str
    quality_status: QualityStatus
    message: str
    created_at: datetime
