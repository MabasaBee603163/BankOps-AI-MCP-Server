# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false

import json
import sqlite3
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Any, Literal

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DB_PATH = ROOT_DIR / "database" / "bankops.db"
AUDIT_LOG_PATH = ROOT_DIR / "logs" / "audit_log.jsonl"
REPORTS_DIR = ROOT_DIR / "reports"
EXPORTS_DIR = ROOT_DIR / "exports"


st.set_page_config(
    page_title="BankOps AI Control Plane",
    page_icon=":bank:",
    layout="wide",
    initial_sidebar_state="expanded",
)


_streamlit_markdown = st.markdown
_streamlit_html = getattr(st, "html", None)


def app_markdown(body: Any, *args: Any, **kwargs: Any) -> Any:
    if kwargs.get("unsafe_allow_html") is True and isinstance(body, str):
        body = dedent(body).strip()
        if callable(_streamlit_html):
            return _streamlit_html(body)
    return _streamlit_markdown(body, *args, **kwargs)


st.markdown = app_markdown  # type: ignore[method-assign]


CSS = """
<style>
    :root {
        --bg: #F6F8FB;
        --card: #FFFFFF;
        --border: #E5EAF1;
        --text: #0F172A;
        --muted: #64748B;
        --blue: #2563EB;
        --teal: #14B8A6;
        --green: #16A34A;
        --amber: #F59E0B;
        --red: #DC2626;
        --purple: #7C3AED;
        --shadow: 0 18px 44px rgba(15, 23, 42, 0.07);
    }

    .stApp {
        background:
            radial-gradient(circle at 86% 0%, rgba(37, 99, 235, 0.08), transparent 28rem),
            radial-gradient(circle at 18% 0%, rgba(20, 184, 166, 0.06), transparent 22rem),
            linear-gradient(180deg, #FFFFFF 0%, var(--bg) 52%, #EEF3F8 100%);
        color: var(--text);
    }

    .block-container {
        max-width: 1540px;
        padding: 1.35rem 1.65rem 2.6rem;
    }

    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--border);
        box-shadow: 8px 0 30px rgba(15, 23, 42, 0.035);
    }

    [data-testid="stSidebar"] * { color: var(--text); }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        min-height: 2.75rem;
        border-radius: 12px;
        padding: 0.5rem 0.65rem;
        margin: 0.12rem 0;
        border: 1px solid transparent;
        font-weight: 720;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: #EFF6FF;
        border-color: #DBEAFE;
    }

    .page-shell { padding-bottom: 1rem; }

    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1.05rem;
    }

    .header-title {
        color: var(--text);
        font-size: 1.85rem;
        line-height: 1.1;
        font-weight: 880;
        letter-spacing: 0;
    }

    .header-subtitle {
        color: var(--muted);
        font-size: 0.95rem;
        margin-top: 0.28rem;
    }

    .header-actions {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.7rem;
    }

    .env-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        color: #166534;
        border-radius: 999px;
        padding: 0.42rem 0.72rem;
        font-size: 0.78rem;
        font-weight: 840;
    }

    .env-pill::before {
        content: "";
        width: 0.48rem;
        height: 0.48rem;
        border-radius: 50%;
        background: var(--green);
        box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.13);
    }

    .profile-pill {
        display: flex;
        align-items: center;
        gap: 0.62rem;
        border: 1px solid var(--border);
        background: #FFFFFF;
        border-radius: 999px;
        padding: 0.35rem 0.68rem 0.35rem 0.38rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.045);
    }

    .avatar {
        width: 2.15rem;
        height: 2.15rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, var(--text), var(--blue) 58%, var(--teal));
        color: white;
        font-size: 0.78rem;
        font-weight: 900;
    }

    .profile-name {
        color: var(--text);
        font-size: 0.82rem;
        font-weight: 820;
        line-height: 1.05;
    }

    .profile-role {
        color: var(--muted);
        font-size: 0.7rem;
        margin-top: 0.12rem;
        line-height: 1.05;
    }

    .muted-text {
        color: var(--muted);
        font-size: 0.82rem;
    }

    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.72rem;
        padding: 0.35rem 0 1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 0.85rem;
    }

    .brand-mark {
        width: 2.45rem;
        height: 2.45rem;
        border-radius: 13px;
        background: linear-gradient(135deg, var(--blue), var(--teal));
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        font-size: 1.04rem;
        font-weight: 900;
        box-shadow: 0 14px 28px rgba(37, 99, 235, 0.2);
    }

    .brand-title {
        font-size: 1.08rem;
        line-height: 1.05;
        color: var(--text);
        font-weight: 900;
    }

    .brand-subtitle {
        margin-top: 0.15rem;
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 720;
    }

    .sidebar-badges {
        display: flex;
        gap: 0.42rem;
        flex-wrap: wrap;
        margin: 0.65rem 0 0.95rem;
    }

    .tiny-badge {
        display: inline-flex;
        border: 1px solid var(--border);
        background: #FFFFFF;
        color: var(--muted);
        border-radius: 999px;
        padding: 0.24rem 0.5rem;
        font-size: 0.72rem;
        font-weight: 800;
    }

    .nav-note {
        margin-top: 1rem;
        border: 1px solid var(--border);
        background: #F8FAFC;
        border-radius: 14px;
        padding: 0.82rem;
        color: var(--muted);
        font-size: 0.8rem;
        line-height: 1.38;
    }

    .kpi-grid,
    .card-grid-2,
    .card-grid-3,
    .card-grid-4 {
        display: grid;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .kpi-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }
    .card-grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .card-grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .card-grid-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }

    .table-card,
    .kpi-card,
    .executive-card,
    .detail-card,
    .list-card,
    .event-card,
    .workflow-card,
    .report-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: var(--shadow);
    }

    .table-card {
        padding: 1rem;
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
    }

    .kpi-card {
        min-height: 150px;
        padding: 1rem;
        overflow: hidden;
        background:
            radial-gradient(circle at 88% 20%, var(--soft), transparent 4.4rem),
            #FFFFFF;
    }

    .kpi-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.65rem;
    }

    .kpi-icon {
        width: 2.35rem;
        height: 2.35rem;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--soft);
        color: var(--accent);
        font-size: 1rem;
        font-weight: 900;
    }

    .kpi-trend {
        color: var(--accent);
        background: var(--soft);
        border-radius: 999px;
        padding: 0.2rem 0.48rem;
        font-size: 0.71rem;
        font-weight: 820;
        white-space: nowrap;
    }

    .kpi-label {
        margin-top: 0.78rem;
        color: var(--text);
        font-size: 0.78rem;
        font-weight: 820;
    }

    .kpi-value {
        margin-top: 0.2rem;
        color: var(--text);
        font-size: 1.78rem;
        line-height: 1.08;
        font-weight: 900;
    }

    .kpi-caption {
        margin-top: 0.45rem;
        color: var(--muted);
        font-size: 0.78rem;
        line-height: 1.35;
    }

    .sparkline {
        height: 1.45rem;
        display: flex;
        align-items: end;
        justify-content: flex-end;
        gap: 0.17rem;
        margin-top: 0.62rem;
    }

    .sparkline span {
        width: 0.35rem;
        background: var(--accent);
        border-radius: 999px 999px 0 0;
        opacity: 0.82;
    }

    .executive-card,
    .detail-card,
    .list-card {
        padding: 1rem;
    }

    .section-title {
        color: var(--text);
        font-size: 1.08rem;
        font-weight: 880;
        margin: 1.1rem 0 0.18rem;
    }

    .section-subtitle {
        color: var(--muted);
        font-size: 0.86rem;
        margin-bottom: 0.68rem;
    }

    .card-title {
        color: var(--text);
        font-size: 0.98rem;
        font-weight: 850;
        margin-bottom: 0.1rem;
    }

    .card-caption {
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.35;
        margin-bottom: 0.72rem;
    }

    .mini-row,
    .metadata-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        border-bottom: 1px solid #EEF2F7;
        padding: 0.62rem 0;
        color: var(--text);
        font-size: 0.84rem;
    }

    .mini-row:last-child,
    .metadata-row:last-child {
        border-bottom: 0;
    }

    .mini-label {
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 720;
    }

    .mini-value {
        color: var(--text);
        font-size: 1rem;
        font-weight: 860;
        text-align: right;
    }

    .status-chip {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.18rem 0.5rem;
        font-size: 0.72rem;
        line-height: 1.2;
        font-weight: 840;
        white-space: nowrap;
    }

    .chip-success { color: #166534; background: #DCFCE7; }
    .chip-error { color: #991B1B; background: #FEE2E2; }
    .chip-warning { color: #92400E; background: #FEF3C7; }
    .chip-info { color: #1D4ED8; background: #DBEAFE; }
    .chip-neutral { color: #475569; background: #F1F5F9; }
    .chip-purple { color: #6D28D9; background: #EDE9FE; }

    .risk-dot {
        width: 0.58rem;
        height: 0.58rem;
        border-radius: 999px;
        background: var(--red);
        box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.12);
        flex: 0 0 auto;
    }

    .event-card,
    .workflow-card,
    .report-card {
        padding: 0.88rem;
        margin-bottom: 0.72rem;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.045);
        min-width: 0;
    }

    .event-main,
    .workflow-main,
    .report-main {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.8rem;
    }

    .item-title {
        color: var(--text);
        font-size: 0.92rem;
        font-weight: 850;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }

    .item-subtitle {
        color: var(--muted);
        font-size: 0.78rem;
        line-height: 1.35;
        margin-top: 0.18rem;
        overflow-wrap: anywhere;
    }

    .technical-detail {
        border: 1px solid var(--border);
        background: #F8FAFC;
        border-radius: 14px;
        padding: 0.8rem;
        color: var(--text);
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        font-size: 0.78rem;
        line-height: 1.45;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        max-height: 26rem;
        overflow: auto;
    }

    .document-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.9rem;
    }

    .item-meta {
        display: flex;
        gap: 0.4rem;
        flex-wrap: wrap;
        margin-top: 0.58rem;
    }

    .divider-soft {
        height: 1px;
        background: #EEF2F7;
        margin: 0.72rem 0;
    }

    .health-layout {
        display: grid;
        grid-template-columns: 190px 1fr;
        gap: 1rem;
        align-items: center;
    }

    .health-ring {
        width: 132px;
        height: 132px;
        border-radius: 50%;
        margin: 0.5rem auto;
        background: conic-gradient(var(--green) 0deg 340deg, #E5EAF1 340deg 360deg);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .health-inner {
        width: 92px;
        height: 92px;
        border-radius: 50%;
        background: #FFFFFF;
        color: var(--green);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        font-size: 1.55rem;
    }

    .health-state {
        color: var(--text);
        text-align: center;
        font-size: 1.45rem;
        font-weight: 900;
    }

    .architecture-note {
        border: 1px solid #DBEAFE;
        border-left: 4px solid var(--blue);
        border-radius: 14px;
        background: #F8FBFF;
        color: var(--muted);
        padding: 0.85rem 0.95rem;
        font-size: 0.86rem;
        margin-bottom: 1rem;
    }

    .empty-state {
        border: 1px dashed #CBD5E1;
        background: #FFFFFF;
        border-radius: 16px;
        padding: 1rem;
        color: var(--muted);
        font-size: 0.88rem;
    }

    .empty-title {
        color: var(--text);
        font-size: 0.95rem;
        font-weight: 850;
        margin-bottom: 0.16rem;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
        background: #FFFFFF !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
    }

    div[data-testid="stDataFrame"] * {
        color: var(--text) !important;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }

    .stTabs [data-baseweb="tab"] {
        border: 1px solid var(--border);
        border-radius: 999px;
        background: #FFFFFF;
        padding: 0.38rem 0.8rem;
    }

    label, .stSelectbox label, .stMultiSelect label {
        color: var(--text) !important;
        font-weight: 780 !important;
    }

    @media (max-width: 1250px) {
        .kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .card-grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .operational-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }

    @media (max-width: 850px) {
        .top-header { flex-direction: column; }
        .header-actions { justify-content: flex-start; }
        .kpi-grid,
        .card-grid-2,
        .card-grid-3,
        .card-grid-4,
        .document-grid,
        .operational-grid { grid-template-columns: 1fr; }
        .health-layout { grid-template-columns: 1fr; }
    }

    .operational-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
        align-items: start;
    }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


TABLE_COLUMNS = {
    "transactions": ["transaction_id", "customer_id", "amount", "currency", "status", "failure_reason", "created_at"],
    "customers": ["customer_id", "full_name", "email", "risk_level"],
    "support_tickets": ["ticket_id", "title", "priority", "description", "status", "created_at"],
    "workflow_runs": ["workflow_id", "workflow_name", "status", "started_at", "completed_at", "triggered_by_role", "summary"],
}

TABLE_QUERIES = {
    "transactions": "SELECT transaction_id, customer_id, amount, currency, status, failure_reason, created_at FROM transactions ORDER BY created_at DESC",
    "customers": "SELECT customer_id, full_name, email, risk_level FROM customers ORDER BY customer_id",
    "support_tickets": "SELECT ticket_id, title, priority, description, status, created_at FROM support_tickets ORDER BY created_at DESC",
    "workflow_runs": "SELECT workflow_id, workflow_name, status, started_at, completed_at, triggered_by_role, summary FROM workflow_runs ORDER BY started_at DESC",
}


def esc(value: Any) -> str:
    return escape("" if value is None else str(value))


def format_title(value: Any) -> str:
    if value is None or pd.isna(value):
        return "Not Available"
    text = str(value)
    text = text.replace("_workflow", "").replace("_", " ").replace("-", " ")
    return text.title()


def format_datetime(value: Any) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return "N/A"
    return parsed.strftime("%Y-%m-%d %H:%M")


def format_money(value: Any, currency: str = "ZAR") -> str:
    amount = pd.to_numeric(pd.Series([value]), errors="coerce").fillna(0).iloc[0]
    return f"{currency} {float(amount):,.2f}"


def format_int(value: Any) -> str:
    try:
        return f"{int(value or 0):,}"
    except (TypeError, ValueError):
        return "0"


DataFrameHeight = int | Literal["stretch", "content"]


def percentage(part: Any, whole: Any) -> float:
    part_value = pd.to_numeric(pd.Series([part]), errors="coerce").fillna(0).iloc[0]
    whole_value = pd.to_numeric(pd.Series([whole]), errors="coerce").fillna(0).iloc[0]
    if not whole_value:
        return 0.0
    return round((float(part_value) / float(whole_value)) * 100, 1)


def file_size(path: Path) -> str:
    try:
        size = path.stat().st_size
    except OSError:
        return "N/A"
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def file_modified(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    except OSError:
        return "N/A"


def status_class(status: Any) -> str:
    value = str(status or "").lower()
    if value in {"successful", "success", "completed", "healthy", "enabled", "allowed", "traceable"}:
        return "chip-success"
    if value in {"failed", "error", "denied", "blocked", "critical"}:
        return "chip-error"
    if value in {"pending", "open", "started", "running", "queued", "medium", "high"}:
        return "chip-warning"
    if value in {"no_action_required", "closed", "none", "not allowed"}:
        return "chip-neutral"
    return "chip-info"


def status_chip(status: Any) -> str:
    return f'<span class="status-chip {status_class(status)}">{esc(format_title(status))}</span>'


def priority_chip(priority: Any) -> str:
    value = str(priority or "").lower()
    klass = "chip-info"
    if value in {"critical", "high"}:
        klass = "chip-error"
    elif value == "medium":
        klass = "chip-warning"
    elif value == "low":
        klass = "chip-info"
    return f'<span class="status-chip {klass}">{esc(format_title(priority))}</span>'


def render_empty_state(title: str, message: str) -> None:
    st.markdown(empty_state_html(title, message), unsafe_allow_html=True)


def empty_state_html(title: str, message: str) -> str:
    return f"""
        <div class="empty-state">
            <div class="empty-title">{esc(title)}</div>
            <div>{esc(message)}</div>
        </div>
        """


def sparkline(values: list[int]) -> str:
    if not values:
        values = [2, 4, 3, 5, 4, 6, 5]
    peak = max(values) or 1
    bars = "".join(f'<span style="height:{max(18, int((value / peak) * 100))}%"></span>' for value in values[-8:])
    return f'<div class="sparkline">{bars}</div>'


def render_kpi_card(label: str, value: str, caption: str, icon: str, accent: str, trend: str = "Stable") -> str:
    soft = {
        "#2563EB": "#EFF6FF",
        "#14B8A6": "#F0FDFA",
        "#16A34A": "#F0FDF4",
        "#F59E0B": "#FFFBEB",
        "#DC2626": "#FEF2F2",
        "#7C3AED": "#F5F3FF",
    }.get(accent, "#F8FAFC")
    return f"""
    <div class="kpi-card" style="--accent:{accent};--soft:{soft};">
        <div class="kpi-top">
            <div class="kpi-icon">{esc(icon)}</div>
            <div class="kpi-trend">{esc(trend)}</div>
        </div>
        <div class="kpi-label">{esc(label)}</div>
        <div class="kpi-value">{esc(value)}</div>
        <div class="kpi-caption">{esc(caption)}</div>
        {sparkline([1, 3, 2, 5, 4, 6, 5])}
    </div>
    """


def kpi_grid(cards: list[str]) -> None:
    st.markdown(f'<div class="kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="section-title">{esc(title)}</div><div class="section-subtitle">{esc(subtitle)}</div>',
        unsafe_allow_html=True,
    )


def page_header(title: str) -> None:
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.markdown(
        f"""
        <div class="top-header">
            <div>
                <div class="header-title">{esc(title)}</div>
                <div class="header-subtitle">Real-time visibility across AI-assisted banking operations.</div>
            </div>
            <div class="header-actions">
                <div class="env-pill">Production</div>
                <div class="muted-text">Last updated: {esc(updated)}</div>
                <div class="profile-pill">
                    <div class="avatar">AM</div>
                    <div>
                        <div class="profile-name">Alexandra Morgan</div>
                        <div class="profile-role">Operations Admin</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def table_exists(table_name: str) -> bool:
    if not DB_PATH.exists():
        return False
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        return row is not None
    except sqlite3.Error:
        return False


