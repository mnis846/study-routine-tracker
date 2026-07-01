"""Login and open signup for Study Routine Tracker."""

import streamlit as st
import streamlit_authenticator as stauth

from database import (
    DatabaseError,
    get_user_credentials_dict,
    get_user_id_by_username,
    save_registered_user,
    set_current_user,
)


def _auth_secrets():
    try:
        return dict(st.secrets["auth"])
    except (KeyError, FileNotFoundError, AttributeError, TypeError):
        return {
            "cookie_name": "study_tracker_auth",
            "cookie_key": "dev_only_change_in_streamlit_secrets",
            "cookie_expiry_days": 30,
        }


def render_auth_gate():
    """
    Show login / signup until the user is authenticated.
    Returns the authenticator instance for logout handling.
    """
    credentials = get_user_credentials_dict()
    cfg = _auth_secrets()
    authenticator = stauth.Authenticate(
        credentials,
        cfg["cookie_name"],
        cfg["cookie_key"],
        float(cfg.get("cookie_expiry_days", 30)),
        auto_hash=False,
    )

    st.markdown("## 📚 Study Tracker")
    st.caption("Log in or create a free account. Your data stays private to you.")

    login_tab, register_tab = st.tabs(["Log in", "Sign up"])

    with login_tab:
        try:
            authenticator.login(location="main", key="study_login")
        except Exception as exc:
            st.error(str(exc))

    with register_tab:
        try:
            email, username, name = authenticator.register_user(
                location="main",
                key="study_register",
                captcha=False,
            )
            if email and username:
                try:
                    save_registered_user(username, email, name, credentials)
                    st.success("Account created! Switch to **Log in** and sign in.")
                except DatabaseError as exc:
                    st.error(f"Could not save account: {exc}")
        except Exception as exc:
            st.error(str(exc))

    status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")

    if status:
        user_id = get_user_id_by_username(username)
        set_current_user(user_id)
        st.session_state["user_id"] = user_id
        return authenticator

    if status is False:
        st.error("Invalid username or password.")
    else:
        st.info("Please log in or sign up to continue.")
    st.stop()