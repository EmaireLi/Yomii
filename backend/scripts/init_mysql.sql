-- ============================================================
-- Yomii 用户行为数据库 (MySQL)
-- 数据库名: yomii
-- ============================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS yomii
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE yomii;

-- 删除已存在的表（开发环境用，注意顺序：先删除有外键依赖的表）
DROP TABLE IF EXISTS learning_sessions;
DROP TABLE IF EXISTS study_plans;
DROP TABLE IF EXISTS essay_scores;
DROP TABLE IF EXISTS essays;
DROP TABLE IF EXISTS quiz_results;
DROP TABLE IF EXISTS word_progress;
DROP TABLE IF EXISTS users;

-- ============================================================
-- 1. users - 用户表
-- ============================================================
CREATE TABLE users (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    email           VARCHAR(255) NOT NULL UNIQUE,       -- 邮箱
    username        VARCHAR(100) NOT NULL UNIQUE,       -- 用户名
    hashed_password VARCHAR(255) NOT NULL,              -- 密码哈希 (bcrypt)
    is_active       BOOLEAN DEFAULT TRUE,               -- 是否启用
    is_superuser    BOOLEAN DEFAULT FALSE,              -- 是否管理员
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- 更新时间
    
    INDEX idx_users_email (email),
    INDEX idx_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. word_progress - 单词学习进度表
-- ============================================================
CREATE TABLE word_progress (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL,                       -- 用户ID
    word_id          INT NOT NULL,                       -- 单词ID (引用SQLite中的words.id)
    status           VARCHAR(20) DEFAULT 'unknown',      -- 状态: unknown/fuzzy/known
    review_count     INT DEFAULT 0,                      -- 复习次数
    correct_count    INT DEFAULT 0,                      -- 正确次数
    last_reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 最后复习时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_word (user_id, word_id),          -- 一个用户对一个单词只有一条记录
    INDEX idx_word_progress_user_id (user_id),
    INDEX idx_word_progress_word_id (word_id),
    INDEX idx_word_progress_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. quiz_results - 测试结果表
-- ============================================================
CREATE TABLE quiz_results (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                        -- 用户ID
    question_id     INT NOT NULL,                        -- 题目ID (引用SQLite中的quiz_questions.id)
    user_answer     VARCHAR(255) NOT NULL,               -- 用户答案
    is_correct      BOOLEAN NOT NULL,                    -- 是否正确
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 答题时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_quiz_results_user_id (user_id),
    INDEX idx_quiz_results_question_id (question_id),
    INDEX idx_quiz_results_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. essays - 作文表
-- ============================================================
CREATE TABLE essays (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                        -- 用户ID
    title           VARCHAR(255) NOT NULL,               -- 标题
    content         TEXT NOT NULL,                       -- 作文内容
    topic           VARCHAR(255) NOT NULL,               -- 主题
    word_count      INT NOT NULL,                        -- 字数
    submit_time     DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 提交时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_essays_user_id (user_id),
    INDEX idx_essays_submit_time (submit_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. essay_scores - 作文评分表
-- ============================================================
CREATE TABLE essay_scores (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    essay_id         INT NOT NULL UNIQUE,                -- 作文ID (一篇作文一个评分)
    overall_score    INT NOT NULL,                       -- 总分 (0-100)
    grammar_score    INT NOT NULL,                       -- 语法分 (0-100)
    vocabulary_score INT NOT NULL,                       -- 词汇分 (0-100)
    fluency_score    INT NOT NULL,                       -- 流畅度分 (0-100)
    coherence_score  INT NOT NULL,                       -- 连贯性分 (0-100)
    comments         TEXT NOT NULL,                      -- 评语
    ai_evaluated     BOOLEAN DEFAULT FALSE,              -- 是否AI评测
    evaluation_time  DATETIME DEFAULT CURRENT_TIMESTAMP, -- 评测时间
    
    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE CASCADE,
    INDEX idx_essay_scores_essay_id (essay_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. study_plans - 学习计划表
-- ============================================================
CREATE TABLE study_plans (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                        -- 用户ID
    name            VARCHAR(100) NOT NULL,               -- 计划名称
    daily_goal      INT DEFAULT 10,                      -- 每日目标单词数
    review_ratio    FLOAT DEFAULT 0.5,                   -- 复习比例 (0-1)
    is_active       BOOLEAN DEFAULT FALSE,               -- 是否激活
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- 更新时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_study_plans_user_id (user_id),
    INDEX idx_study_plans_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 7. learning_sessions - 学习轮次表
-- ============================================================
CREATE TABLE learning_sessions (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    plan_id         INT NOT NULL,                        -- 计划ID
    date            VARCHAR(10) NOT NULL,                -- 日期 (YYYY-MM-DD)
    learned_words   TEXT NOT NULL,                       -- 新学单词ID列表 (JSON数组)
    reviewed_words  TEXT NOT NULL,                       -- 复习单词ID列表 (JSON数组)
    known_count     INT DEFAULT 0,                       -- 已掌握数量
    fuzzy_count     INT DEFAULT 0,                       -- 模糊数量
    unknown_count   INT DEFAULT 0,                       -- 未掌握数量
    completed_at    DATETIME NULL,                       -- 完成时间
    
    FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE CASCADE,
    UNIQUE KEY uk_plan_date (plan_id, date),             -- 一个计划一天只有一条记录
    INDEX idx_learning_sessions_plan_id (plan_id),
    INDEX idx_learning_sessions_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 示例数据（可选）
-- ============================================================

-- 插入测试用户 (密码: password123, 使用bcrypt哈希)
-- 注意: 实际使用时应通过应用程序创建用户
INSERT INTO users (email, username, hashed_password, is_active, is_superuser) VALUES
('admin@yomii.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4FRWOPVBrF9X2Cyu', TRUE, TRUE),
('test@yomii.com', 'testuser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4FRWOPVBrF9X2Cyu', TRUE, FALSE);

-- 插入示例学习计划
INSERT INTO study_plans (user_id, name, daily_goal, review_ratio, is_active) VALUES
(2, '默认计划', 10, 0.5, TRUE),
(2, 'N5备考计划', 20, 0.6, FALSE);

-- ============================================================
-- 完成提示
-- ============================================================
SELECT '✅ MySQL 数据库初始化完成!' AS message;
SELECT COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS plan_count FROM study_plans;