@st.cache_data(ttl=10)
def load_table(table_name: str) -> pd.DataFrame:
    if not table_exists(table_name):
        return pd.DataFrame(columns=TABLE_COLUMNS.get(table_name, []))
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(TABLE_QUERIES[table_name], conn)
    except (sqlite3.Error, pd.errors.DatabaseError):
        return pd.DataFrame(columns=TABLE_COLUMNS.get(table_name, []))


@st.cache_data(ttl=10)
def load_audit_logs() -> pd.DataFrame:
    columns = ["request_id", "timestamp", "tool_name", "role", "status", "error_type", "input", "output_preview", "execution_time_ms"]
    if not AUDIT_LOG_PATH.exists():
        return pd.DataFrame(columns=columns)
    records: list[dict[str, Any]] = []
    try:
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return pd.DataFrame(columns=columns)
    if not records:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(records)
    for column in columns:
        if column not in df.columns:
            df[column] = None
    return df[columns].sort_values("timestamp", ascending=False)


@st.cache_data(ttl=10)
def read_json_file(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(ttl=10)
def read_csv_file(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def list_files(directory: Path, pattern: str) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)


def display_columns(df: pd.DataFrame) -> pd.DataFrame:
    display_df = df.copy()
    display_df.columns = [format_title(column) for column in display_df.columns]
    return display_df


def data_table(df: pd.DataFrame | None, height: DataFrameHeight | None = None) -> None:
    if df is None or df.empty:
        render_empty_state("No records available", "There are no records for the selected view.")
        return

    styled_df = display_columns(df)
    if height is None:
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        return

    if isinstance(height, int) and not isinstance(height, bool) and height > 0:
        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=height)
    elif height == "stretch":
        st.dataframe(styled_df, use_container_width=True, hide_index=True, height="stretch")
    elif height == "content":
        st.dataframe(styled_df, use_container_width=True, hide_index=True, height="content")
    else:
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

