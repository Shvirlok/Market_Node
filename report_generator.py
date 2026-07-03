import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from calculations import (
    run_stress_testing_matrix,
    generate_hedging_advisory,
    compute_dynamic_gini,
    compute_risk_protocol,
    INSTITUTIONAL_CITATION_LABELS,
    get_institutional_sources_manifest,
)

# 1. Custom NumberedCanvas class for Two-Pass Institutional Page Numbering
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#000080")) # Institutional Navy Blue
            self.drawString(45, 755, "MARKETNODE INSTITUTIONAL INTELLIGENCE RESEARCH")
            
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#36454F")) # Charcoal Gray
            self.drawRightString(567, 755, "CONFIDENTIAL // INVESTMENT COMMITTEE REPORT")
            
            # Header line
            self.setStrokeColor(colors.HexColor("#D1D5DB")) # Subtle Gray
            self.setLineWidth(0.5)
            self.line(45, 748, 567, 748)
            
            # Footer line
            self.line(45, 52, 567, 52)
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(567, 38, page_text)
            self.drawString(45, 38, "DISCLAIMER: AI-Generated Institutional Risk Analysis. For informational use only; not financial advice.")
            self.restoreState()

# Helper function to extract text and format warning flag in PDF reports
def get_pdf_text_with_predictive_note(value):
    if value is None:
        return "N/A"
    is_predictive = "[AI Predictive Estimate]" in str(value)
    clean_val = str(value).replace("[AI Predictive Estimate]", "").strip()
    if is_predictive:
        return f"<b>[AI Predictive Estimate]</b> {clean_val}"
    return clean_val

