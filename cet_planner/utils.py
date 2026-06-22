"""
工具函数 — 日期计算、终端输出、常量
"""
import os
from datetime import date, datetime, timedelta


# ── 日期工具 ────────────────────────────────────────────

def today() -> date:
    """返回今天日期"""
    return date.today()


def format_date(d: date) -> str:
    """格式化日期为中文可读形式"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    wd = weekdays[d.weekday()]
    return f"{d.isoformat()} ({wd})"


def week_range(start_date: date, week_num: int) -> tuple:
    """返回第 week_num 周的起止日期（week_num 从 1 开始）"""
    ws = start_date + timedelta(weeks=week_num - 1)
    we = ws + timedelta(days=6)
    return ws, we


def days_between(d1: date, d2: date) -> int:
    return (d2 - d1).days


# ── 终端输出 ────────────────────────────────────────────

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str):
    width = 56
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    print()


def print_section(title: str):
    print(f"\n  [{title}]")
    print("  " + "-" * 52)


def print_success(msg: str):
    print(f"  [OK] {msg}")


def print_warning(msg: str):
    print(f"  [!!] {msg}")


def print_info(msg: str):
    print(f"  [i]  {msg}")


def print_task_line(task, index: int = None):
    """格式化输出一个任务行"""
    prefix = f"  {index})" if index else "   -"
    status = "[x]" if task.completed else "[ ]"
    print(f"  {status} {prefix} {task.description}")


def confirm(prompt: str) -> bool:
    """询问用户确认"""
    ans = input(f"  {prompt} (y/n): ").strip().lower()
    return ans in ("y", "yes")


def press_enter():
    input("\n  按 Enter 继续...")


# ── 进度显示 ────────────────────────────────────────────

def progress_bar(percent: float, width: int = 30) -> str:
    """ASCII 进度条"""
    filled = int(width * percent / 100)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {percent:.0f}%"


def sparkline(values: list, width: int = 30) -> str:
    """ASCII 迷你趋势图"""
    if not values or len(values) < 2:
        return ""
    mn, mx = min(values), max(values)
    if mx == mn:
        mx = mn + 1
    chars = "▁▂▃▄▅▆▇█"
    result = []
    for v in values:
        idx = int((v - mn) / (mx - mn) * (len(chars) - 1))
        result.append(chars[idx])
    return "".join(result)


# ── 字符串格式化 ────────────────────────────────────────

def fit(s: str, width: int) -> str:
    """字符串截断或补齐到 width"""
    if len(s) > width:
        return s[:width - 1] + "..."
    return s.ljust(width)


# ── 常量 ────────────────────────────────────────────────

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

TASK_TYPE_LABELS = {
    "vocabulary": "词汇",
    "listening": "听力",
    "reading": "阅读",
    "writing": "写作",
    "translation": "翻译",
    "review": "复习",
    "mini_test": "小测",
}

LEVEL_NAMES = {
    1: "入门 (Beginner)",
    2: "初级 (Elementary)",
    3: "中级 (Intermediate)",
    4: "中高级 (Upper-Intermediate)",
    5: "高级 (Advanced)",
}