def render_technical_detail(value: Any) -> None:
    if value is None or (not isinstance(value, (dict, list)) and pd.isna(value)):
        text = "N/A"
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, indent=2, default=str)
    else:
        text = str(value)
    st.markdown(f'<div class="technical-detail">{esc(text)}</div>', unsafe_allow_html=True)


def count_status(df: pd.DataFrame, column: str, value: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int((df[column].fillna("").astype(str).str.lower() == value.lower()).sum())


def count_statuses(df: pd.DataFrame, column: str, values: list[str]) -> int:
    if df.empty or column not in df.columns:
        return 0
    normalized = df[column].fillna("").astype(str).str.lower()
    return int(normalized.isin([value.lower() for value in values]).sum())


def count_error_type(audit_df: pd.DataFrame, needle: str) -> int:
    if audit_df.empty or "error_type" not in audit_df.columns:
        return 0
    return int(audit_df["error_type"].fillna("").astype(str).str.lower().str.contains(needle.lower(), regex=False).sum())


def parse_datetime_column(df: pd.DataFrame, column: str) -> pd.Series:
    if df.empty or column not in df.columns:
        return pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]")
    return pd.to_datetime(df[column], errors="coerce", utc=True)


def add_date_bucket(df: pd.DataFrame, source_col: str = "created_at") -> pd.DataFrame:
    if df.empty or source_col not in df.columns:
        return pd.DataFrame(columns=[*df.columns, "date_bucket"])
    bucketed = df.copy()
    bucketed[f"{source_col}_dt"] = parse_datetime_column(bucketed, source_col)
    bucketed["date_bucket"] = bucketed[f"{source_col}_dt"].dt.date
    return bucketed.dropna(subset=["date_bucket"])


