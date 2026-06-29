from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from flask import Flask, render_template, request, send_file, url_for

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
TEMPLATE_PATH = BASE_DIR / "templates" / "cv_template.tex"
GENERATED_DIR.mkdir(exist_ok=True)


def latex_escape(value: str) -> str:
    """Escape common LaTeX special characters while preserving normal text."""
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
    # Keep URLs readable. Escape braces and spaces only enough for href usage.
    return value.replace(" ", "%20").replace("{", "%7B").replace("}", "%7D")


def clean_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    return cleaned or "resume"


def getlist(name: str) -> list[str]:
    return [v.strip() for v in request.form.getlist(name)]


def build_skills() -> str:
    names = getlist("skill_name")
    values = getlist("skill_value")
    rows = []
    for name, value in zip(names, values):
        if name or value:
            rows.append(
                f"  \\resumeSubItem{{{latex_escape(name)}}}\n"
                f"    {{{latex_escape(value)}}}"
            )
    return "\n\n".join(rows)


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

        bullets = [b.strip() for b in bullets_text.splitlines() if b.strip()]
        if bullets:
            block += "\n      \\resumeItemListStart\n"
            for bullet in bullets:
                block += f"        \\resumeItemPlain{{{latex_escape(bullet)}}}\n"
            block += "      \\resumeItemListEnd\n"
        blocks.append(block)
    return "\n".join(blocks)


def build_projects() -> str:
    names = getlist("project_name")
    urls = getlist("project_url")
    descriptions = getlist("project_description")
    rows = []
    for name, url, desc in zip(names, urls, descriptions):
        if not any([name, url, desc]):
            continue
        title = latex_escape(name)
        if url:
            title = f"\\href{{{safe_url(url)}}}{{{title}}}"
        rows.append(f"    \\resumeSubItem{{{title}}}\n      {{{latex_escape(desc)}}}")
    return "\n\n".join(rows)


def build_awards() -> str:
    names = getlist("award_name")
    descriptions = getlist("award_description")
    dates = getlist("award_dates")
    bullets_raw = getlist("award_bullets")
    blocks = []
    for name, desc, dates, bullets_text in zip(names, descriptions, dates, bullets_raw):
        if not any([name, desc, dates, bullets_text]):
            continue
        block = (
            f"    \\resumeAward\n"
            f"      {{{latex_escape(name)}}}\n"
            f"      {{{latex_escape(desc)}}}\n"
            f"      {{{latex_escape(dates)}}}\n"
        )
        bullets = [b.strip() for b in bullets_text.splitlines() if b.strip()]
        if bullets:
            block += "\n      \\resumeItemListStart\n"
            for bullet in bullets:
                block += f"        \\resumeItemPlain{{{latex_escape(bullet)}}}\n"
            block += "      \\resumeItemListEnd\n"
        blocks.append(block)
    return "\n".join(blocks)



def build_publications() -> str:
    titles = getlist("publication_title")
    authors = getlist("publication_authors")
    urls = getlist("publication_url")
    rows = []
    for title, authors, url in zip(titles, authors, urls):
        if not any([title, authors, url]):
            continue
        safe_title = latex_escape(title)
        if url:
            safe_title = f"\\href{{{safe_url(url)}}}{{{safe_title}}}"
        rows.append(
            f"\\resumePublication\n"
            f"{{{safe_title}}}\n"
            f"{{{latex_escape(authors)}}}"
        )
    return "\n\n".join(rows)

def nonempty(value: str) -> bool:
    return bool((value or "").strip())


def build_header(data: dict[str, str]) -> str:
    lines = []
    name = data.get("NAME", "") or "Resume"
    lines.append(r"    {\fontsize{21}{23}\selectfont\bfseries " + name + r"}\\[5pt]")

    github_url = data.get("GITHUB_URL", "")
    github_text = data.get("GITHUB_TEXT", "")
    if github_url and github_text:
        lines.append(r"    \href{" + github_url + r"}{" + github_text + r"}\\[5pt]")
    elif github_text:
        lines.append(r"    " + github_text + r"\\[5pt]")

    linkedin_url = data.get("LINKEDIN_URL", "")
    linkedin_text = data.get("LINKEDIN_TEXT", "")
    if linkedin_url and linkedin_text:
        lines.append(r"    \href{" + linkedin_url + r"}{" + linkedin_text + r"}\\[5pt]")
    elif linkedin_text:
        lines.append(r"    " + linkedin_text + r"\\[5pt]")

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
        lines.append((r"    \hspace{1em}\textbar\hspace{1em}" ).join(contact_parts))

    return "\n".join(lines)


def section_block(title: str, body: str, list_section: bool = False) -> str:
    if not body.strip():
        return ""
    if list_section:
        return f"\\section{{{title}}}\n  \\resumeSubHeadingListStart\n{body}\n  \\resumeSubHeadingListEnd\n"
    return f"\\section{{{title}}}\n\\small{{\n{body}\n}}\n"


