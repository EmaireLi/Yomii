from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from functools import lru_cache
from datetime import datetime
from time import perf_counter
from dataclasses import dataclass
from pathlib import Path
import unicodedata
import xml.etree.ElementTree as ET

import zlib


CATALOG_ENTRY_SIZE = 164
PAGE_SIZE = 2048
EBZIP_HEADER_SIZE = 22

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DEFAULT_DICT_ROOT = BASE_DIR / "data" / "EPWING_shougakukan_2"
DEFAULT_DB_PATH = BASE_DIR / "data" / "dictionary.db"


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _parse_gaiji_replacement(attributes: dict[str, str]) -> str:
    unicode_value = attributes.get("unicode", "")
    if unicode_value.startswith("#x"):
        try:
            return chr(int(unicode_value[2:], 16))
        except ValueError:
            pass

    alt_value = attributes.get("alt", "")
    if alt_value:
        return alt_value

    return attributes.get("name", "")


def _looks_like_preface(text: str) -> bool:
    markers = ("Copyright", "本辞書", "製作", "Printed in", "EBPocket", "EBWin")
    return any(marker in text for marker in markers)


def _looks_like_heading_line(line: str) -> bool:
    candidate = line.strip()
    if not candidate:
        return False
    if len(candidate) > 48:
        return False
    if candidate.startswith(("▲", "（", "〔", "→", "＊", "#")):
        return False
    if re.search(r"[。．.!?！？:：;；]", candidate):
        return False
    if not re.search(r"[\u3040-\u30ff\u3400-\u9fffA-Za-z0-9]", candidate):
        return False
    return True


def _normalize_headword_line(line: str) -> str:
    candidate = line.strip()
    candidate = candidate.strip(" `\"'!?,。、．・[](){}<>|")
    candidate = re.sub(r"^[0-9０-９]+", "", candidate)
    kana_match = re.match(r"[\u3040-\u30ffー・]+", candidate)
    if kana_match:
        candidate = kana_match.group(0).strip("ー・")
    return candidate.strip()


def _derive_section_title(line: str) -> str:
    candidate = _normalize_headword_line(line)
    if not candidate:
        return ""

    kana_match = re.match(r"[\u3040-\u30ffー・]+", candidate)
    if not kana_match:
        return ""

    title = kana_match.group(0).strip("ー・")
    return title[:200]


def _looks_like_noisy_headword(headword: str) -> bool:
    return not re.search(r"[\u3040-\u30ff]", headword)


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate
    return ""


def normalize_lookup_text(text: str) -> str:
    candidate = unicodedata.normalize("NFKC", text)
    candidate = candidate.replace("\u3000", " ")
    candidate = candidate.strip()
    candidate = re.sub(r"\s+", "", candidate)
    candidate = candidate.strip(" `\"'!?,。、．・[](){}<>|/\\")
    candidate = re.sub(r"^[0-9０-９]+", "", candidate)
    return candidate.casefold()


def _split_definition_text(text: str) -> tuple[str, str]:
    japanese_parts: list[str] = []
    chinese_parts: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        separator = "／" if "／" in stripped else "/" if "/" in stripped else ""
        if separator:
            left, right = stripped.split(separator, 1)
            left = left.strip()
            right = right.strip()
            if left:
                japanese_parts.append(left)
            if right:
                chinese_parts.append(right)
            continue

        if re.search(r"[\u3040-\u30ff]", stripped):
            japanese_parts.append(stripped)
        elif re.search(r"[\u4e00-\u9fff]", stripped):
            chinese_parts.append(stripped)
        else:
            japanese_parts.append(stripped)

    return "\n".join(japanese_parts).strip(), "\n".join(chinese_parts).strip()


def split_entry_records(decoded: str) -> list[dict[str, str]]:
    if _looks_like_preface(decoded):
        return []

    lines = [line.rstrip() for line in decoded.splitlines()]
    records: list[dict[str, str]] = []
    current_lines: list[str] = []
    last_section_title = ""

    def flush_current() -> None:
        nonlocal last_section_title
        if not current_lines:
            return
        text = "\n".join(current_lines).strip()
        if text:
            japanese_text, chinese_text = _split_definition_text(text)
            raw_headword = _first_nonempty_line(text)
            headword = extract_headword(text)
            section_title = _derive_section_title(current_lines[0])
            if _looks_like_noisy_headword(headword) and last_section_title:
                headword = last_section_title
            elif section_title:
                last_section_title = section_title
            records.append(
                {
                    "raw_headword": raw_headword,
                    "headword": headword,
                    "text": text,
                    "japanese_text": japanese_text,
                    "chinese_text": chinese_text,
                }
            )
        elif current_lines:
            section_title = _derive_section_title(current_lines[0])
            if section_title:
                last_section_title = section_title
        current_lines.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_lines and current_lines[-1] != "":
                current_lines.append("")
            continue

        if _looks_like_heading_line(stripped) and current_lines:
            flush_current()

        current_lines.append(stripped)

    flush_current()
    return records


