import re
import streamlit as st


_BG_PRIMARY   = "#0D1117"
_BG_CARD      = "#161B22"
_BORDER       = "#21262D"
_BORDER_MID   = "#30363D"
_TEXT_HIGH    = "#F0F6FC"
_TEXT_BODY    = "#C9D1D9"
_TEXT_MUTED   = "#8B949E"
_ACCENT_BLUE  = "#58A6FF"
_ACCENT_GREEN = "#3FB950"
_ACCENT_AMBER = "#F59E0B"
_ACCENT_RED   = "#FF4B4B"

_RISK_COLOURS = {
    "CRITICAL SYSTEMIC RISK": _ACCENT_RED,
    "CRITICAL":               _ACCENT_RED,
    "ELEVATED RISK":          _ACCENT_AMBER,
    "ELEVATED":               _ACCENT_AMBER,
    "MODERATE RISK":          _ACCENT_AMBER,
    "MODERATE":               _ACCENT_AMBER,
    "INVESTMENT GRADE":       _ACCENT_GREEN,
    "HEALTHY":                _ACCENT_GREEN,
    "NORMAL":                 _TEXT_HIGH,
}


def _resolve_risk_colour(risk_status: str) -> str:
    key = risk_status.upper().strip()
    for token, colour in _RISK_COLOURS.items():
        if token in key:
            return colour
    return _TEXT_HIGH


# GLOBAL THEME INJECTION

def inject_terminal_theme() -> None:

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"], .stApp, .main {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    background-color: {_BG_PRIMARY} !important;
    color: {_TEXT_BODY} !important;
}}

[data-testid="stSidebar"] {{
    background-color: {_BG_PRIMARY} !important;
    border-right: 1px solid {_BORDER} !important;
}}
[data-testid="stSidebar"] * {{ color: {_TEXT_BODY} !important; }}
[data-testid="stSidebar"] .stButton > button {{
    background-color: {_BG_CARD} !important;
    border: 1px solid {_BORDER_MID} !important;
    color: {_TEXT_BODY} !important;
    border-radius: 6px !important;
    font-size: 0.82rem !important;
    transition: all 0.15s ease !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    border-color: {_ACCENT_BLUE} !important;
    color: {_ACCENT_BLUE} !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    background-color: {_BG_PRIMARY} !important;
    border-bottom: 1px solid {_BORDER} !important;
    gap: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
    background-color: transparent !important;
    color: {_TEXT_MUTED} !important;
    border-radius: 0 !important;
    padding: 10px 20px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    border-bottom: 2px solid transparent !important;
    text-transform: uppercase !important;
}}
.stTabs [aria-selected="true"] {{
    color: {_TEXT_HIGH} !important;
    border-bottom: 2px solid {_ACCENT_BLUE} !important;
    background-color: transparent !important;
}}

[data-testid="stExpander"] {{
    background-color: {_BG_CARD} !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 6px !important;
    margin-bottom: 6px !important;
}}
[data-testid="stExpander"] summary {{
    color: {_TEXT_MUTED} !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
}}
[data-testid="stExpander"] summary:hover {{ color: {_TEXT_HIGH} !important; }}

[data-testid="stMetric"] {{
    background-color: {_BG_CARD} !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 8px !important;
    padding: 14px 16px !important;
}}
[data-testid="stMetricLabel"] {{
    color: {_TEXT_MUTED} !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}}
[data-testid="stMetricValue"] {{
    color: {_TEXT_HIGH} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricDelta"] {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
}}

[data-testid="stDataFrame"] {{
    border: 1px solid {_BORDER} !important;
    border-radius: 6px !important;
}}
.dvn-scroller {{ scrollbar-width: thin; scrollbar-color: {_BORDER_MID} {_BG_PRIMARY}; }}

[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{
    background-color: {_ACCENT_BLUE} !important;
}}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {{
    background-color: {_BG_CARD} !important;
    border: 1px solid {_BORDER_MID} !important;
    color: {_TEXT_HIGH} !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {{
    border-color: {_ACCENT_BLUE} !important;
    box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
}}

[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    background-color: {_BG_CARD} !important;
    border: 1px solid {_BORDER_MID} !important;
    color: {_TEXT_HIGH} !important;
    border-radius: 6px !important;
}}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #1F6FEB 0%, #0D47A1 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(31,111,235,0.4) !important;
}}

