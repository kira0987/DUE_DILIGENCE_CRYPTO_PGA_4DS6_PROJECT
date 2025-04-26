import os
import json
import pandas as pd
import re
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_DATA_LABEL_POSITION
from collections import defaultdict
import spacy
from uuid import uuid4

# --- Paths ---
ANSWERS_CSV = "data/auto_answered_questions.csv"
CLASSIFIED_JSON = "data/classified_questions.json"
LOGO_PATH = "assets/shield.png"
OUTPUT_DIR = "output"
BASE_NAME = "due_diligence_report"
ANALYTICS_BASE_NAME = "due_diligence_analytics"

# --- Global Variables ---
tag_to_slides = defaultdict(list)
CRYPTO_COLORS = {
    "primary": RGBColor(0, 102, 204),
    "accent": RGBColor(153, 51, 255),
    "highlight": RGBColor(0, 255, 153),
    "text": RGBColor(255, 255, 255),
    "background": RGBColor(10, 25, 50),
}

TAG_OBJECTIVES = {
    "AML / KYC": "Ensure robust Anti-Money Laundering and Know Your Customer compliance.",
    "Community & UX": "Assess user engagement, usability, and community transparency.",
    "Custody & Asset Security": "Evaluate asset storage and custody security mechanisms.",
    "Cybersecurity & Data Privacy": "Examine cybersecurity and data protection practices.",
    "ESG & Sustainability": "Evaluate environmental, social, and governance sustainability.",
    "Financial Health": "Analyze financial statements and health indicators.",
    "Governance": "Assess decision-making and board oversight structures.",
    "IP & Contracts": "Evaluate intellectual property and contract integrity.",
    "Legal & Regulatory": "Ensure legal and regulatory compliance.",
    "Risk Management": "Identify risk management strategies.",
    "Strategy & Competitive Positioning": "Understand strategy and market positioning.",
    "Technology & Infrastructure": "Evaluate technological scalability and reliability.",
    "Tokenomics & Trading Integrity": "Assess token economics and trading transparency.",
    "Future Outlook": "Evaluate alignment with 2025 crypto trends and innovations."
}

DUE_DILIGENCE_CRITERIA = {
    "AML / KYC": [
        "AML policies", "KYC procedures", "compliance measures", "regulatory adherence",
        "anti-money laundering", "know your customer", "transaction monitoring", "sanctions screening",
        "client verification", "due diligence checks", "risk-based approach", "compliance program"
    ],
    "Community & UX": [
        "user engagement", "platform usability", "community transparency", "feedback mechanisms",
        "user experience", "interface design", "community governance", "social media presence",
        "user support", "accessibility", "stakeholder interaction", "transparency reports"
    ],
    "Custody & Asset Security": [
        "asset storage", "multi-signature wallets", "asset ownership verification", "insurance coverage",
        "cold storage", "hot wallets", "custodial services", "security protocols",
        "asset protection", "private key management", "audit trails", "fund safeguarding"
    ],
    "Cybersecurity & Data Privacy": [
        "blockchain technology", "cybersecurity measures", "two-factor authentication", "data protection policy",
        "encryption standards", "network security", "data privacy compliance", "penetration testing",
        "firewall protection", "GDPR compliance", "security audits", "threat detection"
    ],
    "ESG & Sustainability": [
        "sustainability practices", "energy consumption", "environmental impact", "sustainability audits",
        "carbon footprint", "green initiatives", "social responsibility", "governance standards",
        "ethical investing", "renewable energy", "ESG reporting", "community impact"
    ],
    "Financial Health": [
        "financial statements", "cash flow projections", "tax disputes", "annual auditing",
        "balance sheet", "profit and loss", "liquidity ratios", "debt obligations",
        "revenue streams", "expense management", "financial audits", "capital reserves"
    ],
    "Governance": [
        "board of directors", "conflict of interest policies", "external audits", "succession planning",
        "governance framework", "decision-making process", "transparency measures", "executive oversight",
        "stakeholder rights", "policy enforcement", "ethical standards", "board independence"
    ],
    "IP & Contracts": [
        "intellectual property assets", "IP infringement", "smart contract audits", "major contracts",
        "patent protection", "trademark registration", "contract compliance", "legal agreements",
        "code licensing", "proprietary technology", "IP portfolio", "contractual obligations"
    ],
    "Legal & Regulatory": [
        "licenses and permits", "international law compliance", "sanctions monitoring", "regulatory filings",
        "legal compliance", "regulatory framework", "compliance audits", "jurisdictional adherence",
        "securities law", "tax compliance", "legal disputes", "regulatory reporting"
    ],
    "Risk Management": [
        "risk management strategies", "market volatility", "business continuity plan", "operational resilience",
        "risk assessment", "mitigation plans", "crisis management", "risk exposure",
        "contingency planning", "market risk", "operational risk", "compliance risk"
    ],
    "Strategy & Competitive Positioning": [
        "market positioning", "competitor analysis", "investment strategies", "growth strategies",
        "market share", "competitive advantage", "strategic planning", "business development",
        "market trends", "innovation strategy", "partnerships", "go-to-market strategy"
    ],
    "Technology & Infrastructure": [
        "scalability plans", "security measures", "blockchain technology", "infrastructure upgrades",
        "system architecture", "network reliability", "tech stack", "performance metrics",
        "cloud infrastructure", "protocol security", "system redundancy", "tech audits"
    ],
    "Tokenomics & Trading Integrity": [
        "securities compliance", "trade surveillance", "valuation consistency", "code reviews",
        "token distribution", "market manipulation", "liquidity provision", "trading policies",
        "token economics", "exchange compliance", "price stability", "audit reports"
    ],
    "Future Outlook": [
        "stablecoin compliance", "AI integration", "institutional adoption", "quantum resistance",
        "market trends", "technological innovation", "regulatory evolution", "growth projections",
        "digital asset trends", "blockchain adoption", "strategic foresight", "innovation pipeline"
    ]
}