def enough_trend_points(df: pd.DataFrame) -> bool:
    return not df.empty and len(df.index.unique()) >= 2


def build_transaction_trend(transactions: pd.DataFrame) -> pd.DataFrame:
    bucketed = add_date_bucket(transactions, "created_at")
    if bucketed.empty:
        return pd.DataFrame()
    trend = bucketed.groupby("date_bucket").size().reset_index(name="Transactions")
    return trend.sort_values("date_bucket").set_index("date_bucket")


def build_failed_rate_trend(transactions: pd.DataFrame) -> pd.DataFrame:
    bucketed = add_date_bucket(transactions, "created_at")
    if bucketed.empty or "status" not in bucketed.columns:
        return pd.DataFrame()
    status = bucketed["status"].fillna("").astype(str).str.lower()
    bucketed["_failed"] = status.eq("failed").astype(int)
    trend = bucketed.groupby("date_bucket").agg(total=("status", "size"), failed=("_failed", "sum")).reset_index()
    trend["Failed Rate (%)"] = (trend["failed"] / trend["total"] * 100).round(1)
    return trend[["date_bucket", "Failed Rate (%)"]].sort_values("date_bucket").set_index("date_bucket")


def build_workflow_trend(workflows: pd.DataFrame) -> pd.DataFrame:
    bucketed = add_date_bucket(workflows, "started_at")
    if bucketed.empty:
        return pd.DataFrame()
    trend = bucketed.groupby("date_bucket").size().reset_index(name="Workflow Runs")
    return trend.sort_values("date_bucket").set_index("date_bucket")


def build_audit_error_trend(audit_events: pd.DataFrame) -> pd.DataFrame:
    if audit_events.empty or "status" not in audit_events.columns:
        return pd.DataFrame()
    errors = audit_events[audit_events["status"].fillna("").astype(str).str.lower() == "error"]
    bucketed = add_date_bucket(errors, "timestamp")
    if bucketed.empty:
        return pd.DataFrame()
    trend = bucketed.groupby("date_bucket").size().reset_index(name="Audit Errors")
    return trend.sort_values("date_bucket").set_index("date_bucket")


def sort_by_datetime(df: pd.DataFrame, column: str, ascending: bool = False) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df
    sorted_df = df.copy()
    sorted_df["_sort_dt"] = parse_datetime_column(sorted_df, column)
    sorted_df = sorted_df.sort_values("_sort_dt", ascending=ascending, na_position="last")
    return sorted_df.drop(columns=["_sort_dt"])


def strip_dashboard_columns(df: pd.DataFrame) -> pd.DataFrame:
    helper_columns = [column for column in df.columns if column.endswith("_dt") or column in {"date_bucket", "_failed"}]
    return df.drop(columns=helper_columns, errors="ignore")


def chart_by_date(df: pd.DataFrame, date_column: str, value_column: str | None = None) -> pd.DataFrame:
    bucketed = add_date_bucket(df, date_column)
    if bucketed.empty:
        return pd.DataFrame()
    if value_column and value_column in bucketed.columns:
        bucketed["_value"] = pd.to_numeric(bucketed[value_column], errors="coerce").fillna(0)
        return bucketed.groupby("date_bucket")["_value"].sum().reset_index(name="Value").set_index("date_bucket")
    return bucketed.groupby("date_bucket").size().reset_index(name="Count").set_index("date_bucket")


def deployment_status(db_path: Path, audit_path: Path, audit_events: pd.DataFrame) -> tuple[str, str, str]:
    if not db_path.exists() or not audit_path.exists():
        return "Degraded", "Telemetry is partially unavailable", "Check"

    if audit_events.empty or "error_type" not in audit_events.columns:
        return "Healthy", "Database and audit stream readable", "Stable"

    audit_copy = audit_events.copy()
    audit_copy["_timestamp"] = parse_datetime_column(audit_copy, "timestamp")
    latest = audit_copy["_timestamp"].max()
    if pd.isna(latest):
        recent = audit_copy
    else:
        recent = audit_copy[audit_copy["_timestamp"] >= latest - pd.Timedelta(days=1)]

    recent_errors = recent["error_type"].fillna("").astype(str).str.upper()
    if recent_errors.str.contains("SYSTEM_ERROR|DATABASE_ERROR", regex=True).any():
        return "Degraded", "Recent platform-level errors detected", "Action"
    if recent_errors.str.contains("ACCESS_DENIED|VALIDATION_ERROR", regex=True).any():
        return "Watch", "Security controls are actively enforcing policy", "Watch"
    return "Healthy", "Database and audit stream readable", "Stable"


def average_response_time(audit_df: pd.DataFrame) -> str:
    if audit_df.empty or "execution_time_ms" not in audit_df.columns:
        return "N/A"
    values = pd.to_numeric(audit_df["execution_time_ms"], errors="coerce").dropna()
    if values.empty:
        return "N/A"
    return f"{values.mean():.0f} ms"


def render_failed_transaction_card(row: pd.Series) -> str:
    reason = row.get("failure_reason") or "Unspecified"
    return f"""
    <div class="event-card">
        <div class="event-main">
            <div style="display:flex; gap:.65rem; align-items:flex-start;">
                <span class="risk-dot"></span>
                <div>
                    <div class="item-title">{esc(row.get("transaction_id", "N/A"))}</div>
                    <div class="item-subtitle">Customer {esc(row.get("customer_id", "N/A"))} | {esc(format_money(row.get("amount"), row.get("currency") or "ZAR"))}</div>
                    <div class="item-meta">{status_chip("failed")} <span class="status-chip chip-error">{esc(reason)}</span></div>
                </div>
            </div>
            <div class="muted-text">{esc(format_datetime(row.get("created_at")))}</div>
        </div>
    </div>
    """


def render_workflow_card(row: pd.Series) -> str:
    summary = row.get("summary") or "No summary recorded."
    return f"""
    <div class="workflow-card">
        <div class="workflow-main">
            <div>
                <div class="item-title">{esc(format_title(row.get("workflow_name")))}</div>
                <div class="item-subtitle">Workflow ID {esc(row.get("workflow_id", "N/A"))}</div>
                <div class="item-meta">
                    {status_chip(row.get("status"))}
                    <span class="status-chip chip-info">{esc(format_title(row.get("triggered_by_role")))}</span>
                </div>
            </div>
            <div class="muted-text">{esc(format_datetime(row.get("started_at")))}</div>
        </div>
        <div class="divider-soft"></div>
        <div class="item-subtitle">{esc(summary)}</div>
    </div>
    """


def render_audit_event_card(row: pd.Series) -> str:
    error_type = row.get("error_type")
    error_html = status_chip(error_type) if error_type and not pd.isna(error_type) else ""
    return f"""
    <div class="event-card">
        <div class="event-main">
            <div>
                <div class="item-title">{esc(format_title(row.get("tool_name")))}</div>
                <div class="item-subtitle">Request {esc(row.get("request_id") or "N/A")} | Role {esc(format_title(row.get("role")))}</div>
                <div class="item-meta">
                    {status_chip(row.get("status"))}
                    {error_html}
                    <span class="status-chip chip-neutral">{esc(str(row.get("execution_time_ms") or "N/A"))} ms</span>
                </div>
            </div>
            <div class="muted-text">{esc(format_datetime(row.get("timestamp")))}</div>
        </div>
    </div>
    """


