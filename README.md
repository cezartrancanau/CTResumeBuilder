# CTResumeBuilder

Create professional, ATS-friendly resumes through an intuitive web interface.

CTResumeBuilder enables users to generate polished LaTeX resumes without manually editing templates, producing high-quality PDF output in just a few steps.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20App-black)
![LaTeX](https://img.shields.io/badge/LaTeX-PDF-green)

---

## Overview

CTResumeBuilder is a Flask-based web application that simplifies the creation of professional resumes. Users complete an interactive form while the application automatically generates both the LaTeX source and a professionally formatted PDF.

The application combines the flexibility of LaTeX with the simplicity of a graphical interface, allowing users to create high-quality resumes without prior LaTeX knowledge.

---

## Prerequisites

Before running CTDesk, install:

- Python 3.10+
- pip
- MiKTeX (required for PDF generation)

---

## What's New in v2

- Improved dark mode visibility and contrast
- Added resume statistics summary before export
- Added character counters for long text fields
- Improved generated PDF/TEX download filenames using the candidate name
- Added reset form option
- Added duplicate buttons for repeated resume entries
- Improved form spacing, buttons, focus states and overall UI polish

---

## What's New in v1

- Multiple resume templates: Classic, Modern and Minimal
- Optional profile photo upload
- Professional Summary section
- Improved Work Experience section with company, position, location, start date, end date and current job checkbox
- Languages section
- Certifications section
- Interests / Hobbies section
- Extended social links: GitHub, LinkedIn, Portfolio, Website, X, Stack Overflow, LeetCode, Codeforces and Kaggle
- Drag-and-drop section ordering
- Improved dark mode
- Save resume as JSON draft
- Import existing `resume.json`
- One-click example resume loader
- Better form validation for required fields, email and URLs
- Success page with PDF, TEX and JSON downloads
- Automatic cleanup for older generated files
- Cleaner generated filenames
- Improved fallback PDF generation when LaTeX is unavailable

---

## Key Highlights

- Built with Python and Flask
- Automatically generates professional LaTeX resumes
- Produces ATS-friendly PDF output
- Dynamic resume sections with unlimited entries
- Duplicate buttons for repeated entries
- Resume statistics summary
- Character counters for text areas
- Reset form option
- Resume import/export support
- Lightweight and fully customizable

---

## Features

- Professional PDF generation powered by LaTeX
- Automatic fallback PDF generation when a LaTeX distribution is unavailable
- Responsive and intuitive web interface
- Dynamic resume sections with unlimited entries
- Duplicate buttons for repeated entries
- Resume statistics summary
- Character counters for text areas
- Reset form option
- Drag-and-drop section ordering
- Improved dark mode
- Save and load resume drafts using JSON
- Support for:
  - Professional Summary
  - Work Experience
  - Education
  - Skills
  - Projects
  - Languages
  - Certifications
  - Awards
  - Publications
  - Interests / Hobbies
- Extended profile and social link integration
- Automatic generation of:
  - `cv.tex`
  - `cv.pdf`
  - `resume.json`
- Easily customizable LaTeX templates

---

## Tech Stack

| Category | Technologies |
| :--- | :--- |
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| PDF Generation | LaTeX, ReportLab fallback |
| Template Engine | Jinja2 |
| Data Export | JSON |

---

## Installation

Clone the repository:

```bash
git clone https://github.com/cezartrancanau/CTResumeBuilder.git
cd CTResumeBuilder
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

On Windows, you can also double-click:

```text
run_app.bat
```

Open your browser:

```text
http://127.0.0.1:5050
```

---

## Usage

1. Launch the application.
2. Choose a resume template.
3. Complete the resume form.
4. Add or remove resume entries dynamically.
5. Reorder sections with drag and drop.
6. Use duplicate buttons, character counters and resume statistics to polish the CV.
7. Optional: save or import a JSON resume draft.
8. Generate your resume.
9. Download:
   - `cv.pdf`
   - `cv.tex`
   - `resume.json`

---

## Default Templates

- **Classic** - traditional resume layout
- **Modern** - slightly stronger section styling
- **Minimal** - simple and clean layout

---

## Contributing

Contributions, feature requests and bug reports are welcome.

If you have an idea for an improvement, feel free to open an issue or submit a pull request.
