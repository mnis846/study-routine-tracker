"""Authentication helpers (currently disabled).

The Streamlit app uses a single local SQLite profile instead of login/signup.
See database.ensure_local_user() and database.get_db_path().
"""

from database import ensure_local_user, get_local_display_name


def render_auth_gate():
    """
    No-op compatibility shim.

    Previously showed login/signup. Now ensures the local profile exists and
    returns None (no authenticator object).
    """
    ensure_local_user()
    return None


def current_display_name() -> str:
    return get_local_display_name()
