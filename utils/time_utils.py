"""Generic datetime utility helpers for PrimeTrade AI.

Provides standard converters between UNIX timestamps, string dates, and timezone-naive
Pandas/Python datetimes.
"""

from datetime import datetime, timezone
from typing import Union
import pandas as pd


def parse_timestamp_to_datetime(ts: Union[int, float, str]) -> datetime:
    """Standardizes unix seconds, unix milliseconds, or ISO strings to a datetime.

    All returned datetime objects are timezone-naive (local/UTC raw values) to prevent
    lookahead merging alignment issues in pandas.

    Args:
        ts: Input timestamp (int/float UNIX timestamp or string representation).

    Returns:
        Timezone-naive datetime object.
    """
    if isinstance(ts, (int, float)):
        # Check if in milliseconds (standard Binance format has 13 digits, e.g. 1600000000000)
        if ts > 1e11:
            dt = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
        else:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    else:
        # String parsing
        try:
            # First try pandas parser which handles most ISO/excel formats
            dt = pd.to_datetime(ts).to_pydatetime()
        except Exception:
            # Fallback to standard ISO parser
            dt = datetime.fromisoformat(str(ts))

    # Strip timezone information to make it timezone-naive
    return dt.replace(tzinfo=None)


def format_datetime_to_string(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Formats a datetime object to a string format.

    Args:
        dt: The datetime object.
        fmt: Output string format.

    Returns:
        Formatted datetime string.
    """
    return dt.strftime(fmt)


def get_current_utc_timestamp() -> float:
    """Returns the current UTC UNIX timestamp in seconds.

    Returns:
        Current UNIX epoch timestamp (seconds).
    """
    return datetime.now(timezone.utc).timestamp()


def get_current_utc_datetime() -> datetime:
    """Returns the current timezone-naive UTC datetime.

    Returns:
        Timezone-naive datetime object representing current UTC time.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
