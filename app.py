from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from flask import Flask, render_template, request, send_file, url_for
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
TEMPLATES_DIR = BASE_DIR / "templates"
GENERATED_DIR.mkdir(exist_ok=True)

ALLOWED_TEMPLATES = {"classic", "modern", "minimal"}
ALLOWED_DOWNLOADS = {"cv.tex", "cv.pdf", "resume.json"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

SECTION_LABELS = {
    "summary": "Professional Summary",
    "experience": "Work Experience",
    "education": "Education",
    "skills": "Skills",
    "projects": "Projects",
    "languages": "Languages",
    "certifications": "Certifications",
    "awards": "Awards",
    "publications": "Publications",
    "interests": "Interests",
}
DEFAULT_SECTION_ORDER = [
    "summary", "experience", "education", "skills", "projects", "languages",
    "certifications", "awards", "publications", "interests"
]


def cleanup_generated(max_folders: int = 40) -> None:
    """Keep the generated folder small by deleting old build folders."""
    if not GENERATED_DIR.exists():
        return
    folders = [p for p in GENERATED_DIR.iterdir() if p.is_dir()]
    folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for folder in folders[max_folders:]:
        shutil.rmtree(folder, ignore_errors=True)


cleanup_generated()


def latex_escape(value: str) -> str:
    if not value:
        return ""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in value)


def safe_url(value: str) -> str:
    value = (value or "").strip()
    return value.replace(" ", "%20").replace("{", "%7B").replace("}", "%7D")


def clean_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    return cleaned or "resume"


def getlist(name: str) -> list[str]:
    return [v.strip() for v in request.form.getlist(name)]


def split_nonempty_lines(value: str) -> list[str]:
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def plain_text(value: str) -> str:
    return html.escape((value or "").strip()).replace("\n", "<br/>")


def section_block(title: str, body: str, list_section: bool = False) -> str:
    if not body.strip():
        return ""
    if list_section:
        return f"\\section{{{title}}}\n  \\resumeSubHeadingListStart\n{body}\n  \\resumeSubHeadingListEnd\n"
    return f"\\section{{{title}}}\n\\small{{\n{body}\n}}\n"


def bullet_list_latex(text: str) -> str:
    bullets = split_nonempty_lines(text)
    if not bullets:
        return ""
    content = "\n      \\resumeItemListStart\n"
    for bullet in bullets:
        content += f"        \\resumeItemPlain{{{latex_escape(bullet)}}}\n"
    content += "      \\resumeItemListEnd\n"
    return content


def build_header(data: dict[str, str], social_links: list[tuple[str, str]]) -> str:
    lines = []
    name = data.get("NAME", "") or "Resume"
    lines.append(r"    {\fontsize{21}{23}\selectfont\bfseries " + name + r"}\\[5pt]")

    links = []
    for label, url in social_links:
        if label and url:
            links.append(r"\href{" + safe_url(url) + r"}{" + latex_escape(label) + r"}")
        elif label:
            links.append(latex_escape(label))
    if links:
        lines.append(r"    " + r" \hspace{0.75em}\textbar\hspace{0.75em} ".join(links) + r"\\[5pt]")

    contact_parts = []
    email = data.get("EMAIL", "")
    email_raw = data.get("EMAIL_RAW", "")
    if email:
        contact_parts.append(r"\href{mailto:" + email_raw + r"}{" + email + r"}")
    if data.get("PHONE", ""):
        contact_parts.append(data["PHONE"])
    if data.get("LOCATION", ""):
        contact_parts.append(data["LOCATION"])
    if contact_parts:
        lines.append(r"    " + r" \hspace{0.75em}\textbar\hspace{0.75em} ".join(contact_parts))
    return "\n".join(lines)


