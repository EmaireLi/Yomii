from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DEFAULT_INPUT_ZIP = BASE_DIR / "data" / "shougakukan_2.zip"
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

POS_BLACKLIST = {"慣用句", "注意", "補説", "参考", "例", "用法", "語法", "派生"}


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text).replace("\u3000", " ").strip()


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", normalize_text(text))


def unique_join(parts: list[str], separator: str = "\n") -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for part in parts:
        value = normalize_text(part)
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return separator.join(ordered).strip()


def read_json_from_zip(zip_file: zipfile.ZipFile, name: str) -> object:
    try:
        data = zip_file.read(name)
    except KeyError as exc:
        raise FileNotFoundError(f"zip 缺少文件: {name}") from exc
    return json.loads(data.decode("utf-8-sig"))


def sort_term_bank_names(names: list[str]) -> list[str]:
    def bank_key(name: str) -> tuple[int, str]:
        match = re.search(r"term_bank_(\d+)\.json$", name)
        return (int(match.group(1)) if match else 10**9, name)

    return sorted([name for name in names if re.fullmatch(r"term_bank_\d+\.json", Path(name).name)], key=bank_key)


def extract_part_of_speech(definition_tags: str | None, term_tags: list[str], meaning_text: str) -> str:
    parts: list[str] = []

    if definition_tags:
        parts.extend(re.split(r"[\s,|/]+", normalize_text(definition_tags)))

    for tag in term_tags:
        parts.extend(re.split(r"[\s,|/]+", normalize_text(tag)))

    for line in meaning_text.splitlines()[:6]:
        for match in re.findall(r"[〔【]\s*([^〕】]+?)\s*[〕】]", line):
            candidate = normalize_text(match)
            if not candidate:
                continue
            if candidate in POS_BLACKLIST:
                continue
            if re.search(r"[A-Za-z0-9]", candidate):
                continue
            if len(candidate) > 6:
                continue
            parts.append(candidate)

    return unique_join(parts, separator=", ")


def extract_example(meaning_text: str) -> str:
    for line in meaning_text.splitlines():
        stripped = normalize_text(line)
        if not stripped.startswith("▲"):
            continue
        candidate = stripped.lstrip("▲").strip()
        if "/" in candidate:
            candidate = candidate.split("/", 1)[0].strip()
        candidate = re.sub(r"^(?:[〔【（(][^〕】）)]*[〕】）)])+\s*", "", candidate)
        candidate = candidate.strip(" 　.．。!！?？;；:：")
        if candidate:
            return candidate
    return ""


def split_glossary_text(expression: str, glossary_item: str) -> tuple[str, str]:
    text = normalize_text(glossary_item)
    if not text:
        return "", ""

    lines = [normalize_text(line) for line in text.splitlines() if normalize_text(line)]
    if not lines:
        return "", ""

    japanese_parts = lines[1:]
    chinese_parts: list[str] = []

    first_line = lines[0]
    expression_norm = normalize_text(expression)
    if first_line.startswith(expression_norm):
        remainder = first_line[len(expression_norm):].strip()
        if remainder:
            chinese_parts.append(remainder)
    else:
        japanese_parts.insert(0, first_line)

    for line in lines[1:]:
        candidate = line
        if "/" in candidate:
            candidate = candidate.rsplit("/", 1)[-1].strip()
        candidate = re.sub(r"^(?:[〔【（(][^〕】）)]*[〕】）)])+\s*", "", candidate)
        candidate = re.sub(r"^[▲◆△▽＊\-\s]+", "", candidate)
        if candidate and re.search(r"[\u4e00-\u9fff]\w*|[A-Za-z][^\n]*[\u4e00-\u9fff]", candidate):
            chinese_parts.append(candidate)

    japanese_text = unique_join(japanese_parts)
    chinese_text = unique_join(chinese_parts)
    return japanese_text, chinese_text


