"""
学习统计服务
"""
from datetime import date, datetime, time, timedelta

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.progress import WordProgress
from app.models.stats import StudyStats
from app.models.study_plan import LearningSession, StudyPlan


class StudyStatsService:
    """学习统计服务"""

    async def refresh_from_history(
        self,
        db: AsyncSession,
        user_id: int,
        stats: StudyStats,
    ) -> bool:
        """根据真实学习记录回填连续天数，避免单一路径漏写时始终为 0。"""
        session_statement = (
            select(LearningSession.date)
            .join(StudyPlan, LearningSession.plan_id == StudyPlan.id)
            .where(StudyPlan.user_id == user_id)
        )
        session_result = await db.exec(session_statement)
        session_dates = session_result.all()

        progress_statement = select(WordProgress.last_review).where(WordProgress.user_id == user_id)
        progress_result = await db.exec(progress_statement)
        progress_dates = progress_result.all()

        study_dates: set[date] = set()
        for raw_date in session_dates:
            if isinstance(raw_date, str):
                try:
                    study_dates.add(date.fromisoformat(raw_date))
                except ValueError:
                    continue
        for reviewed_at in progress_dates:
            if isinstance(reviewed_at, datetime):
                study_dates.add(reviewed_at.date())

        if not study_dates:
            return False

        ordered_dates = sorted(study_dates)
        latest_date = ordered_dates[-1]

        longest_streak = 1
        current_chain = 1
        for previous, current in zip(ordered_dates, ordered_dates[1:]):
            if current == previous + timedelta(days=1):
                current_chain += 1
            else:
                current_chain = 1
            longest_streak = max(longest_streak, current_chain)

        ending_streak = 1
        for idx in range(len(ordered_dates) - 1, 0, -1):
            if ordered_dates[idx] == ordered_dates[idx - 1] + timedelta(days=1):
                ending_streak += 1
            else:
                break

        changed = False
        if stats.last_study_date != latest_date:
            stats.last_study_date = latest_date
            changed = True
        if stats.current_streak != ending_streak:
            stats.current_streak = ending_streak
            changed = True
        if stats.longest_streak < longest_streak:
            stats.longest_streak = longest_streak
            changed = True
        if changed:
            stats.updated_at = datetime.utcnow()
        return changed

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