def build_social_links() -> list[tuple[str, str]]:
    links = []
    fields = [
        ("GitHub", "github_text", "github_url"),
        ("LinkedIn", "linkedin_text", "linkedin_url"),
        ("Portfolio", "portfolio_text", "portfolio_url"),
        ("Website", "website_text", "website_url"),
        ("X", "x_text", "x_url"),
        ("Stack Overflow", "stackoverflow_text", "stackoverflow_url"),
        ("LeetCode", "leetcode_text", "leetcode_url"),
        ("Codeforces", "codeforces_text", "codeforces_url"),
        ("Kaggle", "kaggle_text", "kaggle_url"),
    ]
    for default_label, text_name, url_name in fields:
        text = request.form.get(text_name, "").strip()
        url = request.form.get(url_name, "").strip()
        if text or url:
            links.append((text or default_label, url))
    return links


def build_experience() -> str:
    companies = getlist("exp_company")
    positions = getlist("exp_position")
    locations = getlist("exp_location")
    starts = getlist("exp_start")
    ends = getlist("exp_end")
    currents = request.form.getlist("exp_current")
    bullets_raw = getlist("exp_bullets")
    blocks = []
    for idx, (company, position, location, start, end, bullets) in enumerate(zip(companies, positions, locations, starts, ends, bullets_raw)):
        if not any([company, position, location, start, end, bullets]):
            continue
        current = str(idx) in currents
        dates = f"{start} - {'Present' if current else end}".strip(" -")
        block = (
            f"    \\resumeSubheading\n"
            f"      {{{latex_escape(company)}}}\n"
            f"      {{{latex_escape(location)}}}\n"
            f"      {{{latex_escape(position)}}}\n"
            f"      {{{latex_escape(dates)}}}\n"
        )
        block += bullet_list_latex(bullets)
        blocks.append(block)
    return "\n".join(blocks)


def build_education() -> str:
    schools = getlist("edu_school")
    locations = getlist("edu_location")
    degrees = getlist("edu_degree")
    dates = getlist("edu_dates")
    notes = getlist("edu_note")
    bullets_raw = getlist("edu_bullets")
    blocks = []
    for school, location, degree, dates, note, bullets_text in zip(schools, locations, degrees, dates, notes, bullets_raw):
        if not any([school, location, degree, dates, note, bullets_text]):
            continue
        if note:
            block = (
                f"    \\resumeSubheadingFive\n"
                f"      {{{latex_escape(school)}}}\n"
                f"      {{{latex_escape(location)}}}\n"
                f"      {{{latex_escape(degree)}}}\n"
                f"      {{{latex_escape(dates)}}}\n"
                f"      {{{latex_escape(note)}}}\n"
            )
        else:
            block = (
                f"    \\resumeSubheading\n"
                f"      {{{latex_escape(school)}}}\n"
                f"      {{{latex_escape(location)}}}\n"
                f"      {{{latex_escape(degree)}}}\n"
                f"      {{{latex_escape(dates)}}}\n"
            )
        block += bullet_list_latex(bullets_text)
        blocks.append(block)
    return "\n".join(blocks)


def build_pair_section(name_field: str, value_field: str) -> str:
    rows = []
    for name, value in zip(getlist(name_field), getlist(value_field)):
        if name or value:
            rows.append(f"    \\resumeSubItem{{{latex_escape(name)}}}\n      {{{latex_escape(value)}}}")
    return "\n\n".join(rows)


def build_projects() -> str:
    rows = []
    for name, url, desc in zip(getlist("project_name"), getlist("project_url"), getlist("project_description")):
        if not any([name, url, desc]):
            continue
        title = latex_escape(name)
        if url:
            title = f"\\href{{{safe_url(url)}}}{{{title}}}"
        rows.append(f"    \\resumeSubItem{{{title}}}\n      {{{latex_escape(desc)}}}")
    return "\n\n".join(rows)


def build_certifications() -> str:
    rows = []
    for name, issuer, date, url in zip(getlist("cert_name"), getlist("cert_issuer"), getlist("cert_date"), getlist("cert_url")):
        if not any([name, issuer, date, url]):
            continue
        title = latex_escape(name)
        if url:
            title = f"\\href{{{safe_url(url)}}}{{{title}}}"
        detail = " | ".join(latex_escape(x) for x in [issuer, date] if x)
        rows.append(f"    \\resumeSubItem{{{title}}}\n      {{{detail}}}")
    return "\n\n".join(rows)


