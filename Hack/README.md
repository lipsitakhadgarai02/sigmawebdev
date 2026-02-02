# Resume Analyzer (MVP)

Simple Flask app: upload a resume PDF, DOCX, or image (JPG/PNG), extract text, score 0–100, show basic suggestions.

## Setup

1) Create and activate a virtual environment

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

2) Install dependencies

```powershell
pip install -r requirements.txt

If you plan to upload images (JPG/PNG), install Tesseract OCR:
- Windows: download installer from `https://github.com/UB-Mannheim/tesseract/wiki` and install.
- After install, if needed, set the path in your environment or in code. By default `pytesseract` will try to find it on PATH.
```

3) Run the app

```powershell
python run.py
```

Then open `http://localhost:5000` in your browser.

## Notes
- Max upload size is 5 MB.
- Supported types: PDF, DOCX, JPG, PNG.
- PDF text extraction uses `pdfplumber` (fallback `pdfminer.six`).
- DOCX extraction uses `docx2txt`.
- Image text extraction uses `pytesseract` + Tesseract (external binary).
- Scoring is heuristic and for demo purposes.