@lru_cache(maxsize=1)
def load_gaiji_map() -> dict[str, str]:
    gaiji_path = _script_dir() / "gaijimap.xml"
    if not gaiji_path.exists():
        return {}

    try:
        root = ET.fromstring(gaiji_path.read_bytes().decode("shift_jis", errors="replace"))
    except (ET.ParseError, UnicodeError, LookupError):
        return {}

    mapping: dict[str, str] = {}
    for item in root.findall(".//gaijiMap"):
        ebcode = item.attrib.get("ebcode", "").upper()
        if not ebcode:
            continue
        replacement = _parse_gaiji_replacement(item.attrib)
        if replacement:
            mapping[ebcode] = replacement
    return mapping


def _format_percent(current: int, total: int) -> str:
    if total <= 0:
        return "0.0"
    return f"{(current * 100.0) / total:.1f}"


def report_progress(stage: str, current: int, total: int, detail: str = "") -> None:
    stage_labels = {
        "scan": "扫描",
        "decompress": "解压",
        "entries": "条目",
        "done": "完成",
    }
    stage_label = stage_labels.get(stage, stage)
    message = f"[{stage}] {_format_percent(current, total)}% ({current}/{total})"
    if detail:
        message += f" {detail}"
    message = message.replace(f"[{stage}]", f"[{stage_label}]")
    print(message, file=sys.stderr, flush=True)


def emit_progress(message: str) -> None:
    print(f"[进度] {message}", flush=True)


@dataclass(frozen=True)
class CatalogInfo:
    root: Path
    title: str
    directory: str
    text_file: Path


class EbZipReader:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = path.read_bytes()
        if self.data[:5] != b"EBZip":
            raise ValueError(f"{path} is not an EBZip file")

        self.zip_level = self.data[5] & 0x0F
        self.slice_size = PAGE_SIZE << self.zip_level
        self.file_size = int.from_bytes(self.data[9:14], "big")
        self.index_width = 2
        if self.file_size < (1 << 16):
            self.index_width = 2
        elif self.file_size < (1 << 24):
            self.index_width = 3
        elif self.file_size < (1 << 32):
            self.index_width = 4
        else:
            self.index_width = 5

        self.slice_count = (self.file_size + self.slice_size - 1) // self.slice_size
        table_size = (self.slice_count + 1) * self.index_width
        table = self.data[EBZIP_HEADER_SIZE : EBZIP_HEADER_SIZE + table_size]
        if len(table) < table_size:
            raise ValueError("EBZip index table is truncated")

        self.slice_locations = [
            int.from_bytes(
                table[i * self.index_width : (i + 1) * self.index_width], "big"
            )
            for i in range(self.slice_count + 1)
        ]
        self._slice_cache: dict[int, bytes] = {}

    def _read_slice(self, slice_index: int) -> bytes:
        cached = self._slice_cache.get(slice_index)
        if cached is not None:
            return cached

        start = self.slice_locations[slice_index]
        end = self.slice_locations[slice_index + 1]
        chunk = self.data[start:end]
        if len(chunk) == self.slice_size:
            out = chunk
        else:
            out = zlib.decompress(chunk)
            if len(out) != self.slice_size:
                raise ValueError(
                    f"Unexpected uncompressed slice length: {len(out)} != {self.slice_size}"
                )

        self._slice_cache[slice_index] = out
        return out

    def read(self, offset: int, length: int) -> bytes:
        if offset < 0 or length < 0:
            raise ValueError("offset and length must be non-negative")
        if offset >= self.file_size:
            return b""

        remaining = min(length, self.file_size - offset)
        pieces: list[bytes] = []
        current = offset
        while remaining > 0:
            slice_index = current // self.slice_size
            within = current % self.slice_size
            slice_data = self._read_slice(slice_index)
            chunk_length = min(remaining, self.slice_size - within)
            pieces.append(slice_data[within : within + chunk_length])
            current += chunk_length
            remaining -= chunk_length
        return b"".join(pieces)

    def read_all(self, progress_interval: int = 200, progress_stage: str = "decompress") -> bytes:
        chunks: list[bytes] = []
        slice_total = self.slice_count
        for slice_index, slice_start in enumerate(range(0, self.file_size, self.slice_size), 1):
            chunks.append(self.read(slice_start, self.slice_size))
            if progress_interval > 0 and (
                slice_index == 1
                or slice_index == slice_total
                or slice_index % progress_interval == 0
            ):
                report_progress(
                    progress_stage,
                    slice_index,
                    slice_total,
                    f"slice={slice_index} size={self.slice_size}",
                )
        return b"".join(chunks)