.mn-section-header {{
    color: {_TEXT_HIGH};
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 6px 0 8px 0;
    border-bottom: 1px solid {_BORDER};
    margin-bottom: 14px;
    font-family: 'JetBrains Mono', monospace;
}}

.mn-metric-card {{
    background-color: {_BG_CARD};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 14px 18px;
    height: 100%;
}}
.mn-metric-card .mc-label {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: {_TEXT_MUTED};
    margin-bottom: 4px;
}}
.mn-metric-card .mc-value {{
    font-size: 1.4rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.2;
}}
.mn-metric-card .mc-sub {{
    font-size: 0.72rem;
    color: {_TEXT_MUTED};
    margin-top: 5px;
}}

.mn-alert-critical {{
    background-color: rgba(255,75,75,0.08);
    border: 1px solid {_ACCENT_RED};
    border-left: 3px solid {_ACCENT_RED};
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 14px;
}}
.mn-alert-elevated {{
    background-color: rgba(245,158,11,0.08);
    border: 1px solid {_ACCENT_AMBER};
    border-left: 3px solid {_ACCENT_AMBER};
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 14px;
}}
.mn-alert-healthy {{
    background-color: rgba(35,134,54,0.08);
    border: 1px solid #238636;
    border-left: 3px solid #238636;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 14px;
}}
.mn-alert-neutral {{
    background-color: {_BG_CARD};
    border: 1px solid {_BORDER_MID};
    border-left: 3px solid {_BORDER_MID};
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 14px;
}}

.mn-demo-banner {{
    background: linear-gradient(90deg,rgba(31,111,235,0.12) 0%,rgba(13,71,161,0.06) 100%);
    border: 1px solid #1F6FEB;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 0.78rem;
    font-weight: 600;
    color: {_ACCENT_BLUE};
    letter-spacing: 0.4px;
    text-align: center;
    margin-bottom: 14px;
}}

.bb-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    font-family: 'Inter', sans-serif;
}}
.bb-table th {{
    background-color: {_BG_CARD};
    color: {_TEXT_MUTED};
    text-align: left;
    padding: 9px 12px;
    border-bottom: 1px solid {_BORDER};
    font-weight: 700;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}
.bb-table td {{
    padding: 9px 12px;
    border-bottom: 1px solid {_BG_CARD};
    color: {_TEXT_BODY};
    vertical-align: top;
}}
.bb-table tr:nth-child(even) td {{ background-color: rgba(22,27,34,0.6); }}
.bb-table tr:hover td {{ background-color: rgba(31,111,235,0.05); }}

.mn-ticker-ribbon {{
    background-color: {_BG_PRIMARY};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 9px 18px;
    margin-bottom: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
}}

.mn-pill {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
}}
.mn-pill-critical {{ background-color:rgba(255,75,75,0.15); color:{_ACCENT_RED}; border:1px solid rgba(255,75,75,0.3); }}
.mn-pill-grade    {{ background-color:rgba(35,134,54,0.15);  color:{_ACCENT_GREEN}; border:1px solid rgba(35,134,54,0.3); }}
.mn-pill-moderate {{ background-color:rgba(245,158,11,0.15); color:{_ACCENT_AMBER}; border:1px solid rgba(245,158,11,0.3); }}

.mn-divider {{
    border: none;
    border-top: 1px solid {_BORDER};
    margin: 22px 0;
}}

