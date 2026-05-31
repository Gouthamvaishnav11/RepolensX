from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import datetime
from loguru import logger


# ── Colors ────────────────────────────────────────────────
GREEN  = colors.HexColor("#22c55e")
DARK   = colors.HexColor("#0f172a")
SLATE  = colors.HexColor("#334155")
LIGHT  = colors.HexColor("#f1f5f9")
YELLOW = colors.HexColor("#eab308")
RED    = colors.HexColor("#ef4444")


def score_color(score: float):
    if score >= 80: return GREEN
    if score >= 60: return YELLOW
    return RED


def generate_pdf_report(repo: dict, analysis: dict) -> bytes:
    """Generate a full PDF report for a repository analysis."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle("Title", parent=styles["Heading1"],
        fontSize=22, textColor=DARK, spaceAfter=6, alignment=TA_LEFT, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=SLATE, spaceAfter=20)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"],
        fontSize=14, textColor=DARK, spaceBefore=16, spaceAfter=8, fontName="Helvetica-Bold")
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
        fontSize=10, textColor=SLATE, spaceAfter=6, leading=16)
    small_style = ParagraphStyle("Small", parent=styles["Normal"],
        fontSize=9, textColor=SLATE)

    elements = []

    # ── Header ────────────────────────────────────────────
    elements.append(Paragraph("RepoLens X", ParagraphStyle("Brand",
        parent=styles["Normal"], fontSize=10, textColor=GREEN, fontName="Helvetica-Bold")))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(f"Repository Analysis Report", title_style))
    elements.append(Paragraph(
        f"{repo.get('full_name', 'Unknown')} · Generated {datetime.now().strftime('%B %d, %Y')}",
        subtitle_style
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=GREEN, spaceAfter=16))

    # ── Overall Score ─────────────────────────────────────
    overall = analysis.get("overall_score") or 0
    recruiter = analysis.get("recruiter_score") or 0

    score_data = [
        ["Overall Score", "Recruiter Score", "Language", "Total Files", "Commits"],
        [
            f"{int(overall)}/100",
            f"{int(recruiter)}/100",
            repo.get("language", "N/A"),
            str(analysis.get("total_files", 0)),
            str(analysis.get("total_commits", 0)),
        ]
    ]
    score_table = Table(score_data, colWidths=[3.2*cm]*5)
    score_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), DARK),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 9),
        ("BACKGROUND",   (0,1), (-1,1), LIGHT),
        ("FONTNAME",     (0,1), (-1,1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,1), (-1,1), 13),
        ("TEXTCOLOR",    (0,1), (0,1), score_color(overall)),
        ("TEXTCOLOR",    (1,1), (1,1), score_color(recruiter)),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[DARK, LIGHT]),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.white),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("BORDERRADIUS", (0,0), (-1,-1), 4),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 0.5*cm))

    # ── Summary ───────────────────────────────────────────
    elements.append(Paragraph("AI Summary", h2_style))
    elements.append(Paragraph(analysis.get("summary", "No summary available."), body_style))

    # ── Score Breakdown ───────────────────────────────────
    elements.append(Paragraph("Score Breakdown", h2_style))
    breakdown_data = [
        ["Category", "Score", "Rating"],
        ["Code Quality",   f"{int(analysis.get('code_quality_score') or 0)}/100",   _rating(analysis.get('code_quality_score') or 0)],
        ["Documentation",  f"{int(analysis.get('documentation_score') or 0)}/100",  _rating(analysis.get('documentation_score') or 0)],
        ["Testing",        f"{int(analysis.get('testing_score') or 0)}/100",         _rating(analysis.get('testing_score') or 0)],
        ["DevOps / CI/CD", f"{int(analysis.get('devops_score') or 0)}/100",          _rating(analysis.get('devops_score') or 0)],
        ["Architecture",   f"{int(analysis.get('architecture_score') or 0)}/100",    _rating(analysis.get('architecture_score') or 0)],
    ]
    breakdown_table = Table(breakdown_data, colWidths=[6*cm, 4*cm, 6*cm])
    breakdown_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), DARK),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN",         (1,0), (2,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    elements.append(breakdown_table)
    elements.append(Spacer(1, 0.4*cm))

    # ── Strengths ─────────────────────────────────────────
    strengths = analysis.get("strengths") or []
    if strengths:
        elements.append(Paragraph("✅ Strengths", h2_style))
        for s in strengths:
            elements.append(Paragraph(f"• {s}", body_style))

    # ── Weaknesses ────────────────────────────────────────
    weaknesses = analysis.get("weaknesses") or []
    if weaknesses:
        elements.append(Paragraph("❌ Weaknesses", h2_style))
        for w in weaknesses:
            elements.append(Paragraph(f"• {w}", body_style))

    # ── Missing Practices ─────────────────────────────────
    missing = analysis.get("missing_practices") or []
    if missing:
        elements.append(Paragraph("⚠️ Missing Practices", h2_style))
        for m in missing:
            elements.append(Paragraph(f"• {m}", body_style))

    # ── Recruiter Feedback ────────────────────────────────
    recruiter_feedback = analysis.get("recruiter_feedback") or {}
    if recruiter_feedback:
        elements.append(Paragraph("🧑‍💼 Recruiter Evaluation", h2_style))
        if recruiter_feedback.get("written_feedback"):
            elements.append(Paragraph(recruiter_feedback["written_feedback"], body_style))
        if recruiter_feedback.get("hiring_recommendation"):
            elements.append(Paragraph(
                f"Hiring Recommendation: <b>{recruiter_feedback['hiring_recommendation']}</b>",
                body_style
            ))
        if recruiter_feedback.get("seniority_level"):
            elements.append(Paragraph(
                f"Assessed Level: <b>{recruiter_feedback['seniority_level']}</b>",
                body_style
            ))

    # ── Mentor Roadmap ────────────────────────────────────
    roadmap = analysis.get("mentor_roadmap") or {}
    if roadmap and roadmap.get("roadmap"):
        elements.append(Paragraph("🗺️ 30-Day Improvement Roadmap", h2_style))
        if roadmap.get("motivational_message"):
            elements.append(Paragraph(f'"{roadmap["motivational_message"]}"',
                ParagraphStyle("Quote", parent=body_style, textColor=GREEN, fontName="Helvetica-Oblique")))
            elements.append(Spacer(1, 0.2*cm))

        for week_key, week_data in roadmap["roadmap"].items():
            week_num = week_key.replace("week_", "Week ")
            elements.append(Paragraph(f"<b>{week_num.title()}: {week_data.get('title', '')}</b>", body_style))
            for task in week_data.get("tasks", []):
                elements.append(Paragraph(f"  → {task}", small_style))
            elements.append(Spacer(1, 0.2*cm))

    # ── Footer ────────────────────────────────────────────
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=SLATE))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        f"Generated by RepoLens X · {datetime.now().strftime('%Y-%m-%d %H:%M')} · repolens.ai",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=SLATE, alignment=TA_CENTER)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def _rating(score: float) -> str:
    if score >= 80: return "Excellent ✅"
    if score >= 60: return "Good 🟡"
    if score >= 40: return "Needs Work 🟠"
    return "Poor ❌"
