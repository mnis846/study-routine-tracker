import streamlit as st


def inject_mobile_styles() -> None:
    st.markdown(
        """
        <style>
        /* ── Mobile-first layout ── */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 720px !important;
        }

        /* Touch-friendly buttons */
        .stButton > button {
            min-height: 44px;
            font-size: 0.95rem;
            border-radius: 10px;
        }
        .stButton > button[kind="primary"] {
            font-weight: 600;
        }

        /* Tabs: scrollable on small screens */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            flex-wrap: nowrap;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        .stTabs [data-baseweb="tab"] {
            min-height: 44px;
            padding: 0.5rem 0.75rem;
            font-size: 0.85rem;
            white-space: nowrap;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
        }

        /* Form inputs */
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            min-height: 44px;
            font-size: 1rem;
            border-radius: 8px;
        }
        .stSelectbox > div > div {
            min-height: 44px;
        }

        /* Expander headers */
        .streamlit-expanderHeader {
            min-height: 44px;
            font-size: 0.95rem;
        }

        /* Data editor on mobile */
        .stDataFrame {
            font-size: 0.8rem;
        }

        /* Hide Streamlit branding footer on mobile */
        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }

        /* App title */
        .app-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.25rem;
        }
        .app-subtitle {
            font-size: 0.85rem;
            color: #64748b;
            margin-bottom: 1rem;
        }

        /* Target cards */
        .target-card {
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.5rem;
        }
        .target-card.done { border-left: 4px solid #22c55e; }
        .target-card.partial { border-left: 4px solid #f59e0b; }
        .target-card.pending { border-left: 4px solid #94a3b8; }
        .target-card.skipped { border-left: 4px solid #ef4444; opacity: 0.7; }
        .target-card .target-text {
            font-size: 0.95rem;
            font-weight: 500;
            color: #1e293b;
        }
        .target-card .target-meta {
            font-size: 0.75rem;
            color: #64748b;
            margin-top: 0.25rem;
        }

        /* Status badges */
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge-done { background: #dcfce7; color: #166534; }
        .badge-partial { background: #fef3c7; color: #92400e; }
        .badge-pending { background: #f1f5f9; color: #475569; }
        .badge-skipped { background: #fee2e2; color: #991b1b; }

        /* Desktop: slightly wider */
        @media (min-width: 768px) {
            .block-container { max-width: 900px !important; }
            .app-title { font-size: 1.75rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
