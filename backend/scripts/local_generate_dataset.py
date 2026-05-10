"""
Local synthetic dataset generator for Japanese essay scoring + revision.
Generates 500+ training samples with controlled error injection — NO external API needed.

Usage: python scripts/local_generate_dataset.py [--samples 500]
"""
from __future__ import annotations

import json
import math
import random
import hashlib
from pathlib import Path
from typing import Any

random.seed(42)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. TOPIC POOL — 多样化题目库
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOPICS_N5 = [
    "私の家族", "私の一日", "私の趣味", "好きな動物", "私の部屋",
    "毎日の朝ごはん", "私の友達", "学校生活", "好きな季節", "休みの日",
    "私の町", "ペット", "好きな色", "電車", "私の国",
]

TOPICS_N4 = [
    "旅行の思い出", "昔のクラスメート", "誕生日", "大切な人", "私の国と日本",
    "一番好きな場所", "昨日の出来事", "将来の夢", "買い物", "休日の過ごし方",
    "私の宝物", "尊敬する人", "最近読んだ本", "子どもの頃の遊び", "スポーツ",
]

TOPICS_N3 = [
    "健康と運動", "便利な技術", "読書", "環境問題", "アルバイト経験",
    "学校生活の変化", "好きな教科", "日本の習慣", "言語学習", "友情",
    "おすすめの場所", "趣味と勉強の両立", "留学経験", "インターネット", "季節の行事",
]

TOPICS_N2 = [
    "情報社会の問題点", "仕事と生活", "教育", "言語と文化", "観光",
    "ボランティア活動", "食文化の違い", "多様性", "科学技術と社会", "少子化問題",
    "地域活性化", "コミュニケーション", "グローバル化", "メディアの影響", "環境保護",
]

TOPICS_N1 = [
    "少子高齢化", "技術革新と人間性", "持続可能な社会", "グローバル化と文化",
    "AIと雇用", "教育格差", "多文化共生", "人口減少", "幸福とは何か", "自由と責任",
]

LEVEL_TOPICS = {"N5": TOPICS_N5, "N4": TOPICS_N4, "N3": TOPICS_N3, "N2": TOPICS_N2, "N1": TOPICS_N1}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. ESSAY TEMPLATES per level (骨架，注入错误前的基础文本)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ESSAY_TEMPLATES_N5 = [
    """{topic}について書きます。私の{topic}はとてもいいです。
毎日{topic}を見ます。とても楽しいです。
{topic}は私にとって大切です。
これからも{topic}を続けたいです。
{topic}が好きです。""",
    """私の{topic}を紹介します。
{topic}は毎日楽しいです。
私は{topic}が大好きです。
友達も{topic}が好きです。
一緒に{topic}を楽しみたいです。
{topic}はいいものだと思います。""",
    """今日は{topic}の話をします。
私は{topic}が好きです。理由は楽しいからです。
{topic}をしている時、時間を忘れます。
将来も{topic}を続けたいです。
{topic}は私の生活の一部です。""",
    """私の国では{topic}が人気です。
私も{topic}が大好きです。
毎週{topic}をしています。
{topic}はとても面白いです。
友達も{topic}をしたいと言っています。
{topic}をこれからも続けたいです。""",
    """昨日、{topic}について考えました。
{topic}は私にとって大切なものです。
{topic}があるから、毎日頑張れます。
{topic}のためにもっと勉強します。
{topic}を大切にしたいです。""",
]

ESSAY_TEMPLATES_N4 = [
    """先週、{topic}について経験しました。
とても良い経験でした。最初は緊張しましたが、だんだん慣れました。
{topic}を通じて、新しいことを学びました。
特に、友達と一緒に活動したことが印象的でした。
また機会があれば、もう一度挑戦したいです。
{topic}は私にとって大切な思い出です。""",
    """私の{topic}について話したいと思います。
{topic}は私の生活の中で重要な役割を果たしています。
なぜなら、{topic}を通じて多くのことを学べるからです。
例えば、計画性や忍耐力が身につきました。
これからも{topic}を続けて、さらに上達したいです。
{topic}のおかげで毎日が充実しています。""",
    """{topic}に行った時のことを思い出します。
天気が良くて、気持ちがよかったです。
周りの景色がとても綺麗で、感動しました。
{topic}では、いろいろな人に出会いました。
みんな親切で、楽しく過ごせました。
{topic}はまた行きたい場所の一つです。""",
    """先日、友達と{topic}について話しました。
{topic}は、私たちにとって共通の話題です。
{topic}の話をすると、時間があっという間に過ぎます。
{topic}についてもっと知りたいと思います。
{topic}は私たちの関係を深めてくれました。""",
    """私の{topic}の経験を紹介します。
{topic}を始めたのは三年前です。
最初は難しいと思いましたが、続けるうちに好きになりました。
{topic}のおかげで、新しい友達ができました。
{topic}は私の人生を豊かにしています。""",
]

