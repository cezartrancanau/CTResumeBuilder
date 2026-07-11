import html
import re
import shutil

from flask import request

from core.config import GENERATED_DIR


def cleanup_generated(max_folders: int = 40) -> None:
    """Keep the generated folder small by deleting old build folders."""
    if not GENERATED_DIR.exists():
        return
    folders = [p for p in GENERATED_DIR.iterdir() if p.is_dir()]
    folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for folder in folders[max_folders:]:
        shutil.rmtree(folder, ignore_errors=True)


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