def build_row_from_entry(entry: list[object]) -> dict[str, str]:
    expression = compact_text(str(entry[0]))
    reading = compact_text(str(entry[1])) if len(entry) > 1 else ""
    definition_tags = str(entry[2]) if len(entry) > 2 and entry[2] not in (None, "") else ""
    term_tags = [str(item) for item in entry[7]] if len(entry) > 7 and isinstance(entry[7], list) else []
    glossary = entry[5] if len(entry) > 5 and isinstance(entry[5], list) else []

    japanese_parts: list[str] = []
    chinese_parts: list[str] = []
    example = ""

    for glossary_item in glossary:
        japanese_text, chinese_text = split_glossary_text(expression, str(glossary_item))
        if japanese_text:
            japanese_parts.append(japanese_text)
            if not example:
                example = extract_example(japanese_text)
        if chinese_text:
            chinese_parts.append(chinese_text)

    japanese_meaning = unique_join(japanese_parts, separator="\n\n")
    chinese_meaning = unique_join(chinese_parts, separator="\n\n")
    if not japanese_meaning:
        japanese_meaning = expression

    part_of_speech = extract_part_of_speech(definition_tags, term_tags, japanese_meaning)

    return {
        "word": expression,
        "kana": reading or expression,
        "japanese_meaning": japanese_meaning,
        "chinese_meaning": chinese_meaning,
        "example": example,
        "part_of_speech": part_of_speech,
        "audio_url": "",
    }


def iter_term_records(zip_path: Path) -> tuple[dict[str, object], list[dict[str, str]]]:
    if not zip_path.exists():
        raise FileNotFoundError(f"找不到词典压缩包: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as archive:
        index = read_json_from_zip(archive, "index.json")
        term_bank_names = sort_term_bank_names(archive.namelist())

        rows: list[dict[str, str]] = []
        for name in term_bank_names:
            entries = read_json_from_zip(archive, name)
            if not isinstance(entries, list):
                raise ValueError(f"{name} 不是合法的 term bank JSON 数组")
            for entry in entries:
                if not isinstance(entry, list) or len(entry) < 6:
                    continue
                rows.append(build_row_from_entry(entry))

    return index if isinstance(index, dict) else {}, rows


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
        raise RuntimeError(
            "words 表结构不匹配，请确认 data/dictionary.db 与 scripts/init_sqlite.sql 保持一致。"
        )


def clear_dictionary_tables(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("DELETE FROM quiz_questions")
        connection.execute("DELETE FROM word_tags")
        connection.execute("DELETE FROM words")
        connection.commit()


def count_words(database_path: Path) -> int:
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute("SELECT COUNT(*) FROM words")
        return int(cursor.fetchone()[0])


def write_rows_to_database(database_path: Path, rows: list[dict[str, str]], append: bool) -> None:
    ensure_database(database_path)
    ensure_words_schema(database_path)

    if not append:
        clear_dictionary_tables(database_path)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    batch_size = 1000

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        total_batches = max(1, (len(rows) + batch_size - 1) // batch_size)
        for batch_index in range(total_batches):
            start = batch_index * batch_size
            batch_rows = rows[start : start + batch_size]
            if not batch_rows:
                continue

            payload = [
                (
                    row["word"],
                    row["kana"],
                    row["japanese_meaning"],
                    row["chinese_meaning"],
                    row["example"],
                    row["part_of_speech"],
                    row["audio_url"],
                    timestamp,
                )
                for row in batch_rows
            ]

            connection.executemany(
                """
                INSERT INTO words (
                    word, kana, japanese_meaning, chinese_meaning,
                    example, part_of_speech, audio_url, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            connection.commit()
            print(
                f"[写入] {batch_index + 1}/{total_batches} 批，累计 {min(start + len(batch_rows), len(rows))}/{len(rows)} 条",
                flush=True,
            )


def import_dictionary(
    input_zip: Path,
    database_path: Path,
    *,
    append: bool = False,
    dry_run: bool = False,
) -> dict[str, object]:
    started_at = perf_counter()
    index, rows = iter_term_records(input_zip)

    if dry_run:
        for sample in rows[:3]:
            print(f"sample: {sample['word']} | {sample['japanese_meaning'][:120]}")

    before_count = count_words(database_path) if database_path.exists() else 0
    if not dry_run:
        write_rows_to_database(database_path, rows, append=append)

    after_count = count_words(database_path) if database_path.exists() else before_count
    elapsed_seconds = perf_counter() - started_at

    return {
        "title": index.get("title", ""),
        "revision": index.get("revision", ""),
        "format": index.get("format", None),
        "sequenced": index.get("sequenced", None),
        "source_zip": str(input_zip),
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

    parser = argparse.ArgumentParser(description="Import a Yomitan dictionary zip into SQLite words table")
    parser.add_argument("--input-zip", type=Path, default=DEFAULT_INPUT_ZIP, help="Yomitan dictionary zip")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--append", action="store_true", help="append rows instead of clearing existing data")
    parser.add_argument("--dry-run", action="store_true", help="parse input without writing to the database")
    args = parser.parse_args(argv)

    result = import_dictionary(
        args.input_zip,
        args.db_path,
        append=args.append,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())