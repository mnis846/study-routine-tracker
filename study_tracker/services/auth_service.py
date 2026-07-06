"""Authentication and user provisioning."""

from __future__ import annotations

import bcrypt
from sqlmodel import select

from study_tracker.db import get_session

from study_tracker.core.config import (
    ADMIN_BOOTSTRAP_EMAIL,
    ADMIN_BOOTSTRAP_PASSWORD,
)
from study_tracker.models import (
    Institute,
    SubscriptionTier,
    User,
    UserRole,
)
from study_tracker.core.tiers import is_pro_tier
from study_tracker.services.seed_service import seed_user_defaults


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def bootstrap_admin() -> None:
    """Create default institute and admin user on first run."""
    with get_session() as session:
        admin = session.exec(
            select(User).where(User.email == ADMIN_BOOTSTRAP_EMAIL)
        ).first()
        if admin:
            return

        institute = session.exec(
            select(Institute).where(Institute.slug == "default-academy")
        ).first()
        if not institute:
            institute = Institute(name="Default Academy", slug="default-academy")
            session.add(institute)
            session.commit()
            session.refresh(institute)

        admin = User(
            username="admin",
            email=ADMIN_BOOTSTRAP_EMAIL,
            first_name="Admin",
            last_name="User",
            password_hash=hash_password(ADMIN_BOOTSTRAP_PASSWORD),
            role=UserRole.ADMIN.value,
            subscription_tier=SubscriptionTier.ACADEMY.value,
            institute_id=institute.id,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        seed_user_defaults(admin.id)


def register_user(
    username: str,
    email: str,
    password: str,
    first_name: str = "",
    role: str = UserRole.STUDENT.value,
    tier: str = SubscriptionTier.FREE.value,
    institute_id: int | None = None,
) -> tuple[bool, str]:
    username = username.strip().lower()
    email = email.strip().lower()
    if not username or not email or not password:
        return False, "All fields are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    with get_session() as session:
        if session.exec(select(User).where(User.username == username)).first():
            return False, "Username already taken."
        if session.exec(select(User).where(User.email == email)).first():
            return False, "Email already registered."

        user = User(
            username=username,
            email=email,
            first_name=first_name or username,
            password_hash=hash_password(password),
            role=role,
            subscription_tier=tier,
            institute_id=institute_id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        seed_user_defaults(user.id)
    return True, "Account created. You can log in now."


def authenticate(username: str, password: str) -> dict | None:
    username = username.strip().lower()
    with get_session() as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if user and verify_password(password, user.password_hash):
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "role": user.role,
                "subscription_tier": user.subscription_tier,
                "institute_id": user.institute_id,
            }
    return None


def get_user_by_id(user_id: int) -> User | None:
    with get_session() as session:
        return session.get(User, user_id)


def get_user_session(user_id: int) -> dict | None:
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "role": user.role,
            "subscription_tier": user.subscription_tier,
            "institute_id": user.institute_id,
        }


def list_institute_users(institute_id: int) -> list[User]:
    with get_session() as session:
        return list(
            session.exec(select(User).where(User.institute_id == institute_id)).all()
        )


def update_user_tier(user_id: int, tier: str) -> None:
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            user.subscription_tier = tier
            session.add(user)
            session.commit()


