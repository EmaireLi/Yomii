from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DEFAULT_INPUT_TXT = BASE_DIR / "data" / "eggrolls-JLPT10k-v3.txt"
DEFAULT_DB_PATH = BASE_DIR / "data" / "dictionary.db"
DEFAULT_INIT_SQL = SCRIPT_DIR / "init_sqlite.sql"

EXPECTED_WORD_COLUMNS = [
	"word",
	"kana",
	"japanese_meaning",
	"chinese_meaning",
	"example",
	"part_of_speech",
	"audio_url",
	"id",
	"created_at",
]

TARGET_TAGS = {"N4+N5", "N3-高频", "N3-中低频", "N2-高频", "N2-中低频", "N1-高频", "N1-中频", "N1-低频"}


def normalize_text(value: str) -> str:
	return unicodedata.normalize("NFKC", html.unescape(value)).replace("\u3000", " ").strip()


def compact_text(value: str) -> str:
	return re.sub(r"\s+", " ", normalize_text(value))


def strip_html_tags(value: str) -> str:
	return re.sub(r"<[^>]+>", "", value)


def clean_word(value: str) -> str:
	text = compact_text(value)
	text = strip_html_tags(text)
	text = re.sub(r"\[[^\]]*\]", "", text)
	return compact_text(text)


def first_nonempty(*values: str) -> str:
	for value in values:
		text = compact_text(value)
		if text:
			return text
	return ""


def unique_join(parts: list[str], separator: str = "\n") -> str:
	seen: set[str] = set()
	ordered: list[str] = []
	for part in parts:
		text = compact_text(part)
		if not text or text in seen:
			continue
		seen.add(text)
		ordered.append(text)
	return separator.join(ordered).strip()


def extract_sound_reference(*values: str) -> str:
	for value in values:
		text = compact_text(value)
		match = re.search(r"\[sound:([^\]]+)\]", text)
		if match:
			return match.group(1)
	return ""


def extract_category_tag(source_key: str) -> str:
	base_match = re.search(r"(N[1-5](?:\+N5)?)", source_key)
	if not base_match:
		return ""

	base_tag = base_match.group(1)
	if base_tag == "N4+N5":
		return base_tag

	suffix_match = re.search(r"(高频|中频|低频|中低频)", source_key)
	if not suffix_match:
		return base_tag

	candidate = f"{base_tag}-{suffix_match.group(1)}"
	return candidate if candidate in TARGET_TAGS else base_tag


def parse_tsv_line(line: str) -> list[str]:
	columns = line.rstrip("\n").split("\t")
	if len(columns) < 38:
		columns.extend([""] * (38 - len(columns)))
	return columns


def build_example(columns: list[str]) -> str:
	sentence_jp = strip_html_tags(compact_text(columns[11]))
	sentence_zh = compact_text(columns[13])
	extra_sentence_jp = strip_html_tags(compact_text(columns[16]))
	extra_sentence_zh = compact_text(columns[19])

	examples: list[str] = []
	first_example = unique_join([sentence_jp, sentence_zh], separator="\n")
	if first_example:
		examples.append(first_example)

	second_example = unique_join([extra_sentence_jp, extra_sentence_zh], separator="\n")
	if second_example and second_example != first_example:
		examples.append(second_example)

	return unique_join(examples, separator="\n\n")


def build_word_row(columns: list[str]) -> dict[str, str]:
	word = clean_word(columns[2])
	kana = first_nonempty(columns[5], word)
	japanese_meaning = first_nonempty(columns[8], columns[16], columns[17], columns[18], word)
	chinese_meaning = unique_join([columns[6], columns[7], columns[19], columns[20]])
	if not chinese_meaning:
		chinese_meaning = word

	return {
		"word": word,
		"kana": kana,
		"japanese_meaning": japanese_meaning,
		"chinese_meaning": chinese_meaning,
		"example": build_example(columns),
		"part_of_speech": first_nonempty(columns[4]),
		"audio_url": extract_sound_reference(columns[9], columns[15], columns[21]),
	}


def iter_rows_from_txt(txt_path: Path) -> tuple[list[dict[str, str]], list[str]]:
	if not txt_path.exists():
		raise FileNotFoundError(f"找不到词典文本: {txt_path}")

	rows: list[dict[str, str]] = []
	tags: list[str] = []

	with txt_path.open("r", encoding="utf-8-sig") as handle:
		for raw_line in handle:
			line = raw_line.rstrip("\n")
			if not line or line.startswith("#"):
				continue

			columns = parse_tsv_line(line)
			row = build_word_row(columns)
			if not row["word"]:
				continue

			rows.append(row)
			tags.append(extract_category_tag(columns[0]))

	return rows, tags


def get_table_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
	cursor = connection.execute(f"PRAGMA table_info({table_name})")
	return [str(row[1]) for row in cursor.fetchall()]


def ensure_database(database_path: Path) -> None:
	database_path.parent.mkdir(parents=True, exist_ok=True)
	if not database_path.exists():
		if not DEFAULT_INIT_SQL.exists():
			raise FileNotFoundError(f"找不到建库脚本: {DEFAULT_INIT_SQL}")
		with sqlite3.connect(database_path) as connection:
			connection.executescript(DEFAULT_INIT_SQL.read_text(encoding="utf-8"))


