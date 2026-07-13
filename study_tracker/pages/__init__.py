"""Import pages so @rx.page decorators register with the app."""

from study_tracker.pages import admin as admin
from study_tracker.pages import break_page as break_page
from study_tracker.pages import dashboard as dashboard
from study_tracker.pages import garden as garden
from study_tracker.pages import hours as hours
from study_tracker.pages import index as index
from study_tracker.pages import logbook as logbook
from study_tracker.pages import login as login
from study_tracker.pages import register as register
from study_tracker.pages import settings as settings
from study_tracker.pages import sticker as sticker
from study_tracker.pages import targets as targets
from study_tracker.pages import upgrade as upgrade

__all__ = [
    "admin",
    "break_page",
    "dashboard",
    "garden",
    "hours",
    "index",
    "logbook",
    "login",
    "register",
    "settings",
    "sticker",
    "targets",
    "upgrade",
]