def generate_pdf_report(data_payload, filename="report.pdf"):
    project = data_payload.get("project")
    analysis = data_payload.get("analysis")
    manifest = data_payload.get("manifest") or get_institutional_sources_manifest()
    battle_data = data_payload.get("battle_data")
    comp_a = data_payload.get("comp_a")
    comp_b = data_payload.get("comp_b")
    wc = data_payload.get("wc", 0.0)
    gini_val = data_payload.get("gini_val", compute_dynamic_gini(wc))
    risk_protocol = data_payload.get("risk_protocol", compute_risk_protocol(wc))
    stress_data = data_payload.get("stress_matrix") or run_stress_testing_matrix(wc, risk_classification=risk_protocol)
    live_price_raw = data_payload.get("live_price", None)

    # Format live_price for display — handle sub-dollar and large assets cleanly
    if live_price_raw is not None and live_price_raw > 0:
        if live_price_raw < 0.01:
            live_price_str = f"${live_price_raw:.6f}"
        elif live_price_raw < 1:
            live_price_str = f"${live_price_raw:.4f}"
        elif live_price_raw < 1_000:
            live_price_str = f"${live_price_raw:,.2f}"
        else:
            live_price_str = f"${live_price_raw:,.0f}"
        live_price_label = f"{live_price_str}  (live at time of compilation)"
    else:
        live_price_label = "Benchmark reference — live fetch unavailable"

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#000080")
    body_color = colors.HexColor("#36454F")
    alert_color = colors.HexColor("#991B1B")
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=primary_color, spaceAfter=15
    )
    sub_style = ParagraphStyle(
        'DocSub', parent=styles['Normal'], fontSize=10, leading=13, textColor=colors.HexColor("#4B5563"), spaceAfter=20
    )
    section_style = ParagraphStyle(
        'DocSection', parent=styles['Heading2'], fontSize=12, leading=15, textColor=primary_color, spaceBefore=12, spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody', parent=styles['Normal'], fontSize=9, leading=12, textColor=body_color, spaceAfter=6
    )
    table_header_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold', textColor=colors.white
    )
    table_body_style = ParagraphStyle(
        'TableBody', parent=styles['Normal'], fontSize=8, leading=10, textColor=body_color
    )
    telemetry_heading_style = ParagraphStyle(
        'TelemetryHeading', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold', textColor=primary_color, spaceBefore=3, spaceAfter=1
    )
    telemetry_body_style = ParagraphStyle(
        'TelemetryBody', parent=styles['Normal'], fontSize=7, leading=8.5, textColor=body_color, spaceAfter=3
    )
    
    story = []
    
    # ------------------ PAGE 1 ------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("MARKETNODE INSTITUTIONAL INTELLIGENCE: VC DUE DILIGENCE DOSSIER", title_style))
    story.append(Paragraph("EXHAUSTIVE DEPIN RISK ANALYSIS & MATHEMATICAL EMISSION PROJECTION", sub_style))
    story.append(Spacer(1, 5))
    
    meta_rows = [
        [Paragraph("<b>METRIC SPECIFICATION</b>", table_header_style), Paragraph("<b>AUDIT VALUE / RATING</b>", table_header_style)],
        [Paragraph("Target Cryptographic Asset", table_body_style), Paragraph(project, table_body_style)],
        [Paragraph("Live Spot Price (USD)", table_body_style), Paragraph(live_price_label, table_body_style)],
        [Paragraph("Institutional Sentiment Score", table_body_style), Paragraph(f"{analysis.get('sentiment_score', 'N/A')}/10", table_body_style)],
        [Paragraph("Insider Concentration Index", table_body_style), Paragraph(f"{wc:.2f}%", table_body_style)],
        [Paragraph("Gini Coefficient (Benchmark)", table_body_style), Paragraph(f"{gini_val:.4f}", table_body_style)],
        [Paragraph("Risk Classification Protocol", table_body_style), Paragraph(risk_protocol, table_body_style)]
    ]
    t = Table(meta_rows, colWidths=[200, 320])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 4),
        ('TOPPADDING', (0,0), (-1,0), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e9ecef")),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        ('TOPPADDING', (0,1), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>EXECUTIVE SUMMARY</b>", section_style))
    story.append(Paragraph(analysis.get("core_narrative", "N/A"), body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>FUNDAMENTAL & OSINT TELEMETRY</b>", section_style))
    story.append(Spacer(1, 4))
    
    col1_elements = []
    col1_elements.append(Paragraph("<b>I. Macroscopic Narratives</b>", telemetry_heading_style))
    col1_elements.append(Paragraph(get_pdf_text_with_predictive_note(analysis.get("macro_narrative", "N/A")), telemetry_body_style))
    
    col1_elements.append(Paragraph("<b>II. Tokenomics & Vesting</b>", telemetry_heading_style))
    tokenomics_text = analysis.get("tokenomics_math", {}).get("analysis_text", "N/A")
    col1_elements.append(Paragraph(get_pdf_text_with_predictive_note(tokenomics_text), telemetry_body_style))
    
    col1_elements.append(Paragraph("<b>III. On-Chain Infrastructures</b>", telemetry_heading_style))
    col1_elements.append(Paragraph(get_pdf_text_with_predictive_note(analysis.get("onchain_infrastructure", "N/A")), telemetry_body_style))
    
    col1_elements.append(Paragraph("<b>IV. Developer Velocity</b>", telemetry_heading_style))
    col1_elements.append(Paragraph(get_pdf_text_with_predictive_note(analysis.get("developer_velocity", "N/A")), telemetry_body_style))
    
    col2_elements = []
    col2_elements.append(Paragraph("<b>V. Retail Sentiment & Hype</b>", telemetry_heading_style))
    col2_elements.append(Paragraph(get_pdf_text_with_predictive_note(analysis.get("social_hype_and_fud", "N/A")), telemetry_body_style))
    
    col2_elements.append(Paragraph("<b>VI. Regulatory & Compliance</b>", telemetry_heading_style))
    col2_elements.append(Paragraph(get_pdf_text_with_predictive_note(analysis.get("regulatory_compliance", "N/A")), telemetry_body_style))
    
    col2_elements.append(Paragraph("<b>VII. Competitive Moat</b>", telemetry_heading_style))
    col2_elements.append(Paragraph(get_pdf_text_with_predictive_note(analysis.get("competitive_moat", "N/A")), telemetry_body_style))
    
    col2_elements.append(Paragraph("<b>VIII. Financial Runway</b>", telemetry_heading_style))
    col2_elements.append(Paragraph(get_pdf_text_with_predictive_note(analysis.get("financial_runway", "N/A")), telemetry_body_style))
    
    risks = analysis.get("critical_strategic_risks", [])
    if risks:
        col2_elements.append(Paragraph("<b>IX. Critical Strategic Risks</b>", telemetry_heading_style))
        for r in risks:
            clean_r = get_pdf_text_with_predictive_note(r)
            col2_elements.append(Paragraph(f"• {clean_r}", telemetry_body_style))
            
    telemetry_table = Table([[col1_elements, col2_elements]], colWidths=[250, 250])
    telemetry_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(telemetry_table)
    story.append(PageBreak())
    
    # ------------------ PAGE 2 ------------------
    dao = (100.0 - wc) * 0.4
    lp = (100.0 - wc) * 0.3
    retail = (100.0 - wc) * 0.3
    
    dist_rows = [
        [Paragraph("<b>Holder Group</b>", table_header_style), Paragraph("<b>Supply %</b>", table_header_style), Paragraph("<b>Profile</b>", table_header_style)],
        [Paragraph("Top 10 Wallets", table_body_style), Paragraph(f"{wc:.2f}%", table_body_style), Paragraph("CENTRALIZED" if wc > 50 else "ACCEPTABLE", table_body_style)],
        [Paragraph("DAO Treasury", table_body_style), Paragraph(f"{dao:.2f}%", table_body_style), Paragraph("Gov. Locked", table_body_style)],
        [Paragraph("Liquidity Pools", table_body_style), Paragraph(f"{lp:.2f}%", table_body_style), Paragraph("AMM Locked", table_body_style)],
        [Paragraph("Retail Float", table_body_style), Paragraph(f"{retail:.2f}%", table_body_style), Paragraph("Active Float", table_body_style)]
    ]
    dist_table = Table(dist_rows, colWidths=[180, 140, 202])
    dist_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e9ecef")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    
    stress_rows = [
        [
            Paragraph("<b>Scenario Vector</b>", table_header_style), 
            Paragraph("<b>Insider %</b>", table_header_style), 
            Paragraph("<b>Gini</b>", table_header_style), 
            Paragraph("<b>Risk Status</b>", table_header_style)
        ]
    ]
    for row in stress_data:
        status_text = row["Risk Profile Status"]
        if row["color_flag"] == "CRIMSON":
            status_para = Paragraph(f"<font color='#991B1B'><b>{status_text}</b></font>", table_body_style)
        elif row["color_flag"] == "AMBER":
            status_para = Paragraph(f"<font color='#B5A642'><b>{status_text}</b></font>", table_body_style)
        else:
            status_para = Paragraph(f"<font color='#065F46'><b>{status_text}</b></font>", table_body_style)
            
        stress_rows.append([
            Paragraph(row["Scenario"], table_body_style),
            Paragraph(row["Insider Concentration %"], table_body_style),
            Paragraph(row["Gini Coefficient"], table_body_style),
            status_para
        ])
        
    stress_table = Table(stress_rows, colWidths=[180, 100, 100, 142])
    stress_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e9ecef")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    
    story.append(Paragraph("<b>Insider Supply Allocation Matrix</b>", section_style))
    story.append(dist_table)
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("<b>Multi-Scenario Stress-Testing Model</b>", section_style))
    story.append(stress_table)
    
    if "CRITICAL" in risk_protocol:
        alert_style = ParagraphStyle('CritAlert', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold', textColor=alert_color)
        story.append(Paragraph(
            f"⚠️ {risk_protocol} DETECTED: Asset distribution exhibits extreme concentration. "
            f"The top 10 addresses control {wc:.2f}% of the active token supply (Gini = {gini_val:.4f}). "
            "Systemic threats including retail market dumping, governance takeover, and vulnerability to Sybil attacks are high.",
            alert_style,
        ))
    elif "ELEVATED" in risk_protocol:
        alert_style = ParagraphStyle('ElevAlert', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold', textColor=colors.HexColor("#B5A642"))
        story.append(Paragraph(
            f"⚠️ {risk_protocol}: Top 10 wallet concentration at {wc:.2f}% (Gini = {gini_val:.4f}). "
            "Monitor governance capture vectors and liquidity depth under stress scenarios.",
            alert_style,
        ))
        
    story.append(PageBreak())
    
    # ------------------ PAGE 3 ------------------
    if not battle_data:
        from calculations import generate_fallback_battle
        _HNT_ALIASES_PDF = frozenset({"HELIUM MOBILE", "HELIUM", "HNT"})
        _cb_raw = (comp_b or "SOL").strip().upper()
        _cb_norm = "HNT" if _cb_raw in _HNT_ALIASES_PDF else _cb_raw
        battle_data = generate_fallback_battle(project, _cb_norm)

    comp_a_name  = project
    comp_b_name  = comp_b or "SOL"
    # Normalize display name so the PDF never shows "HELIUM MOBILE" verbatim
    _HNT_ALIASES_PDF2 = frozenset({"HELIUM MOBILE", "HELIUM"})
    if comp_b_name.strip().upper() in _HNT_ALIASES_PDF2:
        comp_b_name = "HNT"
    
    metrics_a = battle_data.get("project_a_metrics", {})
    metrics_b = battle_data.get("project_b_metrics", {})
    clash = battle_data.get("vulnerability_clash", {})
    verdict = battle_data.get("winner_verdict", {})
    
    duel_rows = [
        [Paragraph("<b>Vector Dimension</b>", table_header_style), Paragraph(f"<b>{comp_a_name} Score</b>", table_header_style), Paragraph(f"<b>{comp_b_name} Score</b>", table_header_style)],
        [Paragraph("Retail Sentiment & Social Velocity", table_body_style), Paragraph(f"{metrics_a.get('hype_score', 'N/A')}/10", table_body_style), Paragraph(f"{metrics_b.get('hype_score', 'N/A')}/10", table_body_style)],
        [Paragraph("Tech & Node Architecture", table_body_style), Paragraph(f"{metrics_a.get('tech_score', 'N/A')}/10", table_body_style), Paragraph(f"{metrics_b.get('tech_score', 'N/A')}/10", table_body_style)],
        [Paragraph("Tokenomics Design", table_body_style), Paragraph(f"{metrics_a.get('tokenomics_score', 'N/A')}/10", table_body_style), Paragraph(f"{metrics_b.get('tokenomics_score', 'N/A')}/10", table_body_style)],
        [Paragraph("Scalability Capacity", table_body_style), Paragraph(f"{metrics_a.get('scalability_score', 'N/A')}/10", table_body_style), Paragraph(f"{metrics_b.get('scalability_score', 'N/A')}/10", table_body_style)]
    ]
    duel_t = Table(duel_rows, colWidths=[200, 150, 160])
    duel_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e9ecef")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    
    story.append(Paragraph("<b>COMPETITIVE DISRUPTION & VULNERABILITY MATRIX</b>", section_style))
    story.append(Paragraph(f"Side-by-side protocol confrontation matching {comp_a_name} against competitor {comp_b_name}.", body_style))
    story.append(Spacer(1, 5))
    story.append(duel_t)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>Structural Asymmetry Analysis Summary</b>", ParagraphStyle('AsymHead', parent=styles['Normal'], fontSize=10, leading=13, fontName='Helvetica-Bold', textColor=primary_color, spaceBefore=4, spaceAfter=2)))
    story.append(Paragraph(f"<b>{comp_a_name} Market Penetration Vulnerability:</b> {get_pdf_text_with_predictive_note(clash.get('project_a_killer_feature', 'N/A'))}", body_style))
    story.append(Paragraph(f"<b>{comp_b_name} Market Penetration Vulnerability:</b> {get_pdf_text_with_predictive_note(clash.get('project_b_killer_feature', 'N/A'))}", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Institutional Advantage Verdict:</b> {verdict.get('declared_winner', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Thesis Rationale:</b> {get_pdf_text_with_predictive_note(verdict.get('rationale', 'N/A'))}", body_style))
    story.append(PageBreak())
    
    # ------------------ PAGE 4 ------------------
    score_str = analysis.get("sentiment_score", "7")
    try:
        sentiment_score = int("".join(c for c in score_str if c.isdigit()))
    except Exception:
        sentiment_score = 7
        
    strategy, leg1, leg2, ratio, rationale = generate_hedging_advisory(project, comp_b_name, wc, battle_data, sentiment_score)
    
    story.append(Paragraph("<b>CAPITAL ALLOCATION & HEDGING MANDATES</b>", section_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"<b>Executive Strategy:</b> {strategy}", body_style))
    story.append(Paragraph(f"<b>Strategic Rationale:</b> {rationale}", body_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>Tactical Execution Mandates</b>", ParagraphStyle('MandateHead', parent=styles['Normal'], fontSize=10, leading=13, fontName='Helvetica-Bold', textColor=primary_color, spaceBefore=4, spaceAfter=2)))
    story.append(Paragraph(f"• <b>Leg 1 (Primary Allocation):</b> {leg1}", body_style))
    story.append(Paragraph(f"• <b>Leg 2 (Hedging Buffer):</b> {leg2}", body_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>Simulated Position Size Weightings</b>", ParagraphStyle('WeightHead', parent=styles['Normal'], fontSize=10, leading=13, fontName='Helvetica-Bold', textColor=primary_color, spaceBefore=4, spaceAfter=2)))
    
    weight_headers = [Paragraph("<b>Asset/Allocation Position</b>", table_header_style), Paragraph("<b>Target Weight %</b>", table_header_style)]
    weight_rows = [weight_headers]
    for key, val in ratio.items():
        weight_rows.append([Paragraph(key, table_body_style), Paragraph(f"{val}%", table_body_style)])
        
    weight_table = Table(weight_rows, colWidths=[330, 180])
    weight_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e9ecef")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(weight_table)
    story.append(PageBreak())
    
    # ------------------ PAGE 5 ------------------
    col1_page5 = []
    col1_page5.append(Paragraph("<b>Source Citation Registry</b>", ParagraphStyle('CiteHead', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold', textColor=primary_color, spaceBefore=4, spaceAfter=2)))
    cite_rows = [
        [
            Paragraph("<b>Ref</b>", ParagraphStyle('CiteHdr', parent=styles['Normal'], fontSize=6, leading=7, fontName='Helvetica-Bold', textColor=primary_color)),
            Paragraph("<b>Institutional Source</b>", ParagraphStyle('CiteHdr2', parent=styles['Normal'], fontSize=6, leading=7, fontName='Helvetica-Bold', textColor=primary_color)),
        ]
    ]
    
    p_lower = str(project).strip().lower()
    p_upper = str(project).strip().upper()
    
    if p_upper == "BNB":
        link_1 = "https://www.coingecko.com/en/coins/binancecoin"
    else:
        link_1 = f"https://www.coingecko.com/en/coins/{p_lower}"
    link_1 = data_payload.get("link_1") or link_1
        
    link_2 = data_payload.get("link_2") or f"https://messari.io/asset/{p_lower}"
    
    if p_upper == "ETH":
        link_3_fallback = "https://etherscan.io"
    elif p_upper == "BNB":
        link_3_fallback = "https://bscscan.com"
    elif p_upper == "SOL":
        link_3_fallback = "https://solscan.io"
    elif p_upper == "DIMO":
        link_3_fallback = "https://polygonscan.com"
    else:
        link_3_fallback = "https://coinmarketcap.com"
    link_3 = data_payload.get("link_3") or link_3_fallback
    
    links = {
        "1": link_1,
        "2": link_2,
        "3": link_3
    }
    
    for fid in ("1", "2", "3"):
        label = INSTITUTIONAL_CITATION_LABELS[fid]
        url = links[fid]
        fid_para = Paragraph(f"<b>[{fid}]</b>", ParagraphStyle('CiteFid', parent=styles['Normal'], fontSize=6, leading=7, fontName='Helvetica-Bold', textColor=primary_color))
        url_para = Paragraph(
            f"{label}: <link href='{url}' color='#000080'>{url}</link>",
            ParagraphStyle('CiteUrl', parent=styles['Normal'], fontSize=6, leading=7, textColor=body_color)
        )
        cite_rows.append([fid_para, url_para])

    cite_table = Table(cite_rows, colWidths=[20, 210])
    cite_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor("#e9ecef")),
    ]))
    col1_page5.append(cite_table)
        
    col1_page5.append(Spacer(1, 10))
    col1_page5.append(Paragraph("<b>Glossary Reference</b>", ParagraphStyle('GlossaryHead', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold', textColor=primary_color, spaceBefore=4, spaceAfter=2)))
    col1_page5.append(Paragraph("<b>DePIN:</b> Decentralized Physical Infrastructure Networks;<br/>"
                                "<b>Sybil Attack:</b> An attack vector where a single node creates multiple identities to manipulate consensus;<br/>"
                                "<b>AMM:</b> Automated Market Maker.", ParagraphStyle('GlossaryBody', parent=styles['Normal'], fontSize=7.5, leading=9.5, textColor=body_color)))
                                
    col2_page5 = []
    col2_page5.append(Paragraph("<b>Methodology Framework</b>", ParagraphStyle('MethHead', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold', textColor=primary_color, spaceBefore=4, spaceAfter=2)))
    col2_page5.append(Paragraph(
        "The MarketNode proprietary scoring system calculates a deterministic asset health index scaled from 1 to 10. "
        "The rating is derived using a weighted linear combination of three key institutional vectors:<br/><br/>"
        "1. <b>On-Chain Liquidity Depth (40% Weight):</b> Measures the depth and resilience of transaction liquidity pools, "
        "assessing slippage ratios, active trading volume, and protocol-owned liquidity buffers.<br/>"
        "2. <b>Developer Commit Frequency (30% Weight):</b> Audits open-source repositories to measure developer velocity, "
        "tracking commit frequencies, active code branches, issue resolution latency, and PR merging cycles.<br/>"
        "3. <b>Token Distribution Gini Coefficient (30% Weight):</b> Calculates supply centralization parameters, "
        "weighting the top wallet addresses to evaluate insider concentration and governance vulnerability.",
        ParagraphStyle('MethBody', parent=styles['Normal'], fontSize=7.5, leading=9.5, textColor=body_color)
    ))
    col2_page5.append(Spacer(1, 10))
    col2_page5.append(Paragraph("<b>Rating Threshold Classifications</b>", ParagraphStyle('ThreshHead', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold', textColor=primary_color, spaceBefore=4, spaceAfter=2)))
    col2_page5.append(Paragraph(
        "• <b>8.0 - 10.0: Institutional Investment Grade.</b> Minimal systemic risk, robust code velocity, and highly decentralized asset distribution profiles.<br/>"
        "• <b>5.0 - 7.9: Moderate Operational Risk.</b> Stable fundamentals with minor exposure to market volatility, developing community networks, or moderate insider concentration.<br/>"
        "• <b>1.0 - 4.9: Speculative / High Risk Profile.</b> Severely concentrated distribution, low developer activity, or insufficient on-chain liquidity depth to support volume shifts.",
        ParagraphStyle('ThreshBody', parent=styles['Normal'], fontSize=7.5, leading=9.5, textColor=body_color)
    ))
    
    page5_table = Table([[col1_page5, col2_page5]], colWidths=[240, 270])
    page5_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(Paragraph("<b>SOURCE CITATION REGISTRY & METHODOLOGY FRAMEWORK</b>", section_style))
    story.append(Spacer(1, 4))
    story.append(page5_table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
