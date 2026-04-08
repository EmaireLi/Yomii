# Yomii 数据库设计文档

> 版本：1.0 | 最后更新：2026-04-08

## 📋 概述

Yomii 采用**双数据库架构**，将静态词典数据与动态用户数据分离存储：

| 数据库 | 类型 | 用途 | 特点 |
|--------|------|------|------|
| **词典库** | SQLite | 单词、测试题目 | 轻量、只读、便于分发 |
| **用户库** | MySQL | 用户、进度、作文 | 高并发、事务支持、可扩展 |

---

## 🗂️ 数据库架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Yomii Database Architecture                    │
├─────────────────────────────────┬───────────────────────────────────────┤
│        SQLite (词典库)           │           MySQL (用户库)              │
├─────────────────────────────────┼───────────────────────────────────────┤
│                                 │                                       │
│  ┌─────────────┐               │   ┌─────────────┐                     │
│  │   words     │               │   │    users    │                     │
│  │─────────────│               │   │─────────────│                     │
│  │ id (PK)     │◄──────────────┼───│ id (PK)     │──────────┐          │
│  │ word        │               │   │ username    │          │          │
│  │ kana        │               │   │ email       │          │          │
│  │ meaning     │               │   │ password    │          │          │
│  │ example     │               │   └─────────────┘          │          │
│  └──────┬──────┘               │          │                 │          │
│         │                      │          │                 │          │
│         │ 1:N                  │          │ 1:N             │          │
│         ▼                      │          ▼                 │          │
│  ┌─────────────┐               │   ┌───────────────┐        │          │
│  │  word_tags  │               │   │ word_progress │◄───────┘          │
│  └─────────────┘               │   └───────────────┘                   │
│                                │          │                            │
│  ┌────────────────┐            │          │                            │
│  │ quiz_questions │◄───────────┼──────────┼─────────────┐              │
│  │────────────────│            │          │             │              │
│  │ id (PK)        │            │   ┌──────┴──────┐      │              │
│  │ word_id (FK)   │            │   │             │      │              │
│  │ type           │            │   ▼             ▼      ▼              │
│  │ question       │            │ ┌─────────┐ ┌────────────┐            │
│  │ options        │            │ │favorites│ │quiz_results│            │
│  │ correct_answer │            │ └─────────┘ └────────────┘            │
│  └────────────────┘            │                                       │
│                                │ ┌──────────────┐  ┌─────────────┐     │
│                                │ │search_history│  │ study_stats │     │
│                                │ └──────────────┘  └─────────────┘     │
│                                │                                       │
│                                │ ┌─────────┐  ┌──────────────┐         │
│                                │ │ essays  │──│ essay_scores │         │
│                                │ └─────────┘  └──────────────┘         │
│                                │                                       │
│                                │ ┌─────────────┐ ┌──────────────────┐  │
│                                │ │ study_plans │─│ learning_sessions│  │
│                                │ └─────────────┘ └──────────────────┘  │
└─────────────────────────────────┴───────────────────────────────────────┘
```

---

## 📦 SQLite 词典库 (dictionary.db)

### 1. words - 单词表

存储日语词汇的核心数据。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 主键 |
| `word` | VARCHAR(100) | NOT NULL, INDEX | 日语单词 |
| `kana` | VARCHAR(100) | NOT NULL | 假名读音 |
| `meaning` | TEXT | NOT NULL | 中文释义 |
| `example` | TEXT | NOT NULL | 例句 |
| `part_of_speech` | VARCHAR(50) | NULL | 词性 (名词/动词/形容词等) |
| `audio_url` | VARCHAR(255) | NULL | 音频文件URL |
| `created_at` | DATETIME | DEFAULT NOW | 创建时间 |

### 2. word_tags - 单词标签表

支持单词的多标签分类（如 N1/N2、常用、商务等）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 主键 |
| `word_id` | INTEGER | FK → words.id, INDEX | 单词ID |
| `tag` | VARCHAR(50) | NOT NULL, INDEX | 标签名 |

### 3. quiz_questions - 测试题目表

预设的测试题目库。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 主键 |
| `type` | VARCHAR(20) | NOT NULL | 题目类型: multiple-choice / fill-blank / listening |
| `question` | TEXT | NOT NULL | 题目内容 |
| `word_id` | INTEGER | FK → words.id | 关联单词 |
| `options` | TEXT | NOT NULL | 选项列表 (JSON格式) |
| `correct_answer` | VARCHAR(255) | NOT NULL | 正确答案 |
| `explanation` | TEXT | NOT NULL | 解析说明 |
| `difficulty` | VARCHAR(20) | DEFAULT 'medium' | 难度: easy / medium / hard |
| `created_at` | DATETIME | DEFAULT NOW | 创建时间 |

---

## 🗄️ MySQL 用户库 (yomii_user)

### 1. users - 用户表

用户账户信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | 用户名 |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | 邮箱 |
| `hashed_password` | VARCHAR(255) | NOT NULL | 加密后的密码 |
| `is_active` | BOOLEAN | DEFAULT TRUE | 是否激活 |
| `is_superuser` | BOOLEAN | DEFAULT FALSE | 是否管理员 |
| `created_at` | DATETIME | DEFAULT NOW | 注册时间 |
| `updated_at` | DATETIME | DEFAULT NOW ON UPDATE | 更新时间 |

### 2. word_progress - 单词学习进度表

记录用户对每个单词的学习状态。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `user_id` | INT | FK → users.id, INDEX | 用户ID |
| `word_id` | INT | NOT NULL, INDEX | 单词ID (引用SQLite) |
| `status` | ENUM | DEFAULT 'unknown' | 状态: unknown / fuzzy / known |
| `review_count` | INT | DEFAULT 0 | 复习次数 |
| `correct_count` | INT | DEFAULT 0 | 正确次数 |
| `last_reviewed_at` | DATETIME | DEFAULT NOW | 最后复习时间 |

**复合索引**: `(user_id, word_id)` UNIQUE

### 3. favorites - 收藏表

用户收藏的单词。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `user_id` | INT | FK → users.id, INDEX | 用户ID |
| `word_id` | INT | NOT NULL, INDEX | 单词ID (引用SQLite) |
| `created_at` | DATETIME | DEFAULT NOW | 收藏时间 |

**复合索引**: `(user_id, word_id)` UNIQUE

### 4. search_history - 搜索历史表

用户搜索记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `user_id` | INT | FK → users.id, INDEX | 用户ID |
| `keyword` | VARCHAR(100) | NOT NULL | 搜索关键词 |
| `result_count` | INT | DEFAULT 0 | 搜索结果数量 |
| `created_at` | DATETIME | DEFAULT NOW | 搜索时间 |

**索引**: `(user_id, created_at)`

### 5. study_stats - 学习统计表

用户学习数据汇总。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `user_id` | INT | FK → users.id, UNIQUE | 用户ID (一对一) |
| `total_words_learned` | INT | DEFAULT 0 | 总学习单词数 |
| `total_words_recited` | INT | DEFAULT 0 | 总背诵次数 |
| `today_learned` | INT | DEFAULT 0 | 今日学习数 |
| `today_recited` | INT | DEFAULT 0 | 今日背诵数 |
| `current_streak` | INT | DEFAULT 0 | 当前连续天数 |
| `longest_streak` | INT | DEFAULT 0 | 最长连续天数 |
| `last_study_date` | DATE | NULL | 最后学习日期 |
| `updated_at` | DATETIME | DEFAULT NOW ON UPDATE | 更新时间 |

### 6. quiz_results - 测试结果表

用户答题记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `user_id` | INT | FK → users.id, INDEX | 用户ID |
| `question_id` | INT | NOT NULL, INDEX | 题目ID (引用SQLite) |
| `user_answer` | VARCHAR(255) | NOT NULL | 用户答案 |
| `is_correct` | BOOLEAN | NOT NULL | 是否正确 |
| `timestamp` | DATETIME | DEFAULT NOW | 答题时间 |

### 7. essays - 作文表

用户提交的作文。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `user_id` | INT | FK → users.id, INDEX | 用户ID |
| `title` | VARCHAR(200) | NOT NULL | 作文标题 |
| `content` | TEXT | NOT NULL | 作文内容 |
| `topic` | VARCHAR(100) | NOT NULL | 作文主题 |
| `word_count` | INT | NOT NULL | 字数 |
| `submit_time` | DATETIME | DEFAULT NOW | 提交时间 |

### 8. essay_scores - 作文评分表

AI 作文评测结果。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `essay_id` | INT | FK → essays.id, INDEX | 作文ID |
| `overall_score` | INT | NOT NULL | 总分 (0-100) |
| `grammar_score` | INT | NOT NULL | 语法分 (0-100) |
| `vocabulary_score` | INT | NOT NULL | 词汇分 (0-100) |
| `fluency_score` | INT | NOT NULL | 流畅度 (0-100) |
| `coherence_score` | INT | NOT NULL | 连贯性 (0-100) |
| `comments` | TEXT | NOT NULL | AI 评语 |
| `ai_evaluated` | BOOLEAN | DEFAULT FALSE | 是否AI评测 |
| `evaluation_time` | DATETIME | DEFAULT NOW | 评测时间 |

### 9. study_plans - 学习计划表

用户自定义学习计划。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `user_id` | INT | FK → users.id, INDEX | 用户ID |
| `name` | VARCHAR(100) | NOT NULL | 计划名称 |
| `daily_goal` | INT | DEFAULT 10 | 每日目标单词数 |
| `review_ratio` | DECIMAL(3,2) | DEFAULT 0.50 | 复习比例 |
| `is_active` | BOOLEAN | DEFAULT FALSE | 是否激活 |
| `created_at` | DATETIME | DEFAULT NOW | 创建时间 |
| `updated_at` | DATETIME | DEFAULT NOW ON UPDATE | 更新时间 |

### 10. learning_sessions - 学习轮次表

每日学习记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 主键 |
| `plan_id` | INT | FK → study_plans.id, INDEX | 计划ID |
| `date` | DATE | NOT NULL | 学习日期 |
| `learned_words` | JSON | NOT NULL | 新学单词ID列表 |
| `reviewed_words` | JSON | NOT NULL | 复习单词ID列表 |
| `known_count` | INT | DEFAULT 0 | 掌握数量 |
| `fuzzy_count` | INT | DEFAULT 0 | 模糊数量 |
| `unknown_count` | INT | DEFAULT 0 | 未掌握数量 |
| `completed_at` | DATETIME | NULL | 完成时间 |

**复合索引**: `(plan_id, date)` UNIQUE

---

## 🔗 跨库引用说明

由于采用双数据库架构，存在跨库引用关系：

| MySQL 表 | 引用字段 | 引用 SQLite 表 | 说明 |
|----------|----------|----------------|------|
| `word_progress` | `word_id` | `words.id` | 逻辑外键，应用层校验 |
| `favorites` | `word_id` | `words.id` | 逻辑外键，应用层校验 |
| `quiz_results` | `question_id` | `quiz_questions.id` | 逻辑外键，应用层校验 |
| `learning_sessions` | `learned_words` / `reviewed_words` | `words.id` | JSON数组中的单词ID |

**注意**：跨库引用无法使用数据库外键约束，需要在**应用层**进行数据完整性校验。

---

## 📊 索引策略

### 高频查询索引

```sql
-- 用户查询
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- 学习进度查询
CREATE UNIQUE INDEX idx_word_progress_user_word ON word_progress(user_id, word_id);

-- 收藏查询
CREATE UNIQUE INDEX idx_favorites_user_word ON favorites(user_id, word_id);

-- 搜索历史 (按时间倒序)
CREATE INDEX idx_search_history_user_time ON search_history(user_id, created_at DESC);

-- 测试结果统计
CREATE INDEX idx_quiz_results_user ON quiz_results(user_id, timestamp DESC);

-- 作文列表
CREATE INDEX idx_essays_user ON essays(user_id, submit_time DESC);
```

---

## 🔐 安全设计

1. **密码存储**：使用 `bcrypt` 加密，存储哈希值
2. **敏感字段**：`hashed_password` 永不返回给前端
3. **SQL 注入防护**：使用 SQLModel ORM 参数化查询
4. **数据隔离**：用户只能访问自己的数据（通过 `user_id` 过滤）

---

## 📝 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0 | 2026-04-08 | 初始版本 |
