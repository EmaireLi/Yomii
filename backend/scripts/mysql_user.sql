-- =============================================================================
-- Yomii 数据库 - MySQL 用户库建表脚本
-- 文件: mysql_user.sql
-- 数据库: yomii_user
-- 说明: 存储用户行为数据（用户、进度、作文、学习计划）
-- =============================================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS yomii_user
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE yomii_user;


-- -----------------------------------------------------------------------------
-- 1. users - 用户表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    username        VARCHAR(50) NOT NULL UNIQUE,        -- 用户名
    email           VARCHAR(100) NOT NULL UNIQUE,       -- 邮箱
    hashed_password VARCHAR(255) NOT NULL,              -- 加密密码
    is_active       BOOLEAN DEFAULT TRUE,               -- 是否激活
    is_superuser    BOOLEAN DEFAULT FALSE,              -- 是否管理员
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP, -- 注册时间
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_users_email (email),
    INDEX idx_users_username (username)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- 2. word_progress - 单词学习进度表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS word_progress (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                       -- 用户ID
    word_id         INT NOT NULL,                       -- 单词ID (引用SQLite)
    status          ENUM('unknown', 'fuzzy', 'known') DEFAULT 'unknown', -- 学习状态
    review_count    INT DEFAULT 0,                      -- 复习次数
    correct_count   INT DEFAULT 0,                      -- 正确次数
    last_reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 最后复习时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE INDEX idx_word_progress_user_word (user_id, word_id),
    INDEX idx_word_progress_status (user_id, status)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- 3. favorites - 收藏表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS favorites (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                       -- 用户ID
    word_id         INT NOT NULL,                       -- 单词ID (引用SQLite)
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP, -- 收藏时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE INDEX idx_favorites_user_word (user_id, word_id)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- 4. search_history - 搜索历史表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS search_history (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                       -- 用户ID
    keyword         VARCHAR(100) NOT NULL,              -- 搜索关键词
    result_count    INT DEFAULT 0,                      -- 搜索结果数量
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP, -- 搜索时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_search_history_user_time (user_id, created_at DESC)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- 5. study_stats - 学习统计表 (一对一)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS study_stats (
    id                  INT PRIMARY KEY AUTO_INCREMENT,
    user_id             INT NOT NULL UNIQUE,            -- 用户ID (一对一)
    total_words_learned INT DEFAULT 0,                  -- 总学习单词数
    total_words_recited INT DEFAULT 0,                  -- 总背诵次数
    today_learned       INT DEFAULT 0,                  -- 今日学习数
    today_recited       INT DEFAULT 0,                  -- 今日背诵数
    current_streak      INT DEFAULT 0,                  -- 当前连续天数
    longest_streak      INT DEFAULT 0,                  -- 最长连续天数
    last_study_date     DATE,                           -- 最后学习日期
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- 6. quiz_results - 测试结果表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quiz_results (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                       -- 用户ID
    question_id     INT NOT NULL,                       -- 题目ID (引用SQLite)
    user_answer     VARCHAR(255) NOT NULL,              -- 用户答案
    is_correct      BOOLEAN NOT NULL,                   -- 是否正确
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP, -- 答题时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_quiz_results_user (user_id, timestamp DESC),
    INDEX idx_quiz_results_question (question_id)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- 7. essays - 作文表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS essays (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                       -- 用户ID
    title           VARCHAR(200) NOT NULL,              -- 作文标题
    content         TEXT NOT NULL,                      -- 作文内容
    topic           VARCHAR(100) NOT NULL,              -- 作文主题
    word_count      INT NOT NULL,                       -- 字数
    submit_time     DATETIME DEFAULT CURRENT_TIMESTAMP, -- 提交时间
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_essays_user (user_id, submit_time DESC)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- 8. essay_scores - 作文评分表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS essay_scores (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    essay_id        INT NOT NULL,                       -- 作文ID
    overall_score   INT NOT NULL CHECK (overall_score BETWEEN 0 AND 100),    -- 总分
    grammar_score   INT NOT NULL CHECK (grammar_score BETWEEN 0 AND 100),    -- 语法分
    vocabulary_score INT NOT NULL CHECK (vocabulary_score BETWEEN 0 AND 100), -- 词汇分
    fluency_score   INT NOT NULL CHECK (fluency_score BETWEEN 0 AND 100),    -- 流畅度
    coherence_score INT NOT NULL CHECK (coherence_score BETWEEN 0 AND 100),  -- 连贯性
    comments        TEXT NOT NULL,                      -- AI评语
    ai_evaluated    BOOLEAN DEFAULT FALSE,              -- 是否AI评测
    evaluation_time DATETIME DEFAULT CURRENT_TIMESTAMP, -- 评测时间
    
    FOREIGN KEY (essay_id) REFERENCES essays(id) ON DELETE CASCADE,
    INDEX idx_essay_scores_essay (essay_id)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- 9. study_plans - 学习计划表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS study_plans (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    user_id         INT NOT NULL,                       -- 用户ID
    name            VARCHAR(100) NOT NULL,              -- 计划名称
    daily_goal      INT DEFAULT 10,                     -- 每日目标单词数
    review_ratio    DECIMAL(3,2) DEFAULT 0.50,          -- 复习比例 (0.00-1.00)
    is_active       BOOLEAN DEFAULT FALSE,              -- 是否激活
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_study_plans_user (user_id),
    INDEX idx_study_plans_active (user_id, is_active)
) ENGINE=InnoDB;


-- -----------------------------------------------------------------------------
-- 10. learning_sessions - 学习轮次表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS learning_sessions (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    plan_id         INT NOT NULL,                       -- 计划ID
    date            DATE NOT NULL,                      -- 学习日期
    learned_words   JSON NOT NULL,                      -- 新学单词ID列表
    reviewed_words  JSON NOT NULL,                      -- 复习单词ID列表
    known_count     INT DEFAULT 0,                      -- 掌握数量
    fuzzy_count     INT DEFAULT 0,                      -- 模糊数量
    unknown_count   INT DEFAULT 0,                      -- 未掌握数量
    completed_at    DATETIME,                           -- 完成时间
    
    FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE CASCADE,
    UNIQUE INDEX idx_learning_sessions_plan_date (plan_id, date),
    INDEX idx_learning_sessions_date (date)
) ENGINE=InnoDB;


-- =============================================================================
-- 触发器：用户注册时自动创建学习统计记录
-- =============================================================================
DELIMITER //
CREATE TRIGGER IF NOT EXISTS tr_user_after_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO study_stats (user_id) VALUES (NEW.id);
END//
DELIMITER ;


-- =============================================================================
-- 视图：用户学习概览
-- =============================================================================
CREATE OR REPLACE VIEW v_user_learning_overview AS
SELECT 
    u.id AS user_id,
    u.username,
    ss.total_words_learned,
    ss.total_words_recited,
    ss.current_streak,
    ss.longest_streak,
    ss.last_study_date,
    (SELECT COUNT(*) FROM favorites f WHERE f.user_id = u.id) AS favorites_count,
    (SELECT COUNT(*) FROM essays e WHERE e.user_id = u.id) AS essays_count,
    (SELECT COUNT(*) FROM word_progress wp WHERE wp.user_id = u.id AND wp.status = 'known') AS known_words_count
FROM users u
LEFT JOIN study_stats ss ON u.id = ss.user_id;
