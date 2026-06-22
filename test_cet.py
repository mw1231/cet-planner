"""
CET Planner 集成测试
模拟首次使用流程：评估 → 生成计划 → 任务管理 → 进度报告
"""
import sys
import json
import random
from datetime import date, timedelta

sys.path.insert(0, "D:\\test_1")

from cet_planner.assessment import generate_test, conduct_assessment, load_question_bank
from cet_planner.plan_generator import generate_plan, get_recommended_materials
from cet_planner.storage import (
    load_profile, save_profile,
    load_plan, save_plan,
    load_tasks, save_tasks, load_tasks_for_date, save_task, batch_save_tasks,
    load_progress, append_progress_record,
)
from cet_planner.utils import progress_bar, format_date, today, LEVEL_NAMES, TASK_TYPE_LABELS

results = []
def log(msg):
    results.append(msg)
    print(msg)

log("=" * 60)
log("CET Planner 集成测试")
log("=" * 60)
log("")

# ── 测试 1: 题库加载 ──
log("[TEST 1] 题库加载...")
try:
    bank = load_question_bank()
    assert len(bank) >= 25, f"题库不足: {len(bank)} 题"
    vocab_count = sum(1 for q in bank if q["type"] == "vocabulary")
    grammar_count = sum(1 for q in bank if q["type"] == "grammar")
    log(f"  PASS: 共 {len(bank)} 题 (词汇 {vocab_count}, 语法 {grammar_count})")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 2: 测试卷生成 ──
log("[TEST 2] 测试卷生成（25 题分层抽样）...")
try:
    test_qs = generate_test(25)
    assert len(test_qs) == 25, f"题目数不对: {len(test_qs)}"
    types = {}
    for q in test_qs:
        types[q["type"]] = types.get(q["type"], 0) + 1
    log(f"  PASS: 词汇 {types.get('vocabulary', 0)}, 语法 {types.get('grammar', 0)}")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 3: 评分逻辑（模拟满分和零分） ──
log("[TEST 3] 评分逻辑...")
from cet_planner.assessment import _score_to_level, _estimate_vocabulary
try:
    assert _score_to_level(0) == 1
    assert _score_to_level(31) == 2
    assert _score_to_level(55) == 3
    assert _score_to_level(75) == 4
    assert _score_to_level(90) == 5
    log(f"  PASS: 分数→等级映射正确")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 4: 用户资料创建 ──
log("[TEST 4] 创建用户资料...")
try:
    profile = {
        "name": "测试用户",
        "target_exam": "CET-4",
        "level": 3,
        "available_days": 60,
        "start_date": today().isoformat(),
        "assessment_result": {
            "date": today().isoformat(),
            "raw_score": 58,
            "level": 3,
            "vocabulary_estimate": 3500,
            "strengths": ["词汇 (vocabulary)"],
            "weaknesses": ["语法 (grammar)"],
        },
    }
    save_profile(profile)
    loaded = load_profile()
    assert loaded["name"] == "测试用户"
    assert loaded["level"] == 3
    log(f"  PASS: 用户资料保存/加载正确")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 5: 学习计划生成 ──
log("[TEST 5] 生成学习计划...")
try:
    plan = generate_plan(profile)
    assert plan["exam_type"] == "CET-4"
    assert plan["total_weeks"] > 0
    assert len(plan["weeks"]) == plan["total_weeks"]
    assert all(len(w["days"]) == 7 for w in plan["weeks"])
    total_tasks = sum(len(d["tasks"]) for w in plan["weeks"] for d in w["days"])
    log(f"  PASS: {plan['total_weeks']} 周, 共 {total_tasks} 个任务")
    log(f"         目标词汇: {plan['target_vocabulary']}")
except Exception as e:
    log(f"  FAIL: {e}")
    import traceback; traceback.print_exc()

# ── 测试 6: 计划压缩（短备考时间） ──
log("[TEST 6] 短备考时间压缩...")
try:
    short_profile = dict(profile)
    short_profile["available_days"] = 15
    short_plan = generate_plan(short_profile)
    assert short_plan["total_weeks"] == 3  # ceil(15/7) = 3
    log(f"  PASS: 15 天 → {short_plan['total_weeks']} 周（已压缩）")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 7: 任务数据保存 ──
log("[TEST 7] 任务保存/加载...")
try:
    save_tasks({})
    all_tasks = []
    for w in plan["weeks"]:
        for d in w["days"]:
            all_tasks.extend(d["tasks"])
    batch_save_tasks(all_tasks)

    loaded_tasks = load_tasks()
    total_loaded = sum(len(v) for v in loaded_tasks.values())
    assert total_loaded == total_tasks, f"{total_loaded} != {total_tasks}"
    log(f"  PASS: {total_loaded} 个任务已保存")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 8: 今日任务 ──
log("[TEST 8] 今日任务查询...")
try:
    today_tasks = load_tasks_for_date(today().isoformat())
    assert len(today_tasks) > 0, "今日无任务"
    log(f"  PASS: 今日 {len(today_tasks)} 个任务")
    for i, t in enumerate(today_tasks, 1):
        log(f"         {i}. [{TASK_TYPE_LABELS.get(t['type'], t['type'])}] {t['description']}")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 9: 标记任务完成 ──
log("[TEST 9] 标记任务完成...")
try:
    task = today_tasks[0]
    task["completed"] = True
    task["completed_at"] = today().isoformat()
    save_task(task)

    reloaded = load_tasks_for_date(today().isoformat())
    found = [t for t in reloaded if t["id"] == task["id"]]
    assert found and found[0]["completed"], "任务未标记为完成"
    log(f"  PASS: 任务已标记为完成")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 10: 进度记录 ──
log("[TEST 10] 进度记录...")
try:
    append_progress_record({
        "date": today().isoformat(),
        "tasks_total": len(today_tasks),
        "tasks_completed": 1,
        "words_learned": 30,
        "words_reviewed": 0,
        "estimated_vocabulary": 3550,
        "streak_days": 1,
    })
    records = load_progress()
    assert len(records) > 0
    log(f"  PASS: 进度已记录 ({len(records)} 条)")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 11: 推荐资料 ──
log("[TEST 11] 推荐学习资料...")
try:
    materials = get_recommended_materials(3, "CET-4")
    assert len(materials) > 0
    log(f"  PASS: 推荐 {len(materials)} 本资料")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 测试 12: 计划保存/加载 ──
log("[TEST 12] 计划保存/加载...")
try:
    save_plan(plan)
    loaded_plan = load_plan()
    assert loaded_plan["total_weeks"] == plan["total_weeks"]
    log(f"  PASS: 计划序列化正确")
except Exception as e:
    log(f"  FAIL: {e}")

# ── 汇总 ──
log("")
log("=" * 60)
pass_count = results.count("  PASS:") - results.count("FAIL:")  # rough count
log(f"集成测试完成！")
log("=" * 60)

with open("D:\\test_1\\cet_planner\\user_data\\test_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print("\n测试结果已保存到 user_data/test_results.txt")
