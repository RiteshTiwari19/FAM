from datetime import date
from decimal import Decimal
from sqlmodel import SQLModel, Field, UniqueConstraint
from typing import Optional


class FundNavBase(SQLModel):
    fund_code: str | None
    fund_currency: str | None
    share_code: str | None
    share_type: str | None
    isin_code: str | None
    share_currency: str | None
    nav_date: date | None
    price_in_share_currency: Decimal | None = Field(decimal_places=8)
    fx_rate: str | None
    price_in_fund: Decimal | None = Field(decimal_places=8)
    number_of_outstanding_shares: Decimal | None = Field(decimal_places=5)
    tna_share_in_share_currency: Decimal | None = Field(decimal_places=5)
    tna_share_in_fund_currency: Decimal | None = Field(decimal_places=5)
    fx_rate_date: date | None


class FundNav(FundNavBase, table=True):
    __tablename__ = "fund_nav"
    __table_args__ = (
        UniqueConstraint("fund_code", "nav_date", "share_code", "share_type",
                         name="fund_nav_uniq_ctx"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)


class FundNavDaily(FundNavBase, table=True):
    __tablename__ = "fund_nav_daily"
    __table_args__ = (
        UniqueConstraint("fund_code", "nav_date", "share_code", "share_type",
                         name="fund_nav_daily_uniq_ctx"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)

    as_of_date: Decimal | None = Field(decimal_places=8)
