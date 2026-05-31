from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
import os
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import logging


API_BASE_URL = (
    os.environ.get("API_BASE_URL")
    or os.environ.get("api_base_url")
    or os.environ.get("Api_Base_Url")
    or os.environ.get("API_URL")
    or os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
).rstrip("/")

# Log the resolved API base so deployment logs make the source of truth obvious
logger = logging.getLogger("dashboard")
logger.info("Dashboard starting with API_BASE_URL=%s", API_BASE_URL)
DEFAULT_STORE_ID = os.getenv("DEFAULT_STORE_ID", "STORE_BLR_001")
KNOWN_STORE_IDS = [
    store_id.strip()
    for store_id in os.getenv("KNOWN_STORE_IDS", "STORE_BLR_001,store-001,store-002,STORE_BLR_002").split(",")
    if store_id.strip()
]
REFRESH_SECONDS = 10

FUNNEL_ORDER = ["ENTRY", "ZONE_VISIT", "BILLING_QUEUE", "PURCHASE"]
FUNNEL_LABELS = {
    "ENTRY": "Store Entry",
    "ZONE_VISIT": "Zone Engagement",
    "BILLING_QUEUE": "Billing Interest",
    "PURCHASE": "Completed Purchase",
}

ALERT_LABELS = {
    "QUEUE_SPIKE": "Queue Congestion",
    "DEAD_ZONE": "Low Engagement Zone",
    "CONVERSION_DROP": "Conversion Dip",
}

ALERT_DESCRIPTIONS = {
    "QUEUE_SPIKE": "High wait times detected near billing.",
    "DEAD_ZONE": "A historically active zone has lower than normal traffic.",
    "CONVERSION_DROP": "Visitor-to-purchase conversion is below the target range.",
}

SEVERITY_STYLES = {
    "INFO": {"accent": "#2563eb", "bg": "#eff6ff", "text": "#1e3a8a"},
    "WARN": {"accent": "#f97316", "bg": "#fff7ed", "text": "#9a3412"},
    "CRITICAL": {"accent": "#dc2626", "bg": "#fef2f2", "text": "#991b1b"},
}


@dataclass(frozen=True)
class ApiResponse:
    ok: bool
    payload: dict[str, Any] | None
    error: str | None = None


