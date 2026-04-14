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
    """
    清洗规则：
    1. 删除 <sub>...</sub>（包括内容）
    2. 删除所有 HTML 标签
    3. 合并多余空格
    """

    # 删除 sub 标签（含内容）
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
    # 按 8位编号切块
    blocks = re.split(r"\n(?=\d{8})", raw_text)

    entries = []

    for block in blocks:
        if not block.strip():
            continue

        # 提取 entry id
        id_match = re.match(r"(\d{8})", block)
        if not id_match:
            continue

        entry_id = id_match.group(1)

        # 提取 word（标题）
        midashi = re.search(r'<div class="midashi">(.*?)</div>', block)
        word = midashi.group(1).strip() if midashi else ""

        # 提取正文（所有div内容）
        honbun_list = re.findall(r'<div.*?>(.*?)</div>', block, re.S)
        raw_meaning = "\n".join(honbun_list)

        # 清洗
        meaning = clean_text(raw_meaning)

        # 过滤空数据
        if not word or not meaning:
            continue

        entries.append({
            "word": word,
            "kana": "",                 # 按要求留空
            "meaning": meaning,
            "example": "",              # 按要求留空
            "part_of_speech": None,     # 按要求留空
            "audio_url": None,          # 按要求留空
            "created_at": datetime.now()
        })

    return entries


# =========================
# 3. 写入数据库
# =========================
async def insert_data(entries):
    async with SessionLocal() as session:
        async with session.begin():

            result = await session.execute(text("SELECT COUNT(*) FROM words"))
            before_count = result.scalar()
            print(f"导入前数量: {before_count}")

            BATCH_SIZE = 1000
            success = 0

            for i in range(0, len(entries), BATCH_SIZE):
                batch = entries[i:i + BATCH_SIZE]

                await session.execute(
                    text("""
                        INSERT INTO words
                        (word, kana, meaning, example, part_of_speech, audio_url, created_at)
                        VALUES
                        (:word, :kana, :meaning, :example, :part_of_speech, :audio_url, :created_at)
                    """),
                    batch
                )

                success += len(batch)
                print(f"已导入: {success}/{len(entries)}")

            result = await session.execute(text("SELECT COUNT(*) FROM words"))
            after_count = result.scalar()

            print(f"导入后数量: {after_count}")


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