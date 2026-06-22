"""
JSON 持久化层 — 读写用户数据
"""
import json
import os
from pathlib import Path
from typing import Optional, Any

# 项目根目录 (cet_planner/)
ROOT_DIR = Path(__file__).resolve().parent
USER_DATA_DIR = ROOT_DIR / "user_data"


def ensure_user_data_dir() -> Path:
    """确保 user_data 目录存在"""
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return USER_DATA_DIR


def _path(filename: str) -> Path:
    return USER_DATA_DIR / filename


def _load_json(filepath: Path) -> Optional[dict]:
    """加载 JSON 文件，不存在返回 None"""
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(filepath: Path, data: Any) -> None:
    """保存 JSON 文件，使用临时文件 + 重命名确保原子写入"""
    ensure_user_data_dir()
    tmp = filepath.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, filepath)


# ── Profile ──────────────────────────────────────────────

def load_profile() -> Optional[dict]:
    return _load_json(_path("profile.json"))


def save_profile(profile: dict) -> None:
    _save_json(_path("profile.json"), profile)


# ── Learning Plan ────────────────────────────────────────

def load_plan() -> Optional[dict]:
    return _load_json(_path("plan.json"))


def save_plan(plan: dict) -> None:
    _save_json(_path("plan.json"), plan)


# ── Tasks ────────────────────────────────────────────────

def load_tasks() -> dict:
    """返回 {date_str: [task_dict, ...]}"""
    data = _load_json(_path("tasks.json"))
    return data if data else {}


def save_tasks(tasks: dict) -> None:
    _save_json(_path("tasks.json"), tasks)


def load_tasks_for_date(date_str: str) -> list:
    all_tasks = load_tasks()
    return all_tasks.get(date_str, [])


def save_task(task: dict) -> None:
    """保存单个任务（按日期归类）"""
    all_tasks = load_tasks()
    date_str = task["date"]
    if date_str not in all_tasks:
        all_tasks[date_str] = []

    # 查找并更新 或 追加
    updated = False
    for i, t in enumerate(all_tasks[date_str]):
        if t["id"] == task["id"]:
            all_tasks[date_str][i] = task
            updated = True
            break
    if not updated:
        all_tasks[date_str].append(task)

    save_tasks(all_tasks)


def batch_save_tasks(task_dicts: list) -> None:
    """批量保存任务"""
    all_tasks = load_tasks()
    for task in task_dicts:
        date_str = task["date"]
        if date_str not in all_tasks:
            all_tasks[date_str] = []
        all_tasks[date_str].append(task)
    save_tasks(all_tasks)


# ── Progress ─────────────────────────────────────────────

def load_progress() -> list:
    data = _load_json(_path("progress.json"))
    return data if data else []


def save_progress(records: list) -> None:
    _save_json(_path("progress.json"), records)


def append_progress_record(record: dict) -> None:
    records = load_progress()
    # 同一天的记录覆盖
    records = [r for r in records if r["date"] != record["date"]]
    records.append(record)
    records.sort(key=lambda r: r["date"])
    save_progress(records)


# ── 静态数据加载 ─────────────────────────────────────────

def load_static_json(filename: str) -> dict:
    """加载 data/ 目录下的 JSON 文件"""
    filepath = ROOT_DIR / "data" / filename
    if not filepath.exists():
        raise FileNotFoundError(f"数据文件缺失: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
