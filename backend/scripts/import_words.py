import re
import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "dictionary.txt"

DB_URL = settings.SQLITE_DATABASE_URL

engine = create_async_engine(
    DB_URL,
    echo=False,
    connect_args={
        "timeout": 30,
        "check_same_thread": False
    }
)

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# =========================
# 1. 文本清洗函数
# =========================
def clean_text(text: str) -> str:
    # 删除 <sub>...</sub>
    text = re.sub(r"<sub>.*?</sub>", "", text, flags=re.S)

    # 删除所有 HTML 标签
    text = re.sub(r"<.*?>", "", text)

    # 合并空白
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =========================
# 2. 解析词条
# =========================
def parse_entries(raw_text: str):
    blocks = re.split(r"\n(?=\d{8})", raw_text)

    entries = []

    for block in blocks:
        if not block.strip():
            continue

        id_match = re.match(r"(\d{8})", block)
        if not id_match:
            continue

        # 提取单词
        midashi = re.search(r'<div class="midashi">(.*?)</div>', block)
        word = midashi.group(1).strip() if midashi else ""

        # 提取正文
        honbun_list = re.findall(r'<div.*?>(.*?)</div>', block, re.S)
        raw_meaning = "\n".join(honbun_list)

        # 清洗
        meaning = clean_text(raw_meaning)

        if not word or not meaning:
            continue

        entries.append({
            "word": word,
            "kana": "",
            "meaning": meaning,
            "example": "",
            "part_of_speech": None,
            "audio_url": None,
            "created_at": datetime.now(),

            # 👉 固定标签
            "tags": ["N2"]
        })

    return entries


# =========================
# 3. 写入数据库（包含 word_tags）
# =========================
async def insert_data(entries):
    async with SessionLocal() as session:
        async with session.begin():

            result = await session.execute(text("SELECT COUNT(*) FROM words"))
            print(f"导入前数量: {result.scalar()}")

            BATCH_SIZE = 1000

            # =========================
            # 1. 批量插入 words
            # =========================
            for i in range(0, len(entries), BATCH_SIZE):
                batch = entries[i:i+BATCH_SIZE]

                await session.execute(
                    text("""
                        INSERT INTO words
                        (word, kana, meaning, example, part_of_speech, audio_url, created_at)
                        VALUES
                        (:word, :kana, :meaning, :example, :part_of_speech, :audio_url, :created_at)
                    """),
                    batch
                )

                print(f"words已导入: {i + len(batch)}/{len(entries)}")

            # =========================
            # 2. 一次性查出 word -> id 映射
            # =========================
            result = await session.execute(
                text("SELECT id, word FROM words")
            )

            rows = result.fetchall()
            word_id_map = {row.word: row.id for row in rows}

            # =========================
            # 3. 构造 word_tags
            # =========================
            word_tag_rows = []

            for entry in entries:
                word_id = word_id_map.get(entry["word"])
                if not word_id:
                    continue

                for tag in entry["tags"]:
                    word_tag_rows.append({
                        "word_id": word_id,
                        "tag": tag
                    })

            # =========================
            # 4. 批量插入 word_tags
            # =========================
            for i in range(0, len(word_tag_rows), BATCH_SIZE):
                batch = word_tag_rows[i:i+BATCH_SIZE]

                await session.execute(
                    text("""
                        INSERT INTO word_tags (word_id, tag)
                        VALUES (:word_id, :tag)
                    """),
                    batch
                )

                print(f"tags已导入: {i + len(batch)}/{len(word_tag_rows)}")

            result = await session.execute(text("SELECT COUNT(*) FROM words"))
            print(f"导入后数量: {result.scalar()}")

# =========================
# 4. 主函数
# =========================
async def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    entries = parse_entries(raw_text)

    print(f"解析到数据条数: {len(entries)}")

    await insert_data(entries)


if __name__ == "__main__":
    asyncio.run(main())