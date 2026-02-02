from typing import List, Tuple, Dict
from pathlib import Path
import re



def extract_text_from_pdf(pdf_path: str) -> str:
	"""Extract text from PDF using robust fallbacks, with last-resort OCR per page.

	Order: PyMuPDF (fitz) → pdfplumber → pdfminer → OCR pages with Tesseract
	"""
	# Try PyMuPDF first with multiple strategies
	try:
		import fitz  # PyMuPDF
		doc = fitz.open(pdf_path)
		texts: List[str] = []
		for page in doc:
			# Prefer layout-preserving text
			t = page.get_text("text") or page.get_text() or ""
			if not t:
				# Fallback: concatenate blocks
				blocks = page.get_text("blocks") or []
				block_text = "\n".join([b[4] for b in blocks if len(b) >= 5 and isinstance(b[4], str)])
				t = block_text
			if t:
				texts.append(t)
		text_joined = "\n".join(texts)
		if len(text_joined.split()) >= 50:
			return text_joined
	except Exception:
		pass

	# Fallback: pdfplumber
	try:
		import pdfplumber
		texts2: List[str] = []
		with pdfplumber.open(pdf_path) as pdf:
			for page in pdf.pages:
				pt = page.extract_text() or ""
				if pt:
					texts2.append(pt)
		text_joined2 = "\n".join(texts2)
		if len(text_joined2.split()) >= 20:
			return text_joined2
	except Exception:
		pass

	# Fallback: pdfminer
	try:
		from pdfminer.high_level import extract_text as miner_extract
		t3 = miner_extract(pdf_path) or ""
		if len((t3 or "").split()) >= 20:
			return t3
	except Exception:
		pass

	# Last resort: OCR each page (guarded and limited)
	try:
		import fitz
		from PIL import Image
		import pytesseract
		# Ensure Tesseract is available; if not, skip OCR quickly
		try:
			_ = pytesseract.get_tesseract_version()
		except Exception:
			return ""
		doc = fitz.open(pdf_path)
		ocr_texts: List[str] = []
		max_pages = min(3, len(doc))
		for i in range(max_pages):
			page = doc[i]
			# Moderate scale to reduce processing time
			pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
			img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
			ocr_texts.append(pytesseract.image_to_string(img) or "")
			# Early exit if we already have enough words
			if len(" ".join(ocr_texts).split()) >= 150:
				break
		return "\n".join(ocr_texts)
	except Exception:
		return ""


def extract_text_from_image(image_path: str) -> str:
	"""Extract text from a JPG/PNG using Tesseract OCR.

	Requires Tesseract binary installed (see README).
	"""
	try:
		from PIL import Image
		import pytesseract
		image = Image.open(image_path)
		text = pytesseract.image_to_string(image)
		return text or ""
	except Exception:
		return ""


def extract_text_from_docx(docx_path: str) -> str:
	"""Extract text from DOCX using docx2txt."""
	try:
		import docx2txt
		return docx2txt.process(docx_path) or ""
	except Exception:
		return ""


def extract_text_auto(path: str) -> str:
	"""Dispatch PDF, image, or DOCX to the appropriate extractor."""
	file_path = Path(path)
	suffix = file_path.suffix.lower()
	if suffix == ".pdf":
		return extract_text_from_pdf(path)
	if suffix in {".jpg", ".jpeg", ".png"}:
		return extract_text_from_image(path)
	if suffix == ".docx":
		return extract_text_from_docx(path)
	return ""


def _clean_extracted_text(raw_text: str) -> str:
	"""Normalize whitespace and drop likely repeated headers/footers to improve counts.

	Heuristics: remove lines that repeat 3+ times and are short (< 60 chars).
	"""
	if not raw_text:
		return ""
	# Normalize newlines and spaces
	text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
	lines = [ln.strip() for ln in text.split("\n")]
	# Frequency of lines
	from collections import Counter
	counts = Counter(ln for ln in lines if ln)
	filtered: list[str] = []
	for ln in lines:
		if not ln:
			continue
		if counts[ln] >= 6 and len(ln) <= 80:
			# Likely header/footer repeated on many pages
			continue
		filtered.append(ln)
	# Collapse multiple spaces
	cleaned = "\n".join(filtered)
	cleaned = re.sub(r"[\t\u00A0]+", " ", cleaned)
	cleaned = re.sub(r"\s+", " ", cleaned).strip()
	return cleaned