st.set_page_config(
    page_title="Store Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st_autorefresh(interval=REFRESH_SECONDS * 1000, key="store_intelligence_refresh")


st.markdown(
    """
    <style>
        :root {
            --canvas: #f5f7fb;
            --surface: #ffffff;
            --surface-muted: #f8fafc;
            --border: #e2e8f0;
            --text: #0f172a;
            --muted: #64748b;
            --shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
            --shadow-strong: 0 18px 48px rgba(15, 23, 42, 0.12);
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(37, 99, 235, 0.12), transparent 24%),
                radial-gradient(circle at top left, rgba(22, 163, 74, 0.08), transparent 28%),
                linear-gradient(180deg, #f8fafc 0%, var(--canvas) 42%, #eef4ff 100%);
            color: var(--text);
        }

        #MainMenu, footer, header {visibility: hidden;}
        .block-container {
            max-width: 1440px;
            padding-top: 1rem;
            padding-bottom: 1.25rem;
        }
        div[data-testid="stVerticalBlock"] {gap: 1rem;}
        div[data-testid="stHorizontalBlock"] {gap: 1rem;}
        .stPlotlyChart {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: var(--shadow);
            padding: 0.5rem;
        }

        .top-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.85rem 1.05rem;
            margin-bottom: 0.65rem;
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid var(--border);
            border-radius: 18px;
            box-shadow: var(--shadow-strong);
            backdrop-filter: blur(14px);
        }
        .brand-title {
            margin: 0;
            color: var(--text);
            font-size: 1.5rem;
            line-height: 1.1;
            font-weight: 850;
            letter-spacing: 0;
        }
        .brand-subtitle {
            margin: 0.16rem 0 0;
            color: var(--muted);
            font-size: 0.92rem;
            font-weight: 600;
        }
        .kpi-card {
            min-height: 148px;
            height: 148px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 1rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-left: 6px solid var(--accent);
            border-radius: 18px;
            box-shadow: var(--shadow);
        }
        .kpi-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
        }
        .kpi-label {
            color: var(--muted);
            font-size: 0.84rem;
            font-weight: 800;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }
        .kpi-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.35rem;
            height: 2.35rem;
            border-radius: 13px;
            color: var(--accent);
            background: var(--icon-bg);
            font-size: 1.2rem;
        }
        .kpi-value {
            color: var(--text);
            font-size: 2.35rem;
            line-height: 1;
            font-weight: 850;
            letter-spacing: 0;
        }
        .kpi-caption {
            color: var(--muted);
            font-size: 0.86rem;
            font-weight: 650;
        }

        .section-heading {
            margin: 0.25rem 0 0.15rem;
            color: var(--text);
            font-size: 1.12rem;
            font-weight: 850;
            letter-spacing: 0;
        }
        .section-caption {
            margin: -0.05rem 0 0.6rem;
            color: var(--muted);
            font-size: 0.88rem;
            font-weight: 600;
        }

        .anomaly-card {
            min-height: 174px;
            padding: 1rem;
            background: #ffffff;
            border: 1px solid var(--border);
            border-left: 6px solid var(--accent);
            border-radius: 18px;
            box-shadow: var(--shadow);
        }
        .anomaly-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.65rem;
            margin-bottom: 0.75rem;
        }
        .anomaly-type {
            color: var(--text);
            font-size: 1rem;
            font-weight: 850;
        }
        .severity-pill {
            color: var(--severity-text);
            background: var(--severity-bg);
            border: 1px solid var(--accent);
            border-radius: 999px;
            padding: 0.25rem 0.6rem;
            font-size: 0.72rem;
            font-weight: 850;
        }
        .anomaly-description {
            color: #334155;
            font-size: 0.92rem;
            line-height: 1.45;
            margin-bottom: 0.75rem;
        }
        .anomaly-action {
            color: #475569;
            background: #f8fafc;
            border-radius: 12px;
            padding: 0.65rem 0.75rem;
            font-size: 0.86rem;
            line-height: 1.4;
        }
        .empty-state {
            padding: 1.25rem;
            color: #166534;
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 18px;
            box-shadow: var(--shadow);
            font-weight: 800;
        }
        .section-block {
            margin-top: 1rem;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(12px);
        }
        .section-block__header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.9rem;
        }
        .section-block__title {
            color: var(--text);
            font-size: 1.18rem;
            font-weight: 900;
            letter-spacing: 0;
        }
        .section-block__subtitle {
            color: var(--muted);
            font-size: 0.9rem;
            font-weight: 600;
            margin-top: 0.2rem;
        }
        .business-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
        }
        .business-card {
            min-height: 178px;
            padding: 1rem;
            border-radius: 18px;
            border: 1px solid var(--border);
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            box-shadow: var(--shadow);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }
        .business-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 44px rgba(15, 23, 42, 0.12);
            border-color: #cbd5e1;
        }
        .business-card__icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.4rem;
            height: 2.4rem;
            border-radius: 14px;
            margin-bottom: 0.8rem;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            font-size: 1.1rem;
        }
        .business-card__title {
            color: var(--text);
            font-size: 1rem;
            font-weight: 900;
            margin-bottom: 0.45rem;
        }
        .business-card__text {
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.5;
            font-weight: 600;
        }
        .outcomes-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
        }
        .outcome-card {
            padding: 0.95rem 1rem;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: #ffffff;
            box-shadow: var(--shadow);
            min-height: 108px;
        }
        .outcome-card__label {
            color: #64748b;
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            margin-bottom: 0.5rem;
        }
        .outcome-card__value {
            color: var(--text);
            font-size: 1.7rem;
            line-height: 1.05;
            font-weight: 900;
        }
        .footer-closing {
            margin-top: 1rem;
            padding: 1rem 1.1rem;
            text-align: center;
            background: rgba(15, 23, 42, 0.98);
            border-radius: 18px;
            box-shadow: var(--shadow-strong);
            color: #ffffff;
        }
        .footer-closing__title {
            font-size: 1.15rem;
            font-weight: 900;
            letter-spacing: 0;
            margin-bottom: 0.15rem;
        }
        .footer-closing__subtitle {
            color: #cbd5e1;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 0.9rem;
        }
        .footer-closing__credit {
            color: #e2e8f0;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            margin-top: 0.2rem;
        }
        .footer-closing__divider {
            height: 1px;
            background: rgba(255, 255, 255, 0.14);
            margin: 0.75rem 0;
        }
        .footer-highlights {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 0.9rem;
        }
        .footer-highlight {
            padding: 0.9rem;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: left;
        }
        .footer-highlight__title {
            color: #ffffff;
            font-size: 0.95rem;
            font-weight: 900;
            margin-bottom: 0.35rem;
        }
        .footer-highlight__text {
            color: #cbd5e1;
            font-size: 0.86rem;
            line-height: 1.45;
            font-weight: 600;
        }
        @media (max-width: 900px) {
            .top-nav {align-items: flex-start; flex-direction: column;}
            .kpi-value {font-size: 1.95rem;}
            .business-grid, .outcomes-grid, .footer-highlights {grid-template-columns: 1fr;}
            .section-block__header {flex-direction: column;}
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=10)
def fetch_json(path: str) -> ApiResponse:
    try:
        response = requests.get(f"{API_BASE_URL}{path}", timeout=5)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return ApiResponse(ok=True, payload=payload)
        return ApiResponse(ok=True, payload={"data": payload})
    except requests.RequestException as exc:
        return ApiResponse(ok=False, payload=None, error=str(exc))
    except ValueError as exc:
        return ApiResponse(ok=False, payload=None, error=f"Invalid JSON response: {exc}")


@st.cache_data(ttl=60)
def load_store_id() -> str:
    result = fetch_json("/stores")
    candidates: list[str] = []

    if result.ok and result.payload:
        raw_stores = result.payload.get("store_ids", result.payload.get("data", []))
        if isinstance(raw_stores, list):
            for store in raw_stores:
                if isinstance(store, dict):
                    identifier = store.get("store_id") or store.get("name")
                    if identifier is not None:
                        candidates.append(str(identifier))
                elif store is not None:
                    candidates.append(str(store))

    candidates.extend([DEFAULT_STORE_ID, *KNOWN_STORE_IDS])
    seen: set[str] = set()
    for store_id in candidates:
        if store_id in seen:
            continue
        seen.add(store_id)
        metrics = fetch_json(f"/stores/{store_id}/metrics")
        if not metrics.ok or not metrics.payload:
            continue
        if int(metrics.payload.get("unique_visitors", 0) or 0) > 0:
            return store_id

    return candidates[0] if candidates else DEFAULT_STORE_ID


@st.cache_data(ttl=10)
def load_health() -> ApiResponse:
    return fetch_json("/health")


def format_time_stamp() -> str:
    return datetime.now().strftime("%b %d, %Y %I:%M:%S %p")


def format_event_timestamp(value: Any) -> str:
    if value in (None, ""):
        return "—"

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return value
    elif isinstance(value, datetime):
        parsed = value
    else:
        return str(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    return parsed.strftime("%b %d, %I:%M %p UTC")


def format_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def format_percent(value: Any) -> str:
    try:
        numeric_value = float(value)
        if 0 <= numeric_value <= 1:
            numeric_value *= 100
        return f"{numeric_value:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def severity_style(severity: str) -> tuple[str, dict[str, str]]:
    normalized = severity.upper().strip()
    if normalized not in SEVERITY_STYLES:
        normalized = "INFO"
    return normalized, SEVERITY_STYLES[normalized]


def render_top_nav() -> None:
    st.markdown(
        f"""
        <div class="top-nav">
            <div>
                <h1 class="brand-title">Store Intelligence Dashboard</h1>
                <p class="brand-subtitle">Real-Time Retail Analytics &amp; Customer Insights</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, icon: str, accent: str, icon_bg: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card" style="--accent:{accent}; --icon-bg:{icon_bg};">
            <div class="kpi-top">
                <div class="kpi-label">{escape(label)}</div>
                <div class="kpi-icon">{icon}</div>
            </div>
            <div class="kpi-value">{escape(value)}</div>
            <div class="kpi-caption">{escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_funnel_stages(raw_stages: list[dict[str, Any]]) -> pd.DataFrame:
    by_stage = {str(stage.get("stage", "")).upper().replace(" ", "_"): stage for stage in raw_stages}
    rows: list[dict[str, Any]] = []
    previous_count: int | None = None

    for stage_key in FUNNEL_ORDER:
        raw_count = by_stage.get(stage_key, {}).get("count", 0)
        try:
            count = max(int(raw_count), 0)
        except (TypeError, ValueError):
            count = 0

        if previous_count not in (None, 0):
            count = min(count, previous_count)

        dropoff = 0.0 if previous_count in (None, 0) else ((previous_count - count) / previous_count) * 100
        rows.append(
            {
                "stage": FUNNEL_LABELS[stage_key],
                "count": count,
                "dropoff_percentage": max(dropoff, 0.0),
            }
        )
        previous_count = count

    return pd.DataFrame(rows)


def render_section_heading(title: str, caption: str) -> None:
    st.markdown(
        f"""
        <div>
            <div class="section-heading">{escape(title)}</div>
            <div class="section-caption">{escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_funnel_chart(funnel_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Funnel(
                y=funnel_df["stage"],
                x=funnel_df["count"],
                textposition="inside",
                texttemplate="%{label}<br>%{value:,}<br>%{customdata:.1f}% drop-off",
                customdata=funnel_df["dropoff_percentage"],
                marker={
                    "color": ["#2563eb", "#0f766e", "#f97316", "#16a34a"],
                    "line": {"width": 1, "color": "#ffffff"},
                },
                connector={"line": {"color": "#cbd5e1", "width": 1.5}},
                hovertemplate="<b>%{label}</b><br>Visitors: %{value:,}<br>Drop-off: %{customdata:.1f}%<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        height=430,
        margin=dict(l=16, r=16, t=12, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", color="#0f172a"),
    )
    return fig


def build_bar_chart(df: pd.DataFrame, x_column: str, y_column: str, title: str, color: str, suffix: str = "") -> go.Figure:
    fig = go.Figure(
        data=[
            go.Bar(
                x=df[x_column],
                y=df[y_column],
                marker={"color": color, "line": {"color": "rgba(15, 23, 42, 0.08)", "width": 1}},
                text=[f"{value:,.1f}{suffix}" if isinstance(value, float) else f"{value:,}{suffix}" for value in df[y_column]],
                textposition="outside",
                hovertemplate=f"<b>%{{x}}</b><br>{title}: %{{y:,.1f}}{suffix}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        height=390,
        margin=dict(l=18, r=18, t=18, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", color="#0f172a"),
        xaxis=dict(title="", showgrid=False, tickfont=dict(color="#475569")),
        yaxis=dict(title="", gridcolor="#e2e8f0", zeroline=False),
        showlegend=False,
    )
    return fig


def render_anomaly_card(anomaly: dict[str, Any]) -> None:
    anomaly_type = str(anomaly.get("anomaly_type", "Operational Alert"))
    severity_label, style = severity_style(str(anomaly.get("severity", "INFO")))
    title = ALERT_LABELS.get(anomaly_type, anomaly_type.replace("_", " ").title())
    description = ALERT_DESCRIPTIONS.get(
        anomaly_type,
        str(anomaly.get("description", anomaly.get("message", "A store condition needs attention."))),
    )
    suggested_action = str(anomaly.get("suggested_action", "Review the store team dashboard and take action."))
    st.markdown(
        f"""
        <div class="anomaly-card" style="--accent:{style["accent"]}; --severity-bg:{style["bg"]}; --severity-text:{style["text"]};">
            <div class="anomaly-header">
                <div class="anomaly-type">{escape(title)}</div>
                <div class="severity-pill">{escape(severity_label)}</div>
            </div>
            <div class="anomaly-description">{escape(description)}</div>
            <div class="anomaly-action"><strong>Suggested Action:</strong> {escape(suggested_action)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_centered_message(message: str) -> None:
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:center; min-height:48vh;">
            <div style="font-size:1.45rem; font-weight:800; color:#991b1b; background:#fef2f2; padding:1rem 1.3rem; border-radius:18px; border:1px solid #fecaca; box-shadow:0 14px 34px rgba(15,23,42,0.08);">
                {escape(message)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_top_nav()

store_id = load_store_id()
st.caption(f"Showing store: {store_id}")

with st.spinner("Loading store insights..."):
    metrics_result = fetch_json(f"/stores/{store_id}/metrics")
    funnel_result = fetch_json(f"/stores/{store_id}/funnel")
    heatmap_result = fetch_json(f"/stores/{store_id}/heatmap")
    anomalies_result = fetch_json(f"/stores/{store_id}/anomalies")

if not metrics_result.ok and not funnel_result.ok and not heatmap_result.ok and not anomalies_result.ok:
    render_centered_message("Live store insights are temporarily unavailable.")
    st.stop()

metrics: dict[str, Any] = metrics_result.payload if metrics_result.ok and metrics_result.payload else {}
funnel_stages: list[dict[str, Any]] = []
if funnel_result.ok and funnel_result.payload:
    raw_stages = funnel_result.payload.get("stages", [])
    if isinstance(raw_stages, list):
        funnel_stages = raw_stages
stage_counts = {str(stage.get("stage", "")).upper().replace(" ", "_"): stage for stage in funnel_stages if isinstance(stage, dict)}

has_any_data = any(
    [
        int(metrics.get("unique_visitors", 0) or 0) > 0,
        any(int(stage.get("count", 0) or 0) > 0 for stage in funnel_stages if isinstance(stage, dict)),
    ]
)
if metrics_result.ok and funnel_result.ok and not has_any_data:
    st.warning(
        f"No analytics data was found for store '{store_id}'. Check DATABASE_URL and seeding before trusting zero values."
    )

if metrics_result.ok and metrics_result.payload:
    active_visitors = metrics.get(
        "active_visitors",
        max(int(metrics.get("total_entries", 0) or 0) - int(metrics.get("total_exits", 0) or 0), 0),
    )
    converted_visitors = metrics.get("converted_visitors", stage_counts.get("PURCHASE", {}).get("count", 0))
    metrics.setdefault("active_visitors", active_visitors)
    metrics.setdefault("converted_visitors", converted_visitors)
    kpi_cols = st.columns(4)
    kpi_cards = [
        ("Unique Visitors", format_int(metrics.get("unique_visitors", 0)), "👥", "#2563eb", "#eff6ff", "Customers observed today"),
        ("Active Visitors", format_int(metrics.get("active_visitors", 0)), "🛒", "#0f766e", "#f0fdfa", "Currently in store"),
        ("Converted Visitors", format_int(metrics.get("converted_visitors", 0)), "✅", "#16a34a", "#f0fdf4", "Completed purchases"),
        ("Conversion Rate", format_percent(metrics.get("conversion_rate", 0.0)), "📈", "#f97316", "#fff7ed", "Visitor-to-purchase rate"),
    ]
    for col, card in zip(kpi_cols, kpi_cards, strict=True):
        with col:
            render_kpi_card(*card)
else:
    st.info("Customer metrics are temporarily unavailable right now.")

render_section_heading("Customer Activity Overview", "Today's customer flow and store activity at a glance.")
if metrics_result.ok or funnel_result.ok:
    store_entries = stage_counts.get("ENTRY", {}).get("count", 0)
    billing_interactions = stage_counts.get("BILLING_QUEUE", {}).get("count", 0)
    purchases = metrics.get("converted_visitors", stage_counts.get("PURCHASE", {}).get("count", 0))
    total_events_today = int(store_entries or 0) + int(billing_interactions or 0) + int(purchases or 0)
    activity_cards = [
        ("Store Entries", format_int(store_entries), "🚪", "#2563eb", "#eff6ff", "Customers entering today"),
        ("Billing Interactions", format_int(billing_interactions), "💳", "#0f766e", "#f0fdfa", "Queue and checkout activity"),
        ("Purchases", format_int(purchases), "🛍️", "#16a34a", "#f0fdf4", "Completed purchases"),
        ("Total Customer Events Today", format_int(total_events_today), "📊", "#f97316", "#fff7ed", "All recorded customer events"),
    ]
    activity_cols = st.columns(4)
    for col, card in zip(activity_cols, activity_cards, strict=True):
        with col:
            render_kpi_card(*card)
else:
    st.info("Customer activity is temporarily unavailable right now.")

render_section_heading("Customer Journey Funnel", "How customers progress from arrival and re-entry to purchase.")
if funnel_result.ok and funnel_result.payload:
    stages = funnel_result.payload.get("stages", [])
    funnel_df = normalize_funnel_stages(stages if isinstance(stages, list) else [])
    if not funnel_df.empty:
        st.plotly_chart(build_funnel_chart(funnel_df), use_container_width=True)
        st.caption("Re-entry events are included in the arrival stage so repeat visits remain part of the same customer journey analytics.")
    else:
        st.info("No funnel data available yet.")
else:
    st.info("Funnel data is temporarily unavailable right now.")

render_section_heading("Zone Performance", "Traffic concentration and dwell behavior across the store.")
if heatmap_result.ok and heatmap_result.payload:
    zones = heatmap_result.payload.get("zones", heatmap_result.payload.get("value", []))
    heatmap_df = pd.DataFrame(zones if isinstance(zones, list) else [])
    if not heatmap_df.empty:
        if "avg_dwell_ms" in heatmap_df.columns:
            heatmap_df["avg_dwell_ms"] = pd.to_numeric(heatmap_df["avg_dwell_ms"], errors="coerce").fillna(0.0) / 1000
        heatmap_df = heatmap_df.rename(
            columns={
                "zone_id": "Zone",
                "visit_count": "Visit Count",
                "avg_dwell_ms": "Average Dwell Time",
                "avg_dwell_seconds": "Average Dwell Time",
            }
        )
        heatmap_df["Visit Count"] = pd.to_numeric(heatmap_df["Visit Count"], errors="coerce").fillna(0).astype(int)
        heatmap_df["Average Dwell Time"] = pd.to_numeric(
            heatmap_df["Average Dwell Time"], errors="coerce"
        ).fillna(0.0)
        heatmap_df = heatmap_df.sort_values("Visit Count", ascending=False)

        zone_col, dwell_col = st.columns(2)
        with zone_col:
            st.plotly_chart(
                build_bar_chart(heatmap_df, "Zone", "Visit Count", "Zone Visit Count", "#2563eb"),
                use_container_width=True,
            )
        with dwell_col:
            dwell_df = heatmap_df.sort_values("Average Dwell Time", ascending=False)
            st.plotly_chart(
                build_bar_chart(dwell_df, "Zone", "Average Dwell Time", "Average Dwell Time", "#f97316", "s"),
                use_container_width=True,
            )
    else:
        st.info("No heatmap data available yet.")
else:
    st.info("Zone performance data is temporarily unavailable right now.")

render_section_heading("Operational Alerts", "Business-focused alerts for retail managers.")
if anomalies_result.ok and anomalies_result.payload:
    anomalies = anomalies_result.payload.get("anomalies", anomalies_result.payload.get("value", []))
    if isinstance(anomalies, list) and anomalies:
        for row_start in range(0, len(anomalies), 3):
            cols = st.columns(3)
            for col, anomaly in zip(cols, anomalies[row_start : row_start + 3], strict=False):
                with col:
                    render_anomaly_card(anomaly if isinstance(anomaly, dict) else {})
    else:
        st.markdown('<div class="empty-state">No active anomalies detected.</div>', unsafe_allow_html=True)
else:
    st.info("Operational alerts are temporarily unavailable right now.")

st.markdown(
    """
    <div class="section-block">
        <div class="section-block__header">
            <div>
                <div class="section-block__title">How This Solution Helps Retail Stores</div>
                <div class="section-block__subtitle">A clear business overview for store leaders and judges.</div>
            </div>
        </div>
        <div class="business-grid">
            <div class="business-card">
                <div class="business-card__icon">👥</div>
                <div class="business-card__title">Customer Journey Insights</div>
                <div class="business-card__text">Understand how shoppers move through the store and identify opportunities to improve engagement and conversion.</div>
            </div>
            <div class="business-card">
                <div class="business-card__icon">📍</div>
                <div class="business-card__title">Zone Performance Analysis</div>
                <div class="business-card__text">Measure customer interest across product zones and optimize merchandising based on real behavior.</div>
            </div>
            <div class="business-card">
                <div class="business-card__icon">⚡</div>
                <div class="business-card__title">Queue & Congestion Monitoring</div>
                <div class="business-card__text">Detect operational bottlenecks early and reduce customer wait times at critical touchpoints.</div>
            </div>
            <div class="business-card">
                <div class="business-card__icon">📈</div>
                <div class="business-card__title">Real-Time Decision Support</div>
                <div class="business-card__text">Provide store managers with actionable insights that improve customer experience and business outcomes.</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="footer-closing">
        <div class="footer-closing__title">Store Intelligence Dashboard</div>
        <div class="footer-closing__subtitle">Actionable Retail Intelligence for Smarter Stores</div>
        <div class="footer-closing__credit">Prepared by Yelishala Jahnavi • 2026</div>
        <div class="footer-closing__divider"></div>
        <div class="footer-highlights">
            <div class="footer-highlight">
                <div class="footer-highlight__title">Customer Analytics</div>
                <div class="footer-highlight__text">Track visitor behavior and conversion patterns.</div>
            </div>
            <div class="footer-highlight">
                <div class="footer-highlight__title">Zone Performance</div>
                <div class="footer-highlight__text">Understand engagement and dwell time across store zones.</div>
            </div>
            <div class="footer-highlight">
                <div class="footer-highlight__title">Operational Intelligence</div>
                <div class="footer-highlight__text">Identify congestion, dead zones, and performance bottlenecks.</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
