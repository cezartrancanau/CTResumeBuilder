import json
import uuid

from flask import render_template, request, send_file, url_for

from core.config import (
    ALLOWED_DOWNLOADS,
    ALLOWED_TEMPLATES,
    DEFAULT_SECTION_ORDER,
    GENERATED_DIR,
    SECTION_LABELS,
)
from core.helpers import clean_filename, latex_escape, safe_url
from core.latex import (
    build_awards,
    build_certifications,
    build_education,
    build_experience,
    build_header,
    build_pair_section,
    build_projects,
    build_publications,
    build_social_links,
    render_latex,
    save_profile_photo,
    section_block,
)
from core.pdf import build_fallback_pdf, compile_pdf


def collect_resume_json() -> dict:
    data: dict[str, object] = {"version": "v2"}
    for key in request.form.keys():
        values = request.form.getlist(key)
        data[key] = values if len(values) > 1 else values[0]
    return data


def register_routes(app):
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
        download_name = filename
        if filename == "cv.pdf":
            base_name = clean_filename(file_id.rsplit("_", 1)[0])
            download_name = f"{base_name}_Resume.pdf"
        elif filename == "cv.tex":
            base_name = clean_filename(file_id.rsplit("_", 1)[0])
            download_name = f"{base_name}_Resume.tex"
        return send_file(path, as_attachment=True, download_name=download_name)