ESSAY_TEMPLATES_N3 = [
    """最近、{topic}について考える機会が増えました。
{topic}は現代社会において重要なテーマだと思います。
私自身、{topic}に関して様々な経験をしてきました。
良い面もあれば、課題も存在します。
{topic}のメリットは、新しい可能性を広げてくれることです。
一方で、デメリットとしては、時間やコストがかかることが挙げられます。
{topic}とどのように向き合うべきか、これからも考え続けたいです。""",
    """{topic}について、私の意見を述べたいと思います。
{topic}には肯定的な意見と否定的な意見がありますが、
私は{topic}は必要だと、考えます。
なぜなら、{topic}があるからこそ、
人々はより良い生活を送ることができるからです。
もちろん、{topic}には注意すべき点もあります。
しかし、適切に利用すれば、大きな力になるはずです。""",
    """私は{topic}に興味を持っています。
{topic}を始めたきっかけは、友達の勧めでした。
最初は難しかったですが、続けるうちに楽しくなりました。
{topic}を通じて、自分自身の成長を感じられます。
また、同じ趣味を持つ人と交流できるのも魅力です。
{topic}は私にとって、なくてはならないものです。""",
    """{topic}の重要性は、多くの人が認めるところです。
しかし、実際に{topic}を理解している人は少ないかもしれません。
私は{topic}について学ぶことで、視野が広がりました。
{topic}に関する知識は、日常生活でも役立ちます。
これからも{topic}について深く学び続けたいと思います。""",
    """{topic}について、最近よく考えるようになりました。
{topic}には様々な側面があり、一概に評価できません。
良い点としては、新たな価値観を得られることです。
しかし、注意しなければならないこともあります。
{topic}を正しく理解することが大切だと思います。""",
]

ESSAY_TEMPLATES_N2 = [
    """現代社会において、{topic}は避けて通れない問題の一つである。
{topic}には様々な側面があり、単純に良い悪いと判断することは難しい。
例えば、{topic}がもたらす利点としては、効率性や利便性の向上が挙げられる。
しかしその一方で、新たな社会的課題も生み出している。
私は、{topic}に対してバランスの取れた態度が必要だと考える。
極端な肯定も否定もせず、メリットとデメリットを理解した上で、
{topic}とどう付き合っていくべきかを考えるべきである。""",
    """{topic}について、最近よくニュースで見かけるようになった。
{topic}が深刻化している背景には、様々な要因が複雑に絡み合っている。
まず第一に、経済的な問題が挙げられる。
第二に、社会的な意識の変化も影響している。
これらの問題を解決するためには、個人の努力だけでなく、
社会全体としての取り組みが必要不可欠である。
{topic}の解決に向けて、私たち一人ひとりができることから始めるべきだ。""",
    """{topic}は私たちの生活に深く関わっている。
私は{topic}の重要性について、以前から関心を持っていた。
{topic}を考える時、常に忘れてはならないのは、
それが将来の世代にどのような影響を与えるかという視点である。
短期的な利益だけを追求するのではなく、
長期的な持続可能性を考慮することが大切だ。
そのためには、教育や啓発活動を通じて、
{topic}に対する理解を深める必要がある。""",
    """{topic}に関する議論は、しばしば複雑な様相を呈する。
{topic}を巡っては様々な立場があり、容易に結論を出せるものではない。
私は、{topic}について考える際には、客観的なデータに基づくべきだと考える。
感情的になりがちなテーマだからこそ、冷静な議論が求められる。
{topic}の将来について、私たちは真剣に向き合わなければならない。""",
    """{topic}は現代日本が抱える重要課題の一つである。
{topic}の問題は、個人の生活にも大きな影響を及ぼしている。
{topic}に対する認識を改め、積極的に取り組む必要がある。
解決策は一つではないが、まずは問題を正しく認識することが出発点だ。
{topic}とどう向き合うかは、私たち全員に問われている。""",
]