# --- Importance Weights Calculation ---
# Based on a Crypto Risk Priority Framework
# Scoring: Severity (0-5), Likelihood (0-5), Investor Concern (0-5)
# Weight = (Severity * Likelihood * Investor Concern) / 125 (normalized to 0-1)
IMPORTANCE_WEIGHTS = {
    "AML / KYC": (5 * 5 * 5) / 125,  # 1.0 (Critical regulatory requirement)
    "Legal & Regulatory": (5 * 5 * 5) / 125,  # 1.0 (High regulatory scrutiny)
    "Cybersecurity & Data Privacy": (5 * 4 * 5) / 125,  # 0.8 (Critical for trust)
    "Custody & Asset Security": (5 * 4 * 5) / 125,  # 0.8 (Core to fund safety)
    "Financial Health": (4 * 4 * 4) / 125,  # 0.512 (Key for stability)
    "Governance": (4 * 3 * 4) / 125,  # 0.384 (Important for oversight)
    "Risk Management": (4 * 3 * 4) / 125,  # 0.384 (Mitigates losses)
    "Tokenomics & Trading Integrity": (3 * 3 * 4) / 125,  # 0.288 (Affects market trust)
    "Community & UX": (3 * 2 * 3) / 125,  # 0.144 (Enhances adoption)
    "ESG & Sustainability": (2 * 2 * 3) / 125,  # 0.096 (Growing investor interest)
    "IP & Contracts": (2 * 2 * 3) / 125,  # 0.096 (Supports innovation)
    "Strategy & Competitive Positioning": (2 * 2 * 3) / 125,  # 0.096 (Long-term growth)
    "Technology & Infrastructure": (3 * 2 * 3) / 125,  # 0.144 (Operational backbone)
    "Future Outlook": (2 * 2 * 2) / 125  # 0.064 (Speculative but relevant)
}

# --- NLP Setup ---
nlp = spacy.load("en_core_web_sm")

# --- Helper Functions ---
def get_next_output_filename(base_name):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    i = 0
    while True:
        suffix = f" ({i})" if i else ""
        path = os.path.join(OUTPUT_DIR, f"{base_name}{suffix}.pptx")
        if not os.path.exists(path):
            return path
        i += 1

def load_data():
    try:
        df = pd.read_csv(ANSWERS_CSV)
        df.columns = [c.lower() for c in df.columns]
        df["question"] = df["question"].astype(str).str.strip()
        with open(CLASSIFIED_JSON, "r", encoding="utf-8") as f:
            classified = json.load(f)
        return df, classified
    except FileNotFoundError:
        df = pd.DataFrame({
            "question": ["What are the AML policies?", "Who are the managing partners?"],
            "answer": ["The fund has robust AML policies.", "Managing partners oversee operations."]
        })
        classified = [
            {"question": "What are the AML policies?", "tag": "AML / KYC"},
            {"question": "Who are the managing partners?", "tag": "Governance"}
        ]
        return df, classified

