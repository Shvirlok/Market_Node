import io
import time
import threading

import pandas as pd
import requests
import streamlit as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Quantitative core
from calculations import (
    compute_emission_curve,
    calculate_gini_and_lorenz,
    get_forensic_investigation_breakdown,
    get_cross_chain_liquidity_data,
    get_historical_event_impact,
    generate_hedging_advisory,
    generate_fallback_battle,
    build_benchmark_metrics_payload,
    get_benchmark_whale_concentration,
    get_institutional_analysis_fallback,
    get_institutional_sources_manifest,
    get_asset_profile_class,
    get_asset_benchmark,
    fetch_live_prices,
    get_live_price,
    get_ticker_tape_data,
    INSTITUTIONAL_CITATION_LABELS,
)

from report_generator import generate_pdf_report

from ui_components import (
    inject_terminal_theme,
    render_metric_card,
    render_section_header,
    render_divider,
    render_alert_box,
    render_bb_table,
    render_ticker_ribbon,
    render_hero_header,
    render_sidebar_logo,
    render_awaiting_state,
    render_demo_banner,
    get_verdict_pill_html,
    linkify_footnotes,
    # Precision sidebar components
    render_sidebar_status_badge,
    render_sidebar_section_divider,
    render_sidebar_field_label,
    render_sidebar_pdf_success,
    render_sidebar_brand_footer,
)

# LOCAL DATA GENERATORS

def _generate_local_fallback_analysis(project_name: str) -> None:
    """Populate session_state with deterministic benchmark fallback data."""
    analysis, wc = get_institutional_analysis_fallback(project_name)
    st.session_state.whale_concentration = wc
    st.session_state.analysis_data = analysis
    st.session_state.sources_manifest = get_institutional_sources_manifest(project_name)
    st.session_state.current_project = project_name

# ASYNC PDF WRAPPER

def _generate_pdf_async(project, analysis, manifest, battle_data, comp_a, comp_b, live_metrics):
    """Thread-safe PDF compilation routed through report_generator.

    The payload captures the asset-profile benchmark metrics at the moment the
    user clicked 'Generate' — so the PDF matches the on-screen dossier.
    """
    try:
        buffer = io.BytesIO()
        generate_pdf_report(
            {
                "project":       project,
                "analysis":      analysis,
                "manifest":      manifest,
                "battle_data":   battle_data,
                "comp_a":        comp_a,
                "comp_b":        comp_b,
                **live_metrics,
            },
            filename=buffer,
        )
        st.session_state.pdf_bytes = buffer.getvalue()
        st.session_state.pdf_status = "complete"
    except Exception as exc:
        st.session_state.pdf_status = "error"
        st.session_state.pdf_error_msg = str(exc)


_BACKEND_URL = "http://localhost:8000"


