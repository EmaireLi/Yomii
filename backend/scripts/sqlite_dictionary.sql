-- ============================================================
-- Yomii 词典数据库 (SQLite)
-- 文件: data/dictionary.db
-- ============================================================

-- 删除已存在的表（开发环境用）
DROP TABLE IF EXISTS word_tags;
DROP TABLE IF EXISTS quiz_questions;
DROP TABLE IF EXISTS words;

-- ============================================================
-- 1. words - 单词表
-- ============================================================
CREATE TABLE words (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    word            VARCHAR(100) NOT NULL,              -- 日语单词
    kana            VARCHAR(100) NOT NULL,              -- 假名读音
    japanese_meaning TEXT NOT NULL,                     -- 日文释义
    chinese_meaning TEXT NOT NULL DEFAULT '',           -- 中文释义
    example         TEXT NOT NULL,                      -- 例句
    part_of_speech  VARCHAR(50),                        -- 词性 (名詞/動詞/形容詞 等)
    audio_url       VARCHAR(255),                       -- 音频URL
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP  -- 创建时间
);

-- 单词索引
CREATE INDEX idx_words_word ON words(word);
CREATE INDEX idx_words_kana ON words(kana);

-- ============================================================
-- 2. word_tags - 单词标签关联表
-- ============================================================
CREATE TABLE word_tags (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id         INTEGER NOT NULL,                   -- 单词ID
    tag             VARCHAR(50) NOT NULL,               -- 标签名 (N1/N2/N3/动词/名词 等)
    
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
);

-- 标签索引
CREATE INDEX idx_word_tags_word_id ON word_tags(word_id);
CREATE INDEX idx_word_tags_tag ON word_tags(tag);

-- ============================================================
-- 3. quiz_questions - 测试题目表
-- ============================================================
CREATE TABLE quiz_questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    type            VARCHAR(20) NOT NULL,               -- 题型: multiple-choice/fill-blank/listening
    question        TEXT NOT NULL,                      -- 题目内容
    word_id         INTEGER NOT NULL,                   -- 关联单词ID
    options         TEXT NOT NULL,                      -- 选项 (JSON数组格式)
    correct_answer  VARCHAR(255) NOT NULL,              -- 正确答案
    explanation     TEXT NOT NULL,                      -- 解析
    difficulty      VARCHAR(10) DEFAULT 'medium',       -- 难度: easy/medium/hard
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
);

-- 题目索引
CREATE INDEX idx_quiz_questions_word_id ON quiz_questions(word_id);
CREATE INDEX idx_quiz_questions_difficulty ON quiz_questions(difficulty);
CREATE INDEX idx_quiz_questions_type ON quiz_questions(type);

-- ============================================================
-- 完成提示
-- ============================================================
SELECT '✅ Yomii SQLite 词典库初始化完成（无测试数据）' AS message;
