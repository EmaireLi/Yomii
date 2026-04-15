"""
学习统计服务
"""
from datetime import date, datetime, time, timedelta

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.stats import StudyStats


class StudyStatsService:
    """学习统计服务"""

    async def get_or_create(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> tuple[StudyStats, bool]:
        """获取或创建学习统计记录"""
        statement = select(StudyStats).where(StudyStats.user_id == user_id)
        result = await db.exec(statement)
        stats = result.first()
        if stats is not None:
            return stats, False

        stats = StudyStats(user_id=user_id)
        db.add(stats)
        await db.flush()
        return stats, True

    def apply_learning_activity(
        self,
        stats: StudyStats,
        study_date: date,
        recited_count: int,
        learned_count: int,
    ) -> None:
        """应用一次学习活动，更新连续天数与累计统计"""
        safe_recited_count = max(0, recited_count)
        safe_learned_count = max(0, learned_count)

        if safe_recited_count == 0 and safe_learned_count == 0:
            return

        last_date = stats.last_study_date
        if last_date is None:
            stats.current_streak = 1
            stats.last_study_date = study_date
            stats.today_recited = safe_recited_count
            stats.today_learned = safe_learned_count
        elif study_date > last_date:
            if study_date == last_date + timedelta(days=1):
                stats.current_streak += 1
            else:
                stats.current_streak = 1
            stats.last_study_date = study_date
            stats.today_recited = safe_recited_count
            stats.today_learned = safe_learned_count
        elif study_date == last_date:
            stats.today_recited += safe_recited_count
            stats.today_learned += safe_learned_count

        stats.total_words_recited += safe_recited_count
        stats.total_words_learned += safe_learned_count
        stats.longest_streak = max(stats.longest_streak, stats.current_streak)
        stats.updated_at = datetime.utcnow()

    def to_response(self, stats: StudyStats) -> dict:
        """转换为前端返回格式"""
        today = date.today()
        last_date = stats.last_study_date

        today_learned = stats.today_learned if last_date == today else 0
        today_recited = stats.today_recited if last_date == today else 0

        current_streak = stats.current_streak
        if last_date is None:
            current_streak = 0
        else:
            day_gap = (today - last_date).days
            if day_gap > 1:
                current_streak = 0

        last_study_date_ms = 0
        if last_date is not None:
            last_study_date_ms = int(
                datetime.combine(last_date, time.min).timestamp() * 1000
            )

        return {
            "totalWordsLearned": stats.total_words_learned,
            "totalWordsRecited": stats.total_words_recited,
            "todayLearned": today_learned,
            "todayRecited": today_recited,
            "currentStreak": current_streak,
            "longestStreak": stats.longest_streak,
            "lastStudyDate": last_study_date_ms,
        }


study_stats_service = StudyStatsService()