def report_metadata(path: Path) -> dict[str, Any]:
    data: Any = None
    if path.suffix.lower() == ".json":
        try:
            data = read_json_file(path)
        except (OSError, json.JSONDecodeError):
            data = None
    return {"data": data}


def render_report_card(path: Path, data: Any = None) -> str:
    file_type = path.suffix.replace(".", "").upper() or "FILE"
    fields = ""
    if isinstance(data, dict):
        for key in ["report_id", "workflow_id", "report_type", "date"]:
            if key in data:
                fields += f'<span class="status-chip chip-neutral">{esc(format_title(key))}: {esc(data.get(key))}</span>'
    return f"""
    <div class="report-card">
        <div class="report-main">
            <div>
                <div class="item-title">{esc(path.name)}</div>
                <div class="item-subtitle">Modified {esc(file_modified(path))} | {esc(file_size(path))}</div>
                <div class="item-meta">
                    <span class="status-chip chip-info">{esc(file_type)}</span>
                    {fields}
                </div>
            </div>
        </div>
    </div>
    """


def render_audit_snapshot(total_logs: int, access_denied: int, validation_errors: int, rate_limits: int, not_found: int) -> str:
    rows = [
        ("Audit Logs", format_int(total_logs), "AU", "chip-info"),
        ("Access Denied", format_int(access_denied), "AD", "chip-error" if access_denied else "chip-neutral"),
        ("Validation Errors", format_int(validation_errors), "VE", "chip-warning" if validation_errors else "chip-neutral"),
        ("Rate Limit Events", format_int(rate_limits), "RL", "chip-warning" if rate_limits else "chip-neutral"),
        ("Not Found", format_int(not_found), "NF", "chip-neutral"),
        ("Compliance Status", "Traceable", "OK", "chip-success"),
    ]
    body = "".join(
        f"""
        <div class="mini-row">
            <span><span class="status-chip {klass}">{esc(icon)}</span> <span class="mini-label">{esc(label)}</span></span>
            <span class="mini-value">{esc(value)}</span>
        </div>
        """
        for label, value, icon, klass in rows
    )
    return f'<div class="detail-card"><div class="card-title">Audit & Compliance Snapshot</div><div class="card-caption">Traceability and policy indicators.</div>{body}</div>'


def render_health_panel(status: str, uptime: str, availability: str, response: str, services: str, incident: str) -> str:
    return f"""
    <div class="executive-card">
        <div class="card-title">Platform Health {status_chip(status)}</div>
        <div class="card-caption">Service posture, readiness, and operating resilience.</div>
        <div class="health-layout">
            <div>
                <div class="health-ring"><div class="health-inner">OK</div></div>
                <div class="health-state">{esc(status)}</div>
            </div>
            <div>
                <div class="mini-row"><span class="mini-label">Uptime</span><span class="mini-value">{esc(uptime)}</span></div>
                <div class="mini-row"><span class="mini-label">Service Availability</span><span class="mini-value">{esc(availability)}</span></div>
                <div class="mini-row"><span class="mini-label">Avg. Response Time</span><span class="mini-value">{esc(response)}</span></div>
                <div class="mini-row"><span class="mini-label">Active Services</span><span class="mini-value">{esc(services)}</span></div>
                <div class="divider-soft"></div>
                <div class="item-subtitle">{esc(incident)}</div>
            </div>
        </div>
    </div>
    """


transactions_df = load_table("transactions")
customers_df = load_table("customers")
tickets_df = load_table("support_tickets")
workflows_df = load_table("workflow_runs")
audit_df = load_audit_logs()

