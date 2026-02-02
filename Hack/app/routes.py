from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import tempfile
import os

from analyze import extract_text_auto, analyze_resume
from .db import insert_analysis, list_analyses_by_session


bp = Blueprint("main", __name__)


ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "docx"}


def allowed_file(filename: str) -> bool:
	return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/", methods=["GET"]) 
def index():
	sid = session.get("sid")
	rows = []
	if sid:
		try:
			rows = list_analyses_by_session(current_app.config["DATABASE"], sid, limit=4)
		except Exception:
			rows = []
	return render_template("index.html", history_rows=rows)


@bp.route("/upload", methods=["POST"]) 
def upload():
	if "resume" not in request.files:
		flash("No file part")
		return redirect(url_for("main.index"))

	file = request.files["resume"]
	if file.filename == "":
		flash("No selected file")
		return redirect(url_for("main.index"))

	if not allowed_file(file.filename):
		flash("Only PDF/JPG/PNG/DOCX files are supported")
		return redirect(url_for("main.index"))

	filename = secure_filename(file.filename)
	with tempfile.TemporaryDirectory() as tmpdir:
		tmp_path = Path(tmpdir) / filename
		file.save(tmp_path)
		text = extract_text_auto(str(tmp_path))

	score, details, suggestions = analyze_resume(text)

	# Persist analysis with anonymous session id
	sid = session.get("sid")
	if not sid:
		import secrets
		sid = secrets.token_hex(16)
		session["sid"] = sid

	try:
		insert_analysis(
			current_app.config["DATABASE"],
			{
				"session_id": sid,
				"filename": filename,
				"word_count": int(details.get("word_count", 0)),
				"score": int(score),
				"score_keywords_40": int(details.get("score_keywords_40", 0)),
				"score_structure_20": int(details.get("score_structure_20", 0)),
				"score_action_verbs_20": int(details.get("score_action_verbs_20", 0)),
				"score_word_count_20": int(details.get("score_word_count_20", 0)),
				"suggestion_1": suggestions[0] if len(suggestions) > 0 else None,
				"suggestion_2": suggestions[1] if len(suggestions) > 1 else None,
				"suggestion_3": suggestions[2] if len(suggestions) > 2 else None,
			},
		)
	except Exception:
		pass

	return render_template("result.html", score=score, details=details, suggestions=suggestions)


@bp.route("/history", methods=["GET"])
def history():
	sid = session.get("sid")
	rows = []
	if sid:
		try:
			rows = list_analyses_by_session(current_app.config["DATABASE"], sid, limit=20)
		except Exception:
			rows = []
	return render_template("history.html", rows=rows)