def plain_text(value: str) -> str:
    """Clean text for the fallback PDF generator."""
    return html.escape((value or "").strip()).replace("\n", "<br/>")


def split_nonempty_lines(value: str) -> list[str]:
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def build_fallback_pdf(pdf_path: Path, form_data) -> None:
    """Create a simple PDF even when pdflatex is missing or fails."""
    styles = getSampleStyleSheet()
    story = []

    name = plain_text(form_data.get("name", "")) or "Resume"
    story.append(Paragraph(f"<b>{name}</b>", styles["Title"]))

    contact = []
    for key in ["location", "email", "phone", "github_text", "github_url", "linkedin_text", "linkedin_url"]:
        value = form_data.get(key, "").strip()
        if value:
            contact.append(plain_text(value))
    if contact:
        story.append(Paragraph(" | ".join(contact), styles["Normal"]))
    story.append(Spacer(1, 12))

    def add_section(title: str):
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))

    about = form_data.get("about", "").strip()
    if about:
        add_section("About Me")
        story.append(Paragraph(plain_text(about), styles["Normal"]))

    schools = form_data.getlist("edu_school")
    locations = form_data.getlist("edu_location")
    degrees = form_data.getlist("edu_degree")
    dates = form_data.getlist("edu_dates")
    notes = form_data.getlist("edu_note")
    bullets_raw = form_data.getlist("edu_bullets")
    education_any = False
    edu_story = []
    for school, location, degree, date, note, bullets in zip(schools, locations, degrees, dates, notes, bullets_raw):
        if not any([school.strip(), location.strip(), degree.strip(), date.strip(), note.strip(), bullets.strip()]):
            continue
        education_any = True
        title = " — ".join(plain_text(x) for x in [school, location] if x.strip()) or "Education"
        edu_story.append(Paragraph(f"<b>{title}</b>", styles["Normal"]))
        sub = " | ".join(plain_text(x) for x in [degree, date, note] if x.strip())
        if sub:
            edu_story.append(Paragraph(sub, styles["Normal"]))
        for b in split_nonempty_lines(bullets):
            edu_story.append(Paragraph("• " + plain_text(b), styles["Normal"]))
    if education_any:
        add_section("Education")
        story.extend(edu_story)

    skill_names = form_data.getlist("skill_name")
    skill_values = form_data.getlist("skill_value")
    skills_any = False
    skills_story = []
    for k, v in zip(skill_names, skill_values):
        if not k.strip() and not v.strip():
            continue
        skills_any = True
        label = plain_text(k) or "Skill"
        skills_story.append(Paragraph(f"<b>{label}:</b> {plain_text(v)}", styles["Normal"]))
    if skills_any:
        add_section("Skills")
        story.extend(skills_story)

    project_names = form_data.getlist("project_name")
    project_urls = form_data.getlist("project_url")
    project_descriptions = form_data.getlist("project_description")
    projects_any = False
    projects_story = []
    for n, u, d in zip(project_names, project_urls, project_descriptions):
        if not n.strip() and not u.strip() and not d.strip():
            continue
        projects_any = True
        title = plain_text(n) or "Project"
        if u.strip():
            title += " — " + plain_text(u)
        projects_story.append(Paragraph(f"<b>{title}</b>", styles["Normal"]))
        if d.strip():
            projects_story.append(Paragraph(plain_text(d), styles["Normal"]))
    if projects_any:
        add_section("Projects")
        story.extend(projects_story)

    award_names = form_data.getlist("award_name")
    award_descriptions = form_data.getlist("award_description")
    award_dates = form_data.getlist("award_dates")
    award_bullets = form_data.getlist("award_bullets")
    awards_any = False
    awards_story = []
    for n, d, date, bullets in zip(award_names, award_descriptions, award_dates, award_bullets):
        if not n.strip() and not d.strip() and not date.strip() and not bullets.strip():
            continue
        awards_any = True
        title = plain_text(n) or "Award"
        if date.strip():
            title += " — " + plain_text(date)
        awards_story.append(Paragraph(f"<b>{title}</b>", styles["Normal"]))
        if d.strip():
            awards_story.append(Paragraph(plain_text(d), styles["Normal"]))
        for b in split_nonempty_lines(bullets):
            awards_story.append(Paragraph("• " + plain_text(b), styles["Normal"]))
    if awards_any:
        add_section("Awards")
        story.extend(awards_story)

    pub_titles = form_data.getlist("publication_title")
    pub_authors = form_data.getlist("publication_authors")
    pub_urls = form_data.getlist("publication_url")
    pubs_any = False
    pubs_story = []
    for t, a, u in zip(pub_titles, pub_authors, pub_urls):
        if not t.strip() and not a.strip() and not u.strip():
            continue
        pubs_any = True
        title = plain_text(t) or "Publication"
        if u.strip():
            title += " — " + plain_text(u)
        pubs_story.append(Paragraph(f"<b>{title}</b>", styles["Normal"]))
        if a.strip():
            pubs_story.append(Paragraph("(" + plain_text(a) + ")", styles["Normal"]))
    if pubs_any:
        add_section("Publications")
        story.extend(pubs_story)

    if len(story) <= 3:
        story.append(Paragraph("Fill in more fields to build your CV.", styles["Normal"]))

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(pdf_path), pagesize=letter).build(story)

