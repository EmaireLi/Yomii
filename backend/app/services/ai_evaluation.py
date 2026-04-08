"""
AI 评测服务 - 作文评分
"""
import httpx
from typing import Optional
import random

from app.core.config import settings


class AIEvaluationService:
    """AI 评测服务"""
    
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.api_url = settings.AI_API_URL
        self.model = settings.AI_MODEL
    
    async def evaluate_essay(
        self,
        content: str,
        topic: str
    ) -> dict:
        """
        评测作文
        
        Args:
            content: 作文内容
            topic: 作文主题
            
        Returns:
            包含评分和评语的字典
        """
        if not self.api_key:
            # 无 API Key 时返回模拟评分
            return self._generate_mock_score()
        
        # TODO: 实现真实 AI 评测调用
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         self.api_url,
        #         headers={"Authorization": f"Bearer {self.api_key}"},
        #         json={
        #             "model": self.model,
        #             "messages": [
        #                 {"role": "system", "content": "你是一个日语作文评测专家..."},
        #                 {"role": "user", "content": f"请评测以下作文：\n主题：{topic}\n内容：{content}"}
        #             ]
        #         }
        #     )
        #     result = response.json()
        #     return self._parse_ai_response(result)
        
        return self._generate_mock_score()
    
    def _generate_mock_score(self) -> dict:
        """生成模拟评分（用于开发/测试）"""
        def random_score(base: int = 70, range_: int = 25) -> int:
            return min(100, max(0, base + random.randint(-range_ // 2, range_ // 2)))
        
        grammar = random_score(75)
        vocabulary = random_score(72)
        fluency = random_score(70)
        coherence = random_score(68)
        overall = (grammar + vocabulary + fluency + coherence) // 4
        
        comments = [
            "语法结构清晰，词汇运用恰当，整体流畅自然。建议多加练习复杂句式。",
            "表达简洁有力，逻辑层次分明，词汇选择得体。可以尝试使用更多的从句来丰富表达。",
            "文章结构完整，思路清晰，语言简洁。建议增加更多具体例子来支撑观点。",
        ]
        
        return {
            "overall_score": overall,
            "grammar_score": grammar,
            "vocabulary_score": vocabulary,
            "fluency_score": fluency,
            "coherence_score": coherence,
            "comments": random.choice(comments),
            "ai_evaluated": False
        }
    
    def _parse_ai_response(self, response: dict) -> dict:
        """解析 AI 响应（预留接口）"""
        # TODO: 根据实际 AI 接口格式解析响应
        pass


# 单例实例
ai_evaluation_service = AIEvaluationService()