def ensure_words_schema(database_path: Path) -> None:
	with sqlite3.connect(database_path) as connection:
		try:
			current_columns = get_table_columns(connection, "words")
		except sqlite3.DatabaseError as exc:
			raise RuntimeError("数据库中找不到 words 表，请先执行 init_sqlite.sql 建库") from exc

	if current_columns != EXPECTED_WORD_COLUMNS:
		raise RuntimeError("words 表结构不匹配，请确认 data/dictionary.db 与 scripts/init_sqlite.sql 保持一致。")


def clear_dictionary_tables(database_path: Path) -> None:
	with sqlite3.connect(database_path) as connection:
		connection.execute("PRAGMA foreign_keys = ON")
		connection.execute("DELETE FROM quiz_questions")
		connection.execute("DELETE FROM word_tags")
		connection.execute("DELETE FROM words")
		connection.commit()


def get_next_word_id(database_path: Path) -> int:
	with sqlite3.connect(database_path) as connection:
		cursor = connection.execute("SELECT COALESCE(MAX(id), 0) FROM words")
		return int(cursor.fetchone()[0]) + 1


def count_words(database_path: Path) -> int:
	with sqlite3.connect(database_path) as connection:
		cursor = connection.execute("SELECT COUNT(*) FROM words")
		return int(cursor.fetchone()[0])


def insert_rows(database_path: Path, rows: list[dict[str, str]], tags: list[str], append: bool) -> None:
	ensure_database(database_path)
	ensure_words_schema(database_path)

	if not append:
		clear_dictionary_tables(database_path)

	timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
	start_id = get_next_word_id(database_path) if append else 1
	batch_size = 1000

	with sqlite3.connect(database_path) as connection:
		connection.execute("PRAGMA foreign_keys = ON")
		total_batches = max(1, (len(rows) + batch_size - 1) // batch_size)

		for batch_index in range(total_batches):
			start = batch_index * batch_size
			batch_rows = rows[start : start + batch_size]
			batch_tags = tags[start : start + batch_size]
			if not batch_rows:
				continue

			word_payload = [
				(
					row["word"],
					row["kana"],
					row["japanese_meaning"],
					row["chinese_meaning"],
					row["example"],
					row["part_of_speech"],
					row["audio_url"],
					start_id + start + offset,
					timestamp,
				)
				for offset, row in enumerate(batch_rows)
			]

			connection.executemany(
				"""
				INSERT INTO words (
					word, kana, japanese_meaning, chinese_meaning,
					example, part_of_speech, audio_url, id, created_at
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				word_payload,
			)

			tag_payload = [
				(start_id + start + offset, tag)
				for offset, tag in enumerate(batch_tags)
				if tag
			]
			if tag_payload:
				connection.executemany(
					"INSERT INTO word_tags (word_id, tag) VALUES (?, ?)",
					tag_payload,
				)

			connection.commit()
			print(
				f"[写入] {batch_index + 1}/{total_batches} 批，累计 {min(start + len(batch_rows), len(rows))}/{len(rows)} 条",
				flush=True,
			)


def import_dictionary(
	input_txt: Path,
	database_path: Path,
	*,
	append: bool = False,
	dry_run: bool = False,
) -> dict[str, object]:
	started_at = perf_counter()
	rows, tags = iter_rows_from_txt(input_txt)

	if dry_run:
		for sample, tag in list(zip(rows, tags))[:3]:
			print(f"sample: {sample['word']} | {sample['japanese_meaning'][:120]} | tag={tag}")

	before_count = count_words(database_path) if database_path.exists() else 0
	if not dry_run:
		insert_rows(database_path, rows, tags, append=append)

	after_count = count_words(database_path) if database_path.exists() else before_count
	elapsed_seconds = perf_counter() - started_at

	return {
		"source_txt": str(input_txt),
		"rows_parsed": len(rows),
		"before_words": before_count,
		"after_words": after_count,
		"written_rows": 0 if dry_run else len(rows),
		"elapsed_seconds": round(elapsed_seconds, 3),
		"dry_run": dry_run,
		"append": append,
	}


def main(argv: list[str] | None = None) -> int:
	try:
		sys.stdout.reconfigure(encoding="utf-8")
	except Exception:
		pass
	try:
		sys.stderr.reconfigure(encoding="utf-8")
	except Exception:
		pass

	parser = argparse.ArgumentParser(description="Import an Anki TXT export into SQLite words table")
	parser.add_argument("--input-txt", type=Path, default=DEFAULT_INPUT_TXT, help="Anki export txt path")
	parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="SQLite database path")
	parser.add_argument("--append", action="store_true", help="append rows instead of clearing existing data")
	parser.add_argument("--dry-run", action="store_true", help="parse input without writing to the database")
	args = parser.parse_args(argv)

	result = import_dictionary(
		args.input_txt,
		args.db_path,
		append=args.append,
		dry_run=args.dry_run,
	)
	print(json.dumps(result, ensure_ascii=False, indent=2))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
