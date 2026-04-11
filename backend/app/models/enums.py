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
