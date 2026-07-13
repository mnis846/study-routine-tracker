"""
Experimental Streamlit-in-WebView launcher for Android (Buildozer).

NOTE: Streamlit + pandas + plotly is very heavy for python-for-android and
often fails to build. Prefer the Flet mobile app (mobile/main.py) and
scripts/build_apk.ps1 for a reliable standalone APK on Windows.

This wrapper starts a local Streamlit server and opens it in an Android WebView.
Build on Linux/WSL with: docker compose -f android/docker-compose.yml run buildozer
"""

import os
import sys
import threading
import time
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STREAMLIT_HOST = "127.0.0.1"
STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://{STREAMLIT_HOST}:{STREAMLIT_PORT}"


def _configure_storage():
    try:
        from android.storage import app_storage_path

        os.environ["TRACKER_DATA_DIR"] = app_storage_path()
    except ImportError:
        os.environ.setdefault("TRACKER_DATA_DIR", str(ROOT))


def _start_streamlit():
    _configure_storage()
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_SERVER_PORT", str(STREAMLIT_PORT))
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", STREAMLIT_HOST)
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")

    from streamlit.web import bootstrap

    bootstrap.run(
        str(ROOT / "app.py"),
        "",
        [],
        flag_options={
            "server.headless": True,
            "server.port": STREAMLIT_PORT,
            "server.address": STREAMLIT_HOST,
            "browser.gatherUsageStats": False,
            "global.developmentMode": False,
        },
    )


class StreamlitWebViewApp(App):
    def build(self):
        self.browser = None
        self.status = Label(
            text="Starting Study Routine Tracker...",
            halign="center",
            valign="middle",
        )
        root = BoxLayout(orientation="vertical", padding=24, spacing=12)
        root.add_widget(self.status)
        threading.Thread(target=_start_streamlit, daemon=True).start()
        Clock.schedule_once(self._open_webview, 4)
        return root

    def _open_webview(self, _dt):
        try:
            from webview import WebView

            self.status.text = "Opening app..."
            self.browser = WebView(
                STREAMLIT_URL,
                enable_javascript=True,
                enable_zoom=True,
            )
            self.status.opacity = 0
        except Exception as exc:
            self.status.text = f"Could not open WebView: {exc}"

    def on_pause(self):
        if self.browser:
            self.browser.pause()
        return True

    def on_resume(self):
        if self.browser:
            self.browser.resume()


if __name__ == "__main__":
    StreamlitWebViewApp().run()