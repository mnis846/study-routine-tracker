"""Shared mobile / tablet CSS for the Study Routine Tracker."""

MOBILE_CSS = """
<style>
    /* ---- Base touch-friendly controls ---- */
    .stButton button {
        min-height: 2.85rem;
        font-size: 0.95rem;
        border-radius: 12px;
        touch-action: manipulation;
        -webkit-tap-highlight-color: transparent;
    }
    .stCheckbox label { min-height: 2.5rem; }
    div[data-testid="stFormSubmitButton"] button {
        min-height: 3rem;
        font-weight: 600;
    }

    /* 16px inputs prevent Android Chrome auto-zoom on focus */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stSelectbox [data-baseweb="select"],
    .stDateInput input {
        font-size: 16px !important;
    }

    /* Scrollable tabs (phone + tablet) */
    div[data-testid="stTabs"] div[role="tablist"] {
        overflow-x: auto;
        overflow-y: hidden;
        flex-wrap: nowrap;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        gap: 0.2rem;
    }
    div[data-testid="stTabs"] div[role="tablist"]::-webkit-scrollbar {
        display: none;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        white-space: nowrap;
        flex-shrink: 0;
        min-height: 2.6rem;
        touch-action: manipulation;
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

    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-bottom: 0.75rem;
    }

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

    /* Safe area for notched Android / tablets */
    .block-container {
        padding-left: max(0.75rem, env(safe-area-inset-left, 0px)) !important;
        padding-right: max(0.75rem, env(safe-area-inset-right, 0px)) !important;
        padding-bottom: max(1.5rem, env(safe-area-inset-bottom, 0px)) !important;
    }

    /* Heatmap: always horizontal-scroll friendly */
    .showup-weeks-col,
    .gh-graph,
    .gh-wrap {
        -webkit-overflow-scrolling: touch;
        max-width: 100%;
    }
    .gh-cell {
        transition: transform 0.1s ease;
    }

    /* iframe embeds (garden / games) */
    iframe {
        max-width: 100% !important;
        border: none;
    }

    /* ---- Tablet & phone (portrait or narrow) ---- */
    @media (max-width: 1024px) {
        .block-container {
            padding-top: 0.85rem !important;
            max-width: 100% !important;
        }

        .app-hero {
            padding: 1.05rem 1.15rem !important;
            border-radius: 14px !important;
        }
        .app-hero-title { font-size: 1.25rem !important; }
        .app-hero-greeting { font-size: 0.92rem !important; }
        .app-hero-motto { font-size: 0.82rem !important; }

        .main-header { font-size: 1.35rem !important; }
        .date-time { font-size: 0.88rem !important; }

        div[data-testid="stMetric"] {
            padding: 0.55rem 0.7rem !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.15rem !important;
        }

        div[data-testid="stTabs"] button[role="tab"] {
            font-size: 0.8rem;
            padding: 0.45rem 0.65rem;
        }

        /* Soft wrap for wide metric/button rows; compact rows stay readable */
        div[data-testid="stHorizontalBlock"] {
            gap: 0.45rem !important;
        }

        .next-test-card {
            padding: 1rem !important;
        }
        .next-test-card .test-title {
            font-size: 1.1rem !important;
        }

        .garden-compact,
        .garden-hero {
            flex-direction: column;
            text-align: center;
            padding: 0.9rem !important;
            gap: 0.75rem !important;
        }
        .garden-compact-tree,
        .garden-visual {
            width: 140px;
            margin: 0 auto;
        }
        .garden-stage-title { font-size: 1.2rem !important; }
        .badge { font-size: 0.72rem; }

        section[data-testid="stSidebar"] {
            min-width: 16rem;
        }

        /* Plotly: allow touch pan/zoom without page scroll fight */
        .js-plotly-plot .plotly {
            touch-action: pan-y;
        }

        .coach-card {
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
    }

    /* ---- Phones ---- */
    @media (max-width: 640px) {
        .main-header { font-size: 1.2rem !important; }
        .quick-stat-value { font-size: 1rem; }
        .target-card { padding: 0.75rem 0.85rem; }
        .app-hero-title { font-size: 1.15rem !important; }

        div[data-testid="stTabs"] button[role="tab"] {
            font-size: 0.74rem;
            padding: 0.4rem 0.5rem;
        }

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.05rem !important;
        }
    }

    /* Prefer reduced motion on low-power tablets */
    @media (prefers-reduced-motion: reduce) {
        .stButton > button,
        .gh-cell {
            transition: none !important;
        }
    }
</style>
"""
