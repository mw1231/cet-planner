"""
学习计划生成器 — 根据水平评估结果生成个性化周计划
"""
import math
import random
from datetime import date, timedelta

from .storage import load_static_json


def generate_plan(profile: dict) -> dict:
    """
    根据用户 profile 生成完整学习计划。

    profile 需包含: target_exam, level, available_days, start_date, assessment_result
    返回 LearningPlan dict
    """
    exam = profile["target_exam"]
    level = profile["level"]
    available_days = profile["available_days"]
    start_date = date.fromisoformat(profile["start_date"])

    templates = load_static_json("templates.json")
    vocab_data = load_static_json("vocabulary.json")

    # 1. 计算周数
    durations = templates["study_durations"][exam]
    recommended_weeks = durations[str(level)]
    requested_weeks = math.ceil(available_days / 7)

    if requested_weeks >= recommended_weeks:
        total_weeks = requested_weeks
        intensity = 1.0
    else:
        total_weeks = requested_weeks
        intensity = recommended_weeks / requested_weeks
        intensity = min(intensity, 2.5)  # 强度上限 2.5x

    # 2. 目标词汇量
    target_vocab = vocab_data["targets"][exam]
    current_vocab = 0
    if profile.get("assessment_result"):
        current_vocab = profile["assessment_result"].get("vocabulary_estimate", 1500)

    # 3. 选择周主题
    themes_pool = templates["weekly_themes"][exam]
    themes = _select_themes(themes_pool, total_weeks)

    # 4. 生成每周计划
    weeks = []
    for w in range(total_weeks):
        week_start = start_date + timedelta(weeks=w)
        week_end = week_start + timedelta(days=6)
        theme = themes[w]
        days = _generate_week(week_start, theme, level, intensity, templates)

        weeks.append({
            "week_number": w + 1,
            "theme": theme,
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat(),
            "days": days,
        })

    return {
        "exam_type": exam,
        "target_vocabulary": target_vocab,
        "total_weeks": total_weeks,
        "weeks": weeks,
    }


def _select_themes(pool: list, total_weeks: int) -> list:
    """选择周主题，不足时循环补充"""
    if total_weeks <= len(pool):
        return pool[:total_weeks]
    result = list(pool)
    for i in range(total_weeks - len(pool)):
        result.append(f"拓展训练 {i + 1}")
    return result


def _generate_week(week_start: date, theme: str, level: int,
                    intensity: float, templates: dict) -> list:
    """生成一周 7 天的计划"""
    vocab_data = load_static_json("vocabulary.json")
    quotas = vocab_data["daily_quotas"][str(level)]
    max_daily = vocab_data["max_daily"]

    # 按强度缩放每日词汇量
    new_words = min(int(quotas["new_words"] * intensity), max_daily["new_words"])
    review_words = min(int(quotas["review_words"] * intensity), max_daily["review_words"])

    skill_rotation = templates["skill_rotation"]
    ds = templates["daily_structure"]

    days = []
    for day_idx in range(7):
        day_date = week_start + timedelta(days=day_idx)
        tasks = []

        # -- 每日必做：词汇 --
        tasks.append({
            "id": f"{day_date.isoformat()}_vocab_new",
            "date": day_date.isoformat(),
            "type": "vocabulary",
            "description": f"学习 {new_words} 个新单词",
            "target_count": new_words,
            "completed": False,
            "completed_at": None,
            "notes": "",
        })
        tasks.append({
            "id": f"{day_date.isoformat()}_vocab_review",
            "date": day_date.isoformat(),
            "type": "vocabulary",
            "description": f"复习 {review_words} 个旧单词",
            "target_count": review_words,
            "completed": False,
            "completed_at": None,
            "notes": "",
        })

        # -- 技能训练（周日休息，只有复习）--
        if day_idx < 6:
            skill = skill_rotation[day_idx % len(skill_rotation)]
            skill_task = _build_skill_task(skill, level, day_date, ds)
            tasks.append(skill_task)
        else:
            # 周日综合复习
            tasks.append({
                "id": f"{day_date.isoformat()}_review",
                "date": day_date.isoformat(),
                "type": "review",
                "description": ds["review"]["description"],
                "target_count": 1,
                "completed": False,
                "completed_at": None,
                "notes": "",
            })

        days.append({
            "date": day_date.isoformat(),
            "day_of_week": day_idx,
            "tasks": tasks,
        })

    return days


def _build_skill_task(skill: str, level: int, d: date, ds: dict) -> dict:
    """构建一个技能训练任务"""
    skill_cfg = ds.get(skill, {})

    if skill == "listening":
        minutes = skill_cfg.get("duration_minutes", 30)
        material = random.choice(skill_cfg.get("materials", ["英语听力素材"]))
        desc = f"听力训练 {minutes} 分钟，素材：{material}"
        target = minutes

    elif skill == "reading":
        count = skill_cfg.get("count", 2)
        desc = f"阅读 {count} 篇短文并完成理解题"
        target = count

    elif skill == "writing":
        wc = skill_cfg.get("word_count", 150)
        topic = random.choice(skill_cfg.get("topics", ["自选主题"]))
        desc = f"写一篇 {wc} 词短文，主题：{topic}"
        target = wc

    elif skill == "translation":
        count = skill_cfg.get("count", 5)
        desc = f"翻译 {count} 个句子（汉译英），注重语法准确度"
        target = count

    else:
        desc = f"{skill} 训练"
        target = 1

    return {
        "id": f"{d.isoformat()}_skill",
        "date": d.isoformat(),
        "type": skill,
        "description": desc,
        "target_count": target,
        "completed": False,
        "completed_at": None,
        "notes": "",
    }


def get_recommended_materials(level: int, exam: str) -> list:
    """根据水平和目标考试推荐学习资料"""
    recs = []

    if level <= 2:
        recs.append("《新概念英语 2》— 巩固基础语法和词汇")
        recs.append("VOA 慢速英语 — 每日听力入门")
        recs.append("四级词汇闪过 — 高频词优先记忆")

    elif level == 3:
        if exam == "CET-4":
            recs.append("《星火英语四级真题》— 近 5 年真题精练")
            recs.append("四级词汇词根+联想记忆法")
            recs.append("BBC 6 Minute English — 中等难度听力")
        else:
            recs.append("六级词汇 3000 核心词")
            recs.append("TED-Ed 短演讲 — 学术听力训练")

    else:
        if exam == "CET-4":
            recs.append("四级真题模拟卷 — 限时训练")
            recs.append("China Daily 双语新闻 — 翻译素材")
        else:
            recs.append("《星火英语六级真题》— 近 5 年真题精练")
            recs.append("六级翻译专项训练 100 篇")
            recs.append("The Economist 短文章 — 高阶阅读")

    recs.append("每日英语听力 App — 泛听素材")
    recs.append("墨墨背单词 / 不背单词 App — 碎片时间记词")
    return recs