ESSAY_TEMPLATES_N1 = [
    """{topic}は、現代日本が直面する最も深刻な課題の一つである。
この問題の背景には、複数の社会的要因が存在している。
経済的要因、文化的要因、そして制度的要因が複雑に絡み合い、
{topic}を一層困難なものにしている。
私は、この問題の解決には長期的な視点に立った戦略が必要だと考える。
短期的な施策だけでは、根本的な解決には至らないだろう。
{topic}に対しては、官民学が連携した包括的なアプローチが求められている。""",
    """{topic}というテーマは、本質的に極めて複雑である。
一方では、{topic}の進展がもたらす恩恵は計り知れない。
他方で、それに伴う倫理的・社会的な課題も無視できない。
私は、{topic}に対して楽観も悲観もせず、
冷静かつ客観的な分析に基づいて判断すべきだと考える。
重要なのは、{topic}の本質を理解した上で、
人間中心の価値観をどのように維持していくかという点である。""",
    """{topic}を考察する際、まず認識すべきは、
この問題が単一の原因によって引き起こされているわけではないということだ。
{topic}は多層的な構造を持ち、様々な要素が相互に影響し合っている。
したがって、解決策も多角的である必要がある。
私は、{topic}に対して「適応」と「変革」の両方が必要だと考える。
既存の枠組みに固執するのではなく、柔軟に変化に対応しながら、
同時に望ましい未来に向けて能動的に社会を変革していく姿勢が重要である。""",
    """{topic}を論じる際、まず理解すべきはその複雑性である。
{topic}の問題は、単独で存在するわけではなく、
経済、社会、文化など様々な領域と相互に連関している。
したがって、{topic}への対策も多面的である必要がある。
私は、{topic}について考えることは、
現代社会の本質を理解することに他ならないと考える。
今後も{topic}に関心を持ち続けていきたい。""",
    """{topic}は、私たちに多くの問いを投げかけている。
{topic}の進展は、確かに生活を豊かにした。
しかし同時に、新たな倫理的課題も生み出している。
{topic}に関する議論では、短期的な便益と長期的な影響を
慎重に比較検討する必要がある。
{topic}とどう向き合うかは、私たち一人ひとりが考えなければならない。""",
]

