from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    LEADER = "LEADER"
    INTERN = "INTERN"


class LeaveType(str, Enum):
    UNIVERSITY = "UNIVERSITY"
    SICK = "SICK"
    PERSONAL = "PERSONAL"
    OTHER = "OTHER"


class LeaveStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class OnboardingStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class ProcessingStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