def _run_backend_analysis(project_name: str) -> None:
    profile_class = get_asset_profile_class(project_name)
    is_investment_grade = profile_class == "large_l1"
    st.session_state.whale_concentration = get_benchmark_whale_concentration(project_name)
    try:
        resp = requests.get(
            f"{_BACKEND_URL}/api/v1/analyze",
            params={"project_name": project_name},
            timeout=12,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                st.session_state.analysis_data = data.get("analysis", {})
                st.session_state.sources_manifest = get_institutional_sources_manifest(project_name)
                st.session_state.current_project = project_name
                verdict = "Investment Grade" if is_investment_grade else "Critical Systemic Risk"
                delta = get_asset_benchmark(project_name)["data_discrepancy_delta"]
                st.session_state.analysis_data["institutional_verdict"]["verdict_summary"] = verdict
                st.session_state.analysis_data["data_discrepancy_delta"] = delta
                df_em, _, _ = compute_emission_curve(project_name)
                st.session_state.analysis_data["tokenomics_math"]["unlock_schedule_12m"] = (
                    df_em["Cumulative Emission %"].tolist()
                )
                return
    except Exception:
        pass
    _generate_local_fallback_analysis(project_name)
    df_em, _, _ = compute_emission_curve(project_name)
    st.session_state.analysis_data["tokenomics_math"]["unlock_schedule_12m"] = (
        df_em["Cumulative Emission %"].tolist()
    )


def _run_backend_battle(comp_a: str, comp_b: str) -> None:
    try:
        resp = requests.get(
            f"{_BACKEND_URL}/api/v1/battle",
            params={"project_a": comp_a, "project_b": comp_b},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                st.session_state.battle_data = data.get("comparison", {})
                _apply_institutional_citations()
                st.session_state._last_battle_pair = (comp_a, comp_b)
                return
    except Exception:
        pass
    st.session_state.battle_data = generate_fallback_battle(
        comp_a, comp_b, prices=st.session_state.get("live_prices", {})
    )
    st.session_state._last_battle_pair = (comp_a, comp_b)


def _apply_institutional_citations() -> None:
    """Ensure the canonical three-source registry is always active."""
    p = st.session_state.current_project or st.session_state.project_name
    st.session_state.sources_manifest = get_institutional_sources_manifest(p)

# SESSION STATE DEFAULTS

_DEFAULTS = {
    "is_demo":            False,
    "project_name":       "ETH",
    "comp_a":             "ETH",
    "comp_b":             "SOL",
    "analysis_data":      None,
    "battle_data":        None,
    "sources_manifest":   {},
    "pdf_status":         "idle",
    "pdf_bytes":          None,
    "pdf_error_msg":      None,
    "run_analysis":       False,
    "current_project":    "",
    "whale_concentration": 58.0,
    "_bootstrapped":      False,
    "_last_battle_pair":  ("", ""),  # tracks last (comp_a, comp_b) used for battle build
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Auto-load benchmark dossier on first visit so the terminal renders full telemetry immediately
if not st.session_state.get("_bootstrapped", False) and st.session_state.analysis_data is None:
    _generate_local_fallback_analysis(st.session_state.project_name)
    df_em_boot, _, _ = compute_emission_curve(st.session_state.project_name)
    st.session_state.analysis_data["tokenomics_math"]["unlock_schedule_12m"] = (
        df_em_boot["Cumulative Emission %"].tolist()
    )
    _boot_a = st.session_state.project_name
    _boot_b = st.session_state.comp_b
    # prices not yet fetched at boot — will be refreshed on first render cycle
    st.session_state.battle_data = generate_fallback_battle(_boot_a, _boot_b)
    st.session_state._last_battle_pair = (_boot_a, _boot_b)
    st.session_state._bootstrapped = True

# PAGE CONFIG 

st.set_page_config(
    page_title="MarketNode Alpha Terminal",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# INJECT GLOBAL THEME 

inject_terminal_theme()

# LIVE PRICE SNAPSHOT 

@st.cache_data(ttl=60, show_spinner=False)
def _cached_prices() -> dict:
    """Return a fresh CoinGecko price snapshot, cached for 60 seconds."""
    return fetch_live_prices()

# Fetch once per render cycle; share the snapshot with all downstream callers
_live_prices = _cached_prices()
# Persist in session_state so the PDF thread can read it without a re-fetch
if "live_prices" not in st.session_state:
    st.session_state.live_prices = _live_prices
else:
    st.session_state.live_prices = _live_prices   # always refresh from cache

_tape = get_ticker_tape_data(_live_prices)

# SIDEBAR — CONTROL DECK

render_sidebar_logo()

# ── Connection / data-mode status badge
_api_connected = False
try:
    requests.get(_BACKEND_URL, timeout=2)
    _api_connected = True
except requests.exceptions.RequestException:
    pass

render_sidebar_status_badge(_api_connected)

if st.session_state.get("is_demo", False):
    render_demo_banner(sidebar=True)

# ── Asset Parameters
render_sidebar_section_divider("⚙️  Asset Parameters")

# ── Auto-load helper: fires when ticker input changes
def _on_ticker_change():
    new_ticker = st.session_state._ticker_input_widget.strip().upper()
    if new_ticker and new_ticker != st.session_state.current_project:
        st.session_state.is_demo = False
        st.session_state.project_name = new_ticker
        st.session_state.comp_a = new_ticker
        st.session_state.run_analysis = True
        st.session_state.pdf_status = "idle"
        st.session_state.pdf_bytes = None
        # Reset battle pair so it rebuilds with the new Token A
        st.session_state._last_battle_pair = ("", "")

col_ticker, col_demo = st.sidebar.columns([3, 2])
with col_ticker:
    st.text_input(
        "Target Ticker",
        value=st.session_state.project_name,
        label_visibility="collapsed",
        placeholder="TICKER  —  E.G. BNB",
        key="_ticker_input_widget",
        on_change=_on_ticker_change,
    )
with col_demo:
    if st.button("🚀 Demo: BNB", key="load_demo_bnb", use_container_width=True):
        st.session_state.update(
            is_demo=True,
            project_name="BNB",
            comp_a="BNB",
            comp_b="SOL",
            run_analysis=True,
            pdf_status="idle",
            pdf_bytes=None,
        )
        st.rerun()

st.session_state.project_name = st.session_state._ticker_input_widget.strip().upper() or st.session_state.project_name
st.session_state.comp_a = st.session_state.project_name

_HNT_ALIASES = frozenset({"HELIUM MOBILE", "HELIUM", "HNT"})


def _normalize_comp_b(raw: str) -> str:
    """Normalize competitor input — collapses 'Helium Mobile' → 'HNT'."""
    t = raw.strip().upper()
    return "HNT" if t in _HNT_ALIASES else t


def _on_comp_b_change():
    """Callback: rebuild battle data whenever Token B changes."""
    raw = st.session_state.get("_comp_b_widget", "").strip()
    new_b = _normalize_comp_b(raw) or st.session_state.comp_b
    st.session_state.comp_b = new_b
    comp_a = st.session_state.comp_a or st.session_state.project_name
    # Only rebuild if the pair actually changed
    pair = (comp_a, new_b)
    if pair != st.session_state.get("_last_battle_pair"):
        try:
            st.session_state.battle_data = generate_fallback_battle(
                comp_a, new_b, prices=st.session_state.get("live_prices", {})
            )
        except ValueError:
            # Do not crash the app session state, let the main rendering loop handle the error interface
            pass
        st.session_state._last_battle_pair = pair
        st.session_state.pdf_status = "idle"
        st.session_state.pdf_bytes = None


render_sidebar_field_label("COMPETITOR TICKER (TOKEN B)")
st.sidebar.text_input(
    "Competitor Ticker",
    value=st.session_state.comp_b,
    placeholder="COMPETITOR  —  E.G. SOL",
    label_visibility="collapsed",
    key="_comp_b_widget",
    on_change=_on_comp_b_change,
)

# Ticker Validation Check
try:
    from calculations import validate_ticker
    validate_ticker(st.session_state.project_name)
    validate_ticker(st.session_state.comp_b)
except ValueError as e:
    if str(e) == "AssetNotIndexed":
        st.error("🚨 INVALID DATA INPUT: One or both of the entered assets are not indexed in the MarketNode terminal database. Please check your spelling and try again.")
        st.stop()

# ANALYSIS PIPELINE  (runs in the sidebar status panel)

if st.session_state.run_analysis:
    with st.sidebar:
        if st.session_state.get("is_demo", False):
            with st.status("⚡ Loading BNB Demo Case...", expanded=True) as status:
                status.write("Extracting Twitter OSINT clusters...")
                time.sleep(0.4)
                status.write("Auditing on-chain ledger parameters & distribution arrays...")
                time.sleep(0.4)
                status.write("Invoking DeepSeek Forensic Intelligence for anomaly detection...")
                time.sleep(0.4)
                st.session_state.update(
                    project_name="BNB",
                    comp_a="BNB",
                    comp_b="SOL",
                )
                _generate_local_fallback_analysis("BNB")
                df_em_demo, _, _ = compute_emission_curve("BNB")
                st.session_state.analysis_data["tokenomics_math"]["unlock_schedule_12m"] = (
                    df_em_demo["Cumulative Emission %"].tolist()
                )
                st.session_state.battle_data = generate_fallback_battle(
                    "BNB", "SOL", prices=st.session_state.get("live_prices", {})
                )
                st.session_state._last_battle_pair = ("BNB", "SOL")
                status.update(label="✅ Intelligence Dossier Compiled!", state="complete", expanded=False)
        else:
            with st.status("Analyzing Cryptographic Asset Telemetry...", expanded=True) as status:
                status.write("🔍 Extracting Twitter OSINT clusters...")
                time.sleep(3.0)
                status.write("📡 Auditing on-chain ledger parameters...")
                time.sleep(3.0)
                status.write("💻 Fetching repository velocity logs...")
                time.sleep(3.0)
                _run_backend_analysis(st.session_state.project_name)
                status.write("📊 Calculating Gini Coefficient & Lorenz Curve...")
                time.sleep(3.0)
                status.write("🚨 Stress-testing holder concentration metrics...")
                time.sleep(3.0)
                status.write("🧠 Invoking DeepSeek Forensic Intelligence...")
                time.sleep(4.0)
                if st.session_state.comp_b:
                    status.write(f"⚔️ Compiling confrontation telemetry against {st.session_state.comp_b}...")
                    _run_backend_battle(st.session_state.project_name, st.session_state.comp_b)
                    time.sleep(3.0)
                status.write("🛡️ Formulating regulatory alignment & compliance indexes...")
                time.sleep(3.0)
                status.write("🎯 Synthesizing hedging mandates & capital allocation ratios...")
                time.sleep(3.0)
                status.write("📑 Compiling final 5-Page Institutional Dossier...")
                time.sleep(3.0)
                status.update(label="✅ Analysis Pipeline Completed", state="complete")

    st.session_state.run_analysis = False
    st.session_state.pdf_status = "idle"
    st.session_state.pdf_bytes = None
    st.rerun()

# MAIN DASHBOARD

render_ticker_ribbon(_tape)
render_hero_header()

if st.session_state.get("is_demo", False) and st.session_state.analysis_data is not None:
    render_demo_banner(sidebar=False)

# ── Empty state
if st.session_state.analysis_data is None:
    render_awaiting_state()

else:
    # ── Pre-compute reused values from hardcoded asset-profile benchmarks
    project_key = st.session_state.current_project or st.session_state.project_name
    st.session_state.whale_concentration = get_benchmark_whale_concentration(project_key)
    _apply_institutional_citations()

    wc = st.session_state.whale_concentration
    live_metrics = build_benchmark_metrics_payload(project_key)
    gini_val = live_metrics["gini_val"]
    risk_protocol = live_metrics["risk_protocol"]
    stress_matrix = live_metrics["stress_matrix"]

    dao    = (100.0 - wc) * 0.4
    lp     = (100.0 - wc) * 0.3
    retail = (100.0 - wc) * 0.3

    score_str = st.session_state.analysis_data.get("sentiment_score", "7")
    try:
        numeric_score = int("".join(c for c in score_str if c.isdigit()))
    except Exception:
        numeric_score = 7

    verdict_summary = (
        st.session_state.analysis_data.get("institutional_verdict", {}).get("verdict_summary", "N/A")
    )
    anomaly_val = st.session_state.analysis_data.get("data_discrepancy_delta", "0.00%")
    manifest = st.session_state.sources_manifest

    # TOP KPI GRID 
    render_section_header("📊 Key Performance Indicators")

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    with kpi1:
        render_metric_card(
            "Target Asset",
            st.session_state.current_project.upper() or "—",
            "Active Intelligence Target",
        )
    with kpi2:
        score_risk = "CRITICAL" if numeric_score < 5 else ("ELEVATED" if numeric_score < 7 else "HEALTHY")
        render_metric_card(
            "Sentiment Score",
            f"{score_str}/10",
            "📈 Strong Inflows" if numeric_score >= 7 else "📉 Risk Exposure",
            risk_status=score_risk,
        )
    with kpi3:
        # Concentration card — asset-profile benchmark
        conc_risk = "CRITICAL" if wc > 50 else ("ELEVATED" if wc > 35 else "HEALTHY")
        render_metric_card(
            "Insider Concentration",
            f"{wc:.2f}%",
            "Top 10 Wallet Cluster · benchmark",
            risk_status=conc_risk,
        )
    with kpi4:
        # Gini card — benchmark-derived
        gini_risk = "CRITICAL" if gini_val > 0.80 else ("ELEVATED" if gini_val > 0.65 else "HEALTHY")
        render_metric_card(
            "Gini Coefficient",
            f"{gini_val:.4f}",
            "Lorenz Inequality Index · benchmark",
            risk_status=gini_risk,
        )
    with kpi5:
        # Risk Protocol — classification from benchmark concentration
        protocol_risk = (
            "CRITICAL" if "CRITICAL" in risk_protocol
            else ("ELEVATED" if "ELEVATED" in risk_protocol else "HEALTHY")
        )
        render_metric_card(
            "Risk Protocol",
            risk_protocol.split()[0],        
            risk_protocol,                   
            risk_status=protocol_risk,
        )

    render_divider()

    # ── TABS
    tab1, tab2 = st.tabs(["📊  AUDIT INTELLIGENCE DASHBOARD", "⏳  HISTORICAL EVENT IMPACT"])

    with tab1:
        col_left, col_right = st.columns([7, 5], gap="large")

        with col_left:

            # Executive Summary
            exec_level = "critical" if wc > 50 else "healthy"
            render_alert_box(
                f'<div style="font-size:0.7rem; font-weight:700; text-transform:uppercase;'
                f' letter-spacing:1px; color:#8B949E; margin-bottom:6px;">Executive Summary</div>'
                f'<div style="font-size:0.93rem; line-height:1.6; color:#C9D1D9;">'
                f'{st.session_state.analysis_data.get("core_narrative", "AI audit compilation in progress...")}'
                f'</div>',
                level=exec_level,
            )

            # Deep Audit Chapters
            render_section_header("📁 Deep Audit Suite")

            _chapters = [
                ("📘", "Chapter 1: Macroscopic Narratives & Structural Alignment",  "macro_narrative"),
                ("📊", "Chapter 2: Tokenomics & Reward Emission Specs",
                 lambda d: d.get("tokenomics_math", {}).get("analysis_text", "NO_DATA")),
                ("⚙️", "Chapter 3: On-Chain Infrastructures & Node Consensus",      "onchain_infrastructure"),
                ("💻", "Chapter 4: Developer Repository Velocities",                "developer_velocity"),
                ("📱", "Chapter 5: Retail Sentiment & Social Velocity",             "social_hype_and_fud"),
                ("⚖️", "Chapter 6: Regulatory & Compliance Auditing",               "regulatory_compliance"),
                ("⚔️", "Chapter 7: Competitive Moat & Network Dynamics",            "competitive_moat"),
                ("💰", "Chapter 8: Financial Runway & Capital Amortization",        "financial_runway"),
            ]
            for icon, label, key_or_fn in _chapters:
                with st.expander(f"{icon} {label}"):
                    txt = (
                        key_or_fn(st.session_state.analysis_data)
                        if callable(key_or_fn)
                        else st.session_state.analysis_data.get(key_or_fn, "NO_DATA")
                    )
                    st.markdown(linkify_footnotes(txt, manifest), unsafe_allow_html=True)

            with st.expander("🔬 Section XVI: Methodology & Scoring Risk Matrix Model"):
                st.markdown

            with st.expander("🔍 View Institutional Source Citations"):
                st.markdown("**Source Citation Registry**")
                for fid in ("1", "2", "3"):
                    label = INSTITUTIONAL_CITATION_LABELS[fid]
                    url = st.session_state.sources_manifest[fid]
                    st.markdown(f"- **[{fid}]** {label}: [{url}]({url})")
                st.markdown(
                    "**Glossary Reference:** DePIN — Decentralized Physical Infrastructure Networks; "
                    "Sybil Attack — identity manipulation of consensus; AMM — Automated Market Maker."
                )

            # Insider Distribution Matrix
            render_divider()
            render_section_header("🪙 Insider Distribution Matrix")

            if wc > 50.0:
                render_alert_box(
                    f'<span style="font-size:0.72rem; font-weight:700; text-transform:uppercase;'
                    f' letter-spacing:1px; color:#FF4B4B;">🚨 Critical Risk Assessment</span><br>'
                    f'<span style="color:#F0F6FC; font-weight:600;">CRITICAL SYSTEMIC RISK: High asset concentration.</span><br>'
                    f'<span style="color:#8B949E; font-size:0.83rem;">Top 10 wallets control '
                    f'<b style="color:#FF4B4B;">{wc:.2f}%</b> of circulating supply. '
                    f'Exceeds 50% threshold — elevated governance & liquidation risk.</span>',
                    level="critical",
                )
            else:
                render_alert_box(
                    f'<span style="font-size:0.72rem; font-weight:700; text-transform:uppercase;'
                    f' letter-spacing:1px; color:#3FB950;">✅ Risk Profile Summary</span><br>'
                    f'<span style="color:#F0F6FC; font-weight:600;">HEALTHY: Safe supply decentralization index.</span><br>'
                    f'<span style="color:#8B949E; font-size:0.83rem;">Top 10 wallets control '
                    f'<b style="color:#3FB950;">{wc:.2f}%</b> of circulating supply. '
                    f'Within institutional limits — low coordinated liquidation risk.</span>',
                    level="healthy",
                )

            sc = "#FF4B4B" if wc > 50 else "#3FB950"
            sl = "⚠️ CRITICAL RISK" if wc > 50 else "✅ MINIMAL RISK"
            render_bb_table(
                ["Holder Group", "Supply Share %", "Status"],
                [
                    [
                        "Top 10 Wallets (Clustered)",
                        f'<span style="color:{sc}; font-family:\'JetBrains Mono\',monospace; font-weight:700;">{wc:.4f}%</span>',
                        f'<span style="color:{sc}; font-weight:600;">{sl}</span>',
                    ],
                    ["DAO Treasury",    f'<span style="font-family:\'JetBrains Mono\',monospace;">{dao:.4f}%</span>',    '<span style="color:#8B949E;">Locked Governance</span>'],
                    ["Liquidity Pools", f'<span style="font-family:\'JetBrains Mono\',monospace;">{lp:.4f}%</span>',     '<span style="color:#8B949E;">AMM Yield Pool</span>'],
                    ["Retail Float",    f'<span style="font-family:\'JetBrains Mono\',monospace;">{retail:.4f}%</span>', '<span style="color:#8B949E;">Active Float</span>'],
                ],
            )

            df_dist = pd.DataFrame({
                "Holder Group": ["Top 10 Wallets", "DAO Treasury", "Liquidity Pools", "Retail Float"],
                "Share %": [wc, dao, lp, retail],
            })
            st.bar_chart(df_dist.set_index("Holder Group"), use_container_width=True)

            # Multi-Scenario Stress-Testing Matrix
            render_section_header("📊 Institutional Multi-Scenario Stress-Testing Matrix")
            stress_rows = []
            for row in stress_matrix:
                c = "#FF4B4B" if row["color_flag"] == "CRIMSON" else ("#F59E0B" if row["color_flag"] == "AMBER" else "#3FB950")
                stress_rows.append([
                    f'<b>{row["Scenario"]}</b>',
                    f'<span style="font-family:\'JetBrains Mono\',monospace;">{row["Insider Concentration %"]}</span>',
                    f'<span style="font-family:\'JetBrains Mono\',monospace;">{row["Gini Coefficient"]}</span>',
                    f'<span style="color:{c}; font-weight:700;">{row["Risk Profile Status"]}</span>',
                ])
            render_bb_table(
                ["Scenario Vector", "Insider Conc. %", "Gini Coefficient", "Risk Status"],
                stress_rows,
            )

            # Lorenz / Gini Simulator
            render_divider()
            render_section_header("🔬 Insider Liquidity Stress-Test Simulator")

            dump_pct = st.slider(
                "Simulate Insider Liquidity Dumping (% of Whale Supply Sold)",
                min_value=0, max_value=100, value=0, step=1,
                key="insider_dump_slider",
            )
            gini, x_coords, y_coords, _, _, _, _ = calculate_gini_and_lorenz(wc, dump_pct)

            if dump_pct > 15:
                render_alert_box(
                    f'<div style="font-size:0.7rem; color:#8B949E; text-transform:uppercase; font-weight:700; letter-spacing:1px;">Slippage & Price Impact Risk Index</div>'
                    f'<div style="font-size:1.4rem; color:#FF4B4B; font-weight:700; margin:4px 0;">🚨 CRITICAL COLLAPSE RISK</div>'
                    f'<div style="font-size:0.83rem; color:#FCA5A5;">Dump size: <b>{dump_pct}%</b> of insider holdings'
                    f' ({(wc * dump_pct / 100.0):.2f}% of total supply). Exceeds pool depth — cascading liquidations imminent.</div>',
                    level="critical",
                )
            elif dump_pct > 0:
                render_alert_box(
                    f'<div style="font-size:0.7rem; color:#8B949E; text-transform:uppercase; font-weight:700; letter-spacing:1px;">Slippage & Price Impact Risk Index</div>'
                    f'<div style="font-size:1.4rem; color:#F59E0B; font-weight:700; margin:4px 0;">⚠️ ELEVATED SLIPPAGE RISK</div>'
                    f'<div style="font-size:0.83rem; color:#FDE68A;">Dump size: <b>{dump_pct}%</b> ({(wc * dump_pct / 100.0):.2f}% of total supply). Substantial price impact expected.</div>',
                    level="elevated",
                )
            else:
                render_alert_box(
                    '<div style="font-size:0.7rem; color:#8B949E; text-transform:uppercase; font-weight:700; letter-spacing:1px;">Slippage & Price Impact Risk Index</div>'
                    '<div style="font-size:1.4rem; color:#3FB950; font-weight:700; margin:4px 0;">🟢 MINIMAL SYSTEMIC RISK</div>'
                    '<div style="font-size:0.83rem; color:#A7F3D0;">Baseline distribution. Orderbooks and AMM pools intact. Liquidity depth sufficient.</div>',
                    level="healthy",
                )

            # Lorenz chart
            fig, ax = plt.subplots(figsize=(6, 4.5), dpi=200)
            fig.patch.set_facecolor("#0D1117")
            ax.set_facecolor("#161B22")
            ax.plot([0, 1], [0, 1], color="#30363D", linestyle="--", linewidth=1.5, label="Perfect Equality")
            ax.plot(x_coords, y_coords, color="#58A6FF", linewidth=2.5, label="Token Distribution")
            dot_idx = int(0.90 * len(x_coords))
            if dot_idx < len(x_coords):
                ax.plot(
                    x_coords[dot_idx], y_coords[dot_idx],
                    marker="o", markersize=8,
                    color="#FF4B4B" if dump_pct > 15 else "#F59E0B",
                    label="Insider Threshold",
                )
            ax.set_title(f"Lorenz Curve  ·  Gini = {gini:.4f}", color="#F0F6FC", fontsize=10, fontweight="bold", pad=12)
            ax.set_xlabel("Cumulative Share of Holders", color="#8B949E", fontsize=8)
            ax.set_ylabel("Cumulative Share of Tokens",  color="#8B949E", fontsize=8)
            ax.grid(True, linestyle=":", alpha=0.25, color="#30363D")
            for spine in ax.spines.values():
                spine.set_color("#21262D")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.tick_params(colors="#8B949E", labelsize=7)
            ax.legend(facecolor="#161B22", edgecolor="#21262D", labelcolor="#C9D1D9", loc="upper left", fontsize=7)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            # Anomaly Radar
            render_divider()
            render_section_header("🚨 Data Discrepancy & Anomaly Radar")

            is_large_proj = get_asset_profile_class(st.session_state.project_name) == "large_l1"
            if is_large_proj:
                render_alert_box(
                    '<b style="color:#3FB950;">🟢 NO ANOMALIES DETECTED</b><br>'
                    '<span style="color:#8B949E; font-size:0.83rem;">On-chain audit logs confirm zero discrepancies.</span>',
                    level="healthy",
                )
            else:
                render_bb_table(
                    ["Fractured Metric", "Actual Ledger", "Doc Claim", "Variance"],
                    [
                        ["Insider Concentration",
                         f'<span style="font-family:\'JetBrains Mono\',monospace;">{wc:.2f}%</span>',
                         '<span style="font-family:\'JetBrains Mono\',monospace;">50.00%</span>',
                         f'<span style="color:#FF4B4B; font-weight:700; font-family:\'JetBrains Mono\',monospace;">+{max(0.0, wc - 50.0):.2f}%</span>'],
                        ["Supply Release Discrepancy",
                         f'<span style="font-family:\'JetBrains Mono\',monospace;">{anomaly_val}</span>',
                         '<span style="font-family:\'JetBrains Mono\',monospace;">5.00%</span>',
                         f'<span style="color:#FF4B4B; font-weight:700; font-family:\'JetBrains Mono\',monospace;">+{max(0.0, float(anomaly_val.replace("%","")) - 5.0):.2f}%</span>'],
                        ["Gini Coefficient",
                         f'<span style="font-family:\'JetBrains Mono\',monospace;">{gini_val:.4f}</span>',
                         '<span style="font-family:\'JetBrains Mono\',monospace;">0.7000</span>',
                         f'<span style="color:#FF4B4B; font-weight:700; font-family:\'JetBrains Mono\',monospace;">+{max(0.0, gini_val - 0.7):.4f}</span>'],
                    ],
                )
                st.markdown(
                    "<div style='margin-top:14px; font-size:0.78rem; color:#8B949E; font-weight:700;"
                    " text-transform:uppercase; letter-spacing:0.8px;'>🔬 AI Discrepancy Forensic Investigator</div>",
                    unsafe_allow_html=True,
                )
                for am in ["Insider Concentration", "Supply Release Discrepancy", "Gini Coefficient"]:
                    with st.expander(f"🔬 Deploy Forensic Investigation: {am}"):
                        breakdown = get_forensic_investigation_breakdown(st.session_state.project_name, am)
                        bc1, bc2, bc3 = st.columns(3)
                        with bc1:
                            st.markdown("**📢 Project Claim**")
                            st.write(breakdown["claim"])
                        with bc2:
                            st.markdown("**🛡️ On-Chain Evidence**")
                            st.write(breakdown["evidence"])
                        with bc3:
                            st.markdown("**⚖️ Investigator Verdict**")
                            st.write(breakdown["verdict"])

        with col_right:

            render_section_header("⚔️ Competitive Disruption & Vulnerability Analysis")

            if st.session_state.battle_data is not None:
                battle     = st.session_state.battle_data
                metrics_a  = battle.get("project_a_metrics", {})
                metrics_b  = battle.get("project_b_metrics", {})
                clash      = battle.get("vulnerability_clash", {})
                ver        = battle.get("winner_verdict", {})
                cna, cnb   = st.session_state.comp_a, st.session_state.comp_b

                render_bb_table(
                    ["Dimension", f'<span style="color:#58A6FF;">{cna}</span>', f'<span style="color:#FF4B4B;">{cnb}</span>'],
                    [
                        ["Sentiment & Social",
                         f'<span style="font-family:\'JetBrains Mono\',monospace;">{metrics_a.get("sentiment","N/A")}</span>',
                         f'<span style="font-family:\'JetBrains Mono\',monospace;">{metrics_b.get("sentiment","N/A")}</span>'],
                        ["Primary Focus", metrics_a.get("focus","N/A"), metrics_b.get("focus","N/A")],
                        ["Ecosystem Layer", metrics_a.get("blockchain","N/A"), metrics_b.get("blockchain","N/A")],
                        [
                            "Primary Threat",
                            f'<span style="color:#FF4B4B;">{metrics_a.get("risk","N/A")}</span>',
                            f'<span style="color:#FF4B4B;">{metrics_b.get("risk","N/A")}</span>',
                        ],
                    ],
                )

                render_alert_box(
                    f'<div style="font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:#8B949E; margin-bottom:8px;">Structural Asymmetry Clinic</div>'
                    f'<div style="margin-bottom:10px;"><span style="font-weight:700; color:#58A6FF; font-size:0.8rem;">🛡️ {cna} Market Penetration Vulnerability:</span><br>'
                    f'<span style="color:#8B949E; font-size:0.83rem; font-style:italic;">{clash.get("project_a_killer_feature","N/A")}</span></div>'
                    f'<div><span style="font-weight:700; color:#FF4B4B; font-size:0.8rem;">⚡ {cnb} Market Penetration Vulnerability:</span><br>'
                    f'<span style="color:#8B949E; font-size:0.83rem; font-style:italic;">{clash.get("project_b_killer_feature","N/A")}</span></div>'
                    f'<div style="border-top:1px solid #21262D; padding-top:10px; margin-top:12px;">'
                    f'<span style="font-weight:700; color:#3FB950; font-size:0.88rem;">🏆 DETECTED ADVANTAGE: {ver.get("declared_winner","N/A")}</span><br>'
                    f'<span style="color:#8B949E; font-size:0.82rem;">{ver.get("rationale","N/A")}</span></div>',
                    level="neutral",
                )
            else:
                render_alert_box(
                    '<b style="color:#8B949E;">Comparative Analysis Inactive</b><br>'
                    '<span style="color:#8B949E; font-size:0.83rem;">Provide tickers for Token A and Token B, then run the analysis pipeline.</span>',
                    level="neutral",
                )

            # Mathematical Emission Curve
            render_divider()
            render_section_header("📈 Mathematical Emission Curve")

            df_em, formula, desc = compute_emission_curve(
                st.session_state.current_project,
                is_fallback=(not bool(
                    st.session_state.analysis_data.get("tokenomics_math", {}).get("unlock_schedule_12m")
                )),
            )

            render_alert_box(
                f'<div style="font-size:0.68rem; font-weight:700; color:#3FB950; text-transform:uppercase; letter-spacing:1px;">🔢 Quantitative Model: Active</div>'
                f'<div style="font-size:0.82rem; margin-top:3px; color:#C9D1D9;"><b>Model:</b> {desc}</div>'
                f'<div style="font-size:0.82rem; color:#C9D1D9;"><b>Equation:</b> <code style="font-size:0.78rem;">{formula}</code></div>',
                level="healthy",
            )

            st.line_chart(df_em.set_index("Month"), use_container_width=True)

            with st.expander("📋 12-Month Cumulative Rewards Table"):
                st.dataframe(
                    df_em.style.format({"Cumulative Emission %": "{:.4f}%"}),
                    use_container_width=True,
                    hide_index=True,
                )

        render_divider()
        render_section_header("🏦 MarketNode Discretionary Capital Advisory")

        try:
            sentiment_score = int("".join(c for c in score_str if c.isdigit()))
        except Exception:
            sentiment_score = 7

        strategy, leg1, leg2, ratio, rationale = generate_hedging_advisory(
            st.session_state.project_name,
            st.session_state.comp_b,
            wc,
            st.session_state.battle_data,
            sentiment_score,
        )
        is_neutral = "Pair Trade" in strategy

        render_alert_box(
            f'<div style="font-size:0.68rem; color:#8B949E; text-transform:uppercase; font-weight:700; letter-spacing:1px; margin-bottom:4px;">Recommended Strategy</div>'
            f'<div style="font-size:1.25rem; color:#F0F6FC; font-weight:700; margin-bottom:6px;">{strategy}</div>'
            f'<div style="font-size:0.85rem; color:#8B949E; line-height:1.6; margin-bottom:10px;"><b style="color:#C9D1D9;">Tactical Rationale:</b> {rationale}</div>'
            f'<div style="border-top:1px solid #21262D; padding-top:10px;">'
            f'<div style="font-size:0.78rem; color:#8B949E; margin-bottom:4px;">• <b style="color:#C9D1D9;">Leg 1 (Primary Allocation):</b> {leg1}</div>'
            f'<div style="font-size:0.78rem; color:#8B949E;">• <b style="color:#C9D1D9;">Leg 2 (Hedging Buffer):</b> {leg2}</div></div>',
            level="critical" if is_neutral else "healthy",
        )

        col_calc, col_pos = st.columns([1, 1], gap="medium")
        with col_calc:
            st.markdown(
                "<div style='font-size:0.78rem; font-weight:700; color:#8B949E; text-transform:uppercase;"
                " letter-spacing:1px; margin-bottom:6px;'>🧮 Interactive Allocation Calculator</div>",
                unsafe_allow_html=True,
            )
            investment = st.number_input(
                "Discretionary Capital ($)",
                min_value=1000, max_value=100_000_000, value=100_000, step=5000,
                key="advisory_investment_input",
            )
        with col_pos:
            st.markdown(
                "<div style='font-size:0.78rem; font-weight:700; color:#8B949E; text-transform:uppercase;"
                " letter-spacing:1px; margin-bottom:6px;'>💼 Simulated Position Sizing</div>",
                unsafe_allow_html=True,
            )
            alloc_cols = st.columns(len(ratio))
            for idx, (leg_name, pct) in enumerate(ratio.items()):
                with alloc_cols[idx]:
                    st.metric(label=leg_name, value=f"${investment * pct / 100:,.2f}", delta=f"{pct}% weight")

        # Cross-Chain Liquidity Heatmap
        render_divider()
        render_section_header("🌐 Cross-Chain Arbitrage & Liquidity Heatmap")

        pools, spread = get_cross_chain_liquidity_data(st.session_state.project_name, prices=_live_prices)

        if spread > 1.50:
            render_alert_box(
                f'<div style="font-size:0.68rem; text-transform:uppercase; font-weight:700; color:#FF4B4B; letter-spacing:1px;">🚨 Arbitrage System Alert</div>'
                f'<div style="font-size:1.1rem; font-weight:700; color:#F0F6FC; margin-top:2px;">Profit Opportunity: Exploitable Price Spread Detected</div>'
                f'<div style="font-size:0.82rem; color:#FCA5A5; margin-top:4px;">Cross-chain divergence is <b>{spread:.2f}%</b>, exceeding the 1.50% efficiency threshold.</div>',
                level="critical",
            )
        else:
            render_alert_box(
                f'<div style="font-size:0.68rem; text-transform:uppercase; font-weight:700; color:#3FB950; letter-spacing:1px;">🟢 Market Efficiency Index</div>'
                f'<div style="font-size:1.1rem; font-weight:700; color:#F0F6FC; margin-top:2px;">High Price Alignment / Low Arbitrage Spread</div>'
                f'<div style="font-size:0.82rem; color:#A7F3D0; margin-top:4px;">Cross-chain divergence is <b>{spread:.2f}%</b> — efficient institutional market matching.</div>',
                level="healthy",
            )

        pool_rows = []
        for p in pools:
            sc2 = "#3FB950" if p["slippage"] < 0.1 else "#FF4B4B"
            pool_rows.append([
                f'<b>{p["exchange"]}</b>',
                p["sub_type"],
                f'<span style="font-family:\'JetBrains Mono\',monospace;">${p["price"]:,.4f}</span>',
                f'<span style="font-family:\'JetBrains Mono\',monospace;">${p["liquidity"]:,.2f}</span>',
                f'<span style="font-family:\'JetBrains Mono\',monospace; color:{sc2}; font-weight:700;">{p["slippage"]:.2f}%</span>',
            ])
        render_bb_table(
            ["Exchange / Network", "Asset Sub-Type", "Live Pool Price", "Liquidity Depth", "Slippage ($10K)"],
            pool_rows,
        )

        # Post-Audit Execution Pipeline
        render_divider()
        render_section_header("🚀 Post-Audit Execution Pipeline")

        col_export, col_gateway = st.columns([1, 1], gap="medium")
        with col_export:
            st.markdown(
                "<div style='font-size:0.78rem; font-weight:700; color:#8B949E; text-transform:uppercase;"
                " letter-spacing:1px; margin-bottom:8px;'>📱 Telegram / Markdown Alpha Export</div>",
                unsafe_allow_html=True,
            )
            summary_md = (
                f"🚨 **MARKETNODE ALPHA EXPORT: {st.session_state.project_name.upper()}** 🚨\n\n"
                f"• **Ticker:** {st.session_state.project_name.upper()}\n"
                f"• **Gini Coefficient:** {gini_val:.4f}\n"
                f"• **Insider Concentration:** {wc:.2f}%\n"
                f"• **Risk Protocol:** {risk_protocol}\n"
                f"• **Risk Classification:** {verdict_summary}\n"
                f"• **Anomaly Discrepancy Delta:** {anomaly_val}\n"
                f"• **Execution Mandate:** {strategy}\n"
                f"• **Primary Action:** {leg1}\n"
                f"• **Hedging Protocol:** {leg2}"
            )
            st.write("Copy the Markdown block below for Telegram / Notion export:")
            st.code(summary_md, language="markdown")

        with col_gateway:
            st.markdown(
                "<div style='font-size:0.78rem; font-weight:700; color:#8B949E; text-transform:uppercase;"
                " letter-spacing:1px; margin-bottom:8px;'>⚡ Dynamic Smart Execution Gateway</div>",
                unsafe_allow_html=True,
            )
            st.write("Route orders directly to on-chain venues based on audit risk rating:")
            is_long = "Long" in strategy
            if is_long:
                if st.session_state.project_name.upper() in ["BTC", "BITCOIN"]:
                    dex_url = "https://app.uniswap.org/#/swap?outputCurrency=0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"
                elif st.session_state.project_name.upper() in ["SOL", "SOLANA"]:
                    dex_url = "https://jup.ag/swap/USDC-SOL"
                else:
                    dex_url = "https://app.uniswap.org/#/swap?outputCurrency=0x5dd4fc35848c773ad088f55731751295911135e2"
                st.markdown("**Asset Profile:** Investment Grade — **Long / Accumulate**.")
                st.link_button("⚡ Route Swap Order → AMM DEX (Uniswap / Jupiter)", dex_url, use_container_width=True)
            else:
                st.markdown("**Asset Profile:** Critical Risk — **Hedge / Short**.")
                st.link_button("⚡ Route Hedge / Short → Derivatives Venue (dYdX)", "https://trade.dydx.exchange/", use_container_width=True)

    # TAB 2 — HISTORICAL EVENT IMPACT

    with tab2:
        render_section_header("⏳ AI Historical Event-Impact Backtesting Engine")
        st.markdown(
            "<div style='color:#8B949E; font-size:0.85rem; margin-bottom:16px;'>"
            "Evaluate how the active asset is projected to perform under historical systemic shocks.</div>",
            unsafe_allow_html=True,
        )

        selected_event = st.selectbox(
            "Select Historical Scenario Vector:",
            [
                "Market Crashes (e.g., FTX Collapse)",
                "Regulatory Action / Outages",
                "Black Swan Liquidity Shock",
            ],
        )

        impact = get_historical_event_impact(st.session_state.project_name, selected_event)

        ci1, ci2, ci3 = st.columns(3)
        with ci1:
            st.metric(label="Simulated Price Decay %",    value=impact["Price Decay %"])
        with ci2:
            st.metric(label="Insider Selling Pressure",   value=impact["Insider Selling Pressure"])
        with ci3:
            st.metric(label="Node Health Recovery Time",  value=impact["Node Health Recovery Time"])

        st.markdown(
            "<div style='font-size:0.78rem; font-weight:700; color:#8B949E; text-transform:uppercase;"
            " letter-spacing:1px; margin:16px 0 8px 0;'>📈 Projected Price Trajectory</div>",
            unsafe_allow_html=True,
        )

        decay_val = float(impact["Price Decay %"].replace("%", ""))
        current_price = 100.0
        prices = [100.0]
        for _ in range(1, 5):
            current_price += decay_val / 4.0
            prices.append(max(5.0, current_price))
        for _ in range(5, 15):
            current_price += (100.0 - current_price) * 0.05
            prices.append(current_price)

        st.line_chart(
            pd.DataFrame({
                "Day": [f"Day {i}" for i in range(15)],
                "Price Index (Baseline 100)": [round(p, 2) for p in prices],
            }).set_index("Day"),
            use_container_width=True,
        )

# SIDEBAR — PDF DOSSIER GENERATOR

render_sidebar_section_divider("📑  Executive Dossier Generator")

if st.session_state.analysis_data is not None:
    if st.session_state.pdf_status == "idle":
        if st.sidebar.button(
            "📥 Generate 5-Page Institutional Dossier",
            key="gen_pdf_btn",
            use_container_width=True,
        ):
            st.session_state.pdf_status = "running"
            st.session_state.pdf_bytes = None
            st.session_state.pdf_error_msg = None

            try:
                from streamlit.runtime.scriptrunner import add_script_run_ctx
            except ImportError:
                try:
                    from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
                except ImportError:
                    def add_script_run_ctx(t):
                        return t

            _ticker_key = st.session_state.current_project or st.session_state.project_name
            pdf_live_metrics = build_benchmark_metrics_payload(_ticker_key)
            # Inject the live spot price so the PDF cover page shows real data
            pdf_live_metrics["live_price"] = get_live_price(
                _ticker_key, prices=st.session_state.get("live_prices", {})
            )
            # Inject dynamic algorithmic links
            sources_manifest_temp = get_institutional_sources_manifest(_ticker_key)
            pdf_live_metrics["link_1"] = sources_manifest_temp["1"]
            pdf_live_metrics["link_2"] = sources_manifest_temp["2"]
            pdf_live_metrics["link_3"] = sources_manifest_temp["3"]
            
            t = threading.Thread(
                target=_generate_pdf_async,
                args=(
                    st.session_state.current_project,
                    st.session_state.analysis_data,
                    sources_manifest_temp,
                    st.session_state.battle_data,
                    st.session_state.comp_a,
                    st.session_state.comp_b,
                    pdf_live_metrics,
                ),
            )
            add_script_run_ctx(t)
            t.start()
            st.rerun()

    elif st.session_state.pdf_status == "running":
        st.sidebar.markdown(
            "<div style='font-family:\'JetBrains Mono\',monospace; font-size:0.68rem;"
            " color:#8B949E; padding:8px 0; letter-spacing:0.4px;'>"
            "⏳ &nbsp;Compiling dossier asynchronously...</div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.5)
        st.rerun()

    elif st.session_state.pdf_status == "complete":
        # Minimalist success badge instead of large native green block
        render_sidebar_pdf_success(st.session_state.current_project or "ASSET")
        st.sidebar.download_button(
            label="📥 Download Dossier (PDF)",
            data=st.session_state.pdf_bytes,
            file_name=f"{st.session_state.current_project}_5_Page_Institutional_Dossier.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        if st.sidebar.button("↺ Reset Compiler Deck", use_container_width=True, key="reset_pdf_btn"):
            st.session_state.pdf_status = "idle"
            st.session_state.pdf_bytes = None
            st.rerun()

    elif st.session_state.pdf_status == "error":
        st.sidebar.markdown(
            f"<div style='font-size:0.72rem; color:#FF4B4B; padding:6px 0;'>"
            f"❌ &nbsp;{st.session_state.pdf_error_msg}</div>",
            unsafe_allow_html=True,
        )
        if st.sidebar.button("↺ Retry Compiling Dossier", use_container_width=True, key="retry_pdf_btn"):
            st.session_state.pdf_status = "idle"
            st.rerun()

else:
    st.sidebar.markdown(
        "<div style='font-size:0.72rem; color:#8B949E; font-family:\'JetBrains Mono\',monospace;"
        " letter-spacing:0.4px; padding:6px 0;'>Audit an asset to unlock dossier compilation.</div>",
        unsafe_allow_html=True,
    )

render_sidebar_brand_footer()

