-- ============================================================
-- Yomii 用户行为数据库 (MySQL)
-- 数据库名: yomii
-- 
-- 使用方法:
--   mysql -u root -p < init_mysql.sql
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
DROP TABLE IF EXISTS quiz_sessions;
DROP TABLE IF EXISTS search_history;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS word_progress;
DROP TABLE IF EXISTS study_stats;
DROP TABLE IF EXISTS users;

-- ============================================================
-- 1. users - 用户表
-- ============================================================
CREATE TABLE users (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    email           VARCHAR(255) UNIQUE,                 -- 邮箱（可选）
    phone           VARCHAR(20) UNIQUE,                  -- 手机号（可选）
    username        VARCHAR(100) NOT NULL UNIQUE,        -- 用户名
    hashed_password VARCHAR(255) NOT NULL,               -- 密码哈希 (bcrypt)
    is_active       BOOLEAN DEFAULT TRUE,                -- 是否启用
    is_superuser    BOOLEAN DEFAULT FALSE,               -- 是否管理员
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_users_email (email),
    INDEX idx_users_phone (phone),
    INDEX idx_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. study_stats - 学习统计表
-- ============================================================
CREATE TABLE study_stats (
    id                   INT PRIMARY KEY AUTO_INCREMENT,
    user_id              INT NOT NULL UNIQUE,             -- 用户ID（一对一）
    total_words_learned  INT DEFAULT 0,                   -- 累计学习单词数
    total_words_recited  INT DEFAULT 0,                   -- 累计背诵单词数
    today_learned        INT DEFAULT 0,                   -- 今日学习数
    today_recited        INT DEFAULT 0,                   -- 今日背诵数
    current_streak       INT DEFAULT 0,                   -- 当前连续学习天数
    longest_streak       INT DEFAULT 0,                   -- 最长连续学习天数
    last_study_date      DATE DEFAULT NULL,               -- 最后学习日期
    updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_study_stats_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. word_progress - 单词学习进度表
-- ============================================================
CREATE TABLE word_progress (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL,                        -- 用户ID
    word_id          INT NOT NULL,                        -- 单词ID (引用SQLite中的words.id)
    status           ENUM('unknown','fuzzy','known') NOT NULL DEFAULT 'unknown',
    `interval`       FLOAT NOT NULL DEFAULT 0.02,         -- 当前复习间隔（天）
    ease             FLOAT NOT NULL DEFAULT 2.5,          -- 熟练度
    review_count     INT NOT NULL DEFAULT 0,              -- 复习次数
    lapse_count      INT NOT NULL DEFAULT 0,              -- 遗忘次数
    correct_count    INT NOT NULL DEFAULT 0,              -- 正确次数
    next_review      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 下次复习时间
    last_review      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 上次复习时间
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_word (user_id, word_id),
    INDEX idx_word_progress_user_id (user_id),
    INDEX idx_word_progress_word_id (word_id),
    INDEX idx_word_progress_status (status),
    INDEX idx_word_progress_next_review (next_review),
    INDEX idx_word_progress_user_next_review (user_id, next_review)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. favorites - 收藏表
-- ============================================================
CREATE TABLE favorites (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    user_id    INT NOT NULL,                              -- 用户ID
    word_id    INT NOT NULL,                              -- 单词ID (引用SQLite)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_favorites_user_word (user_id, word_id),
    INDEX idx_favorites_user_id (user_id),
    INDEX idx_favorites_word_id (word_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. search_history - 搜索历史表
-- ============================================================
CREATE TABLE search_history (
    id           INT PRIMARY KEY AUTO_INCREMENT,
    user_id      INT NOT NULL,                            -- 用户ID
    keyword      VARCHAR(255) NOT NULL,                   -- 搜索关键词
    result_count INT DEFAULT 0,                           -- 结果数量
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_search_history_user_id (user_id),
    INDEX idx_search_history_keyword (keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. quiz_sessions - 测试会话表
-- ============================================================
CREATE TABLE quiz_sessions (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL,                         -- 用户ID
    difficulty       VARCHAR(20) NOT NULL DEFAULT 'medium',
    total_questions  INT NOT NULL DEFAULT 0,
    correct_answers  INT NOT NULL DEFAULT 0,
    accuracy         FLOAT NOT NULL DEFAULT 0,
    duration_seconds INT NOT NULL DEFAULT 0,
    ability_score    FLOAT NOT NULL DEFAULT 0,
    report_level     VARCHAR(50) NOT NULL DEFAULT '入门',
    report_summary   TEXT NOT NULL,
    trend_delta      FLOAT NOT NULL DEFAULT 0,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_quiz_sessions_user_id (user_id),
    INDEX idx_quiz_sessions_difficulty (difficulty),
    INDEX idx_quiz_sessions_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 7. quiz_results - 测试结果表
-- ============================================================
CREATE TABLE quiz_results (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                         -- 用户ID
    session_id      INT DEFAULT NULL,                     -- 会话ID（可选）
    question_id     INT NOT NULL,                         -- 题目ID (引用SQLite)
    user_answer     VARCHAR(255) NOT NULL,                -- 用户答案
    is_correct      BOOLEAN NOT NULL,                     -- 是否正确
    difficulty      VARCHAR(20) NOT NULL DEFAULT 'medium',
    timestamp       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES quiz_sessions(id) ON DELETE SET NULL,
    INDEX idx_quiz_results_user_id (user_id),
    INDEX idx_quiz_results_session_id (session_id),
    INDEX idx_quiz_results_question_id (question_id),
    INDEX idx_quiz_results_difficulty (difficulty),
    INDEX idx_quiz_results_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 8. essays - 作文表
-- ============================================================
CREATE TABLE essays (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                         -- 用户ID
    title           VARCHAR(255) NOT NULL,                -- 标题
    content         TEXT NOT NULL,                        -- 作文内容
    topic           VARCHAR(255) DEFAULT '',              -- 主题
    word_count      INT DEFAULT 0,                        -- 字数
    submit_time     DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_essays_user_id (user_id),
    INDEX idx_essays_submit_time (submit_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 9. essay_scores - 作文评分表
-- ============================================================
CREATE TABLE essay_scores (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    essay_id         INT NOT NULL,                        -- 作文ID
    overall_score    INT DEFAULT 0,                       -- 总分 (0-100)
    grammar_score    INT DEFAULT 0,                       -- 语法分
    vocabulary_score INT DEFAULT 0,                       -- 词汇分
    fluency_score    INT DEFAULT 0,                       -- 流畅度分
    coherence_score  INT DEFAULT 0,                       -- 连贯性分
    comments         TEXT,                                -- 评语
    ai_evaluated     BOOLEAN DEFAULT FALSE,               -- 是否AI评测
    evaluation_time  DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE CASCADE,
    INDEX idx_essay_scores_essay_id (essay_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 10. study_plans - 学习计划表
-- ============================================================
CREATE TABLE study_plans (
    id           INT PRIMARY KEY AUTO_INCREMENT,
    user_id      INT NOT NULL,                            -- 用户ID
    name         VARCHAR(100) NOT NULL,                   -- 计划名称
    daily_goal   INT NOT NULL DEFAULT 10,                 -- 每日目标单词数
    review_ratio FLOAT NOT NULL DEFAULT 0.5,              -- 复习比例 (0-1)
    dictionary_id VARCHAR(64) NOT NULL DEFAULT 'common',  -- 辞书ID
    is_active    BOOLEAN NOT NULL DEFAULT FALSE,          -- 是否激活
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_study_plans_user_id (user_id),
    INDEX idx_study_plans_is_active (is_active),
    INDEX idx_study_plans_dictionary_id (dictionary_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 11. learning_sessions - 学习会话表
-- ============================================================
CREATE TABLE learning_sessions (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    plan_id        INT NOT NULL,                          -- 计划ID
    date           VARCHAR(10) NOT NULL,                  -- 日期 YYYY-MM-DD
    learned_words  JSON DEFAULT NULL,                     -- 新学单词ID列表
    reviewed_words JSON DEFAULT NULL,                     -- 复习单词ID列表
    known_count    INT DEFAULT 0,                         -- 已掌握数量
    fuzzy_count    INT DEFAULT 0,                         -- 模糊数量
    unknown_count  INT DEFAULT 0,                         -- 未掌握数量
    completed_at   DATETIME DEFAULT NULL,                 -- 完成时间
    
    FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE CASCADE,
    UNIQUE KEY uk_plan_date (plan_id, date),
    INDEX idx_learning_sessions_plan_id (plan_id),
    INDEX idx_learning_sessions_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 完成提示
-- ============================================================
SELECT '✅ Yomii MySQL 数据库初始化完成!' AS message;
