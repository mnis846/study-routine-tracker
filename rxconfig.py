import reflex as rx

from study_tracker.core.config import DATABASE_URL

tailwind_config = {
    "theme": {
        "extend": {
            "fontFamily": {
                "sans": ["Inter", "Segoe UI", "system-ui", "sans-serif"],
            },
        },
    },
}

config = rx.Config(
    app_name="study_tracker",
    db_url=DATABASE_URL,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(tailwind_config),
    ],
)