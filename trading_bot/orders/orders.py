"""Order structure validation models for PrimeTrade AI.

Ensures that order structures align with Binance exchange specifications
before transmission, avoiding unnecessary API rejections.
"""

from pydantic import BaseModel, Field, field_validator, model_validator

from config.enums import OrderType, TradingSide


class FuturesOrder(BaseModel):
    """Pydantic validation model representing a Binance Futures Order."""

    symbol: str = Field(..., description="Target asset ticker symbol (e.g. 'BTCUSDT').")
    side: TradingSide = Field(..., description="Execution direction (BUY or SELL).")
    type: OrderType = Field(..., description="Binance Futures order execution format.")
    quantity: float = Field(..., gt=0.0, description="Order sizing unit count.")
    price: float | None = Field(default=None, gt=0.0, description="Limit execution price.")
    stop_price: float | None = Field(default=None, gt=0.0, description="Stop trigger price.")
    time_in_force: str = Field(default="GTC", description="Time-in-force option (GTC, IOC, FOK).")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, val: str) -> str:
        """Standardizes and checks ticker format."""
        cleaned = val.strip().upper()
        if not cleaned:
            raise ValueError("Symbol must be a non-empty string.")
        return cleaned

    @field_validator("time_in_force")
    @classmethod
    def validate_tif(cls, val: str) -> str:
        """Ensures time-in-force is a valid option."""
        allowed = {"GTC", "IOC", "FOK"}
        cleaned = val.strip().upper()
        if cleaned not in allowed:
            raise ValueError(f"Invalid time_in_force '{val}'. Must be one of {allowed}")
        return cleaned

    @model_validator(mode="after")
    def validate_pricing_parameters(self) -> "FuturesOrder":
        """Ensures required prices are provided depending on the OrderType."""
        order_type = self.type
        price = self.price
        stop_price = self.stop_price

        if order_type == OrderType.LIMIT:
            if price is None:
                raise ValueError("LIMIT orders require 'price' parameter to be specified.")

        elif order_type == OrderType.STOP_LIMIT:
            if price is None:
                raise ValueError("STOP_LIMIT orders require 'price' parameter to be specified.")
            if stop_price is None:
                raise ValueError("STOP_LIMIT orders require 'stop_price' parameter to be specified.")

        return self