def extract_fund_name(df):
    try:
        text_series = pd.concat([df["question"].astype(str), df["answer"].astype(str)], ignore_index=True)
        pattern = r'\b[\w\s]+?\sFund\b'
        for text in text_series:
            if pd.isna(text):
                continue
            match = re.search(pattern, text)
            if match:
                return match.group(0).rstrip(" Fund").strip()
        return "Crypto Fund"
    except Exception:
        return "Crypto Fund"

def extract_summary(text):
    if not isinstance(text, str) or len(text.strip()) < 20:
        return None
    lower = text.lower()
    if any(x in lower for x in ["not mentioned", "cannot determine", "unavailable"]):
        return None
    clean = text.replace("Based on the document,", "").replace("According to", "").strip()
    return clean.split(". ")[0].strip().capitalize() + "."

def format_gap(text):
    text = text.strip().rstrip(".")
    if not text:
        return None
    if any(x in text.lower() for x in ["aml", "licens", "compliance", "audit", "governance"]):
        return f"Critical gap: {text}"
    return f"Gap: {text.lower()}"

def apply_crypto_theme(slide):
    bg = slide.background
    fill = bg.fill
    fill.gradient()
    fill.gradient_stops[0].color.rgb = CRYPTO_COLORS["background"]
    fill.gradient_stops[1].color.rgb = CRYPTO_COLORS["primary"]

def add_branding(slide, current_tag="General"):
    if os.path.exists(LOGO_PATH):
        slide.shapes.add_picture(LOGO_PATH, Inches(0.3), Inches(0.1), height=Inches(0.6))
    footer = slide.shapes.add_textbox(Inches(0.5), Inches(7.0), Inches(9), Inches(0.3)).text_frame
    footer.text = f"DueXpert – AI Crypto Fund Due Diligence Suite | {current_tag}"
    footer.paragraphs[0].font.size = Pt(10)
    footer.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    footer.paragraphs[0].font.name = "Montserrat"

def add_nav_button(slide, text, target_slide=None, left=8.5, top=0.5):
    btn = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(1.2), Inches(0.4))
    btn.fill.solid()
    btn.fill.fore_color.rgb = CRYPTO_COLORS["accent"]
    btn.line.color.rgb = CRYPTO_COLORS["highlight"]
    text_frame = btn.text_frame
    text_frame.text = text
    p = text_frame.paragraphs[0]
    p.font.size = Pt(12)
    p.font.color.rgb = CRYPTO_COLORS["text"]
    p.font.name = "Montserrat"
    if target_slide:
        run = p.runs[0] if p.runs else p.add_run()
        add_internal_hyperlink(run, target_slide)
    return btn

def add_internal_hyperlink(run, target_slide):
    try:
        rId = run.part.relate_to(target_slide.part, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide')
        hlink = parse_xml(f'<a:hlinkClick xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" r:id="{rId}" action="ppaction://hlinksldjump"/>')
        run._r.append(hlink)
    except Exception as e:
        print(f"Warning: Could not add hyperlink to slide - {e}")

# --- First PPTX Generation Functions ---
def create_cover_slide(prs, df):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    apply_crypto_theme(slide)
    title = slide.shapes.title
    fund_name = extract_fund_name(df)
    title.text = f"{fund_name} Due Diligence Report"
    title.text_frame.paragraphs[0].font.size = Pt(36)
    title.text_frame.paragraphs[0].font.bold = True
    title.text_frame.paragraphs[0].font.color.rgb = CRYPTO_COLORS["highlight"]
    title.text_frame.paragraphs[0].font.name = "Montserrat"
    subtitle = slide.placeholders[1]
    subtitle.text = f"Prepared by DueXpert AI | {datetime.today().strftime('%Y-%m-%d')}"
    subtitle.text_frame.paragraphs[0].font.size = Pt(20)
    subtitle.text_frame.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    subtitle.text_frame.paragraphs[0].font.name = "Montserrat"
    add_branding(slide)
    return slide

def create_executive_summary_slide(prs, tag_summary):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_crypto_theme(slide)
    add_branding(slide)
    title = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.0), Inches(0.5)).text_frame
    title.text = "Executive Summary"
    title.paragraphs[0].font.size = Pt(28)
    title.paragraphs[0].font.bold = True
    title.paragraphs[0].font.color.rgb = CRYPTO_COLORS["highlight"]
    title.paragraphs[0].font.name = "Montserrat"
    
    content = slide.shapes.add_textbox(Inches(0.8), Inches(1.2), Inches(4.5), Inches(3.5)).text_frame
    content.text = "Key Findings Overview:"
    content.word_wrap = True
    p = content.paragraphs[0]
    p.font.size = Pt(18)
    p.font.color.rgb = CRYPTO_COLORS["text"]
    p.font.name = "Montserrat"
    
    paragraph_index = 1
    for tag in sorted(tag_summary):
        findings_count, issues_count = tag_summary[tag]
        p = content.add_paragraph()
        run = p.add_run()
        run.text = f"{tag}: {findings_count} findings, {issues_count} issues"
        run.font.size = Pt(14)
        run.font.color.rgb = CRYPTO_COLORS["text"] if issues_count <= 2 else CRYPTO_COLORS["highlight"]
        run.font.name = "Montserrat"
        tag_to_slides[tag].append((paragraph_index, run))
        paragraph_index += 1

    chart_data = CategoryChartData()
    chart_data.categories = sorted(tag_summary.keys())
    chart_data.add_series("Findings", [tag_summary[tag][0] for tag in sorted(tag_summary)])
    chart_data.add_series("Issues", [tag_summary[tag][1] for tag in sorted(tag_summary)])
    x, y, cx, cy = Inches(5.5), Inches(1.2), Inches(4.0), Inches(2.5)
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.chart_title.text_frame.text = "Findings vs Issues"
    chart.chart_title.text_frame.paragraphs[0].font.size = Pt(12)
    chart.chart_title.text_frame.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]

    return slide