def decode_epwing_bytes(data: bytes) -> str:
    gaiji_map = load_gaiji_map()
    fragments: list[str] = []
    buffer = bytearray()

    def flush_buffer() -> None:
        if not buffer:
            return
        try:
            fragments.append(buffer.decode("euc_jp", errors="ignore"))
        except LookupError:
            fragments.append(buffer.decode(errors="ignore"))
        buffer.clear()

    index = 0

    while index < len(data):
        current = data[index]

        if current == 0x1F and index + 1 < len(data):
            code = data[index + 1]
            if code in {0x02, 0x03, 0x09, 0x41, 0x42, 0x43, 0x63}:
                flush_buffer()
                fragments.append("\n")
            elif code == 0x0A:
                flush_buffer()
                fragments.append("\n")
            index += 2
            continue

        if current in {0x0A, 0x0D}:
            flush_buffer()
            fragments.append("\n")
            index += 1
            continue

        if 0x20 <= current <= 0x7E:
            if (
                index + 1 < len(data)
                and 0x21 <= data[index] <= 0x7E
                and 0x21 <= data[index + 1] <= 0x7E
            ):
                buffer.extend((data[index] + 0x80, data[index + 1] + 0x80))
                index += 2
            else:
                buffer.append(current)
                index += 1
            continue

        if current >= 0x80:
            if index + 1 < len(data):
                next_byte = data[index + 1]
                if 0x21 <= next_byte <= 0x7E:
                    code = f"{current:02X}{next_byte:02X}"
                    replacement = gaiji_map.get(code)
                    flush_buffer()
                    if replacement:
                        fragments.append(replacement)
                    else:
                        fragments.append(f"⟦{code}⟧")
                    index += 2
                    continue
                if next_byte >= 0x80:
                    buffer.extend(data[index : index + 2])
                    index += 2
                    continue

            buffer.append(current)
            index += 1
            continue

        index += 1

    flush_buffer()

    return "".join(fragments)


def extract_headword(text: str) -> str:
    candidate = _first_nonempty_line(text)
    candidate = _normalize_headword_line(candidate)
    return candidate[:200]


def find_catalog_info(root: Path) -> CatalogInfo:
    catalog_path = root / "CATALOGS"
    catalog_path.read_bytes()

    candidates = sorted(root.glob("*/DATA/HONMON.ebz"))
    if not candidates:
        candidates = sorted(root.rglob("HONMON.ebz"))
    if not candidates:
        raise FileNotFoundError("Could not locate an EBZip text file")

    text_file = candidates[0]
    directory = text_file.parents[1].name

    raw_title = directory
    if not text_file.exists():
        raise FileNotFoundError("Could not locate an EBZip text file")

    return CatalogInfo(root=root, title=raw_title or directory, directory=directory, text_file=text_file)


def find_entry_boundaries(raw_text: bytes) -> list[int]:
    boundaries: list[int] = []
    pos = 0
    while True:
        pos = raw_text.find(b"\x1f\x02", pos)
        if pos < 0:
            break
        boundaries.append(pos)
        pos += 2
    return boundaries


def build_entries(raw_text: bytes, progress_interval: int = 1000) -> list[dict[str, object]]:
    return build_entries_limited(raw_text, progress_interval=progress_interval, max_entries=None)


