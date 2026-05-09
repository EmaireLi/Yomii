"""
数据模型

SQLite (词典库):
- Word, WordTag: 单词和标签
- QuizQuestion: 测试题目

MySQL (用户库):
- User: 用户账户
- WordProgress: 单词学习进度
- Favorite: 收藏
- SearchHistory: 搜索历史
- StudyStats: 学习统计
- QuizResult: 测试结果
- Essay, EssayScore, EssayRevision, EssayJob: 作文评测
- StudyPlan, LearningSession: 学习计划
"""

# SQLite 模型
from .word import Word, WordTag, WordCreate, WordRead
from .quiz import (
    QuizQuestion,
    QuizResult,
    QuizSubmit,
    QuizSession,
    QuizSessionSubmit,
    QuizAnswerItem,
    QuestionType,
)

# MySQL 模型
from .user import User, UserCreate, UserUpdate, UserInDB
from .progress import WordProgress, WordProgressCreate, WordProgressRead, ProgressStatus
from .favorite import Favorite, FavoriteCreate, FavoriteRead, SearchHistory, SearchHistoryCreate, SearchHistoryRead
from .stats import StudyStats, StudyStatsUpdate, StudyStatsRead
from .essay import (
    Essay,
    EssayScore,
    EssayRevision,
    EssayJob,
    EssayCreate,
    EssayRead,
    EssayScoreRead,
    EssayRevisionRead,
    EssayJobRead,
)
from .study_plan import StudyPlan, LearningSession, StudyPlanCreate, StudyPlanUpdate, LearningSessionCreate

__all__ = [
    # SQLite
    "Word", "WordTag", "WordCreate", "WordRead",
    "QuizQuestion", "QuizResult", "QuizSubmit", "QuizSession", "QuizSessionSubmit", "QuizAnswerItem", "QuestionType",
    # MySQL - User
    "User", "UserCreate", "UserUpdate", "UserInDB",
    # MySQL - Progress
    "WordProgress", "WordProgressCreate", "WordProgressRead", "ProgressStatus",
    # MySQL - Favorites & History
    "Favorite", "FavoriteCreate", "FavoriteRead",
    "SearchHistory", "SearchHistoryCreate", "SearchHistoryRead",
    # MySQL - Stats
    "StudyStats", "StudyStatsUpdate", "StudyStatsRead",
    # MySQL - Essay
    "Essay", "EssayScore", "EssayRevision", "EssayJob",
    "EssayCreate", "EssayRead", "EssayScoreRead", "EssayRevisionRead", "EssayJobRead",
    # MySQL - Study Plan
    "StudyPlan", "LearningSession", "StudyPlanCreate", "StudyPlanUpdate", "LearningSessionCreate",
]