TEMPLATES_BY_LEVEL = {
    "N5": ESSAY_TEMPLATES_N5,
    "N4": ESSAY_TEMPLATES_N4,
    "N3": ESSAY_TEMPLATES_N3,
    "N2": ESSAY_TEMPLATES_N2,
    "N1": ESSAY_TEMPLATES_N1,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. ERROR INJECTION — 适合各等级的典型错误
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ERRORS_N5 = [
    # (search, replace, severity, explanation)
    ("が好きです", "を好きです", "medium", "助詞「が」の代わりに「を」を使う誤り"),
    ("ます。", "まし。", "high", "動詞の活用が不完全（ます→まし）"),
    ("楽しいです", "楽しです", "medium", "形容詞の活用ミス「楽しい」→「楽し」"),
    ("食べます", "食べるます", "high", "動詞の活用の二重誤り"),
    ("があります", "をあります", "medium", "存在を表す「が」の代わりに「を」を使用"),
    ("に行きます", "にいくます", "high", "「行きます」の活用誤り"),
    ("美味しい", "美味い", "low", "形容詞の語形誤り"),
    ("好きです", "好きだです", "medium", "「だ」と「です」の混同"),
    ("毎日", "毎日", "low", "（ダミー）"),
    ("とても", "とっても", "low", "促音の過剰使用（口語的）"),
    ("大切です", "大切だです", "medium", "ナ形容詞＋だ＋ですの誤り"),
    ("見ます", "みるます", "high", "辞書形＋ますの過剰修正"),
    ("友達", "友だち", "low", "漢字とひらがなの混在"),
    ("したいです", "したいだ", "medium", "「です」の欠落"),
    ("いい", "よい", "low", "形容詞の不自然な交替"),
]

ERRORS_N4 = [
    ("でした", "かったです", "high", "ナ形容詞過去形の誤り（綺麗かったです）"),
    ("ています", "てます", "low", "「い」の脱落（口語的）"),
    ("た", "と", "medium", "過去形と条件形の混同"),
    ("ことができる", "ことがあります", "medium", "可能表現と存在表現の混同"),
    ("が", "を", "medium", "助詞の誤用"),
    ("を", "に", "medium", "目的格と方向格の混同"),
    ("ので", "からので", "high", "原因理由の接続の重複"),
    ("しかし", "しかしながら", "low", "接続詞の過剙使用（過剰）"),
    ("なければなりません", "なければいけません", "low", "「〜なければならない」と「〜いけない」の混同等"),
    ("綺麗", "きれい", "low", "漢字とひらがなの不統一"),
    ("とても", "とてもとても", "low", "強調の重複"),
    ("美味しかった", "美味しかったでした", "medium", "形容詞過去形と「です」の二重"),
    ("思います", "おもいます", "low", "漢字の不使用"),
    ("と言います", "といった", "medium", "引用と例示の混同"),
    ("から", "だからの", "medium", "「から」と「ので」の混同"),
]

ERRORS_N3 = [
    ("と思う", "とおもう", "low", "漢字→ひらがなの誤り"),
    ("しなければならない", "しないと", "medium", "「〜しなければならない」の口語的な省略"),
    ("考える", "考えれる", "high", "可能動詞の誤形成（ら抜き言葉）"),
    ("言われている", "言っている", "medium", "受身と能動の混同"),
    ("しかし", "しかしながら", "low", "冗長な接続詞"),
    ("できない", "できらない", "high", "可能形の誤り"),
    ("特に", "特に特に", "low", "強調表現の重複"),
    ("大切だ", "大切", "low", "「だ」の欠落"),
    ("重要だ", "大事だ", "low", "類義語の不適切な選択"),
    ("と呼ばれる", "という", "medium", "「と呼ばれる」と「という」の混同"),
    ("必要がある", "必要なある", "medium", "ナ形容詞＋「が」の欠落"),
    ("ことができる", "ことができれる", "high", "可能動詞の二重誤り"),
    ("と言われている", "と言っている", "medium", "受身形の欠落"),
    ("に対して", "にたいして", "low", "漢字→ひらがな"),
    ("関して", "かんして", "low", "漢字→ひらがな"),
    ("様々な", "様々の", "medium", "ナ形容詞とノ形容詞の混同"),
    ("多い", "多く", "low", "連体形と連用形の混同"),
    ("さらに", "もっと", "low", "硬さと柔らかさの不統一"),
]

# N2 级别错误更微妙
ERRORS_N2 = [
    ("おいて", "おけて", "medium", "可能動詞の誤形成"),
    ("関して", "関しては", "low", "過剰な「は」"),
    ("考えられる", "考えられる", "low", "（ダミー）"),
    ("と", "ということ", "low", "過剰な説明"),
    ("べきだ", "はずだ", "medium", "「べき」と「はず」の混同"),
    ("言わざるを得ない", "言わない", "high", "慣用表現の不使用"),
    ("の", "ことの", "low", "名詞化の過剰"),
    ("など", "などなど", "low", "重複表現"),
    ("多い", "多く", "low", "連体形と連用形の混同"),
    ("様々な", "様々の", "medium", "ナ形容詞とノ形容詞の混同"),
]

# N1 级别几乎没有显性错误，主要是表达可微调
ERRORS_N1 = [
    ("あろう", "ありうる", "low", "推量と可能性の混同"),
    ("である", "であります", "low", "文体の不統一"),
    ("の", "のこと", "low", "過剰な名詞化"),
    ("なくてはならない", "なければ", "low", "条件表現の簡略化"),
    ("言える", "言うことができる", "low", "冗長な可能表現"),
    ("から", "ので", "low", "理由表現の不自然な交替"),
    ("と考えられる", "と考えれる", "low", "可能表現の誤り"),
    ("関して", "関してもって", "low", "冗長表現"),
    ("おいて", "おきまして", "low", "過剰敬語"),
    ("の", "のこととして", "low", "過剰な名詞化"),
    ("言わざるを得ない", "言わないわけにはいかない", "low", "二重否定表現の冗長化"),
    ("極めて", "すごく", "low", "文体の不統一（硬→軟）"),
]

ERRORS_BY_LEVEL = {
    "N5": ERRORS_N5,
    "N4": ERRORS_N4,
    "N3": ERRORS_N3,
    "N2": ERRORS_N2,
    "N1": ERRORS_N1,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. ERROR DENSITY per level
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ERROR_COUNT_RANGE = {
    "N5": (3, 6),
    "N4": (3, 5),
    "N3": (2, 4),
    "N2": (1, 3),
    "N1": (0, 2),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. GENERATION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def estimate_level_from_score(avg_score: float) -> str:
    if avg_score >= 85: return "N1"
    if avg_score >= 75: return "N2"
    if avg_score >= 60: return "N3"
    if avg_score >= 45: return "N4"
    return "N5"


def clamp(v: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(round(v))))


def score_for_level(level: str) -> dict[str, int]:
    """Base score ranges per JLPT level."""
    ranges = {
        "N5": (15, 40),
        "N4": (35, 55),
        "N3": (50, 70),
        "N2": (68, 85),
        "N1": (82, 95),
    }
    lo, hi = ranges[level]
    base = random.randint(lo, hi)
    variation = lambda: clamp(base + random.randint(-8, 8))
    return {
        "overall_score": clamp(base),
        "task_completion_score": variation(),
        "grammar_score": clamp(base - random.randint(5, 15)),
        "vocabulary_score": variation(),
        "coherence_score": clamp(base - random.randint(3, 10)),
        "naturalness_score": clamp(base - random.randint(5, 12)),
    }


def inject_errors(text: str, level: str) -> tuple[str, list[dict]]:
    """Inject errors into the text. Returns (corrupted_text, error_list)."""
    errors_pool = ERRORS_BY_LEVEL[level]
    lo, hi = ERROR_COUNT_RANGE[level]
    target = random.randint(lo, hi)
    target = min(target, len(errors_pool))

    applied_errors = []
    result = text
    available = list(errors_pool)
    random.shuffle(available)

    for search, replace, severity, explanation in available:
        if len(applied_errors) >= target:
            break
        if search == "（ダミー）":
            continue
        if search in result:
            result = result.replace(search, replace, 1)
            applied_errors.append({
                "source": search,
                "suggestion": replace,
                "explanation": explanation,
                "severity": severity,
            })

    return result, applied_errors


def generate_sample(topic: str, level: str) -> dict[str, Any]:
    """Generate one complete training sample (essay + scores + revision)."""
    template = random.choice(TEMPLATES_BY_LEVEL[level])
    clean_essay = template.format(topic=topic)

    # Inject errors
    corrupted, errors = inject_errors(clean_essay, level)

    # Compute scores (adjusted by error count & severity)
    severity_penalty = sum(
        8 if e["severity"] == "high" else 4 if e["severity"] == "medium" else 1
        for e in errors
    )
    base_scores = score_for_level(level)
    penalty = min(severity_penalty, 20)

    scores = {
        k: clamp(v - penalty if k in ("grammar_score", "naturalness_score", "coherence_score") else v)
        for k, v in base_scores.items()
    }

    avg_score = (scores["grammar_score"] + scores["vocabulary_score"] +
                 scores["coherence_score"] + scores["naturalness_score"]) / 4
    level_est = estimate_level_from_score(avg_score)

    # Build score output
    score_output = {
        "overall_score": scores["overall_score"],
        "task_completion_score": scores["task_completion_score"],
        "grammar_score": scores["grammar_score"],
        "vocabulary_score": scores["vocabulary_score"],
        "coherence_score": scores["coherence_score"],
        "naturalness_score": scores["naturalness_score"],
        "jlpt_fit_score": clamp(clamp(scores["overall_score"] - abs(
            "N5N4N3N2N1".index(level_est[1]) - "N5N4N3N2N1".index(level[1]) if level[1] in "54321" else 0
        ) * 3 + 5)),
        "level_estimate": level_est,
        "summary": f"「{topic}」について{level}レベルで書かれた作文。{len(errors)}箇所の誤用があり、全体的に{level_est}レベルの日本語力である。",
        "comments": f"「{topic}」の内容は理解できる。{'、'.join(e['explanation'] for e in errors[:3])}に注意して練習を続けよう。",
    }

    # Build revision output
    revision_issues = []
    sentence_suggestions = []

    for e in errors:
        rev = {
            "original": e["source"],
            "suggested": e["suggestion"],
            "reason": e["explanation"],
        }
        sentence_suggestions.append(rev)
        revision_issues.append({
            "source": e["source"],
            "suggestion": e["suggestion"],
            "explanation": e["explanation"],
            "severity": e["severity"],
        })

    revision_output = {
        "issues": revision_issues,
        "sentence_suggestions": sentence_suggestions,
        "full_revision": clean_essay,
        "revision_notes": f"修正内容のまとめ：{level}レベルの作文から{len(errors)}箇所の誤用を修正した。主な修正項目は{ '、'.join(e['explanation'] for e in errors[:5]) }など。",
    }

    return {
        "learner_essay": corrupted,
        "score_report": score_output,
        "revision_report": revision_output,
        "_meta": {
            "level": level,
            "topic": topic,
            "num_errors": len(errors),
            "errors": errors,
            "clean_essay": clean_essay,
        },
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. FORMATTING for training pipeline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def format_score_record(data: dict[str, Any], topic: str, level: str) -> dict:
    s = data["score_report"]
    return {
        "input": {"topic": topic, "target_level": level, "content": data["learner_essay"]},
        "output": {
            "overall_score": int(s["overall_score"]),
            "task_completion_score": int(s["task_completion_score"]),
            "grammar_score": int(s["grammar_score"]),
            "vocabulary_score": int(s["vocabulary_score"]),
            "coherence_score": int(s["coherence_score"]),
            "naturalness_score": int(s["naturalness_score"]),
            "jlpt_fit_score": int(s["jlpt_fit_score"]),
            "level_estimate": s["level_estimate"],
            "summary": s["summary"],
            "comments": s["comments"],
        },
    }


def format_revision_record(data: dict[str, Any], topic: str, level: str) -> dict:
    r = data["revision_report"]
    return {
        "input": {"topic": topic, "target_level": level, "content": data["learner_essay"]},
        "output": {
            "issues": r["issues"],
            "sentence_suggestions": r["sentence_suggestions"],
            "full_revision": r["full_revision"],
            "revision_notes": r["revision_notes"],
        },
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SAMPLE_DIST = {"N5": 100, "N4": 100, "N3": 120, "N2": 100, "N1": 80}
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "essay_processed"


def main(total: int = 500):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Scale distribution
    total_config = sum(SAMPLE_DIST.values())
    dist = {k: max(1, int(total * v / total_config)) for k, v in SAMPLE_DIST.items()}
    diff = total - sum(dist.values())
    if diff > 0:
        dist["N3"] += diff

    print(f"Generating {sum(dist.values())} samples ({total} target)")
    print(f"Distribution: {dist}")

    score_records = []
    revision_records = []
    seen = set()

    for level, count in dist.items():
        topics = LEVEL_TOPICS[level]
        success = 0
        attempts = 0
        while success < count and attempts < count * 3:
            attempts += 1
            topic = random.choice(topics)
            sample = generate_sample(topic, level)

            fp = hashlib.md5(sample["learner_essay"].encode()).hexdigest()
            if fp in seen:
                continue
            seen.add(fp)

            score_records.append(format_score_record(sample, topic, level))
            revision_records.append(format_revision_record(sample, topic, level))
            success += 1

        print(f"  {level}: {success}/{count} samples generated")

    # Sort deterministically
    score_records.sort(key=lambda r: hashlib.md5(r["input"]["content"].encode()).hexdigest())
    revision_records.sort(key=lambda r: hashlib.md5(r["input"]["content"].encode()).hexdigest())

    # Split 9:1
    split = max(1, len(score_records) // 10)

    def write_jsonl(records, name):
        path = OUTPUT_DIR / name
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  {name}: {len(records)} records")

    write_jsonl(score_records[split:], "score_train.jsonl")
    write_jsonl(score_records[:split], "score_eval.jsonl")
    write_jsonl(revision_records[split:], "revision_train.jsonl")
    write_jsonl(revision_records[:split], "revision_eval.jsonl")

    print(f"\nDone! {len(score_records)} paired samples -> {OUTPUT_DIR}")
    print("Ready for training: python training/train_score_lora.py")
    print("                    python training/train_revision_lora.py")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=500, help="Total samples to generate")
    args = parser.parse_args()
    main(args.samples)