def build_awards() -> str:
    blocks = []
    for name, desc, dates, bullets_text in zip(getlist("award_name"), getlist("award_description"), getlist("award_dates"), getlist("award_bullets")):
        if not any([name, desc, dates, bullets_text]):
            continue
        block = (
            f"    \\resumeAward\n"
            f"      {{{latex_escape(name)}}}\n"
            f"      {{{latex_escape(desc)}}}\n"
            f"      {{{latex_escape(dates)}}}\n"
        )
        block += bullet_list_latex(bullets_text)
        blocks.append(block)
    return "\n".join(blocks)


def build_publications() -> str:
    rows = []
    for title, authors, url in zip(getlist("publication_title"), getlist("publication_authors"), getlist("publication_url")):
        if not any([title, authors, url]):
            continue
        safe_title = latex_escape(title)
        if url:
            safe_title = f"\\href{{{safe_url(url)}}}{{{safe_title}}}"
        rows.append(f"    \\resumePublication\n      {{{safe_title}}}\n      {{{latex_escape(authors)}}}")
    return "\n\n".join(rows)


def save_profile_photo(work_dir: Path) -> tuple[str, Path | None]:
    if request.form.get("include_photo") != "on":
        return "", None
    photo = request.files.get("profile_photo")
    if not photo or not photo.filename:
        return "", None
    ext = Path(photo.filename).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        return "", None
    photo_path = work_dir / f"profile_photo{ext}"
    photo.save(photo_path)
    latex_path = photo_path.name.replace("\\", "/")
    return f"\\includegraphics[width=1.05in]{{{latex_path}}}\\\\[5pt]", photo_path


def collect_resume_json() -> dict:
    data: dict[str, object] = {"version": "v1"}
    for key in request.form.keys():
        values = request.form.getlist(key)
        data[key] = values if len(values) > 1 else values[0]
    return data


def render_latex(data: dict[str, str], template_name: str) -> str:
    template_name = template_name if template_name in ALLOWED_TEMPLATES else "classic"
    template_path = TEMPLATES_DIR / f"cv_template_{template_name}.tex"
    if not template_path.exists():
        template_path = TEMPLATES_DIR / "cv_template_classic.tex"
    template = template_path.read_text(encoding="utf-8")
    for key, value in data.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def compile_pdf(tex_path: Path) -> tuple[Path | None, str | None]:
    pdflatex = shutil.which("pdflatex")
    if pdflatex is None:
        return None, "pdflatex was not found. Install MiKTeX or TeX Live for exact LaTeX output."
    cmd = [pdflatex, "--disable-installer", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", tex_path.name]
    try:
        result = subprocess.run(cmd, cwd=tex_path.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=8)
    except subprocess.TimeoutExpired:
        return None, "Exact LaTeX generation timed out. MiKTeX may be waiting for package installation."
    pdf_path = tex_path.with_suffix(".pdf")
    if result.returncode != 0 or not pdf_path.exists():
        return None, result.stdout[-3000:] if result.stdout else "Unknown LaTeX error."
    return pdf_path, None


def add_pdf_section(story, styles, title: str):
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>{html.escape(title)}</b>", styles["Heading2"]))


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
    for key in ["location", "email", "phone", "github_text", "linkedin_text", "portfolio_text", "website_text"]:
        value = form_data.get(key, "").strip()
        if value:
            contact.append(plain_text(value))
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
                    story.append(Paragraph(f"<b>{plain_text(n)}</b> {plain_text(u)}", styles["Normal"]))
                    story.append(Paragraph(plain_text(d), styles["Normal"]))
        elif section == "certifications":
            rows = [(n, i, d, u) for n, i, d, u in zip(form_data.getlist("cert_name"), form_data.getlist("cert_issuer"), form_data.getlist("cert_date"), form_data.getlist("cert_url")) if n.strip() or i.strip() or d.strip() or u.strip()]
            if rows:
                add_pdf_section(story, styles, SECTION_LABELS[section])
                for n, i, d, u in rows:
                    story.append(Paragraph(f"<b>{plain_text(n)}</b> — {' | '.join(plain_text(x) for x in [i, d, u] if x.strip())}", styles["Normal"]))
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
                    story.append(Paragraph(f"<b>{plain_text(t)}</b> — {plain_text(a)} {plain_text(u)}", styles["Normal"]))
    if len(story) <= 3:
        story.append(Paragraph("Fill in more fields to build your CV.", styles["Normal"]))
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(pdf_path), pagesize=letter).build(story)


