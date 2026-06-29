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

## Key Highlights

- Built with Python and Flask
- Automatically generates professional LaTeX resumes
- Produces ATS-friendly PDF output
- Dynamic resume sections with unlimited entries
- Lightweight and fully customizable

---

## Features

- Professional PDF generation powered by LaTeX
- Responsive and intuitive web interface
- Dynamic resume sections with unlimited entries
- Support for:
  - Education
  - Skills
  - Projects
  - Awards
  - Publications
- GitHub and LinkedIn profile integration
- Automatic generation of `cv.tex`
- Easily customizable LaTeX template
- Automatic fallback PDF generation when a LaTeX distribution is unavailable

---

## Tech Stack

| Category | Technologies |
| :--- | :--- |
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| PDF Generation | LaTeX |
| Template Engine | Jinja2 |

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

or simply execute:

```bash
RUN_APP.bat
```

Open your browser:

```text
http://127.0.0.1:5050
```

---

## Usage

1. Launch the application.
2. Complete the resume form.
3. Add or remove resume entries dynamically.
4. Generate your resume.
5. Download:
   - `cv.tex`
   - `cv.pdf`

---

## Roadmap

- Multiple resume templates
- Live PDF preview
- Drag-and-drop section ordering
- Theme customization
- Dark mode
- Resume import and export
- Multi-language support

---

## Contributing

Contributions, feature requests and bug reports are welcome.

If you have an idea for an improvement, feel free to open an issue or submit a pull request.

---

## Preview

   * **Example of generated CV**

<p align="center">
<img src="https://i.imgur.com/CkjSB5P.png"></img>
</p>