code, pre {{
    font-family: 'JetBrains Mono', monospace !important;
    background-color: {_BG_CARD} !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 4px !important;
    color: #79C0FF !important;
}}
</style>
""", unsafe_allow_html=True)


# COMPONENT RENDERERS

def render_metric_card(
    label: str,
    value: str,
    sub_text: str = "",
    risk_status: str = "NORMAL",
) -> None:

    colour = _resolve_risk_colour(risk_status)
    sub_html = f'<div class="mc-sub">{sub_text}</div>' if sub_text else ""
    st.markdown(
        f'<div class="mn-metric-card">'
        f'<div class="mc-label">{label}</div>'
        f'<div class="mc-value" style="color:{colour};">{value}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_section_header(text: str) -> None:
    st.markdown(
        f"<div class='mn-section-header'>{text}</div>",
        unsafe_allow_html=True,
    )


def render_divider() -> None:
    st.markdown("<hr class='mn-divider'/>", unsafe_allow_html=True)


def render_alert_box(message: str, level: str = "healthy") -> None:

    css_cls = {
        "critical": "mn-alert-critical",
        "elevated": "mn-alert-elevated",
        "healthy":  "mn-alert-healthy",
        "neutral":  "mn-alert-neutral",
    }.get(level.lower(), "mn-alert-neutral")
    st.markdown(f'<div class="{css_cls}">{message}</div>', unsafe_allow_html=True)


def render_bb_table(headers: list, rows: list) -> None:

    th_html = "".join(f"<th>{h}</th>" for h in headers)
    tr_html = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
        for row in rows
    )
    st.markdown(
        f'<table class="bb-table"><thead><tr>{th_html}</tr></thead>'
        f'<tbody>{tr_html}</tbody></table>',
        unsafe_allow_html=True,
    )


def render_ticker_ribbon(tape: dict | None = None) -> None:

    if tape is None:
        tape = {
            "dimo_price": 0.1645, "dimo_change":  3.12,
            "hnt_price":  6.8520, "hnt_change":  -1.45,
            "sol_price":  184.25, "sol_change":   5.82,
            "depin_sentiment": 78,
        }

    def _fmt_price(price: float) -> str:
        if price < 0.01:
            return f"${price:.6f}"
        if price < 1:
            return f"${price:.4f}"
        if price < 1_000:
            return f"${price:,.2f}"
        return f"${price:,.0f}"

    def _fmt_change(chg: float) -> tuple[str, str]:
        """Return (arrow+text, colour)."""
        arrow  = "▲" if chg >= 0 else "▼"
        colour = _ACCENT_GREEN if chg >= 0 else _ACCENT_RED
        return f"{arrow} {chg:+.2f}%", colour

    dimo_p_str           = _fmt_price(tape["dimo_price"])
    hnt_p_str            = _fmt_price(tape["hnt_price"])
    sol_p_str            = _fmt_price(tape["sol_price"])
    dimo_chg_str, dimo_c = _fmt_change(tape["dimo_change"])
    hnt_chg_str,  hnt_c  = _fmt_change(tape["hnt_change"])
    sol_chg_str,  sol_c  = _fmt_change(tape["sol_change"])
    sentiment            = tape.get("depin_sentiment", 78)
    sent_label           = "Stable/Bullish" if sentiment >= 65 else ("Neutral" if sentiment >= 45 else "Bearish")

    st.markdown(
        f'<div class="mn-ticker-ribbon">'
        f'<span style="color:{dimo_c}; font-weight:600;">&#9679; DIMO/USD &nbsp;{dimo_p_str} &nbsp;{dimo_chg_str}</span>'
        f'<span style="color:{hnt_c}; font-weight:600;">&#9679; HNT/USD &nbsp;{hnt_p_str} &nbsp;{hnt_chg_str}</span>'
        f'<span style="color:{sol_c}; font-weight:600;">&#9679; SOL/USD &nbsp;{sol_p_str} &nbsp;{sol_chg_str}</span>'
        f'<span style="color:{_ACCENT_BLUE}; font-weight:600;">&#9679; DePIN Sentiment Index &nbsp;{sentiment} &nbsp;&mdash; {sent_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_hero_header() -> None:
    """Render the MARKETNODE ALPHA TERMINAL title block."""
    st.markdown(
        f'<div style="text-align:center; margin-bottom:6px;">'
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:1.9rem; font-weight:700;'
        f' color:{_TEXT_HIGH}; letter-spacing:3px;">MARKETNODE ALPHA TERMINAL</span>'
        f'</div>'
        f'<div style="text-align:center; margin-bottom:20px;">'
        f'<span style="font-size:0.7rem; color:{_TEXT_MUTED}; letter-spacing:3.5px;'
        f' text-transform:uppercase; font-family:\'Inter\',sans-serif;">'
        f'Institutional-Grade Intelligence &nbsp;·&nbsp; Quantitative Risk Analysis'
        f'</span></div>',
        unsafe_allow_html=True,
    )


def render_sidebar_logo() -> None:
    """Render the MARKETNODE wordmark and tagline in the sidebar."""
    st.sidebar.markdown(
        f'<div style="text-align:center; padding:10px 0 4px 0;">'
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:1.25rem;'
        f' font-weight:700; color:{_TEXT_HIGH}; letter-spacing:2px;">MARKETNODE</span><br>'
        f'<span style="font-size:0.62rem; color:{_TEXT_MUTED}; letter-spacing:3px;'
        f' text-transform:uppercase;">Alpha Terminal</span>'
        f'</div>'
        f'<hr style="border-color:{_BORDER}; margin:12px 0;"/>',
        unsafe_allow_html=True,
    )


def render_awaiting_state() -> None:
    """Render the empty-state placeholder before any analysis is run."""
    st.markdown(
        f'<div style="background-color:{_BG_CARD}; border:1px solid {_BORDER};'
        f' border-left:3px solid {_BORDER_MID}; border-radius:8px;'
        f' padding:48px 36px; text-align:center; margin-top:20px;">'
        f'<div style="font-size:2rem; margin-bottom:12px;">📡</div>'
        f'<div style="font-size:1.1rem; font-weight:600; color:{_TEXT_HIGH}; margin-bottom:8px;">'
        f'Awaiting Intelligence Query</div>'
        f'<div style="font-size:0.88rem; color:{_TEXT_MUTED}; max-width:440px;'
        f' margin:0 auto; line-height:1.6;">'
        f'No active intelligence target selected. Type a cryptographic asset ticker'
        f' (e.g. <b style="color:{_ACCENT_BLUE};">ETH</b>, <b style="color:{_ACCENT_BLUE};">BNB</b>,'
        f' <b style="color:{_ACCENT_BLUE};">DIMO</b>) into the Asset Parameters field'
        f' — telemetry loads automatically — or hit'
        f' <b style="color:{_ACCENT_BLUE};">🚀 Demo: BNB</b> for an instant preview.'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def render_demo_banner(sidebar: bool = False) -> None:
    """
    Render the blue DEMONSTRATION MODE banner.

    Parameters
    ----------
    sidebar : True → render into sidebar; False → main area.
    """
    if sidebar:
        st.sidebar.markdown(
            "<div class='mn-demo-banner'>🧪 &nbsp;DEMONSTRATION MODE — BNB ASSET LOADED</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='mn-demo-banner' style='font-size:0.82rem; margin-bottom:18px;'>"
            "🧪 &nbsp;DEMONSTRATION MODE ACTIVE &nbsp;—&nbsp; BNB ASSET INTELLIGENCE LOADED"
            " &nbsp;—&nbsp; All metrics are deterministic fallback data for evaluation purposes."
            "</div>",
            unsafe_allow_html=True,
        )


def get_verdict_pill_html(verdict_summary: str) -> str:
    """Return an inline HTML <span> verdict pill for the given verdict string."""
    if "Critical" in verdict_summary:
        cls = "mn-pill mn-pill-critical"
    elif "Investment Grade" in verdict_summary or "Grade" in verdict_summary:
        cls = "mn-pill mn-pill-grade"
    else:
        cls = "mn-pill mn-pill-moderate"
    return f'<span class="{cls}">{verdict_summary}</span>'


def linkify_footnotes(text: str, manifest: dict) -> str:

    if not text or not manifest:
        return text

    def replace_fn(match):
        fid = match.group(1)
        if fid in manifest:
            url = manifest[fid]
            return (
                f'<sup><a href="{url}" target="_blank"'
                f' style="color:{_ACCENT_BLUE}; font-weight:bold; text-decoration:none;">'
                f'[{fid}]</a></sup>'
            )
        return match.group(0)

    return re.sub(r'\[(\d+)\]', replace_fn, text)


def render_ai_badge_field(title: str, value: str, manifest: dict) -> None:

    is_predictive = "[AI Predictive Estimate]" in str(value)
    clean_val = str(value).replace("[AI Predictive Estimate]", "").strip()
    clean_val = linkify_footnotes(clean_val, manifest)

    if is_predictive:
        st.markdown(
            f'<div style="border-left:3px solid #1F6FEB; padding:0.5rem 0.85rem;'
            f' margin-bottom:0.85rem; background-color:rgba(31,111,235,0.06); border-radius:4px;">'
            f'<span style="font-size:0.68rem; background-color:#1F6FEB; color:#FFFFFF;'
            f' padding:1px 6px; border-radius:3px; font-weight:700; text-transform:uppercase;'
            f' font-family:monospace; letter-spacing:0.5px;">AI Predictive Estimate</span>'
            f'<p style="margin:5px 0 0 0; font-size:0.93rem; line-height:1.5; color:{_TEXT_BODY};">'
            f'<b>{title}:</b> {clean_val}</p></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="padding:0.25rem 0; margin-bottom:0.75rem;">'
            f'<p style="margin:0; font-size:0.93rem; line-height:1.5; color:{_TEXT_BODY};">'
            f'<b>{title}:</b> {clean_val}</p></div>',
            unsafe_allow_html=True,
        )

# SIDEBAR — PRECISION COMPONENTS

def render_sidebar_status_badge(api_connected: bool) -> None:

    if api_connected:
        dot_colour  = _ACCENT_GREEN
        dot_shadow  = "0 0 6px rgba(63,185,80,0.8)"
        mode_label  = "DATA MODE: LIVE ENGINE"
        mode_colour = _ACCENT_GREEN
    else:
        dot_colour  = _ACCENT_AMBER
        dot_shadow  = "none"
        mode_label  = "DATA MODE: BENCHMARK ENGINE"
        mode_colour = _ACCENT_AMBER

    st.sidebar.markdown(
        f'<div style="display:flex; align-items:center; gap:8px;'
        f' background-color:{_BG_CARD}; border:1px solid {_BORDER};'
        f' border-radius:20px; padding:5px 12px; margin:4px 0 12px 0;">'
        f'<span style="width:7px; height:7px; border-radius:50%;'
        f' background-color:{dot_colour}; box-shadow:{dot_shadow};'
        f' flex-shrink:0; display:inline-block;"></span>'
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:0.62rem;'
        f' font-weight:700; color:{mode_colour}; letter-spacing:0.8px;'
        f' text-transform:uppercase;">{mode_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_section_divider(label: str) -> None:

    st.sidebar.markdown(
        f'<hr style="border:none; border-top:1px solid {_BORDER}; margin:14px 0 10px 0;"/>'
        f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:0.62rem;'
        f' font-weight:700; text-transform:uppercase; letter-spacing:1.4px;'
        f' color:{_TEXT_MUTED}; padding-bottom:8px;">{label}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_field_label(label: str) -> None:

    st.sidebar.markdown(
        f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:0.58rem;'
        f' font-weight:700; text-transform:uppercase; letter-spacing:1.2px;'
        f' color:{_TEXT_MUTED}; padding: 6px 0 3px 0; margin-top:4px;">{label}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_pdf_success(project: str) -> None:

    st.sidebar.markdown(
        f'<div style="display:flex; align-items:center; gap:8px;'
        f' background-color:rgba(35,134,54,0.08); border:1px solid #238636;'
        f' border-left:3px solid {_ACCENT_GREEN}; border-radius:4px;'
        f' padding:8px 12px; margin-bottom:8px;">'
        f'<span style="color:{_ACCENT_GREEN}; font-size:0.88rem;">✓</span>'
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:0.65rem;'
        f' font-weight:700; color:{_ACCENT_GREEN}; letter-spacing:0.6px;'
        f' text-transform:uppercase;">{project.upper()} DOSSIER COMPILED</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_brand_footer() -> None:

    st.sidebar.markdown(
        f'<div style="margin-top:auto; padding-top:18px;">'
        f'<div style="background-color:{_BG_CARD}; border:1px solid {_BORDER};'
        f' border-radius:4px; padding:8px 12px; text-align:center;">'
        f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:0.58rem;'
        f' font-weight:700; color:{_TEXT_MUTED}; letter-spacing:0.6px;'
        f' text-transform:uppercase; line-height:1.6;">'
        f'MARKETNODE INTEL ALPHA v1.0.4</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:0.55rem;'
        f' color:{_BORDER_MID}; letter-spacing:0.4px; text-transform:uppercase;">'
        f'— COMPLIANCE LOCKED —</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