def build_entries_limited(
    raw_text: bytes,
    progress_interval: int = 1000,
    max_entries: int | None = None,
) -> list[dict[str, object]]:
    boundaries = find_entry_boundaries(raw_text)
    if not boundaries:
        return []

    boundaries.append(len(raw_text))
    entries: list[dict[str, object]] = []

    article_total = len(boundaries) - 1
    for entry_index, start in enumerate(boundaries[:-1]):
        if max_entries is not None and entry_index >= max_entries:
            break
        next_start = boundaries[entry_index + 1]
        stop_pos = raw_text.find(b"\x1f\x03", start + 2, next_start)
        end = stop_pos if stop_pos != -1 else next_start

        segment = raw_text[start:end]
        decoded = decode_epwing_bytes(segment)

        split_records = split_entry_records(decoded)
        if not split_records:
            continue

        for record_index, record in enumerate(split_records):
            entries.append(
                {
                    "entry_id": len(entries),
                    "article_id": entry_index,
                    "record_id": record_index,
                    "raw_headword": record.get("raw_headword", ""),
                    "offset": start,
                    "size": end - start,
                    "headword": record["headword"],
                    "normalized_headword": normalize_lookup_text(record["headword"] or record.get("raw_headword", "")),
                    "text": record["text"],
                    "japanese_text": record.get("japanese_text", ""),
                    "chinese_text": record.get("chinese_text", ""),
                }
            )

        if progress_interval > 0 and (
            entry_index == 0
            or entry_index + 1 == article_total
            or (entry_index + 1) % progress_interval == 0
        ):
            report_progress(
                "entries",
                entry_index + 1,
                article_total,
                f"offset={start}",
            )

    return entries


def make_sqlite_row(
    catalog: CatalogInfo,
    reader: EbZipReader,
    total_entries: int,
    entry: dict[str, object],
) -> dict[str, object]:
    return {
        "entry_id": entry["entry_id"],
        "article_id": entry.get("article_id"),
        "record_id": entry.get("record_id"),
        "raw_headword": entry.get("raw_headword", ""),
        "headword": entry["headword"],
        "normalized_headword": entry.get("normalized_headword", normalize_lookup_text(str(entry["headword"]))),
        "text": entry["text"],
        "japanese_text": entry.get("japanese_text", ""),
        "chinese_text": entry.get("chinese_text", ""),
        "offset": entry["offset"],
        "size": entry["size"],
        "total_entries": total_entries,
    }


