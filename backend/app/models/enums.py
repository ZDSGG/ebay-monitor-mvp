from enum import Enum


class Marketplace(str, Enum):
    EBAY_US = "EBAY_US"
    EBAY_UK = "EBAY_UK"
    EBAY_DE = "EBAY_DE"
    EBAY_AU = "EBAY_AU"


class ItemStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class EventType(str, Enum):
    NO_CHANGE = "NO_CHANGE"
    PRICE_DROP = "PRICE_DROP"
    PRICE_RISE = "PRICE_RISE"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ShopStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ListingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    MUTED = "MUTED"


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AlertRuleType(str, Enum):
    NEW_LISTING_SPIKE = "NEW_LISTING_SPIKE"
    DELISTED_SPIKE = "DELISTED_SPIKE"
    PRICE_DROP_SPIKE = "PRICE_DROP_SPIKE"
    ACTIVE_LISTING_DROP = "ACTIVE_LISTING_DROP"
