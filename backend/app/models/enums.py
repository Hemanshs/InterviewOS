import enum


class PlanEnum(str, enum.Enum):
    free = "free"
    pro = "pro"
    team = "team"


class SessionStatusEnum(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"
    expired = "expired"
