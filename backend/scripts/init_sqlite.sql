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
    meaning         TEXT NOT NULL,                      -- 中文释义
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
-- 示例数据（可选）
-- ============================================================

-- 插入示例单词
INSERT INTO words (word, kana, meaning, example, part_of_speech) VALUES
('勉強', 'べんきょう', '学习', '毎日日本語を勉強しています。', '名詞/動詞'),
('食べる', 'たべる', '吃', '朝ごはんを食べます。', '動詞'),
('美しい', 'うつくしい', '美丽的', '富士山は美しいです。', '形容詞'),
('学校', 'がっこう', '学校', '学校に行きます。', '名詞'),
('読む', 'よむ', '读', '本を読むのが好きです。', '動詞');

-- 插入示例标签
INSERT INTO word_tags (word_id, tag) VALUES
(1, 'N5'), (1, 'JLPT'),
(2, 'N5'), (2, 'JLPT'), (2, '動詞'),
(3, 'N4'), (3, 'JLPT'), (3, '形容詞'),
(4, 'N5'), (4, 'JLPT'),
(5, 'N5'), (5, 'JLPT'), (5, '動詞');

-- 插入示例题目
INSERT INTO quiz_questions (type, question, word_id, options, correct_answer, explanation, difficulty) VALUES
('multiple-choice', '「勉強」的读音是？', 1, '["べんきょう","べんきょ","べんきゅう","べんきゅ"]', 'べんきょう', '勉強（べんきょう）是学习的意思。', 'easy'),
('multiple-choice', '「食べる」的意思是？', 2, '["喝","吃","看","听"]', '吃', '食べる是吃的意思，是一类动词。', 'easy'),
('fill-blank', '富士山は＿＿です。（美丽的）', 3, '["美しい","楽しい","悲しい","嬉しい"]', '美しい', '美しい是美丽的意思。', 'medium');