def render_latex(data: dict[str, str]) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    for key, value in data.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def compile_pdf(tex_path: Path) -> tuple[Path | None, str | None]:
    """Try to compile the real LaTeX template, but never let Flask hang forever.

    MiKTeX can block while asking to install missing packages. --disable-installer
    makes it fail fast instead of waiting for an invisible prompt.
    """
    pdflatex = shutil.which("pdflatex")
    if pdflatex is None:
        return None, "pdflatex was not found. Install MiKTeX or TeX Live to generate the exact LaTeX PDF."

    cmd = [
        pdflatex,
        "--disable-installer",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        tex_path.name,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=tex_path.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return None, (
            "Exact LaTeX generation timed out after 5 seconds. MiKTeX is probably stuck on package installation "
            "or a hidden prompt. Open MiKTeX Console and install/update the missing packages, or compile the downloaded cv.tex manually."
        )

    pdf_path = tex_path.with_suffix(".pdf")
    if result.returncode != 0 or not pdf_path.exists():
        log = result.stdout[-3000:] if result.stdout else "Unknown LaTeX error."
        return None, log
    return pdf_path, None


@app.route("/", methods=["GET"])
def index():
    return render_template("form.html")


@app.route("/generate", methods=["POST"])
def generate():
    name = request.form.get("name", "Resume").strip() or "Resume"
    file_id = f"{clean_filename(name)}_{uuid.uuid4().hex[:8]}"
    work_dir = GENERATED_DIR / file_id
    work_dir.mkdir(parents=True, exist_ok=True)

    education_blocks = build_education()
    skill_blocks = build_skills()
    project_blocks = build_projects()
    award_blocks = build_awards()
    publication_blocks = build_publications()

    data = {
        "NAME": latex_escape(name),
        "GITHUB_URL": safe_url(request.form.get("github_url", "")),
        "GITHUB_TEXT": latex_escape(request.form.get("github_text", "")),
        "LINKEDIN_URL": safe_url(request.form.get("linkedin_url", "")),
        "LINKEDIN_TEXT": latex_escape(request.form.get("linkedin_text", "")),
        "EMAIL": latex_escape(request.form.get("email", "")),
        "EMAIL_RAW": safe_url(request.form.get("email", "")),
        "PHONE": latex_escape(request.form.get("phone", "")),
        "LOCATION": latex_escape(request.form.get("location", "")),
    }
    data["HEADER_BLOCK"] = build_header(data)
    data["ABOUT_SECTION"] = section_block("About Me", latex_escape(request.form.get("about", "")), list_section=False)
    data["EDUCATION_SECTION"] = section_block("Education", education_blocks, list_section=True)
    data["SKILLS_SECTION"] = section_block("Skills", skill_blocks, list_section=True)
    data["PROJECTS_SECTION"] = section_block("Projects", project_blocks, list_section=True)
    data["AWARDS_SECTION"] = section_block("Awards", award_blocks, list_section=True)
    data["PUBLICATIONS_SECTION"] = section_block("Publications", publication_blocks, list_section=True)

    tex_content = render_latex(data)
    tex_path = work_dir / "cv.tex"
    tex_path.write_text(tex_content, encoding="utf-8")

    # First try the exact .tex template. If MiKTeX hangs/fails, do not keep the page loading forever.
    pdf_path, error = compile_pdf(tex_path)

    # Safety net: always create a PDF so the app returns quickly.
    # The generated cv.tex is still downloadable and matches the user's LaTeX template.
    if pdf_path is None:
        fallback_path = tex_path.with_suffix(".pdf")
        latex_error = error
        try:
            build_fallback_pdf(fallback_path, request.form)
            pdf_path = fallback_path
            error = (
                "MiKTeX/LaTeX did not finish, so a fast fallback PDF was generated. "
                "For the exact template look, download cv.tex and compile it after fixing MiKTeX.\n\n"
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
    )


@app.route("/download/<file_id>/<filename>")
def download_file(file_id: str, filename: str):
    safe_id = clean_filename(file_id)
    if safe_id != file_id or filename not in {"cv.tex", "cv.pdf"}:
        return "Invalid file", 400
    path = GENERATED_DIR / file_id / filename
    if not path.exists():
        return "File not found", 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=False)