@app.route("/", methods=["GET"])
def index():
    return render_template("form.html", section_order=DEFAULT_SECTION_ORDER, section_labels=SECTION_LABELS)


@app.route("/generate", methods=["POST"])
def generate():
    name = request.form.get("name", "Resume").strip() or "Resume"
    template_name = request.form.get("resume_template", "classic")
    if template_name not in ALLOWED_TEMPLATES:
        template_name = "classic"
    file_id = f"{clean_filename(name)}_{uuid.uuid4().hex[:8]}"
    work_dir = GENERATED_DIR / file_id
    work_dir.mkdir(parents=True, exist_ok=True)

    photo_block, photo_path = save_profile_photo(work_dir)
    social_links = build_social_links()
    data = {
        "NAME": latex_escape(name),
        "EMAIL": latex_escape(request.form.get("email", "")),
        "EMAIL_RAW": safe_url(request.form.get("email", "")),
        "PHONE": latex_escape(request.form.get("phone", "")),
        "LOCATION": latex_escape(request.form.get("location", "")),
        "PHOTO_BLOCK": photo_block,
    }
    data["HEADER_BLOCK"] = build_header(data, social_links)
    sections = {
        "summary": section_block("Professional Summary", latex_escape(request.form.get("summary", ""))),
        "experience": section_block("Work Experience", build_experience(), list_section=True),
        "education": section_block("Education", build_education(), list_section=True),
        "skills": section_block("Skills", build_pair_section("skill_name", "skill_value"), list_section=True),
        "projects": section_block("Projects", build_projects(), list_section=True),
        "languages": section_block("Languages", build_pair_section("language_name", "language_level"), list_section=True),
        "certifications": section_block("Certifications", build_certifications(), list_section=True),
        "awards": section_block("Awards", build_awards(), list_section=True),
        "publications": section_block("Publications", build_publications(), list_section=True),
        "interests": section_block("Interests", build_pair_section("interest_name", "interest_value"), list_section=True),
    }
    order = request.form.get("section_order", ",".join(DEFAULT_SECTION_ORDER)).split(",")
    ordered_sections = "\n".join(sections[key] for key in order if key in sections)
    data["ORDERED_SECTIONS"] = ordered_sections

    tex_content = render_latex(data, template_name)
    tex_path = work_dir / "cv.tex"
    tex_path.write_text(tex_content, encoding="utf-8")
    (work_dir / "resume.json").write_text(json.dumps(collect_resume_json(), indent=2), encoding="utf-8")

    pdf_path, error = compile_pdf(tex_path)
    if pdf_path is None:
        fallback_path = tex_path.with_suffix(".pdf")
        latex_error = error
        try:
            build_fallback_pdf(fallback_path, request.form, photo_path)
            pdf_path = fallback_path
            error = (
                "MiKTeX/LaTeX did not finish, so a fast fallback PDF was generated. "
                "The cv.tex file is still available for exact LaTeX compilation.\n\n"
                f"LaTeX message:\n{latex_error}"
            )
        except Exception as fallback_error:
            error = f"LaTeX failed: {latex_error}\n\nBuilt-in PDF generator also failed: {fallback_error}"

    return render_template(
        "result.html",
        pdf_ready=pdf_path is not None,
        error=error,
        tex_url=url_for("download_file", file_id=file_id, filename="cv.tex"),
        pdf_url=url_for("download_file", file_id=file_id, filename="cv.pdf") if pdf_path else None,
        json_url=url_for("download_file", file_id=file_id, filename="resume.json"),
    )


@app.route("/download/<file_id>/<filename>")
def download_file(file_id: str, filename: str):
    safe_id = clean_filename(file_id)
    if safe_id != file_id or filename not in ALLOWED_DOWNLOADS:
        return "Invalid file", 400
    path = GENERATED_DIR / file_id / filename
    if not path.exists():
        return "File not found", 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=False, port=5050)
