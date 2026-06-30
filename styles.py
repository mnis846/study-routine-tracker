"""Shared mobile-first CSS for the Study Routine Tracker."""

MOBILE_CSS = """
<style>
    /* Touch-friendly controls */
    .stButton button {
        min-height: 2.75rem;
        font-size: 0.95rem;
        border-radius: 12px;
    }
    .stCheckbox label { min-height: 2.5rem; }
    div[data-testid="stFormSubmitButton"] button {
        min-height: 3rem;
        font-weight: 600;
    }

    /* App-like spacing */
    .block-container {
        padding-top: 1rem;
        max-width: 720px;
    }

    /* Scrollable tabs on narrow screens */
    div[data-testid="stTabs"] div[role="tablist"] {
        overflow-x: auto;
        overflow-y: hidden;
        flex-wrap: nowrap;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
    }
    div[data-testid="stTabs"] div[role="tablist"]::-webkit-scrollbar {
        display: none;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        white-space: nowrap;
        flex-shrink: 0;
    }

    /* Target cards */
    .target-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.65rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .target-card-done { background: #F0FFF4; border-color: #C6F6D5; }
    .target-card-skipped { background: #F7FAFC; border-color: #E2E8F0; opacity: 0.9; }
    .target-card-text {
        font-size: 1rem;
        line-height: 1.45;
        color: #2D3748;
        margin: 0.35rem 0 0.5rem 0;
        word-break: break-word;
    }

    /* Compact header chips */
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-bottom: 0.75rem;
    }

    /* Quick stats row */
    .quick-stat {
        background: #F7FAFC;
        border-radius: 12px;
        padding: 0.65rem 0.5rem;
        text-align: center;
    }
    .quick-stat-label {
        font-size: 0.72rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .quick-stat-value {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1E3A5F;
    }

    @media (max-width: 768px) {
        .main-header { font-size: 1.35rem !important; }
        .date-time { font-size: 0.88rem !important; }
        .stat-chip {
            font-size: 0.72rem;
            padding: 0.18rem 0.55rem;
            margin-right: 0;
        }
        .block-container {
            padding-left: 0.65rem !important;
            padding-right: 0.65rem !important;
            padding-top: 0.75rem !important;
        }
        .next-test-card {
            padding: 1rem !important;
        }
        .next-test-card .test-title {
            font-size: 1.1rem !important;
        }
        .next-test-card .test-date {
            font-size: 0.88rem !important;
            line-height: 1.4;
        }
        div[data-testid="stTabs"] button[role="tab"] {
            font-size: 0.78rem;
            padding: 0.45rem 0.55rem;
        }
        .garden-compact {
            flex-direction: column;
            text-align: center;
            padding: 0.85rem !important;
        }
        .garden-compact-tree {
            width: 120px;
            margin: 0 auto;
        }
        .garden-hero {
            flex-direction: column;
            text-align: center;
            padding: 1rem !important;
            gap: 0.75rem !important;
        }
        .garden-visual {
            width: 160px;
            margin: 0 auto;
        }
        .garden-stage-title { font-size: 1.2rem !important; }
        .badge { font-size: 0.72rem; }
        section[data-testid="stSidebar"] {
            min-width: 16rem;
        }
    }

    @media (max-width: 480px) {
        .main-header { font-size: 1.2rem !important; }
        .quick-stat-value { font-size: 1rem; }
        .target-card { padding: 0.75rem 0.85rem; }
    }
</style>
"""