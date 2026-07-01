"""Free vs Pro tier limits and manual unlock (Razorpay payment link + codes)."""

from datetime import datetime

import streamlit as st

from database import get_setting, set_setting
from garden import GARDEN_STAGES

FREE_MAX_TARGETS = 3
FREE_GARDEN_MAX_STAGE = 3  # stages 0–3 (Seed → Young Sapling)
PRO_SETTING_KEY = "pro_unlocked"
PRO_UNLOCKED_AT_KEY = "pro_unlocked_at"

DEFAULT_PRICE_INR = 499
DEFAULT_PAYMENT_LINK = ""
DEFAULT_SUPPORT_EMAIL = ""


def _pro_config():
    try:
        cfg = st.secrets.get("pro", {})
    except (FileNotFoundError, AttributeError, KeyError, TypeError):
        cfg = {}
    return {
        "payment_link": cfg.get("payment_link", DEFAULT_PAYMENT_LINK),
        "price_inr": int(cfg.get("price_inr", DEFAULT_PRICE_INR)),
        "unlock_codes": [str(c).strip().upper() for c in cfg.get("unlock_codes", [])],
        "support_email": cfg.get("support_email", DEFAULT_SUPPORT_EMAIL),
        "support_whatsapp": cfg.get("support_whatsapp", ""),
    }


def is_pro():
    return get_setting(PRO_SETTING_KEY, "0") == "1"


def unlock_with_code(code):
    """Validate unlock code and enable Pro in local settings. Returns (ok, message)."""
    normalized = (code or "").strip().upper()
    if not normalized:
        return False, "Enter your Pro unlock code."

    if is_pro():
        return True, "Pro is already active on this device."

    valid_codes = _pro_config()["unlock_codes"]
    if not valid_codes:
        return (
            False,
            "Unlock codes are not configured yet. Contact support after payment.",
        )

    if normalized not in valid_codes:
        return False, "Invalid code. Check the code from your payment confirmation."

    set_setting(PRO_SETTING_KEY, "1")
    set_setting(PRO_UNLOCKED_AT_KEY, datetime.now().isoformat(timespec="seconds"))
    return True, "Pro unlocked! Enjoy unlimited targets, full test series, and more."


def free_target_cap_reached(count):
    return not is_pro() and count > FREE_MAX_TARGETS


def effective_garden_stage_index(xp):
    """Cap visible garden stage for free users; XP still accumulates."""
    from garden import get_stage_info

    info = get_stage_info(xp)
    if is_pro():
        return info
    capped_idx = min(info["index"], FREE_GARDEN_MAX_STAGE)
    if capped_idx == info["index"]:
        return info
    current = GARDEN_STAGES[capped_idx]
    next_stage = GARDEN_STAGES[capped_idx + 1] if capped_idx + 1 < len(GARDEN_STAGES) else None
    if next_stage:
        span = next_stage["min_xp"] - current["min_xp"]
        progress = (xp - current["min_xp"]) / span if span else 1.0
        xp_to_next = next_stage["min_xp"] - xp
    else:
        progress = 1.0
        xp_to_next = 0
    return {
        "index": capped_idx,
        "current": current,
        "next": next_stage,
        "progress": min(max(progress, 0.0), 1.0),
        "xp_to_next": max(xp_to_next, 0),
        "is_max": False,
        "free_capped": True,
    }


def pro_feature_label(feature):
    labels = {
        "targets": "Unlimited daily targets",
        "tests": "Full test series + score tracking",
        "garden": "All 10 garden evolution stages",
        "export": "CSV data export",
        "analytics": "Extended analytics & longest streak",
    }
    return labels.get(feature, "Pro feature")


def render_upgrade_cta(feature=None, compact=False):
    cfg = _pro_config()
    price = cfg["price_inr"]
    link = cfg["payment_link"]
    feature_line = ""
    if feature:
        feature_line = f" Unlock **{pro_feature_label(feature)}** and more."

    if compact:
        st.caption(f"⭐ Pro — one-time ₹{price}{' · ' + feature_line if feature_line else ''}")
    else:
        st.info(
            f"**Pro unlock — ₹{price} one-time**{feature_line}\n\n"
            "Pay via Razorpay, then enter your unlock code below (sent after payment confirmation)."
        )

    if link:
        st.link_button(f"Pay ₹{price} — Get Pro", link, type="primary", width="stretch")
    else:
        st.caption(
            "Payment link: add `pro.payment_link` in `.streamlit/secrets.toml` "
            "after creating your Razorpay Payment Link."
        )

    support_bits = []
    if cfg["support_email"]:
        support_bits.append(f"Email: {cfg['support_email']}")
    if cfg["support_whatsapp"]:
        support_bits.append(f"WhatsApp: {cfg['support_whatsapp']}")
    if support_bits:
        st.caption("After paying, send payment screenshot to " + " · ".join(support_bits))


def render_pro_unlock_panel():
    cfg = _pro_config()
    if is_pro():
        unlocked_at = get_setting(PRO_UNLOCKED_AT_KEY, "")
        when = f" (since {unlocked_at[:10]})" if unlocked_at else ""
        st.success(f"⭐ Pro is active{when}")
        return

    st.markdown("**Upgrade to Pro**")
    st.caption(
        f"One-time ₹{cfg['price_inr']} — unlimited targets, full test series, "
        "complete garden, CSV export."
    )
    render_upgrade_cta()

    st.markdown("**Already paid? Enter unlock code**")
    code = st.text_input(
        "Pro unlock code",
        placeholder="e.g. STUDY-XXXX",
        key="pro_unlock_code_input",
        label_visibility="collapsed",
    )
    if st.button("Activate Pro", key="activate_pro_btn", width="stretch"):
        ok, message = unlock_with_code(code)
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)