-- =============================================================================
-- Yomii 数据库 - SQLite 词典库建表脚本
-- 文件: sqlite_dictionary.sql
-- 数据库: dictionary.db
-- 说明: 存储静态词典数据（单词、测试题目）
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. words - 单词表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS words (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    word            VARCHAR(100) NOT NULL,              -- 日语单词
    kana            VARCHAR(100) NOT NULL,              -- 假名读音
    meaning         TEXT NOT NULL,                      -- 中文释义
    example         TEXT NOT NULL,                      -- 例句
    part_of_speech  VARCHAR(50),                        -- 词性
    audio_url       VARCHAR(255),                       -- 音频URL
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP  -- 创建时间
);

-- 单词索引 (支持快速搜索)
CREATE INDEX IF NOT EXISTS idx_words_word ON words(word);
CREATE INDEX IF NOT EXISTS idx_words_kana ON words(kana);


-- -----------------------------------------------------------------------------
-- 2. word_tags - 单词标签表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS word_tags (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id         INTEGER NOT NULL,                   -- 单词ID
    tag             VARCHAR(50) NOT NULL,               -- 标签名 (N1/N2/常用/商务等)
    
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
);

-- 标签索引
CREATE INDEX IF NOT EXISTS idx_word_tags_word_id ON word_tags(word_id);
CREATE INDEX IF NOT EXISTS idx_word_tags_tag ON word_tags(tag);


-- -----------------------------------------------------------------------------
-- 3. quiz_questions - 测试题目表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quiz_questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    type            VARCHAR(20) NOT NULL                -- 题目类型
                    CHECK (type IN ('multiple-choice', 'fill-blank', 'listening')),
    question        TEXT NOT NULL,                      -- 题目内容
    word_id         INTEGER NOT NULL,                   -- 关联单词
    options         TEXT NOT NULL,                      -- 选项 (JSON格式)
    correct_answer  VARCHAR(255) NOT NULL,              -- 正确答案
    explanation     TEXT NOT NULL,                      -- 解析说明
    difficulty      VARCHAR(20) DEFAULT 'medium'        -- 难度级别
                    CHECK (difficulty IN ('easy', 'medium', 'hard')),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
);

-- 题目索引
CREATE INDEX IF NOT EXISTS idx_quiz_questions_word_id ON quiz_questions(word_id);
CREATE INDEX IF NOT EXISTS idx_quiz_questions_difficulty ON quiz_questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_quiz_questions_type ON quiz_questions(type);


-- =============================================================================
-- 示例数据
-- =============================================================================

-- 插入示例单词
INSERT INTO words (word, kana, meaning, example, part_of_speech) VALUES
('勉強', 'べんきょう', '学习', '毎日日本語を勉強しています。', '名词/动词'),
('食べる', 'たべる', '吃', '朝ごはんを食べます。', '动词'),
('美しい', 'うつくしい', '美丽的', 'この花は美しいです。', '形容词'),
('学校', 'がっこう', '学校', '学校へ行きます。', '名词'),
('読む', 'よむ', '读', '本を読むのが好きです。', '动词'),
('書く', 'かく', '写', '手紙を書きます。', '动词'),
('聞く', 'きく', '听', '音楽を聞きます。', '动词'),
('話す', 'はなす', '说话', '日本語を話せます。', '动词'),
('見る', 'みる', '看', '映画を見ます。', '动词'),
('行く', 'いく', '去', '日本へ行きたいです。', '动词');

-- 插入标签
INSERT INTO word_tags (word_id, tag) VALUES
(1, 'N5'), (1, '常用'),
(2, 'N5'), (2, '常用'),
(3, 'N4'), (3, '形容词'),
(4, 'N5'), (4, '常用'),
(5, 'N5'), (5, '常用'),
(6, 'N5'), (6, '常用'),
(7, 'N5'), (7, '常用'),
(8, 'N5'), (8, '常用'),
(9, 'N5'), (9, '常用'),
(10, 'N5'), (10, '常用');

-- 插入测试题目
INSERT INTO quiz_questions (type, question, word_id, options, correct_answer, explanation, difficulty) VALUES
('multiple-choice', '「勉強」的读音是什么？', 1, 
 '["べんきょう", "べんこう", "べんきゅう", "べんがく"]', 
 'べんきょう', '勉強（べんきょう）意为学习', 'easy'),
 
('multiple-choice', '「食べる」是什么意思？', 2, 
 '["喝", "吃", "睡觉", "走路"]', 
 '吃', '食べる（たべる）是一类动词，意为"吃"', 'easy'),
 
('fill-blank', '私は毎日日本語を____しています。（学习）', 1, 
 '["勉強", "勉学", "学習", "学校"]', 
 '勉強', '勉強する表示"学习"的动作', 'medium');