def create_toc_slide(prs, tag_page_numbers):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_crypto_theme(slide)
    add_branding(slide)
    title = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.0), Inches(0.5)).text_frame
    title.text = "Table of Contents"
    title.paragraphs[0].font.size = Pt(28)
    title.paragraphs[0].font.bold = True
    title.paragraphs[0].font.color.rgb = CRYPTO_COLORS["highlight"]
    title.paragraphs[0].font.name = "Montserrat"
    
    content = slide.shapes.add_textbox(Inches(0.8), Inches(1.2), Inches(8.5), Inches(5.5)).text_frame
    content.word_wrap = True
    paragraph_index = 0
    for tag in sorted(tag_page_numbers.keys()):
        page_num = tag_page_numbers[tag]
        p = content.add_paragraph()
        run = p.add_run()
        run.text = f"{page_num}. {tag}"
        run.font.size = Pt(16)
        run.font.color.rgb = CRYPTO_COLORS["text"]
        run.font.name = "Montserrat"
        tag_to_slides[tag].append((paragraph_index, run))
        paragraph_index += 1
    return slide

def create_section_slide(prs, tag, findings, issues, page_num, prev_slide=None, next_slide=None, summary_slide=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_crypto_theme(slide)
    add_branding(slide, current_tag=tag)
    
    if summary_slide:
        add_nav_button(slide, "Back to Summary", summary_slide, left=8.5, top=0.5)
    if prev_slide:
        add_nav_button(slide, "Previous", prev_slide, left=7.0, top=0.5)
    if next_slide:
        add_nav_button(slide, "Next", next_slide, left=9.8, top=0.5)
    
    y = 0.8
    title = slide.shapes.add_textbox(Inches(0.8), Inches(y), Inches(8.0), Inches(0.5)).text_frame
    title.text = f"{page_num}. {tag}"
    title.paragraphs[0].font.size = Pt(24)
    title.paragraphs[0].font.bold = True
    title.paragraphs[0].font.color.rgb = CRYPTO_COLORS["highlight"]
    title.paragraphs[0].font.name = "Montserrat"
    
    y += 0.6
    obj = slide.shapes.add_textbox(Inches(0.8), Inches(y), Inches(8.5), Inches(0.8)).text_frame
    obj.text = f"Objective: {TAG_OBJECTIVES.get(tag, 'Not defined')}"
    obj.word_wrap = True
    obj.paragraphs[0].font.size = Pt(14)
    obj.paragraphs[0].font.italic = True
    obj.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    obj.paragraphs[0].font.name = "Montserrat"
    
    y += 1.0
    content = slide.shapes.add_textbox(Inches(0.8), Inches(y), Inches(8.5), Inches(5.0)).text_frame
    content.word_wrap = True
    content.text = "Key Findings:"
    p = content.paragraphs[0]
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = CRYPTO_COLORS["text"]
    p.font.name = "Montserrat"
    
    lines = 1
    max_findings = 6
    for finding in findings[:max_findings]:
        p = content.add_paragraph()
        p.text = f"• {finding}"
        p.font.size = Pt(11)
        p.font.color.rgb = CRYPTO_COLORS["text"]
        p.font.name = "Montserrat"
        lines += 1
    
    if issues and lines < 10:
        p = content.add_paragraph()
        p.text = "Outstanding Issues:"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = CRYPTO_COLORS["text"]
        p.font.name = "Montserrat"
        lines += 1
        for issue in issues[:10-lines]:
            p = content.add_paragraph()
            p.text = f"• {format_gap(issue)}"
            p.font.size = Pt(11)
            p.font.color.rgb = CRYPTO_COLORS["text"]
            p.font.name = "Montserrat"
            lines += 1
    
    page = slide.shapes.add_textbox(Inches(9.0), Inches(7.0), Inches(1), Inches(0.3)).text_frame
    page.text = f"Page {page_num}"
    page.paragraphs[0].font.size = Pt(10)
    page.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    page.paragraphs[0].font.name = "Montserrat"
    
    return slide

# --- Second PPTX Generation Functions ---
def create_analytics_cover_slide(prs, fund_name):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    apply_crypto_theme(slide)
    title = slide.shapes.title
    title.text = f"{fund_name} Due Diligence Analytics"
    title.text_frame.paragraphs[0].font.size = Pt(36)
    title.text_frame.paragraphs[0].font.bold = True
    title.text_frame.paragraphs[0].font.color.rgb = CRYPTO_COLORS["highlight"]
    title.text_frame.paragraphs[0].font.name = "Montserrat"
    subtitle = slide.placeholders[1]
    subtitle.text = f"Prepared by DueXpert AI | {datetime.today().strftime('%Y-%m-%d')}"
    subtitle.text_frame.paragraphs[0].font.size = Pt(20)
    subtitle.text_frame.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    subtitle.text_frame.paragraphs[0].font.name = "Montserrat"
    add_branding(slide)
    return slide

def create_analytics_toc_slide(prs, tag_page_numbers):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_crypto_theme(slide)
    add_branding(slide, current_tag="Table of Contents")
    title = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.0), Inches(0.5)).text_frame
    title.text = "Table of Contents"
    title.paragraphs[0].font.size = Pt(28)
    title.paragraphs[0].font.bold = True
    title.paragraphs[0].font.color.rgb = CRYPTO_COLORS["highlight"]
    title.paragraphs[0].font.name = "Montserrat"
    
    content = slide.shapes.add_textbox(Inches(0.8), Inches(1.2), Inches(8.5), Inches(5.5)).text_frame
    content.word_wrap = True
    for tag, page_num in sorted(tag_page_numbers.items()):
        p = content.add_paragraph()
        run = p.add_run()
        run.text = f"{page_num}. {tag} Analytics"
        run.font.size = Pt(16)
        run.font.color.rgb = CRYPTO_COLORS["text"]
        run.font.name = "Montserrat"
    return slide

