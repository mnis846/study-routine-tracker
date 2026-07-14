"""Desktop dashboard CSS — minimal layout, soft colour accents."""

APP_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    :root {
        --bg: #f0f4ff;
        --surface: #ffffff;
        --text: #1e293b;
        --muted: #64748b;
        --border: #e2e8f0;
        --teal: #14b8a6;
        --teal-soft: #ccfbf1;
        --violet: #8b5cf6;
        --violet-soft: #ede9fe;
        --coral: #fb7185;
        --coral-soft: #ffe4e6;
        --sky: #38bdf8;
        --sky-soft: #e0f2fe;
        --amber: #fbbf24;
        --amber-soft: #fef3c7;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
        color: var(--text);
    }

    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #f0f4ff 0%, #faf5ff 50%, #f0fdfa 100%) !important;
        background-attachment: fixed !important;
    }

    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        max-width: 980px;
    }

    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer, .stDeployButton { visibility: hidden; height: 0; }

    /* Hero — soft colour wash */
    .app-hero {
        background: linear-gradient(120deg, #0d9488 0%, #6366f1 55%, #a855f7 100%);
        border-radius: 16px;
        padding: 1.35rem 1.6rem;
        margin-bottom: 1.1rem;
        color: #ffffff;
        box-shadow: 0 10px 40px rgba(99, 102, 241, 0.22);
    }
    .app-hero-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.02em;
    }
    .app-hero-greeting {
        font-size: 0.95rem;
        font-weight: 500;
        margin: 0 0 0.15rem 0;
        opacity: 0.92;
    }
    .app-hero-motto {
        font-size: 0.85rem;
        margin: 0 0 0.55rem 0;
        opacity: 0.8;
    }
    .app-hero-meta { font-size: 0.8rem; opacity: 0.75; }

    /* Metrics — tinted cards */
    div[data-testid="column"]:nth-child(1) div[data-testid="stMetric"] {
        border-left: 3px solid var(--coral);
        background: linear-gradient(135deg, #fff 70%, var(--coral-soft));
    }
    div[data-testid="column"]:nth-child(2) div[data-testid="stMetric"] {
        border-left: 3px solid var(--sky);
        background: linear-gradient(135deg, #fff 70%, var(--sky-soft));
    }
    div[data-testid="column"]:nth-child(3) div[data-testid="stMetric"] {
        border-left: 3px solid var(--teal);
        background: linear-gradient(135deg, #fff 70%, var(--teal-soft));
    }
    div[data-testid="column"]:nth-child(4) div[data-testid="stMetric"] {
        border-left: 3px solid var(--violet);
        background: linear-gradient(135deg, #fff 70%, var(--violet-soft));
    }
    div[data-testid="stMetric"] {
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.7rem 0.9rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.68rem !important;
        color: var(--muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        color: var(--text) !important;
        font-weight: 700 !important;
    }

    /* Tabs */
    div[data-testid="stTabs"] div[role="tablist"] {
        gap: 0.25rem;
        background: rgba(255,255,255,0.7);
        border-radius: 12px;
        padding: 0.3rem;
        border: 1px solid var(--border);
        backdrop-filter: blur(8px);
    }
    div[data-testid="stTabs"] button[role="tab"] {
        font-size: 0.86rem;
        font-weight: 600;
        padding: 0.5rem 0.9rem;
        border-radius: 8px;
        color: var(--muted);
        border: none;
        background: transparent;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #fff;
        background: linear-gradient(135deg, var(--teal), #6366f1);
        box-shadow: 0 2px 10px rgba(20, 184, 166, 0.3);
    }

    .section-label {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--teal);
        font-weight: 700;
        margin-bottom: 0.15rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text);
        margin: 0 0 0.6rem 0;
    }

    .target-card-text {
        font-size: 0.92rem;
        line-height: 1.5;
        color: var(--text);
        margin: 0;
    }
    .target-done { text-decoration: line-through; color: var(--muted); }
    .target-skipped { color: #94a3b8; font-style: italic; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border-color: var(--border) !important;
        background: var(--surface);
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
    }

    .period-badge {
        display: inline-block;
        padding: 0.22rem 0.65rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .morning-badge { background: var(--amber-soft); color: #b45309; }
    .afternoon-badge { background: var(--sky-soft); color: #0369a1; }
    .evening-badge { background: var(--violet-soft); color: #6d28d9; }

    .next-test-card {
        background: linear-gradient(135deg, #1e293b 0%, #4f46e5 100%);
        color: #fff;
        padding: 1.15rem 1.35rem;
        border-radius: 14px;
        margin-bottom: 0.75rem;
        box-shadow: 0 8px 24px rgba(79, 70, 229, 0.2);
    }
    .next-test-card h3 {
        margin: 0 0 0.3rem 0;
        font-size: 0.68rem;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .next-test-card .test-title { font-size: 1.15rem; font-weight: 700; margin: 0; }
    .next-test-card .test-date { font-size: 0.85rem; opacity: 0.85; margin-top: 0.25rem; }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--teal), #6366f1);
        border-radius: 999px;
    }

    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.85);
        border-right: 1px solid var(--border);
        backdrop-filter: blur(8px);
    }
    section[data-testid="stSidebar"] h3 {
        color: var(--text) !important;
        font-weight: 700 !important;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--text);
        transition: transform 0.1s ease, box-shadow 0.15s ease;
    }
    .stButton > button:hover {
        border-color: var(--teal);
        box-shadow: 0 2px 8px rgba(20, 184, 166, 0.15);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--teal), #6366f1);
        border: none;
        color: #fff;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        border-radius: 10px !important;
        border-color: var(--border) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 2px var(--teal-soft) !important;
    }

    .stForm {
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        background: var(--surface);
    }

    .log-entry {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 3px solid var(--violet);
        border-radius: 10px;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.4rem;
    }
    .log-entry-meta { font-size: 0.75rem; color: var(--muted); font-weight: 600; margin-bottom: 0.2rem; }
    .log-entry-body { font-size: 0.9rem; color: var(--text); line-height: 1.45; white-space: pre-wrap; }

    /* Star Wars study coach */
    .coach-card {
        display: flex;
        gap: 1rem;
        align-items: flex-start;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        color: #f8fafc;
        box-shadow: 0 8px 28px rgba(15, 23, 42, 0.12);
    }
    .coach-yoda { background: linear-gradient(135deg, #064e3b, #14532d); border: 1px solid #34d399; }
    .coach-vader { background: linear-gradient(135deg, #1f2937, #450a0a); border: 1px solid #f87171; }
    .coach-mando { background: linear-gradient(135deg, #334155, #1e3a5f); border: 1px solid #94a3b8; }
    .coach-dooku { background: linear-gradient(135deg, #3b0764, #1c1917); border: 1px solid #c084fc; }
    .coach-anakin { background: linear-gradient(135deg, #1e3a8a, #172554); border: 1px solid #60a5fa; }
    .coach-deathstar { background: linear-gradient(135deg, #334155, #0f172a); border: 1px solid #94a3b8; }

    .coach-avatar { font-size: 2rem; line-height: 1; }
    .coach-name { font-size: 0.95rem; font-weight: 700; margin: 0 0 0.35rem 0; }
    .coach-title { font-weight: 500; opacity: 0.75; font-size: 0.8rem; }
    .coach-line { font-size: 0.92rem; line-height: 1.5; margin: 0; font-style: italic; opacity: 0.95; }

    /* GitHub-style study show-up heatmap */
    .showup-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1rem 1.15rem 0.85rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.05);
    }
    .showup-head {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.75rem;
        margin-bottom: 0.65rem;
    }
    .showup-title {
        font-size: 0.95rem;
        font-weight: 700;
        margin: 0 0 0.2rem 0;
        color: var(--text);
    }
    .showup-sub {
        font-size: 0.8rem;
        color: var(--muted);
        margin: 0;
    }
    .showup-legend {
        display: flex;
        align-items: center;
        gap: 3px;
    }
    .showup-legend-label {
        font-size: 0.68rem;
        color: var(--muted);
        margin: 0 2px;
    }
    .showup-month-grid {
        display: flex;
        gap: 8px;
        align-items: flex-start;
    }
    .showup-dow-col {
        display: grid;
        grid-template-rows: repeat(7, 14px);
        gap: 3px;
        padding-top: 18px;
    }
    .showup-dow {
        font-size: 0.62rem;
        color: var(--muted);
        line-height: 14px;
        text-align: right;
        padding-right: 2px;
    }
    .showup-weeks-col { flex: 1; overflow-x: auto; }
    .showup-week-hdrs {
        display: grid;
        grid-auto-flow: column;
        gap: 3px;
        margin-bottom: 4px;
        min-height: 14px;
    }
    .showup-week-hdr {
        font-size: 0.62rem;
        color: var(--muted);
        text-align: center;
        white-space: nowrap;
    }
    .showup-grid {
        display: grid;
        grid-auto-flow: column;
        grid-template-rows: repeat(7, 14px);
        gap: 3px;
        padding-bottom: 2px;
    }
    .showup-cell {
        width: 14px;
        height: 14px;
        border-radius: 3px;
        flex-shrink: 0;
    }
    .showup-legend .showup-cell { width: 10px; height: 10px; }
    .heat-out {
        background: #f8fafc;
        box-shadow: none;
        opacity: 0.35;
    }
    .heat-0 {
        background: #e2e8f0;
        box-shadow: none;
    }
    .heat-1 {
        background: #86efac;
        box-shadow: 0 0 6px rgba(34, 197, 94, 0.45);
    }
    .heat-2 {
        background: #4ade80;
        box-shadow: 0 0 7px rgba(34, 197, 94, 0.55);
    }
    .heat-3 {
        background: #22c55e;
        box-shadow: 0 0 9px rgba(34, 197, 94, 0.65);
    }
    .heat-4 {
        background: #16a34a;
        box-shadow: 0 0 11px rgba(22, 163, 74, 0.75);
    }
    .heat-today {
        outline: 1.5px solid #6366f1;
        outline-offset: 1px;
    }
    .showup-foot {
        font-size: 0.72rem;
        color: var(--muted);
        margin: 0.55rem 0 0 0;
    }
</style>
"""