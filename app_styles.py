"""Desktop dashboard CSS for the Study Routine Tracker."""

APP_CSS = """
<style>
    /* Full-width layout on larger screens */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Hero banner */
    .app-hero {
        background: linear-gradient(135deg, #1E3A5F 0%, #2C5282 55%, #3182CE 100%);
        border-radius: 16px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        color: #FFFFFF;
        box-shadow: 0 8px 24px rgba(30, 58, 95, 0.18);
    }
    .app-hero-title {
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.02em;
    }
    .app-hero-greeting {
        font-size: 1.2rem;
        font-weight: 600;
        margin: 0 0 0.25rem 0;
        opacity: 0.95;
    }
    .app-hero-motto {
        font-size: 0.95rem;
        margin: 0 0 0.75rem 0;
        opacity: 0.8;
        font-style: italic;
    }
    .app-hero-meta {
        font-size: 0.9rem;
        opacity: 0.75;
    }

    /* Stat cards row */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.8rem !important;
        color: #718096 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        color: #1E3A5F !important;
    }

    /* Tabs */
    div[data-testid="stTabs"] div[role="tablist"] {
        gap: 0.5rem;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.25rem;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        font-size: 1rem;
        font-weight: 600;
        padding: 0.6rem 1.25rem;
        border-radius: 8px 8px 0 0;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: #EBF8FF;
        color: #1E40AF;
    }

    /* Target list */
    .target-card-text {
        font-size: 1rem;
        line-height: 1.5;
        color: #2D3748;
        margin: 0;
    }

    /* Chips (period badge) */
    .chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }
    .period-badge {
        display: inline-block;
        padding: 0.3rem 0.85rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .morning-badge { background: rgba(254, 243, 199, 0.9); color: #92400E; }
    .afternoon-badge { background: rgba(219, 234, 254, 0.9); color: #1E40AF; }
    .evening-badge { background: rgba(237, 233, 254, 0.9); color: #5B21B6; }

    /* Next test card */
    .next-test-card {
        background: linear-gradient(135deg, #1E3A5F 0%, #2C5282 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 16px rgba(30, 58, 95, 0.2);
    }
    .next-test-card h3 { margin: 0 0 0.5rem 0; font-size: 1rem; opacity: 0.85; text-transform: uppercase; letter-spacing: 0.05em; }
    .next-test-card .test-title { font-size: 1.5rem; font-weight: 600; margin: 0; }
    .next-test-card .test-date { font-size: 1rem; opacity: 0.85; margin-top: 0.35rem; }

    .target-done { text-decoration: line-through; color: #718096; }
    .target-skipped { color: #A0AEC0; font-style: italic; }
    .stProgress > div > div > div > div { background-color: #48BB78; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #F7FAFC;
        border-right: 1px solid #E2E8F0;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }

    /* Buttons */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
    }

    @media (max-width: 768px) {
        .app-hero {
            padding: 1.25rem 1.25rem;
        }
        .app-hero-title {
            font-size: 1.5rem;
        }
        .app-hero-greeting {
            font-size: 1rem;
        }
        .block-container {
            max-width: 720px;
        }
    }
</style>
"""