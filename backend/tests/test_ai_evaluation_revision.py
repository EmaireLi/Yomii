from app.services.ai_evaluation import EssayRevisionService


def test_mock_revision_generates_sentence_suggestions_for_polished_text():
    service = EssayRevisionService()
    content = (
        "最近、人工知能の技術が急速に発展しています。"
        "私は特に、日本語の翻訳モデルに興味を持っています。"
    )

    payload = service._generate_mock_revision(
        content=content,
        topic="future-plan",
        target_level="N3",
        score_report={"overall_score": 88},
    )

    assert payload["sentence_suggestions"]
    first = payload["sentence_suggestions"][0]
    assert first["original"]
    assert first["suggested"]
    assert first["original"] != first["suggested"]
    assert payload["full_revision"] != content


def test_remote_revision_normalization_backfills_sentence_suggestions():
    service = EssayRevisionService()
    content = (
        "最近、人工知能の技術が急速に発展しています。"
        "言葉の細かいニュアンスを伝えるのはまだ難しいです。"
    )
    payload = {
        "issues": [],
        "sentence_suggestions": [],
        "full_revision": content,
        "revision_notes": "全体として自然ですが、書き言葉らしさを高められます。",
    }

    normalized = service._normalize_remote_payload(payload, content)

    assert normalized["sentence_suggestions"]
    assert normalized["issues"]
    assert normalized["full_revision"] != content
