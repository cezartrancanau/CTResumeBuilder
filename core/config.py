from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
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