def create_topic_analytics_slide(prs, tag, analysis, risk_score, page_num):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_crypto_theme(slide)
    add_branding(slide, current_tag=f"{tag} Analytics")
    
    title = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.0), Inches(0.5)).text_frame
    title.text = f"{page_num}. {tag} Analytics"
    title.paragraphs[0].font.size = Pt(24)
    title.paragraphs[0].font.bold = True
    title.paragraphs[0].font.color.rgb = CRYPTO_COLORS["highlight"]
    title.paragraphs[0].font.name = "Montserrat"
    
    obj = slide.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(8.0), Inches(0.5)).text_frame
    obj.text = f"Objective: {TAG_OBJECTIVES.get(tag, 'Not defined')}"
    obj.word_wrap = True
    obj.paragraphs[0].font.size = Pt(14)
    obj.paragraphs[0].font.italic = True
    obj.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    obj.paragraphs[0].font.name = "Montserrat"
    
    completeness = analysis[tag]["completeness"]
    found = analysis[tag]["found"]
    missing = analysis[tag]["missing"]
    
    # Normalize pie chart data to proportions (sum to 1)
    total_criteria = len(found) + len(missing)
    covered_proportion = (len(found) / total_criteria) if total_criteria > 0 else 0
    missing_proportion = (len(missing) / total_criteria) if total_criteria > 0 else 0
    
    pie_data = CategoryChartData()
    pie_data.categories = ["Covered", "Missing"]
    pie_data.add_series("Criteria", [covered_proportion, missing_proportion])
    x, y, cx, cy = Inches(5.5), Inches(1.8), Inches(5.0), Inches(3.5)
    pie_chart = slide.shapes.add_chart(XL_CHART_TYPE.PIE, x, y, cx, cy, pie_data).chart
    pie_chart.has_legend = True
    pie_chart.legend.position = XL_LEGEND_POSITION.RIGHT
    pie_chart.chart_title.text_frame.text = f"{tag} Completeness"
    pie_chart.chart_title.text_frame.paragraphs[0].font.size = Pt(14)
    pie_chart.chart_title.text_frame.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    plot = pie_chart.plots[0]
    plot.has_data_labels = True
    data_labels = plot.data_labels
    data_labels.number_format = '0.0%'
    data_labels.position = XL_DATA_LABEL_POSITION.OUTSIDE_END
    
    content = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(5.5), Inches(4.5)).text_frame
    content.word_wrap = True
    content.text = (f"Completeness: {completeness:.1f}%\n"
                    f"Risk Score: {risk_score:.1f}/100\n\n"
                    f"Found Criteria:\n" +
                    (("\n".join(f"• {c}" for c in found) + "\n") if found else "• None\n") +
                    f"\nMissing Criteria:\n" +
                    (("\n".join(f"• {c}" for c in missing) + "\n") if missing else "• None\n") +
                    f"\nImportance Weight: {IMPORTANCE_WEIGHTS[tag]:.3f}")
    
    for p in content.paragraphs:
        p.font.size = Pt(12)
        p.font.color.rgb = CRYPTO_COLORS["text"]
        p.font.name = "Montserrat"
        if p.text.strip().startswith("Risk Score") or p.text.strip().startswith("Missing Criteria:"):
            p.font.bold = True
    
    page = slide.shapes.add_textbox(Inches(9.0), Inches(7.0), Inches(1), Inches(0.3)).text_frame
    page.text = f"Page {page_num}"
    page.paragraphs[0].font.size = Pt(10)
    page.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    page.paragraphs[0].font.name = "Montserrat"
    
    return slide

