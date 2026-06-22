"""
CET Planner CLI — 四六级复习规划小程序入口

用法: python -m cet_planner <command> [options]
"""
import argparse
import sys
from datetime import date, timedelta

from . import __version__
from .assessment import generate_test, conduct_assessment, display_result
from .plan_generator import generate_plan, get_recommended_materials
from .storage import (
    load_profile, save_profile,
    load_plan, save_plan,
    load_tasks, save_tasks, load_tasks_for_date, save_task, batch_save_tasks,
    load_progress, append_progress_record,
)
from .utils import (
    clear_screen, print_header, print_section, print_success,
    print_warning, print_info, print_task_line,
    confirm, press_enter, progress_bar, format_date, today,
    LEVEL_NAMES, TASK_TYPE_LABELS,
)


def main():
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 路由到对应命令
    commands = {
        "start": cmd_start,
        "assess": cmd_assess,
        "today": cmd_today,
        "done": cmd_done,
        "undo": cmd_undo,
        "week": cmd_week,
        "progress": cmd_progress,
        "report": cmd_report,
        "adjust": cmd_adjust,
        "info": cmd_info,
    }

    if args.command in commands:
        commands[args.command](args)


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="cet_planner",
        description="CET 四六级复习规划小程序 v" + __version__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
命令:
  start       首次使用：水平评估 + 生成学习计划
  assess      重新进行水平评估
  today       查看今日任务清单
  done  <id>  标记任务完成
  undo  <id>  取消任务完成状态
  week [n]    查看第 n 周计划（默认当前周）
  progress    查看学习进度总览
  report      生成详细进度报告
  adjust      调整备考天数并重新生成计划
  info        查看个人资料和计划摘要
        """,
    )
    parser.add_argument("command", nargs="?", help="执行的命令")
    parser.add_argument("arg", nargs="?", help="命令参数 (如任务 ID)")
    parser.add_argument("--name", help="你的名字")
    parser.add_argument("--exam", choices=["CET-4", "CET-6"], help="目标考试")
    parser.add_argument("--days", type=int, help="距离考试的天数")
    parser.add_argument("--version", action="version",
                        version=f"cet_planner v{__version__}")
    return parser


# ═══════════════════════════════════════════════════════════
#  命令实现
# ═══════════════════════════════════════════════════════════

def cmd_start(args):
    """首次使用向导"""
    clear_screen()
    print_header("欢迎使用 CET 四六级复习规划小程序")
    print_info("让我们先了解你的基本情况，然后做一个快速水平测试")
    print()

    # 收集用户信息
    name = args.name or input("  你的名字: ").strip()
    if not name:
        name = "同学"

    if args.exam:
        exam = args.exam
    else:
        print("\n  目标考试:")
        print("    1. CET-4 (四级)")
        print("    2. CET-6 (六级)")
        choice = input("\n  请选择 (1/2): ").strip()
        exam = "CET-4" if choice == "2" else "CET-4"  # 默认四级

    if args.days:
        days = args.days
    else:
        print("\n  你计划备考多长时间？")
        print("    建议: 1-6 个月 (30-180 天)")
        try:
            days = int(input("  天数: ").strip() or "90")
        except ValueError:
            days = 90

    # 开始评估
    questions = generate_test(25)
    result = conduct_assessment(questions)
    display_result(result)

    # 构建 profile
    profile = {
        "name": name,
        "target_exam": exam,
        "level": result["level"],
        "available_days": days,
        "start_date": today().isoformat(),
        "assessment_result": result,
    }

    # 显示建议
    from .utils import LEVEL_NAMES
    print(f"  你的水平: {LEVEL_NAMES.get(result['level'], '未知')}")
    print(f"  目标考试: {exam}")
    print(f"  备考天数: {days} 天")
    print()

    # 推荐资料
    print_section("推荐学习资料")
    materials = get_recommended_materials(result["level"], exam)
    for m in materials:
        print(f"  - {m}")

    print()
    if not confirm("是否根据以上信息生成学习计划？"):
        print_info("已取消。可稍后运行 cet_planner start 重新开始。")
        return

    # 生成计划
    plan = generate_plan(profile)
    save_profile(profile)

    # 批量保存初始任务（先清空旧任务避免重复）
    save_tasks({})
    all_tasks = []
    for week in plan["weeks"]:
        for day in week["days"]:
            all_tasks.extend(day["tasks"])
    batch_save_tasks(all_tasks)
    save_plan(plan)

    # 初始化第一天的进度记录
    today_tasks = [t for t in all_tasks if t["date"] == today().isoformat()]
    append_progress_record({
        "date": today().isoformat(),
        "tasks_total": len(today_tasks),
        "tasks_completed": 0,
        "words_learned": 0,
        "words_reviewed": 0,
        "estimated_vocabulary": result["vocabulary_estimate"],
        "streak_days": 0,
    })

    # 显示计划摘要
    clear_screen()
    print_header("学习计划已生成！")
    print(f"  总周数:     {plan['total_weeks']} 周")
    print(f"  目标词汇:   {plan['target_vocabulary']} 词")
    print(f"  当前词汇:   ~{result['vocabulary_estimate']} 词")
    print()
    print("  周计划概览:")
    for w in plan["weeks"]:
        print(f"    第 {w['week_number']:2d} 周 | {w['start_date']} ~ {w['end_date']} | {w['theme']}")
    print()
    print_info("运行 'cet_planner today' 查看今日任务")
    print_info("运行 'cet_planner info' 查看完整计划")


def cmd_assess(args):
    """重新评估水平"""
    profile = load_profile()
    if not profile:
        print_warning("尚未创建学习计划，请先运行: cet_planner start")
        return

    print_info("重新进行水平评估...")
    questions = generate_test(25)
    result = conduct_assessment(questions)
    display_result(result)

    print(f"  上次评估: {profile.get('assessment_result', {}).get('level', '?')} 级")
    print(f"  本次评估: {result['level']} 级")
    print()

    if confirm("是否用新评估结果更新学习计划？"):
        profile["level"] = result["level"]
        profile["assessment_result"] = result
        save_profile(profile)

        new_plan = generate_plan(profile)
        save_plan(new_plan)

        # 重新批量保存任务
        all_tasks = []
        for week in new_plan["weeks"]:
            for day in week["days"]:
                all_tasks.extend(day["tasks"])
        save_tasks({})  # 清空旧任务
        batch_save_tasks(all_tasks)

        print_success("学习计划已更新！")


def cmd_today(args):
    """查看今日任务"""
    profile = load_profile()
    plan = load_plan()
    if not profile or not plan:
        print_warning("请先运行: cet_planner start")
        return

    t = today()
    tasks = load_tasks_for_date(t.isoformat())

    # 如果 tasks.json 为空但 plan 有数据，从 plan 恢复
    if not tasks:
        for week in plan["weeks"]:
            for day in week["days"]:
                if day["date"] == t.isoformat():
                    tasks = day["tasks"]
                    break

    # 找到当前第几周
    week_num = _current_week_num(plan)

    clear_screen()
    print_header("今日任务")
    print(f"  {format_date(t)}")
    print(f"  第 {week_num} 周 | 第 {_day_of_plan(plan)} 天 / 共 {plan['total_weeks'] * 7} 天")
    print()

    # 按 ID 去重（防止历史数据导致的重复任务）
    seen = set()
    deduped = []
    for t in tasks:
        if t["id"] not in seen:
            seen.add(t["id"])
            deduped.append(t)
    tasks = deduped

    if not tasks:
        print_info("今天没有安排任务。休息一下或复习之前的内容吧！")
        return

    completed = sum(1 for t in tasks if t.get("completed"))
    total = len(tasks)

    for i, task in enumerate(tasks, 1):
        _print_one_task(task, i)

    print()
    pct = completed / total * 100 if total > 0 else 0
    print(f"  完成: {completed}/{total}  {progress_bar(pct)}")

    # 打卡
    streak = _get_streak()
    print(f"  连续打卡: {streak} 天")

    # 提示下一步
    if completed < total:
        print()
        print_info("运行 cet_planner done <序号> 标记完成任务")


def cmd_done(args):
    """标记任务完成"""
    task_id = args.arg
    if not task_id:
        print_warning("请指定任务 ID，例如: cet_planner done 2026-06-22_vocab_new")
        print_info("也可以使用序号，如: cet_planner done 1")
        return

    profile = load_profile()
    if not profile:
        print_warning("请先运行: cet_planner start")
        return

    t = today()
    tasks = load_tasks_for_date(t.isoformat())

    if not tasks:
        print_warning("今日无任务")
        return

    # 支持序号
    try:
        idx = int(task_id) - 1
        if 0 <= idx < len(tasks):
            task_id = tasks[idx]["id"]
    except ValueError:
        pass

    # 查找并更新
    updated = False
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            task["completed_at"] = t.isoformat()
            updated = True
            print_success(f"任务已完成: {task['description']}")
            break

    if not updated:
        print_warning(f"未找到任务: {task_id}")
        return

    save_task(task)
    _update_progress(tasks)
    _show_quick_status(tasks)


def cmd_undo(args):
    """取消任务完成状态"""
    task_id = args.arg
    if not task_id:
        print_warning("请指定任务 ID")
        return

    t = today()
    tasks = load_tasks_for_date(t.isoformat())

    try:
        idx = int(task_id) - 1
        if 0 <= idx < len(tasks):
            task_id = tasks[idx]["id"]
    except ValueError:
        pass

    updated = False
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = False
            task["completed_at"] = None
            updated = True
            print_success(f"已取消完成: {task['description']}")
            break

    if not updated:
        print_warning(f"未找到任务: {task_id}")
        return

    save_task(task)
    _update_progress(tasks)


def cmd_week(args):
    """查看周计划"""
    profile = load_profile()
    plan = load_plan()
    if not profile or not plan:
        print_warning("请先运行: cet_planner start")
        return

    # 确定查看哪一周
    if args.arg:
        try:
            week_num = int(args.arg)
        except ValueError:
            print_warning(f"无效的周号: {args.arg}")
            return
    else:
        week_num = _current_week_num(plan)

    if week_num < 1 or week_num > plan["total_weeks"]:
        print_warning(f"周号超出范围: 1-{plan['total_weeks']}")
        return

    week = plan["weeks"][week_num - 1]

    clear_screen()
    print_header(f"第 {week_num} 周计划")
    print(f"  主题: {week['theme']}")
    print(f"  日期: {week['start_date']} ~ {week['end_date']}")
    print()

    for day in week["days"]:
        tasks = load_tasks_for_date(day["date"])
        if not tasks:
            tasks = day.get("tasks", [])

        d = date.fromisoformat(day["date"])
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        day_name = day_names[d.weekday()]
        print(f"  {day['date']} {day_name}:")

        if not tasks:
            print("     (休息)")
        else:
            for task in tasks:
                status = "[x]" if task.get("completed") else "[ ]"
                print(f"    {status} {task['description']}")
        print()


def cmd_progress(args):
    """查看进度总览"""
    profile = load_profile()
    plan = load_plan()
    if not profile or not plan:
        print_warning("请先运行: cet_planner start")
        return

    records = load_progress()
    all_tasks = load_tasks()

    # 全局统计
    total_tasks = sum(len(v) for v in all_tasks.values())
    completed_tasks = sum(
        sum(1 for t in v if t.get("completed")) for v in all_tasks.values()
    )

    # 周完成率
    week_num = _current_week_num(plan)
    if week_num <= len(plan["weeks"]):
        week = plan["weeks"][week_num - 1]
        week_tasks_all = 0
        week_tasks_done = 0
        for day in week["days"]:
            ts = load_tasks_for_date(day["date"])
            week_tasks_all += len(ts)
            week_tasks_done += sum(1 for t in ts if t.get("completed"))
    else:
        week_tasks_all = week_tasks_done = 0

    # 词汇进度
    current_vocab = _estimate_vocab_now(profile, records)
    target_vocab = plan["target_vocabulary"]
    vocab_pct = min(current_vocab / target_vocab * 100, 100) if target_vocab else 0

    # 时间进度
    elapsed = (today() - date.fromisoformat(profile["start_date"])).days
    total_days = plan["total_weeks"] * 7
    time_pct = min(elapsed / total_days * 100, 100) if total_days else 0

    clear_screen()
    print_header("学习进度总览")
    print(f"  备考进度: {progress_bar(time_pct)}   ({elapsed}/{total_days} 天)")
    print(f"  词汇进度: {progress_bar(vocab_pct)}   (~{current_vocab}/{target_vocab} 词)")
    print()

    print(f"  任务完成: {completed_tasks}/{total_tasks}  ({completed_tasks / max(total_tasks, 1) * 100:.0f}%)")
    if week_tasks_all:
        print(f"  本周完成: {week_tasks_done}/{week_tasks_all}  ({week_tasks_done / max(week_tasks_all, 1) * 100:.0f}%)")
    print(f"  连续打卡: {_get_streak_from_records(records)} 天")
    print(f"  当前词汇量: ~{current_vocab} 词")

    # 状态判断
    if vocab_pct >= time_pct:
        print_success("进度正常，保持节奏！")
    else:
        print_warning("词汇进度落后于时间进度，建议加强学习强度")

    # 趋势图
    if len(records) >= 5:
        print_section("近 7 日完成趋势")
        recent = records[-7:]
        vals = [r["tasks_completed"] for r in recent]
        labels = "  ".join(f"{r['date'][-5:]}:{r['tasks_completed']}" for r in recent)
        print(f"  {labels}")
        from .utils import sparkline
        print(f"  {sparkline(vals)}")


def cmd_report(args):
    """详细报告"""
    profile = load_profile()
    plan = load_plan()
    if not profile or not plan:
        print_warning("请先运行: cet_planner start")
        return

    records = load_progress()
    all_tasks = load_tasks()

    today_str = today().isoformat()
    total_tasks = sum(len(v) for v in all_tasks.values())
    completed_tasks = sum(
        sum(1 for t in v if t.get("completed")) for v in all_tasks.values()
    )
    current_vocab = _estimate_vocab_now(profile, records)
    target_vocab = plan["target_vocabulary"]
    streak = _get_streak_from_records(records)

    elapsed = (today() - date.fromisoformat(profile["start_date"])).days
    total_days = plan["total_weeks"] * 7
    days_left = max(total_days - elapsed, 0)

    clear_screen()
    print_header("详细进度报告")
    print(f"  生成日期: {today_str}")
    print(f"  用户: {profile['name']}")
    print(f"  目标: {profile['target_exam']}")
    print(f"  水平: {LEVEL_NAMES.get(profile['level'], '未知')}")
    print()

    print_section("时间统计")
    print(f"  已过天数:    {elapsed}")
    print(f"  剩余天数:    {days_left}")
    print(f"  完成比例:    {elapsed / max(total_days, 1) * 100:.0f}%")
    print()

    print_section("任务统计")
    print(f"  总任务数:    {total_tasks}")
    print(f"  已完成:      {completed_tasks}")
    print(f"  完成率:      {completed_tasks / max(total_tasks, 1) * 100:.1f}%")
    print(f"  连续打卡:    {streak} 天")
    print()

    print_section("词汇统计")
    print(f"  起始词汇:    ~{profile.get('assessment_result', {}).get('vocabulary_estimate', 1500)} 词")
    print(f"  当前词汇:    ~{current_vocab} 词")
    print(f"  目标词汇:    {target_vocab} 词")
    print(f"  词汇进度:    {progress_bar(min(current_vocab / max(target_vocab, 1) * 100, 100))}")
    print()

    # 按题型统计
    print_section("各题型完成情况")
    type_counts = {}
    for date_tasks in all_tasks.values():
        for t in date_tasks:
            tp = t.get("type", "unknown")
            if tp not in type_counts:
                type_counts[tp] = {"total": 0, "done": 0}
            type_counts[tp]["total"] += 1
            if t.get("completed"):
                type_counts[tp]["done"] += 1

    for tp, counts in type_counts.items():
        label = TASK_TYPE_LABELS.get(tp, tp)
        pct = counts["done"] / max(counts["total"], 1) * 100
        bar = progress_bar(pct, 20)
        print(f"  {label:6s} {bar}  {counts['done']}/{counts['total']}")
    print()

    # 评估
    print_section("整体评价")
    overall = completed_tasks / max(total_tasks, 1) * 100
    if overall >= 80:
        print_success("表现优异！继续保持当前节奏。")
    elif overall >= 60:
        print_info("进度良好，但仍有提升空间。")
    elif overall >= 40:
        print_warning("进度偏慢，建议增加每日学习时间。")
    else:
        print_warning("进度严重落后，请重新评估你的学习计划。")

    if streak >= 30:
        print_success(f"连续打卡 {streak} 天，非常棒！")


def cmd_adjust(args):
    """调整备考天数"""
    profile = load_profile()
    if not profile:
        print_warning("请先运行: cet_planner start")
        return

    print(f"  当前备考天数: {profile['available_days']} 天")

    if args.days:
        new_days = args.days
    else:
        try:
            new_days = int(input("  新的备考天数: ").strip() or "90")
        except ValueError:
            new_days = 90

    if new_days <= 0:
        print_warning("天数必须大于 0")
        return

    profile["available_days"] = new_days
    save_profile(profile)

    new_plan = generate_plan(profile)
    save_plan(new_plan)

    save_tasks({})
    all_tasks = []
    for week in new_plan["weeks"]:
        for day in week["days"]:
            all_tasks.extend(day["tasks"])
    batch_save_tasks(all_tasks)

    clear_screen()
    print_header("计划已更新")
    print_success(f"备考天数已更新为 {new_days} 天")
    print(f"  总周数: {new_plan['total_weeks']} 周")
    print()
    print_info("运行 'cet_planner week' 查看新计划")


def cmd_info(args):
    """显示个人资料和计划摘要"""
    profile = load_profile()
    plan = load_plan()
    if not profile or not plan:
        print_warning("请先运行: cet_planner start")
        return

    clear_screen()
    print_header("个人资料")
    print(f"  姓名:       {profile['name']}")
    print(f"  目标考试:   {profile['target_exam']}")
    print(f"  当前水平:   {LEVEL_NAMES.get(profile['level'], '?')}")
    print(f"  备考天数:   {profile['available_days']} 天")
    print(f"  开始日期:   {profile['start_date']}")

    ar = profile.get("assessment_result", {})
    if ar:
        print(f"  评估得分:   {ar.get('raw_score', '?')}/100")
        print(f"  词汇量估算: ~{ar.get('vocabulary_estimate', '?')} 词")
    print()

    print_section("学习计划")
    print(f"  总周数:     {plan['total_weeks']} 周")
    print(f"  目标词汇:   {plan['target_vocabulary']} 词")
    print()

    week_num = _current_week_num(plan)
    for w in plan["weeks"]:
        marker = " ← 当前" if w["week_number"] == week_num else ""
        print(f"  第 {w['week_number']:2d} 周 | {w['start_date']} ~ {w['end_date']} | {w['theme']}{marker}")
    print()


# ═══════════════════════════════════════════════════════════
#  内部辅助函数
# ═══════════════════════════════════════════════════════════

def _print_one_task(task, index=None):
    """打印单个任务"""
    prefix = f"  {index}." if index else "   "
    status = "[x]" if task.get("completed") else "[ ]"
    print(f"  {status} {prefix} {task['description']}")


def _current_week_num(plan: dict) -> int:
    """计算当前处于第几周"""
    start = date.fromisoformat(plan["weeks"][0]["start_date"])
    elapsed = (today() - start).days
    week = elapsed // 7 + 1
    return max(1, min(week, plan["total_weeks"]))


def _day_of_plan(plan: dict) -> int:
    """计算当前是计划的第几天"""
    start = date.fromisoformat(plan["weeks"][0]["start_date"])
    elapsed = (today() - start).days + 1
    return max(1, elapsed)


def _update_progress(tasks: list) -> None:
    """根据今日任务完成情况更新进度记录"""
    profile = load_profile()
    records = load_progress()

    t = today()
    completed = sum(1 for task in tasks if task.get("completed"))
    total = len(tasks)

    words_new = sum(
        task["target_count"] for task in tasks
        if task.get("type") == "vocabulary" and "new" in task.get("id", "")
        and task.get("completed")
    )
    words_review = sum(
        task["target_count"] for task in tasks
        if task.get("type") == "vocabulary" and "review" in task.get("id", "")
        and task.get("completed")
    )

    current_vocab = _estimate_vocab_now(profile, records)
    new_vocab = current_vocab + int((words_new + words_review * 0.3) * 0.7)

    streak = _get_streak_from_records(records)
    if completed > 0:
        streak += 1
    else:
        streak = 0

    append_progress_record({
        "date": t.isoformat(),
        "tasks_total": total,
        "tasks_completed": completed,
        "words_learned": words_new,
        "words_reviewed": words_review,
        "estimated_vocabulary": new_vocab,
        "streak_days": streak,
    })


def _estimate_vocab_now(profile: dict, records: list) -> int:
    """估算当前词汇量"""
    base = 1500
    if profile.get("assessment_result"):
        base = profile["assessment_result"].get("vocabulary_estimate", 1500)
    if records:
        learned = sum(r.get("words_learned", 0) for r in records) * 0.7
        reviewed = sum(r.get("words_reviewed", 0) for r in records) * 0.3 * 0.7
        return base + int(learned + reviewed)
    return base


def _get_streak() -> int:
    records = load_progress()
    return _get_streak_from_records(records)


def _get_streak_from_records(records: list) -> int:
    """从进度记录中计算连续打卡天数"""
    if not records:
        return 0

    streak = 0
    check = today()
    for r in reversed(records):
        try:
            rd = date.fromisoformat(r["date"])
        except (ValueError, KeyError):
            continue
        if rd == check and r.get("tasks_completed", 0) > 0:
            streak += 1
            check -= timedelta(days=1)
        elif rd < check:
            break
    return streak


def _show_quick_status(tasks: list) -> None:
    """快速显示今日任务状态"""
    completed = sum(1 for t in tasks if t.get("completed"))
    total = len(tasks)
    print()
    print(f"  今日进度: {completed}/{total}  {progress_bar(completed / max(total, 1) * 100)}")


# ── 入口 ────────────────────────────────────────────────

if __name__ == "__main__":
    main()
