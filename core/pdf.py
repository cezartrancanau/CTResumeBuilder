import html
import shutil
import subprocess
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage

from core.config import DEFAULT_SECTION_ORDER, SECTION_LABELS
from core.helpers import plain_text, split_nonempty_lines


def compile_pdf(tex_path: Path) -> tuple[Path | None, str | None]:
    pdflatex = shutil.which("pdflatex")
    if pdflatex is None:
        return None, "pdflatex was not found. Install MiKTeX or TeX Live for exact LaTeX output."
    cmd = [pdflatex, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", tex_path.name]
    try:
        result = subprocess.run(cmd, cwd=tex_path.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return None, "Exact LaTeX generation timed out. Open MiKTeX Console, install pending updates/packages, then try again."
    pdf_path = tex_path.with_suffix(".pdf")
    if result.returncode != 0 or not pdf_path.exists():
        return None, result.stdout[-3000:] if result.stdout else "Unknown LaTeX error."
    return pdf_path, None


def add_pdf_section(story, styles, title: str):
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>{html.escape(title)}</b>", styles["Heading2"]))


def clickable_text(label: str, url: str) -> str:
    """Return ReportLab-safe clickable text, or plain text when no URL exists."""
    safe_label = html.escape((label or "").strip())
    safe_link = html.escape((url or "").strip(), quote=True)
    if not safe_link:
        return safe_label
    return f'<link href="{safe_link}">{safe_label or safe_link}</link>'


def build_fallback_pdf(pdf_path: Path, form_data, photo_path: Path | None) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallText", parent=styles["Normal"], fontSize=9, leading=11))
    story = []
    if photo_path and photo_path.exists():
        try:
            story.append(RLImage(str(photo_path), width=72, height=72))
        except Exception:
            pass
    name = plain_text(form_data.get("name", "")) or "Resume"
    story.append(Paragraph(f"<b>{name}</b>", styles["Title"]))
    contact = []
    location = form_data.get("location", "").strip()
    email = form_data.get("email", "").strip()
    phone = form_data.get("phone", "").strip()
    if location:
        contact.append(plain_text(location))
    if email:
        contact.append(clickable_text(email, f"mailto:{email}"))
    if phone:
        contact.append(plain_text(phone))
    for platform, text, url in zip(
        form_data.getlist("social_platform"),
        form_data.getlist("social_text"),
        form_data.getlist("social_url"),
    ):
        label = (text or platform or "Website").strip()
        if label or url.strip():
            contact.append(clickable_text(label, url))
    if contact:
        story.append(Paragraph(" | ".join(contact), styles["Normal"]))

    order = form_data.get("section_order", ",".join(DEFAULT_SECTION_ORDER)).split(",")
    for section in [s for s in order if s in SECTION_LABELS]:
        if section == "summary":
            value = form_data.get("summary", "").strip()
            if value:
                add_pdf_section(story, styles, SECTION_LABELS[section])
                story.append(Paragraph(plain_text(value), styles["Normal"]))
        elif section == "experience":
            rows = list(zip(form_data.getlist("exp_company"), form_data.getlist("exp_position"), form_data.getlist("exp_location"), form_data.getlist("exp_start"), form_data.getlist("exp_end"), form_data.getlist("exp_bullets")))
            rows = [r for r in rows if any(x.strip() for x in r)]
            if rows:
                add_pdf_section(story, styles, SECTION_LABELS[section])
                for company, position, location, start, end, bullets in rows:
                    story.append(Paragraph(f"<b>{plain_text(position or company)}</b> — {plain_text(company)}", styles["Normal"]))
                    story.append(Paragraph(" | ".join(plain_text(x) for x in [location, start, end] if x.strip()), styles["SmallText"]))
                    for b in split_nonempty_lines(bullets):
                        story.append(Paragraph("• " + plain_text(b), styles["Normal"]))
        elif section == "education":
            rows = list(zip(form_data.getlist("edu_school"), form_data.getlist("edu_location"), form_data.getlist("edu_degree"), form_data.getlist("edu_dates"), form_data.getlist("edu_note"), form_data.getlist("edu_bullets")))
            rows = [r for r in rows if any(x.strip() for x in r)]
            if rows:
                add_pdf_section(story, styles, SECTION_LABELS[section])
                for school, location, degree, dates, note, bullets in rows:
                    story.append(Paragraph(f"<b>{plain_text(school)}</b> — {plain_text(location)}", styles["Normal"]))
                    story.append(Paragraph(" | ".join(plain_text(x) for x in [degree, dates, note] if x.strip()), styles["SmallText"]))
                    for b in split_nonempty_lines(bullets):
                        story.append(Paragraph("• " + plain_text(b), styles["Normal"]))
        elif section in {"skills", "languages", "interests"}:
            names = form_data.getlist({"skills": "skill_name", "languages": "language_name", "interests": "interest_name"}[section])
            values = form_data.getlist({"skills": "skill_value", "languages": "language_level", "interests": "interest_value"}[section])
            rows = [(n, v) for n, v in zip(names, values) if n.strip() or v.strip()]
            if rows:
                add_pdf_section(story, styles, SECTION_LABELS[section])
                for n, v in rows:
                    story.append(Paragraph(f"<b>{plain_text(n)}</b>: {plain_text(v)}", styles["Normal"]))
        elif section == "projects":
            rows = [(n, u, d) for n, u, d in zip(form_data.getlist("project_name"), form_data.getlist("project_url"), form_data.getlist("project_description")) if n.strip() or u.strip() or d.strip()]
            if rows:
                add_pdf_section(story, styles, SECTION_LABELS[section])
                for n, u, d in rows:
                    story.append(Paragraph(f"<b>{clickable_text(n, u)}</b>", styles["Normal"]))
                    story.append(Paragraph(plain_text(d), styles["Normal"]))
        elif section == "certifications":
            rows = [(n, i, d, u) for n, i, d, u in zip(form_data.getlist("cert_name"), form_data.getlist("cert_issuer"), form_data.getlist("cert_date"), form_data.getlist("cert_url")) if n.strip() or i.strip() or d.strip() or u.strip()]
            if rows:
                add_pdf_section(story, styles, SECTION_LABELS[section])
                for n, i, d, u in rows:
                    detail = " | ".join(plain_text(x) for x in [i, d] if x.strip())
                    title = clickable_text(n, u)
                    story.append(Paragraph(f"<b>{title}</b>" + (f" — {detail}" if detail else ""), styles["Normal"]))
        elif section == "awards":
            rows = [(n, d, da, b) for n, d, da, b in zip(form_data.getlist("award_name"), form_data.getlist("award_description"), form_data.getlist("award_dates"), form_data.getlist("award_bullets")) if n.strip() or d.strip() or da.strip() or b.strip()]
            if rows:
                add_pdf_section(story, styles, SECTION_LABELS[section])
                for n, d, da, b in rows:
                    story.append(Paragraph(f"<b>{plain_text(n)}</b> — {plain_text(da)}", styles["Normal"]))
                    if d.strip(): story.append(Paragraph(plain_text(d), styles["Normal"]))
                    for bullet in split_nonempty_lines(b): story.append(Paragraph("• " + plain_text(bullet), styles["Normal"]))
        elif section == "publications":
            rows = [(t, a, u) for t, a, u in zip(form_data.getlist("publication_title"), form_data.getlist("publication_authors"), form_data.getlist("publication_url")) if t.strip() or a.strip() or u.strip()]
            if rows:
                add_pdf_section(story, styles, SECTION_LABELS[section])
                for t, a, u in rows:
                    title = clickable_text(t, u)
                    story.append(Paragraph(f"<b>{title}</b> — {plain_text(a)}", styles["Normal"]))
    if len(story) <= 3:
        story.append(Paragraph("Fill in more fields to build your CV.", styles["Normal"]))
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(pdf_path), pagesize=letter).build(story)