def create_summary_analytics_slide(prs, analysis, risk_scores, fund_name, page_num):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_crypto_theme(slide)
    add_branding(slide, current_tag="Summary Analytics")
    
    title = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.0), Inches(0.5)).text_frame
    title.text = f"{page_num}. Summary Analytics"
    title.paragraphs[0].font.size = Pt(24)
    title.paragraphs[0].font.bold = True
    title.paragraphs[0].font.color.rgb = CRYPTO_COLORS["highlight"]
    title.paragraphs[0].font.name = "Montserrat"
    
    fully_covered = sum(1 for tag in analysis if analysis[tag]["completeness"] >= 80)
    partially_covered = sum(1 for tag in analysis if 40 <= analysis[tag]["completeness"] < 80)
    not_covered = sum(1 for tag in analysis if analysis[tag]["completeness"] < 40)
    avg_completeness = sum(analysis[tag]["completeness"] for tag in analysis) / len(analysis)
    avg_risk = sum(risk_scores[tag] for tag in risk_scores) / len(risk_scores)
    high_risk_gaps = [tag for tag in analysis if IMPORTANCE_WEIGHTS[tag] >= 0.8 and analysis[tag]["completeness"] < 60]
    
    chart_data = CategoryChartData()
    chart_data.categories = sorted(analysis.keys())
    chart_data.add_series("Risk Score", [risk_scores[tag] for tag in sorted(analysis)])
    x, y, cx, cy = Inches(0.8), Inches(1.2), Inches(8.5), Inches(3.0)
    chart = slide.shapes.add_chart(XL_CHART_TYPE.AREA, x, y, cx, cy, chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.chart_title.text_frame.text = "Risk Heatmap by Topic"
    chart.chart_title.text_frame.paragraphs[0].font.size = Pt(14)
    chart.chart_title.text_frame.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    category_axis = chart.category_axis
    category_axis.tick_labels.font.size = Pt(10)
    category_axis.tick_labels.font.name = "Montserrat"
    
    recommendation = ("Critical Risk: Immediate action required on high-priority gaps." if high_risk_gaps else
                     "Moderate Risk: Proceed with caution and address gaps.")
    
    content = slide.shapes.add_textbox(Inches(0.8), Inches(4.5), Inches(9.0), Inches(3.0)).text_frame
    content.word_wrap = True
    content.text = (f"Summary:\n"
                    f"- Total Topics: {len(analysis)}\n"
                    f"- Fully Covered (>=80%): {fully_covered}\n"
                    f"- Partially Covered (40-80%): {partially_covered}\n"
                    f"- Not Covered (<40%): {not_covered}\n"
                    f"- Avg Completeness: {avg_completeness:.1f}%\n"
                    f"- Avg Risk Score: {avg_risk:.1f}/100\n"
                    f"- High-Risk Gaps: {', '.join(high_risk_gaps) if high_risk_gaps else 'None'}\n"
                    f"Recommendation: {recommendation}")
    
    for p in content.paragraphs:
        p.font.size = Pt(12)
        p.font.color.rgb = CRYPTO_COLORS["text"]
        p.font.name = "Montserrat"
    
    page = slide.shapes.add_textbox(Inches(9.0), Inches(7.0), Inches(1), Inches(0.3)).text_frame
    page.text = f"Page {page_num}"
    page.paragraphs[0].font.size = Pt(10)
    page.paragraphs[0].font.color.rgb = CRYPTO_COLORS["text"]
    page.paragraphs[0].font.name = "Montserrat"
    
    return slide

# --- NLP Analysis Functions ---
def extract_slide_text(slide):
    text = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    text.append(run.text)
    return " ".join(text)

def detect_negative_sentiment(text):
    doc = nlp(text.lower())
    negative_indicators = ["not mentioned", "lacking", "insufficient", "unavailable", "no details", "unknown", "weak", "incomplete"]
    return any(indicator in text.lower() for indicator in negative_indicators)

def analyze_completeness(slide_text, criteria):
    doc = nlp(slide_text.lower())
    found_criteria = []
    similarity_threshold = 0.7
    
    for criterion in criteria:
        criterion_doc = nlp(criterion.lower())
        similarity = doc.similarity(criterion_doc)
        keyword_match = criterion.lower() in slide_text.lower()
        for chunk in doc.noun_chunks:
            if criterion.lower() in chunk.text.lower():
                found_criteria.append(criterion)
                break
        if similarity >= similarity_threshold or keyword_match:
            found_criteria.append(criterion)
    
    found_criteria = list(set(found_criteria))
    completeness = len(found_criteria) / len(criteria) * 100 if criteria else 0
    missing = [c for c in criteria if c not in found_criteria]
    
    if detect_negative_sentiment(slide_text):
        completeness *= 0.8
    
    return completeness, found_criteria, missing

def calculate_risk_score(analysis):
    risk_scores = {}
    for tag in analysis:
        completeness = analysis[tag]["completeness"] / 100
        weight = IMPORTANCE_WEIGHTS[tag]
        risk_score = (1 - completeness) * weight * 100
        if len(analysis[tag]["missing"]) > len(analysis[tag]["found"]):
            risk_score *= 1.2
        risk_scores[tag] = min(risk_score, 100)
    return risk_scores

def analyze_pptx(pptx_path):
    prs = Presentation(pptx_path)
    analysis = {}
    for slide in prs.slides:
        text = extract_slide_text(slide)
        for tag, criteria in DUE_DILIGENCE_CRITERIA.items():
            if tag.lower() in text.lower():
                completeness, found, missing = analyze_completeness(text, criteria)
                analysis[tag] = {
                    "completeness": completeness,
                    "found": found,
                    "missing": missing
                }
    for tag in TAG_OBJECTIVES:
        if tag not in analysis:
            analysis[tag] = {
                "completeness": 0,
                "found": [],
                "missing": DUE_DILIGENCE_CRITERIA[tag]
            }
    return analysis

# --- Main Function ---
def main():
    try:
        # --- Generate First PPTX ---
        output_path = get_next_output_filename(BASE_NAME)
        prs = Presentation()
        prs.slide_width = Inches(12)
        prs.slide_height = Inches(7.5)
        df, classified = load_data()

        tag_map = defaultdict(list)
        for q in classified:
            if isinstance(q, dict) and "tag" in q and "question" in q:
                tag_map[q["tag"]].append(q)
            else:
                print(f"Warning: Invalid question entry skipped: {q}")
        
        tag_summary = {}
        tag_findings = {}
        for tag in sorted(tag_map):
            findings, issues = [], []
            for q in tag_map[tag]:
                qt = q["question"].strip()
                row = df[df["question"] == qt]
                if not row.empty:
                    summary = extract_summary(row.iloc[0]["answer"])
                    if summary and not detect_negative_sentiment(row.iloc[0]["answer"]):
                        findings.append(summary)
                    else:
                        issues.append(qt)
                else:
                    issues.append(qt)
            tag_summary[tag] = (len(findings), len(issues))
            tag_findings[tag] = (findings, issues)

        # Track page numbers for each tag
        tag_page_numbers = {}
        page_counter = 1  # Start at 1 for cover slide

        cover_slide = create_cover_slide(prs, df)
        all_slides = [cover_slide]
        page_counter += 1  # TOC will be page 2

        exec_summary = create_executive_summary_slide(prs, tag_summary)
        all_slides.append(exec_summary)
        page_counter += 1  # Executive Summary is page 3

        # Calculate page numbers for each tag section
        for tag in sorted(tag_map):
            findings, issues = tag_findings[tag]
            finding_chunks = [findings[i:i+6] for i in range(0, len(findings), 6)]
            issue_chunks = [issues[i:i+4] for i in range(0, len(issues), 4)]
            max_chunks = max(len(finding_chunks), len(issue_chunks))
            tag_page_numbers[tag] = page_counter
            page_counter += max_chunks

        toc = create_toc_slide(prs, tag_page_numbers)
        all_slides.insert(1, toc)  # Insert TOC as second slide (page 2)
        
        prev_slide = exec_summary
        page_counter = 3  # Reset to 3 for first section slide
        for tag in sorted(tag_map):
            findings, issues = tag_findings[tag]
            finding_chunks = [findings[i:i+6] for i in range(0, len(findings), 6)]
            issue_chunks = [issues[i:i+4] for i in range(0, len(issues), 4)]
            max_chunks = max(len(finding_chunks), len(issue_chunks))
            
            for chunk_idx in range(max_chunks):
                current_findings = finding_chunks[chunk_idx] if chunk_idx < len(finding_chunks) else []
                current_issues = issue_chunks[chunk_idx] if chunk_idx < len(issue_chunks) else []
                next_slide = None  # Will be set later if needed
                slide = create_section_slide(
                    prs, tag, current_findings, current_issues, page_counter,
                    prev_slide=prev_slide, next_slide=next_slide, summary_slide=toc
                )
                tag_to_slides[tag].append(slide)
                all_slides.append(slide)
                prev_slide = slide
                page_counter += 1

        # Add navigation for next_slide
        for i in range(3, len(all_slides)-1):  # Skip cover, TOC, exec summary
            all_slides[i].shapes[2].text_frame.paragraphs[0].runs[0].hyperlink.address = None
            add_internal_hyperlink(all_slides[i].shapes[2].text_frame.paragraphs[0].runs[0], all_slides[i+1])

        # Add hyperlinks to TOC and Executive Summary
        for tag in sorted(tag_summary):
            if tag in tag_to_slides and tag_to_slides[tag]:
                first_slide = tag_to_slides[tag][0]
                for item in tag_to_slides[tag]:
                    if isinstance(item, tuple) and len(item) == 2:
                        idx, run = item
                        if idx < len(toc.shapes[1].text_frame.paragraphs):
                            p = toc.shapes[1].text_frame.paragraphs[idx]
                            if p.runs:
                                add_internal_hyperlink(p.runs[0], first_slide)
                        if idx < len(exec_summary.shapes[1].text_frame.paragraphs):
                            p = exec_summary.shapes[1].text_frame.paragraphs[idx]
                            if p.runs:
                                add_internal_hyperlink(p.runs[0], first_slide)

        prs.save(output_path)
        print(f"✅ Due Diligence Report Generated: {output_path}")

        # --- Generate Second PPTX ---
        analytics_path = get_next_output_filename(ANALYTICS_BASE_NAME)
        analysis = analyze_pptx(output_path)
        risk_scores = calculate_risk_score(analysis)
        
        prs_analytics = Presentation()
        prs_analytics.slide_width = Inches(12)
        prs_analytics.slide_height = Inches(7.5)
        
        fund_name = extract_fund_name(df)
        cover_slide = create_analytics_cover_slide(prs_analytics, fund_name)
        
        # Create TOC for analytics PPTX
        analytics_tag_page_numbers = {}
        page_counter = 2  # Cover is page 1, TOC is page 2
        for tag in sorted(analysis.keys()):
            analytics_tag_page_numbers[tag] = page_counter
            page_counter += 1
        analytics_tag_page_numbers["Summary Analytics"] = page_counter
        
        toc_slide = create_analytics_toc_slide(prs_analytics, analytics_tag_page_numbers)
        
        page_counter = 2  # Reset for first analytics slide
        analytics_slides = [cover_slide, toc_slide]
        for tag in sorted(analysis.keys()):
            slide = create_topic_analytics_slide(prs_analytics, tag, analysis, risk_scores[tag], page_counter)
            analytics_slides.append(slide)
            page_counter += 1
        
        summary_slide = create_summary_analytics_slide(prs_analytics, analysis, risk_scores, fund_name, page_counter)
        analytics_slides.append(summary_slide)
        
        prs_analytics.save(analytics_path)
        print(f"✅ Analytics Report Generated: {analytics_path}")
    
    except Exception as e:
        print(f"❌ Failed to generate reports: {str(e)}")
        raise

if __name__ == "__main__":
    main()