def _count_words_robust(text: str) -> int:
	"""Count words using a regex that handles Latin letters and hyphenated words.

	Counts tokens with at least one letter. Includes words like "state-of-the-art" as one token.
	"""
	if not text:
		return 0
	# Allow tokens that start with a letter or digit, include hyphens/apostrophes
	pattern = r"[A-Za-z0-9À-ÖØ-öø-ÿ]+(?:[-'][A-Za-z0-9À-ÖØ-öø-ÿ]+)*"
	return len(re.findall(pattern, text))


def analyze_resume(text: str) -> Tuple[int, Dict[str, int], List[str]]:
	"""Heuristic analysis per MVP weights with ATS-style breakdown and detailed tips."""
	cleaned = _clean_extracted_text(text or "")
	normalized = cleaned.lower()
	word_count = _count_words_robust(cleaned)

	# Sections/structure signals
	sections_present = {
		"education": any(k in normalized for k in ["education", "bachelor", "master", "university", "degree"]),
		"experience": any(k in normalized for k in ["experience", "work", "internship", "employment"]),
		"skills": "skills" in normalized,
		"projects": "projects" in normalized or "project" in normalized,
		"bullets": any(ch in normalized for ch in ["•", "- ", " – ", "— "]),
	}

	# Keywords and action verbs (simple lists)
	keywords = [
		"python", "java", "javascript", "typescript", "sql", "react", "node", "aws", "azure",
		"gcp", "docker", "kubernetes", "graphql", "rest", "data", "machine learning", "nlp", "git",
		"pandas", "numpy", "django", "flask"
	]
	action_verbs = [
		"led", "implemented", "built", "created", "designed", "developed", "optimized", "improved",
		"launched", "delivered", "automated", "refactored", "migrated", "collaborated", "mentored",
		"analyzed", "deployed", "configured", "debugged", "resolved"
	]

	keyword_hits = sum(1 for k in keywords if k in normalized)
	action_hits = sum(1 for v in action_verbs if f" {v} " in f" {normalized} ")

	# Scoring per spec
	# 40% skills keywords, 20% structure, 20% action verbs, 20% word count (ideal 350–600)
	max_keywords = max(10, len(keywords))
	keywords_score = min(1.0, keyword_hits / 10.0) * 40

	structure_components = ["education", "experience", "skills", "projects"]
	structure_hits = sum(1 for k, v in sections_present.items() if k in structure_components and v)
	structure_score = (structure_hits / 4.0) * 20

	# Count up to 10 distinct verbs → 20 pts
	action_score = min(action_hits, 10) / 10.0 * 20

	if 350 <= word_count <= 600:
		word_count_score = 20
	elif 250 <= word_count <= 800:
		word_count_score = 10
	else:
		word_count_score = 0

	total = int(round(keywords_score + structure_score + action_score + word_count_score))
	
	# Details for display
	details: Dict[str, int] = {
		"keyword_hits": keyword_hits,
		"action_verbs": action_hits,
		"word_count": word_count,
		"sections_present": structure_hits,
		"score_keywords_40": int(round(keywords_score)),
		"score_structure_20": int(round(structure_score)),
		"score_action_verbs_20": int(round(action_score)),
		"score_word_count_20": int(round(word_count_score)),
	}

	# Suggestions (prioritized) and keep top 3
	suggestions: List[str] = []
	missing_keywords = [k for k in keywords if k in normalized[:0] and False]  # placeholder to keep consistent type
	# Suggest keywords if low
	if keyword_hits < 6:
		suggestions.append("Skills and keywords: Add more role-specific terms (e.g., Python, SQL, React). Recruiters and ATS look for these exact keywords.")
	# Suggest structure additions
	for sec, present in [
		("Education", sections_present["education"]),
		("Experience", sections_present["experience"]),
		("Skills", sections_present["skills"]),
		("Projects", sections_present["projects"]),
	]:
		if not present:
			suggestions.append(f"Structure: Add a {sec} section with a clear heading so ATS can identify it.")
	# Action verbs
	if action_hits < 5:
		suggestions.append("Impact language: Start bullets with strong action verbs (Led, Implemented, Built) and quantify results (e.g., 20% faster).")
	# Word count guidance
	if not (350 <= word_count <= 600):
		suggestions.append("Length: Aim for ~350–600 words (roughly 1 page early-career). Keep bullets concise and remove fluff.")
	# Bullets readability
	if not sections_present["bullets"]:
		suggestions.append("Readability: Use bullet points instead of paragraphs so both humans and ATS can parse achievements.")

	return max(0, min(100, total)), details, suggestions[:3]


