"""
数据模型定义 — 所有 dataclass 集中管理
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExamType(Enum):
    CET4 = "CET-4"
    CET6 = "CET-6"

    def __str__(self):
        return self.value


class TaskType(Enum):
    VOCABULARY = "vocabulary"
    LISTENING = "listening"
    READING = "reading"
    WRITING = "writing"
    TRANSLATION = "translation"
    REVIEW = "review"
    MINI_TEST = "mini_test"

    def label(self):
        labels = {
            "vocabulary": "词汇",
            "listening": "听力",
            "reading": "阅读",
            "writing": "写作",
            "translation": "翻译",
            "review": "复习",
            "mini_test": "小测",
        }
        return labels.get(self.value, self.value)


class QuestionType(Enum):
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"


@dataclass
class Question:
    id: str
    type: str               # "vocabulary" or "grammar"
    difficulty: int         # 1-5
    stem: str
    options: list           # exactly 4 strings
    answer: int             # index 0-3
    explanation: str


@dataclass
class AssessmentResult:
    date: str               # ISO date
    raw_score: int          # 0-100
    level: int              # 1-5
    vocabulary_estimate: int
    strengths: list         # e.g. ["vocabulary"]
    weaknesses: list        # e.g. ["grammar"]


@dataclass
class UserProfile:
    name: str
    target_exam: str        # "CET-4" or "CET-6"
    level: int              # 1-5
    available_days: int
    start_date: str         # ISO date
    assessment_result: Optional[dict] = None


@dataclass
class Task:
    id: str                 # e.g. "2026-06-22_vocab_new"
    date: str               # ISO date
    type: str               # TaskType value
    description: str
    target_count: int
    completed: bool = False
    completed_at: Optional[str] = None
    notes: str = ""


@dataclass
class DayPlan:
    date: str
    day_of_week: int        # 0=Monday
    tasks: list = field(default_factory=list)


@dataclass
class WeekPlan:
    week_number: int
    theme: str
    start_date: str
    end_date: str
    days: list = field(default_factory=list)


@dataclass
class LearningPlan:
    exam_type: str
    target_vocabulary: int
    total_weeks: int
    weeks: list = field(default_factory=list)


@dataclass
class ProgressRecord:
    date: str
    tasks_total: int
    tasks_completed: int
    words_learned: int
    words_reviewed: int
    estimated_vocabulary: int
    streak_days: int