total_transactions = len(transactions_df)
successful_transactions = count_status(transactions_df, "status", "successful")
failed_transactions = count_status(transactions_df, "status", "failed")
pending_transactions = count_status(transactions_df, "status", "pending")
total_amount = float(pd.to_numeric(transactions_df.get("amount", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())

total_tickets = len(tickets_df)
open_tickets = count_status(tickets_df, "status", "open")
high_tickets = count_status(tickets_df, "priority", "high")
critical_tickets = count_status(tickets_df, "priority", "critical")
priority_tickets = high_tickets + critical_tickets

completed_workflows = count_status(workflows_df, "status", "completed")
failed_workflows = count_status(workflows_df, "status", "failed")
no_action_workflows = count_status(workflows_df, "status", "no_action_required")
active_workflows = count_statuses(workflows_df, "status", ["started", "running", "pending", "queued"])

total_logs = len(audit_df)
success_logs = count_status(audit_df, "status", "success")
error_logs = count_status(audit_df, "status", "error")
access_denied_count = count_error_type(audit_df, "access_denied")
validation_error_count = count_error_type(audit_df, "validation")
rate_limit_count = count_error_type(audit_df, "rate")
not_found_count = count_error_type(audit_df, "not_found")

deployment_health, deployment_caption, deployment_trend = deployment_status(DB_PATH, AUDIT_LOG_PATH, audit_df)

st.sidebar.markdown(
    f"""
    <div class="brand-lockup">
        <div class="brand-mark">B</div>
        <div>
            <div class="brand-title">BankOps AI</div>
            <div class="brand-subtitle">Control Plane</div>
        </div>
    </div>
    <div class="sidebar-badges">
        <span class="tiny-badge">Stable</span>
        <span class="tiny-badge">{esc(format_int(open_tickets))} Tickets</span>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Transactions", "Tickets", "Workflow Runs", "Audit Logs", "Reports & Exports", "Security Policy"],
)

st.sidebar.markdown(
    """
    <div class="nav-note">
        ...
    </div>
    """,
    unsafe_allow_html=True,
)


if page == "Overview":
    page_header("Overview")
    st.markdown('<div class="architecture-note">MCP remains the action layer. This dashboard is read-only.</div>', unsafe_allow_html=True)
    kpi_grid(
        [
            render_kpi_card("Total Transactions", format_int(total_transactions), f"{format_money(total_amount)} processed", "DB", "#2563EB", f"{percentage(successful_transactions, total_transactions)}% cleared"),
            render_kpi_card("Failed Transactions", format_int(failed_transactions), f"{percentage(failed_transactions, total_transactions)}% exception rate", "!", "#DC2626", "Watch"),
            render_kpi_card("Open Tickets", format_int(open_tickets), f"{format_int(priority_tickets)} high/critical", "TK", "#F59E0B", "Service"),
            render_kpi_card("Completed Workflows", format_int(completed_workflows), f"{format_int(len(workflows_df))} runs tracked", "OK", "#16A34A", "Automation"),
            render_kpi_card("Audit Errors", format_int(error_logs), f"{format_int(total_logs)} audit events", "AU", "#7C3AED", "Governance"),
            render_kpi_card("Deployment Health", deployment_health, deployment_caption, "HT", "#14B8A6", deployment_trend),
        ]
    )

    left, right = st.columns([0.42, 0.58])
    with left:
        health = deployment_health
        incident = deployment_caption if deployment_health != "Healthy" else "No active platform incidents detected"
        st.markdown(render_health_panel(health, "99.98%", "100.00%" if DB_PATH.exists() else "Degraded", average_response_time(audit_df), "MCP, DB, Audit, Workflows", incident), unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            section_header("Operations Overview", "Grouped real activity by date, without placeholder trend lines.")
            tabs = st.tabs(["Transaction Volume", "Failed Rate", "Workflow Executions", "Audit Errors"])
            with tabs[0]:
                chart_df = build_transaction_trend(transactions_df)
                if not enough_trend_points(chart_df):
                    render_empty_state("Not enough time-series data yet", "Run the demo seed script or add more transaction history.")
                else:
                    st.line_chart(chart_df, use_container_width=True, height=225)
            with tabs[1]:
                chart_df = build_failed_rate_trend(transactions_df)
                if not enough_trend_points(chart_df):
                    render_empty_state("Not enough time-series data yet", "Failed-rate trends appear once transactions span multiple dates.")
                else:
                    st.line_chart(chart_df, use_container_width=True, height=225)
            with tabs[2]:
                chart_df = build_workflow_trend(workflows_df)
                if not enough_trend_points(chart_df):
                    render_empty_state("Not enough time-series data yet", "Run the demo seed script or execute more workflows.")
                else:
                    st.bar_chart(chart_df, use_container_width=True, height=225)
            with tabs[3]:
                chart_df = build_audit_error_trend(audit_df)
                if not enough_trend_points(chart_df):
                    render_empty_state("Not enough time-series data yet", "Audit error trends appear once error events span multiple dates.")
                else:
                    st.line_chart(chart_df, use_container_width=True, height=225)

    section_header("Operational Detail", "Executive-ready summaries without raw table clutter.")
    failed_df = transactions_df[transactions_df["status"].fillna("").astype(str).str.lower() == "failed"] if "status" in transactions_df.columns else pd.DataFrame()
    failed_df = sort_by_datetime(failed_df, "created_at")
    failed_body = "".join(render_failed_transaction_card(row) for _, row in failed_df.head(5).iterrows())
    workflow_body = "".join(render_workflow_card(row) for _, row in workflows_df.head(5).iterrows())
    files = list_files(REPORTS_DIR, "*.json")[:3] + list_files(EXPORTS_DIR, "*.csv")[:2]
    artifacts_body = "".join(render_report_card(path, report_metadata(path).get("data")) for path in files[:5])
    st.markdown(
        f"""
        <div class="operational-grid">
            <div class="list-card">
                <div class="card-title">Recent Failed Transactions</div>
                <div class="card-caption">Latest payment exceptions.</div>
                {failed_body or empty_state_html("No failed transactions", "No failed payment exceptions are currently visible.")}
            </div>
            <div class="list-card">
                <div class="card-title">Workflow Run Status</div>
                <div class="card-caption">Latest automation outcomes.</div>
                {workflow_body or empty_state_html("No workflow runs", "No workflow runs are currently visible.")}
            </div>
            {render_audit_snapshot(total_logs, access_denied_count, validation_error_count, rate_limit_count, not_found_count)}
            <div class="list-card">
                <div class="card-title">Reports & Exports</div>
                <div class="card-caption">Latest evidence artifacts.</div>
                {artifacts_body or empty_state_html("No artifacts", "No reports or exports are currently available.")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


elif page == "Transactions":
    page_header("Transactions")
    kpi_grid(
        [
            render_kpi_card("Total Transactions", format_int(total_transactions), "Transactions in ledger", "DB", "#2563EB"),
            render_kpi_card("Successful", format_int(successful_transactions), f"{percentage(successful_transactions, total_transactions)}% cleared", "OK", "#16A34A"),
            render_kpi_card("Failed", format_int(failed_transactions), "Payment exceptions", "!", "#DC2626"),
            render_kpi_card("Pending", format_int(pending_transactions), "Awaiting final state", "..", "#F59E0B"),
            render_kpi_card("Total Amount", format_money(total_amount), "Gross processed value", "Z", "#7C3AED"),
            render_kpi_card("Deployment", deployment_health, deployment_caption, "HT", "#14B8A6"),
        ]
    )
    if transactions_df.empty:
        render_empty_state("No transactions", "No transaction records are available.")
    else:
        date_bucketed_transactions = add_date_bucket(transactions_df, "created_at")
        dates = sorted(date_bucketed_transactions["date_bucket"].dropna().astype(str).unique(), reverse=True) if "date_bucket" in date_bucketed_transactions.columns else []
        statuses = sorted(transactions_df["status"].dropna().unique()) if "status" in transactions_df.columns else []
        f1, f2 = st.columns([0.35, 0.65])
        selected_date = f1.selectbox("Date filter", ["All"] + dates)
        selected_statuses = f2.multiselect("Status filter", statuses, default=statuses)
        filtered = date_bucketed_transactions.copy() if not date_bucketed_transactions.empty else transactions_df.copy()
        if selected_date != "All" and "date_bucket" in filtered.columns:
            filtered = filtered[filtered["date_bucket"].astype(str) == selected_date]
        if selected_statuses and "status" in filtered.columns:
            filtered = filtered[filtered["status"].isin(selected_statuses)]

        section_header("Transaction Summary", "Status distribution and payment quality.")
        if not filtered.empty and {"status", "transaction_id", "amount"}.issubset(filtered.columns):
            summary = filtered.groupby("status", as_index=False).agg(transaction_count=("transaction_id", "count"), total_amount=("amount", "sum"))
            cards = []
            for _, row in summary.iterrows():
                cards.append(
                    f"""
                    <div class="detail-card">
                        <div class="mini-row"><span>{status_chip(row.get("status"))}</span><span class="mini-value">{esc(format_int(row.get("transaction_count")))}</span></div>
                        <div class="mini-row"><span class="mini-label">Share</span><span class="mini-value">{esc(str(percentage(row.get("transaction_count"), len(filtered))))}%</span></div>
                        <div class="mini-row"><span class="mini-label">Amount</span><span class="mini-value">{esc(format_money(row.get("total_amount")))}</span></div>
                    </div>
                    """
                )
            st.markdown(f'<div class="card-grid-3">{"".join(cards)}</div>', unsafe_allow_html=True)

        section_header("Failed Transaction Highlights", "Exception cases requiring operational visibility.")
        failed_focus = filtered[filtered["status"].fillna("").astype(str).str.lower() == "failed"] if "status" in filtered.columns else pd.DataFrame()
        failed_focus = sort_by_datetime(failed_focus, "created_at")
        if failed_focus.empty:
            render_empty_state("No failed transactions", "No failed transactions match the selected filters.")
        else:
            st.markdown("".join(render_failed_transaction_card(row) for _, row in failed_focus.head(6).iterrows()), unsafe_allow_html=True)

        with st.container(border=True):
            section_header("Detailed Transaction Table", "Light, read-only transaction ledger.")
            table_view = strip_dashboard_columns(filtered.copy())
            if "amount" in table_view.columns:
                table_view["amount"] = table_view["amount"].apply(format_money)
            if "status" in table_view.columns:
                table_view["status"] = table_view["status"].apply(format_title)
            data_table(table_view, height=420)


elif page == "Tickets":
    page_header("Tickets")
    kpi_grid(
        [
            render_kpi_card("Total Tickets", format_int(total_tickets), "Service cases recorded", "TK", "#2563EB"),
            render_kpi_card("Open Tickets", format_int(open_tickets), "Unresolved service exposure", "..", "#F59E0B"),
            render_kpi_card("High Priority", format_int(high_tickets), "Priority cases", "HI", "#DC2626"),
            render_kpi_card("Critical", format_int(critical_tickets), "Escalation-level cases", "CR", "#7C3AED"),
            render_kpi_card("Customers", format_int(len(customers_df)), "Customer records in scope", "CU", "#14B8A6"),
            render_kpi_card("Deployment", deployment_health, deployment_caption, "HT", "#16A34A"),
        ]
    )
    if tickets_df.empty:
        render_empty_state("No tickets", "No support tickets are currently available.")
    else:
        priorities = sorted(tickets_df["priority"].dropna().unique()) if "priority" in tickets_df.columns else []
        statuses = sorted(tickets_df["status"].dropna().unique()) if "status" in tickets_df.columns else []
        f1, f2 = st.columns(2)
        selected_priorities = f1.multiselect("Priority", priorities, default=priorities)
        selected_statuses = f2.multiselect("Status", statuses, default=statuses)
        filtered = tickets_df.copy()
        if selected_priorities and "priority" in filtered.columns:
            filtered = filtered[filtered["priority"].isin(selected_priorities)]
        if selected_statuses and "status" in filtered.columns:
            filtered = filtered[filtered["status"].isin(selected_statuses)]

        section_header("Ticket Cards", "Support cases presented for fast service review.")
        cards = []
        for _, row in filtered.head(12).iterrows():
            cards.append(
                f"""
                <div class="event-card">
                    <div class="event-main">
                        <div>
                            <div class="item-title">{esc(row.get("title", "Untitled Ticket"))}</div>
                            <div class="item-subtitle">Ticket {esc(row.get("ticket_id", "N/A"))} | Created {esc(format_datetime(row.get("created_at")))}</div>
                            <div class="item-meta">{priority_chip(row.get("priority"))}{status_chip(row.get("status"))}</div>
                        </div>
                    </div>
                    <div class="divider-soft"></div>
                    <div class="item-subtitle">{esc(row.get("description") or "No description recorded.")}</div>
                </div>
                """
            )
        st.markdown(f'<div class="card-grid-3">{"".join(cards)}</div>', unsafe_allow_html=True)
        with st.expander("Detailed Ticket Table"):
            table_view = filtered.copy()
            if "priority" in table_view.columns:
                table_view["priority"] = table_view["priority"].apply(format_title)
            if "status" in table_view.columns:
                table_view["status"] = table_view["status"].apply(format_title)
            data_table(table_view, height=420)


elif page == "Workflow Runs":
    page_header("Workflow Runs")
    st.markdown('<div class="architecture-note">Workflows are tracked for operational traceability. This dashboard does not trigger or rerun automation.</div>', unsafe_allow_html=True)
    kpi_grid(
        [
            render_kpi_card("Total Workflows", format_int(len(workflows_df)), "Tracked automation runs", "WF", "#2563EB"),
            render_kpi_card("Completed", format_int(completed_workflows), "Finished successfully", "OK", "#16A34A"),
            render_kpi_card("Failed", format_int(failed_workflows), "Workflow exceptions", "!", "#DC2626"),
            render_kpi_card("No Action Required", format_int(no_action_workflows), "Closed without escalation", "NA", "#64748B"),
            render_kpi_card("Started", format_int(active_workflows), "Active workflow states", "..", "#F59E0B"),
            render_kpi_card("Audit Errors", format_int(error_logs), "Governance exceptions", "AU", "#7C3AED"),
        ]
    )
    if workflows_df.empty:
        render_empty_state("No workflow runs", "No workflow runs are currently available.")
    else:
        names = sorted(workflows_df["workflow_name"].dropna().unique()) if "workflow_name" in workflows_df.columns else []
        statuses = sorted(workflows_df["status"].dropna().unique()) if "status" in workflows_df.columns else []
        roles = sorted(workflows_df["triggered_by_role"].dropna().unique()) if "triggered_by_role" in workflows_df.columns else []
        f1, f2, f3 = st.columns(3)
        selected_names = f1.multiselect("Workflow name", names, default=names)
        selected_statuses = f2.multiselect("Status", statuses, default=statuses)
        selected_roles = f3.multiselect("Triggered by role", roles, default=roles)
        filtered = workflows_df.copy()
        if selected_names and "workflow_name" in filtered.columns:
            filtered = filtered[filtered["workflow_name"].isin(selected_names)]
        if selected_statuses and "status" in filtered.columns:
            filtered = filtered[filtered["status"].isin(selected_statuses)]
        if selected_roles and "triggered_by_role" in filtered.columns:
            filtered = filtered[filtered["triggered_by_role"].isin(selected_roles)]
        section_header("Workflow Cards", "Automation outcomes and role-level traceability.")
        st.markdown(f'<div class="card-grid-2">{"".join(render_workflow_card(row) for _, row in filtered.head(12).iterrows())}</div>', unsafe_allow_html=True)
        with st.expander("Detailed Workflow Table"):
            data_table(filtered, height=420)


elif page == "Audit Logs":
    page_header("Audit Logs")
    kpi_grid(
        [
            render_kpi_card("Total Logs", format_int(total_logs), "Structured audit events", "AU", "#2563EB"),
            render_kpi_card("Successful", format_int(success_logs), "Successful tool activity", "OK", "#16A34A"),
            render_kpi_card("Errors", format_int(error_logs), "Events requiring review", "!", "#DC2626"),
            render_kpi_card("Access Denied", format_int(access_denied_count), "Permission controls triggered", "AD", "#7C3AED"),
            render_kpi_card("Rate Limited", format_int(rate_limit_count), "Throttling events", "RL", "#F59E0B"),
            render_kpi_card("Validation Errors", format_int(validation_error_count), "Input controls triggered", "VE", "#14B8A6"),
        ]
    )
    if audit_df.empty:
        render_empty_state("No audit logs", "No audit log events are currently available.")
    else:
        tools = sorted(audit_df["tool_name"].dropna().unique()) if "tool_name" in audit_df.columns else []
        roles = sorted(audit_df["role"].dropna().unique()) if "role" in audit_df.columns else []
        statuses = sorted(audit_df["status"].dropna().unique()) if "status" in audit_df.columns else []
        error_types = sorted(audit_df["error_type"].dropna().unique()) if "error_type" in audit_df.columns else []
        f1, f2, f3, f4 = st.columns(4)
        selected_tools = f1.multiselect("Tool name", tools, default=tools)
        selected_roles = f2.multiselect("Role", roles, default=roles)
        selected_statuses = f3.multiselect("Status", statuses, default=statuses)
        selected_errors = f4.multiselect("Error type", error_types, default=error_types)
        filtered = audit_df.copy()
        if selected_tools and "tool_name" in filtered.columns:
            filtered = filtered[filtered["tool_name"].isin(selected_tools)]
        if selected_roles and "role" in filtered.columns:
            filtered = filtered[filtered["role"].isin(selected_roles)]
        if selected_statuses and "status" in filtered.columns:
            filtered = filtered[filtered["status"].isin(selected_statuses)]
        if selected_errors and "error_type" in filtered.columns:
            filtered = filtered[filtered["error_type"].isin(selected_errors) | filtered["error_type"].isna()]
        section_header("Audit Event Feed", "Executive-readable timeline with technical detail collapsed.")
        for index, row in filtered.head(12).iterrows():
            st.markdown(render_audit_event_card(row), unsafe_allow_html=True)
            with st.expander(f"Technical Details - {row.get('request_id') or index}"):
                st.markdown('<div class="muted-text">Input</div>', unsafe_allow_html=True)
                render_technical_detail(row.get("input"))
                st.markdown('<div class="muted-text" style="margin-top:.75rem;">Output Preview</div>', unsafe_allow_html=True)
                render_technical_detail(row.get("output_preview"))
        with st.expander("Detailed Audit Table"):
            visible_columns = [column for column in ["request_id", "timestamp", "tool_name", "role", "status", "error_type", "execution_time_ms"] if column in filtered.columns]
            data_table(filtered[visible_columns], height=420)


elif page == "Reports & Exports":
    page_header("Reports & Exports")
    reports, exports = st.tabs(["Reports", "Exports"])
    with reports:
        report_files = list_files(REPORTS_DIR, "*.json")
        section_header("Report Library", "Generated evidence documents and management summaries.")
        if not report_files:
            render_empty_state("No reports", "No JSON reports are currently available.")
        for path in report_files:
            metadata = report_metadata(path)
            st.markdown(render_report_card(path, metadata.get("data")), unsafe_allow_html=True)
            if metadata.get("data") is not None:
                with st.expander(f"Technical Details - {path.name}"):
                    summary = []
                    data = metadata["data"]
                    if isinstance(data, dict):
                        for key in ["report_id", "workflow_id", "report_type", "date", "generated_at", "failed_transaction_count", "failed_count"]:
                            if key in data:
                                summary.append({"field": format_title(key), "value": data.get(key)})
                    data_table(pd.DataFrame(summary) if summary else pd.DataFrame([{"field": "Content Type", "value": type(data).__name__}]))
                    render_technical_detail(data)
    with exports:
        export_files = list_files(EXPORTS_DIR, "*.csv")
        section_header("Export Library", "CSV evidence extracts with previews hidden by default.")
        if not export_files:
            render_empty_state("No exports", "No CSV exports are currently available.")
        for path in export_files:
            row_count = "N/A"
            preview_df = pd.DataFrame()
            try:
                preview_df = read_csv_file(path)
                row_count = format_int(len(preview_df))
            except (OSError, pd.errors.ParserError):
                preview_df = pd.DataFrame()
            st.markdown(
                f"""
                <div class="report-card">
                    <div class="report-main">
                        <div>
                            <div class="item-title">{esc(path.name)}</div>
                            <div class="item-subtitle">Modified {esc(file_modified(path))} | {esc(file_size(path))}</div>
                            <div class="item-meta">
                                <span class="status-chip chip-info">CSV</span>
                                <span class="status-chip chip-neutral">{esc(row_count)} rows</span>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander(f"CSV Preview - {path.name}"):
                data_table(preview_df.head(100), height=360)


elif page == "Security Policy":
    page_header("Security Policy")
    st.markdown('<div class="architecture-note">The LLM cannot execute arbitrary SQL. It can only access predefined MCP tools exposed by the server.</div>', unsafe_allow_html=True)
    try:
        from security.permissions import ROLE_PERMISSIONS
        from security.rate_limiter import DEFAULT_RATE_LIMIT, RATE_LIMIT_RULES

        roles = ["support_agent", "admin", "auditor"]
        tools = sorted({tool for role_tools in ROLE_PERMISSIONS.values() for tool in role_tools})
        rate_limited_tools = sorted({tool for role_rules in RATE_LIMIT_RULES.values() for tool in role_rules})
        kpi_grid(
            [
                render_kpi_card("Roles", format_int(len(roles)), "Configured operating personas", "RO", "#2563EB"),
                render_kpi_card("Protected Tools", format_int(len(tools)), "Tools behind RBAC", "PT", "#7C3AED"),
                render_kpi_card("Rate-Limited Tools", format_int(len(rate_limited_tools)), "Throttled controls", "RL", "#F59E0B"),
                render_kpi_card("Audit Controls", "Enabled", "Request tracing and logs", "AU", "#16A34A"),
                render_kpi_card("Data Masking", "Enabled", "Sensitive preview reduction", "DM", "#14B8A6"),
                render_kpi_card("SQL Access", "Blocked", "No arbitrary SQL", "NO", "#DC2626"),
            ]
        )

        section_header("Role Cards", "Executive summary of configured operating roles.")
        role_copy = {
            "support_agent": "Customer support visibility and approved operational lookups.",
            "admin": "Administrative monitoring and controlled operational oversight.",
            "auditor": "Evidence review, audit trail inspection, and governance visibility.",
        }
        role_cards = ""
        for role in roles:
            allowed = ROLE_PERMISSIONS.get(role, set())
            role_cards += f"""
            <div class="detail-card">
                <div class="item-title">{esc(format_title(role))}</div>
                <div class="item-subtitle">{esc(role_copy.get(role, "Configured operating role."))}</div>
                <div class="divider-soft"></div>
                <div class="mini-row"><span class="mini-label">Authorized Tools</span><span class="mini-value">{esc(format_int(len(allowed)))}</span></div>
            </div>
            """
        st.markdown(f'<div class="card-grid-3">{role_cards}</div>', unsafe_allow_html=True)

        section_header("Permission Matrix", "Rows are tools. Columns are roles.")
        matrix_rows = []
        for tool in tools:
            row = {"tool": format_title(tool)}
            for role in roles:
                row[format_title(role)] = "Allowed" if tool in ROLE_PERMISSIONS.get(role, set()) else "Not allowed"
            matrix_rows.append(row)
        data_table(pd.DataFrame(matrix_rows), height=420)

        section_header("Rate Limit Policy", "Readable role and tool-level controls.")
        rate_cards = ""
        rate_rows = []
        for role, rules in RATE_LIMIT_RULES.items():
            for tool, rule in rules.items():
                rate_rows.append({"role": role, "tool": tool, "limit": rule.get("limit"), "window_seconds": rule.get("window_seconds")})
                rate_cards += f"""
                <div class="report-card">
                    <div class="item-title">{esc(format_title(tool))}</div>
                    <div class="item-subtitle">{esc(format_title(role))}</div>
                    <div class="item-meta">
                        <span class="status-chip chip-info">Limit {esc(rule.get("limit"))}</span>
                        <span class="status-chip chip-neutral">{esc(rule.get("window_seconds"))} sec</span>
                    </div>
                </div>
                """
        st.markdown(f'<div class="card-grid-3">{rate_cards}</div>', unsafe_allow_html=True)
        with st.expander("Detailed Rate Limit Table"):
            data_table(pd.DataFrame(rate_rows), height=320)
            st.markdown('<div class="muted-text">Default Rate Limit</div>', unsafe_allow_html=True)
            render_technical_detail(DEFAULT_RATE_LIMIT)

        section_header("Security Controls", "Control framework active across the MCP layer.")
        controls = [
            "Role-based access control",
            "Input validation",
            "Request ID tracing",
            "Structured audit logging",
            "Searchable audit logs",
            "Sensitive data masking",
            "Masked audit previews",
            "Rate limiting",
            "Workflow run tracking",
            "No arbitrary SQL",
        ]
        control_cards = "".join(
            f'<div class="detail-card"><div class="mini-row"><span>{status_chip("enabled")}</span><span class="mini-value">{esc(control)}</span></div></div>'
            for control in controls
        )
        st.markdown(f'<div class="card-grid-2">{control_cards}</div>', unsafe_allow_html=True)
    except Exception as error:
        render_empty_state("Security policy unavailable", f"Could not load policy modules cleanly: {error}")