def _init_sqlite_database(output_path: Path, catalog: CatalogInfo, reader: EbZipReader) -> sqlite3.Connection:
    if output_path.exists():
        output_path.unlink()

    connection = sqlite3.connect(output_path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute("PRAGMA temp_store=MEMORY")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            entry_id INTEGER PRIMARY KEY,
            article_id INTEGER NOT NULL,
            record_id INTEGER NOT NULL,
            raw_headword TEXT NOT NULL,
            headword TEXT NOT NULL,
            normalized_headword TEXT NOT NULL,
            text TEXT NOT NULL,
            japanese_text TEXT NOT NULL,
            chinese_text TEXT NOT NULL,
            offset INTEGER NOT NULL,
            size INTEGER NOT NULL
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_entries_headword ON entries(normalized_headword, headword)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_entries_article ON entries(article_id, record_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_entries_offset ON entries(offset)")
    metadata = {
        "source_root": str(catalog.root),
        "catalog_title": catalog.title,
        "subbook_directory": catalog.directory,
        "text_file": str(catalog.text_file),
        "text_file_size": str(reader.file_size),
        "slice_size": str(reader.slice_size),
    }
    connection.executemany(
        "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
        metadata.items(),
    )
    return connection


def _write_sqlite_database(
    output_path: Path,
    catalog: CatalogInfo,
    reader: EbZipReader,
    entries: list[dict[str, object]],
    total_entries: int,
) -> None:
    connection = _init_sqlite_database(output_path, catalog, reader)
    try:
        with connection:
            connection.executemany(
                """
                INSERT INTO entries (
                    entry_id, article_id, record_id, raw_headword, headword,
                    normalized_headword, text, japanese_text, chinese_text, offset, size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        entry["entry_id"],
                        entry["article_id"],
                        entry["record_id"],
                        entry.get("raw_headword", ""),
                        entry["headword"],
                        entry.get("normalized_headword", normalize_lookup_text(str(entry["headword"]))),
                        entry["text"],
                        entry.get("japanese_text", ""),
                        entry.get("chinese_text", ""),
                        entry["offset"],
                        entry["size"],
                    )
                    for entry in entries
                ],
            )
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                ("entry_count", str(total_entries)),
            )
    finally:
        connection.close()


def query_sqlite_database(
    database_path: Path,
    query: str,
    match_type: str = "exact",
    limit: int = 20,
) -> list[dict[str, object]]:
    normalized_query = normalize_lookup_text(query)
    if not normalized_query:
        return []

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        if match_type == "prefix":
            pattern = f"{normalized_query}%"
            rows = connection.execute(
                """
                SELECT *
                FROM words
                WHERE word LIKE ?
                ORDER BY word, id
                LIMIT ?
                """,
                (pattern, limit),
            ).fetchall()
        elif match_type == "contains":
            pattern = f"%{normalized_query}%"
            rows = connection.execute(
                """
                SELECT *
                FROM words
                WHERE word LIKE ?
                ORDER BY word, id
                LIMIT ?
                """,
                (pattern, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT *
                FROM words
                WHERE word = ?
                ORDER BY word, id
                LIMIT ?
                """,
                (normalized_query, limit),
            ).fetchall()

        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_table_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    return [str(row[1]) for row in cursor.fetchall()]


def ensure_dictionary_schema(database_path: Path) -> None:
    expected_columns = [
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

    with sqlite3.connect(database_path) as connection:
        try:
            current_columns = get_table_columns(connection, "words")
        except sqlite3.DatabaseError:
            current_columns = []

    if current_columns != expected_columns:
        raise RuntimeError(
            "words 表结构不匹配：请确认 data/dictionary.db 的 words 表字段与脚本一致。"
        )


def clear_dictionary_tables(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        for table_name in ("word_tags", "words"):
            try:
                connection.execute(f"DELETE FROM {table_name}")
            except sqlite3.OperationalError:
                pass
        connection.commit()


def count_words(database_path: Path) -> int:
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute("SELECT COUNT(*) FROM words")
        return int(cursor.fetchone()[0])


def import_dictionary(
    root: Path,
    database_path: Path,
    *,
    append: bool = False,
    dry_run: bool = False,
    progress_interval: int = 200,
    max_entries: int | None = None,
) -> dict[str, object]:
    started_at = perf_counter()
    catalog = find_catalog_info(root)
    reader = EbZipReader(catalog.text_file)

    report_progress("scan", 0, reader.slice_count, f"file={catalog.text_file.name}")
    raw_text = reader.read_all(progress_interval=progress_interval, progress_stage="decompress")
    parsed_entries = build_entries_limited(
        raw_text,
        progress_interval=progress_interval,
        max_entries=max_entries,
    )

    unique_entries: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in parsed_entries:
        word = str(entry.get("headword", "")).strip()
        japanese_meaning = str(entry.get("japanese_text", "")).strip()
        chinese_meaning = str(entry.get("chinese_text", "")).strip()
        fingerprint = (word, japanese_meaning, chinese_meaning)
        if not word or fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique_entries.append(
            {
                "word": word,
                "kana": "",
                "japanese_meaning": japanese_meaning,
                "chinese_meaning": chinese_meaning,
                "example": "",
                "part_of_speech": "",
                "audio_url": "",
            }
        )

    before_count = count_words(database_path) if database_path.exists() else 0
    result = {
        "source_root": str(root),
        "catalog_title": catalog.title,
        "subbook_directory": catalog.directory,
        "text_file": str(catalog.text_file),
        "text_file_size": reader.file_size,
        "slice_size": reader.slice_size,
        "entry_count": len(parsed_entries),
        "successful_entries": len(unique_entries),
        "entry_limit": max_entries,
        "before_words": before_count,
    }

    if dry_run:
        report_progress("done", len(unique_entries), max(len(parsed_entries), 1), "dry-run 模式结束，不写入数据库")
        for entry in unique_entries[: min(3, len(unique_entries))]:
            sample_meaning = str(entry["chinese_meaning"] or entry["japanese_meaning"])
            print(f"sample: {entry['word']} | {sample_meaning[:120]}")
        return result

    if not database_path.exists():
        raise FileNotFoundError(f"database not found: {database_path}")

    ensure_dictionary_schema(database_path)
    if not append:
        clear_dictionary_tables(database_path)

    timestamp = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    rows = [
        (
            entry["word"],
            entry["kana"],
            entry["japanese_meaning"],
            entry["chinese_meaning"],
            entry["example"],
            entry["part_of_speech"],
            entry["audio_url"],
            timestamp,
        )
        for entry in unique_entries
    ]

    with sqlite3.connect(database_path) as connection:
        batch_size = 500
        total_batches = max(1, (len(rows) + batch_size - 1) // batch_size)
        for batch_index in range(total_batches):
            start = batch_index * batch_size
            batch = rows[start:start + batch_size]
            if not batch:
                continue
            written_count = min(start + len(batch), len(rows))
            emit_progress(
                f"写入 words 表 {batch_index + 1}/{total_batches}，{written_count}/{len(rows)} 条，最近词={batch[-1][0]}"
            )
            connection.executemany(
                """
                INSERT INTO words
                    (word, kana, japanese_meaning, chinese_meaning, example, part_of_speech, audio_url, created_at)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                batch,
            )
        connection.commit()

    after_count = count_words(database_path)
    elapsed_seconds = perf_counter() - started_at
    result.update(
        {
            "after_words": after_count,
            "elapsed_seconds": elapsed_seconds,
            "written_rows": len(unique_entries),
        }
    )

    report_progress(
        "done",
        len(unique_entries),
        max(len(parsed_entries), 1),
        f"已写入={len(unique_entries)} 总条目={len(parsed_entries)} 耗时={elapsed_seconds:.1f}秒",
    )
    return result


def export_dictionary(
    root: Path,
    output_path: Path,
    output_format: str = "json",
    progress_interval: int = 200,
    max_entries: int | None = None,
) -> dict[str, object]:
    started_at = perf_counter()
    catalog = find_catalog_info(root)
    reader = EbZipReader(catalog.text_file)
    report_progress("scan", 0, reader.slice_count, f"file={catalog.text_file.name}")
    raw_text = reader.read_all(progress_interval=progress_interval, progress_stage="decompress")
    entries = build_entries_limited(
        raw_text,
        progress_interval=progress_interval,
        max_entries=max_entries,
    )
    total_entries = len(entries)

    result = {
        "source_root": str(root),
        "catalog_title": catalog.title,
        "subbook_directory": catalog.directory,
        "text_file": str(catalog.text_file),
        "text_file_size": reader.file_size,
        "slice_size": reader.slice_size,
        "entry_count": len(entries),
        "entries": entries,
        "entry_limit": max_entries,
    }

    replacement_char_total = sum(str(entry["text"]).count("\ufffd") for entry in entries)
    gaiji_placeholder_total = sum(str(entry["text"]).count("⟦") for entry in entries)
    bilingual_entries = sum(1 for entry in entries if entry.get("japanese_text") or entry.get("chinese_text"))
    result["replacement_char_total"] = replacement_char_total
    result["gaiji_placeholder_total"] = gaiji_placeholder_total
    result["bilingual_entries"] = bilingual_entries

    def write_utf8_text(target_path: Path, content: str) -> None:
        target_path.write_bytes(content.encode("utf-8"))

    def dump_json_utf8(value: object, *, indent: int | None = None) -> str:
        return json.dumps(value, ensure_ascii=False, indent=indent)

    if output_format == "sqlite":
        _write_sqlite_database(output_path, catalog, reader, entries, total_entries)
    elif output_format == "jsonl":
        with output_path.open("wb") as handle:
            handle.write(dump_json_utf8({k: v for k, v in result.items() if k != "entries"}).encode("utf-8"))
            handle.write(b"\n")
            for entry in entries:
                handle.write(dump_json_utf8(entry).encode("utf-8"))
                handle.write(b"\n")
    else:
        write_utf8_text(output_path, dump_json_utf8(result, indent=2))

    elapsed_seconds = perf_counter() - started_at
    output_size = output_path.stat().st_size if output_path.exists() else 0
    report_progress(
        "done",
        len(entries),
        max(total_entries, 1),
        f"已导出={len(entries)} 总条目={total_entries} 替换符={replacement_char_total} gaiji占位={gaiji_placeholder_total} 耗时={elapsed_seconds:.1f}秒 输出大小={output_size}字节",
    )

    result.update(
        {
            "total_entries": total_entries,
            "successful_entries": len(entries),
            "elapsed_seconds": elapsed_seconds,
            "output_size_bytes": output_size,
            "output_format": output_format,
            "replacement_char_total": replacement_char_total,
            "gaiji_placeholder_total": gaiji_placeholder_total,
        }
    )
    return result


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Import the EPWING dictionary into SQLite words table")
    parser.add_argument("--dict-root", type=Path, default=DEFAULT_DICT_ROOT)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--append", action="store_true", help="append to existing rows instead of replacing them")
    parser.add_argument("--dry-run", action="store_true", help="scan entries without writing to the database")
    parser.add_argument(
        "--progress-interval",
        type=int,
        default=200,
        help="Print progress every N slices or entries",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=None,
        help="Stop after importing this many entries",
    )
    args = parser.parse_args(argv)

    result = import_dictionary(
        args.dict_root,
        args.db_path,
        append=args.append,
        dry_run=args.dry_run,
        progress_interval=args.progress_interval,
        max_entries=args.max_entries,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())