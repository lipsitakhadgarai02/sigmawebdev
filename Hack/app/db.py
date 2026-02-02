import sqlite3
from typing import Any, Dict, List, Optional, Tuple


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    score INTEGER NOT NULL,
    score_keywords_40 INTEGER NOT NULL,
    score_structure_20 INTEGER NOT NULL,
    score_action_verbs_20 INTEGER NOT NULL,
    score_word_count_20 INTEGER NOT NULL,
    suggestion_1 TEXT,
    suggestion_2 TEXT,
    suggestion_3 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_analyses_session ON analyses(session_id);
"""


def initialize_database(db_path: str) -> None:
	with sqlite3.connect(db_path) as conn:
		conn.executescript(SCHEMA_SQL)
		conn.commit()


def insert_analysis(db_path: str, row: Dict[str, Any]) -> int:
	with sqlite3.connect(db_path) as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			INSERT INTO analyses (
				session_id, filename, word_count, score,
				score_keywords_40, score_structure_20, score_action_verbs_20, score_word_count_20,
				suggestion_1, suggestion_2, suggestion_3
			) VALUES (?,?,?,?,?,?,?,?,?,?,?)
			""",
			(
				row.get("session_id"), row.get("filename"), row.get("word_count"), row.get("score"),
				row.get("score_keywords_40"), row.get("score_structure_20"), row.get("score_action_verbs_20"), row.get("score_word_count_20"),
				row.get("suggestion_1"), row.get("suggestion_2"), row.get("suggestion_3"),
			),
		)
		conn.commit()
		return int(cur.lastrowid)


def list_analyses_by_session(db_path: str, session_id: str, limit: int = 20) -> List[Tuple[Any, ...]]:
	with sqlite3.connect(db_path) as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT id, filename, score, word_count, created_at
			FROM analyses
			WHERE session_id = ?
			ORDER BY created_at DESC
			LIMIT ?
			""",
			(session_id, limit),
		)
		return cur.fetchall()


