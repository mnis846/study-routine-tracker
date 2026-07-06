"""SQLModel tables for multi-user study tracking."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    STUDENT = "student"
    COACH = "coach"
    ADMIN = "admin"


class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ACADEMY = "academy"


class Institute(SQLModel, table=True):
    """Coaching institute / academy tenant."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    slug: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    users: list["User"] = Relationship(back_populates="institute")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    first_name: str = ""
    last_name: str = ""
    password_hash: str
    role: str = UserRole.STUDENT.value
    subscription_tier: str = SubscriptionTier.FREE.value
    institute_id: Optional[int] = Field(default=None, foreign_key="institute.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    institute: Optional[Institute] = Relationship(back_populates="users")
    settings: list["AppSetting"] = Relationship(back_populates="user")


class DailyPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    plan_date: date
    evening_reflection: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    items: list["DailyTargetItem"] = Relationship(back_populates="plan")


class DailyTargetItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="dailyplan.id")
    description: str
    planned_hours: float = 0.0
    order_index: int = 0
    status: str = "Pending"
    actual_hours: float = 0.0
    completion_notes: str = ""

    plan: Optional[DailyPlan] = Relationship(back_populates="items")


class DailyStudyHours(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    log_date: date
    hours: float = 0.0
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScheduledTest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    test_no: int
    level: str = ""
    test_type: str = ""
    subject: str = ""
    scheduled_date: Optional[date] = None
    topic_focus: str = ""
    status: str = "Not Attempted"
    hours_studied: float = 0.0
    score: Optional[float] = None
    remarks: str = ""
    attempt_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AppSetting(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    key: str = Field(primary_key=True)
    value: str

    user: Optional[User] = Relationship(back_populates="settings")


class GardenEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    event_date: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    xp_amount: int
    message: str


class StudyActivityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    log_date: date
    subject: str = ""
    activity: str
    duration_hours: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)