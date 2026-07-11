from pathlib import Path

from flask import request

from core.config import ALLOWED_TEMPLATES, IMAGE_EXTENSIONS, TEMPLATES_DIR
from core.helpers import getlist, latex_escape, safe_url, split_nonempty_lines


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
            links.append(r"\href{\detokenize{" + safe_url(url) + r"}}{" + latex_escape(label) + r"}")
        elif label:
            links.append(latex_escape(label))
    if links:
        lines.append(r"    " + r" \hspace{0.75em}\textbar\hspace{0.75em} ".join(links) + r"\\[5pt]")

    contact_parts = []
    email = data.get("EMAIL", "")
    email_raw = data.get("EMAIL_RAW", "")
    if email:
        contact_parts.append(r"\href{\detokenize{mailto:" + safe_url(email_raw) + r"}}{" + email + r"}")
    if data.get("PHONE", ""):
        contact_parts.append(data["PHONE"])
    if data.get("LOCATION", ""):
        contact_parts.append(data["LOCATION"])
    if contact_parts:
        lines.append(r"    " + r" \hspace{0.75em}\textbar\hspace{0.75em} ".join(contact_parts))
    return "\n".join(lines)


def build_social_links() -> list[tuple[str, str]]:
    platforms = request.form.getlist("social_platform")
    texts = request.form.getlist("social_text")
    urls = request.form.getlist("social_url")
    links = []

    for platform, text, url in zip(platforms, texts, urls):
        platform = platform.strip()
        text = text.strip()
        url = url.strip()
        if text or url:
            links.append((text or platform or "Website", url))

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
            title = f"\\href{{\\detokenize{{{safe_url(url)}}}}}{{{title}}}"
        rows.append(f"    \\resumeSubItem{{{title}}}\n      {{{latex_escape(desc)}}}")
    return "\n\n".join(rows)


def build_certifications() -> str:
    rows = []
    for name, issuer, date, url in zip(getlist("cert_name"), getlist("cert_issuer"), getlist("cert_date"), getlist("cert_url")):
        if not any([name, issuer, date, url]):
            continue
        title = latex_escape(name)
        if url:
            title = f"\\href{{\\detokenize{{{safe_url(url)}}}}}{{{title}}}"
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
            safe_title = f"\\href{{\\detokenize{{{safe_url(url)}}}}}{{{safe_title}}}"
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


def render_latex(data: dict[str, str], template_name: str) -> str:
    template_name = template_name if template_name in ALLOWED_TEMPLATES else "classic"
    template_path = TEMPLATES_DIR / f"cv_template_{template_name}.tex"
    if not template_path.exists():
        template_path = TEMPLATES_DIR / "cv_template_classic.tex"
    template = template_path.read_text(encoding="utf-8")
    for key, value in data.items():
        template = template.replace("{{" + key + "}}", value)
    return template
