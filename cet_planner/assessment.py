"""
水平测试引擎 — 题目抽样、交互式测试、评分
"""
import random
from datetime import date

from .storage import load_static_json
from .utils import clear_screen, print_header, print_info


def load_question_bank() -> list:
    """加载评估题库"""
    data = load_static_json("questions.json")
    return data["questions"]


def generate_test(num_questions: int = 25) -> list:
    """
    分层随机抽样生成测试卷
    - 60% 词汇 (15题), 40% 语法 (10题)
    - 难度分布: 20% easy(1-2), 50% medium(3), 30% hard(4-5)
    """
    all_qs = load_question_bank()
    vocab_qs = [q for q in all_qs if q["type"] == "vocabulary"]
    grammar_qs = [q for q in all_qs if q["type"] == "grammar"]

    target_vocab = int(num_questions * 0.6)
    target_grammar = num_questions - target_vocab

    def stratified_sample(pool, count):
        easy = [q for q in pool if q["difficulty"] <= 2]
        medium = [q for q in pool if q["difficulty"] == 3]
        hard = [q for q in pool if q["difficulty"] >= 4]

        n_easy = max(1, int(count * 0.2))
        n_medium = max(1, int(count * 0.5))
        n_hard = count - n_easy - n_medium

        result = []
        result.extend(random.sample(easy, min(n_easy, len(easy))))
        result.extend(random.sample(medium, min(n_medium, len(medium))))
        result.extend(random.sample(hard, min(n_hard, len(hard))))

        # 补齐不足
        remaining = [q for q in pool if q not in result]
        while len(result) < count and remaining:
            result.append(remaining.pop(random.randint(0, len(remaining) - 1)))

        random.shuffle(result)
        return result[:count]

    selected = []
    selected.extend(stratified_sample(vocab_qs, target_vocab))
    selected.extend(stratified_sample(grammar_qs, target_grammar))
    random.shuffle(selected)

    return selected


def conduct_assessment(questions: list) -> dict:
    """
    交互式进行测试，返回 AssessmentResult dict
    """
    clear_screen()
    print_header("英语水平评估测试")
    print_info(f"共 {len(questions)} 题，词汇 + 语法，预计用时 10 分钟")
    print_info("每题选 A/B/C/D，输入 Q 可中途退出")
    print()
    input("  按 Enter 开始测试...")

    score = 0
    vocab_correct = 0
    vocab_total = 0
    grammar_correct = 0
    grammar_total = 0
    answered = 0

    for i, q in enumerate(questions, 1):
        clear_screen()
        print(f"  ── 第 {i}/{len(questions)} 题 ──")
        print(f"  类型: {'词汇' if q['type'] == 'vocabulary' else '语法'}  "
              f"难度: {'★' * q['difficulty']}{'☆' * (5 - q['difficulty'])}  "
              f"当前得分: {score}")
        print()
        print(f"  {q['stem']}")
        print()
        labels = ["A", "B", "C", "D"]
        for idx, opt in enumerate(q["options"]):
            print(f"    {labels[idx]}. {opt}")
        print()

        while True:
            ans = input("  你的选择 (A/B/C/D, Q=退出): ").strip().upper()
            if ans in ("A", "B", "C", "D", "Q"):
                break
            print("  输入无效，请输入 A、B、C、D 或 Q")

        if ans == "Q":
            print_info("测试已提前退出")
            break

        chosen = ord(ans) - 65
        if chosen == q["answer"]:
            score += 4
            if q["type"] == "vocabulary":
                vocab_correct += 1
            else:
                grammar_correct += 1
            print("\n  正确！✓")
        else:
            correct_letter = labels[q["answer"]]
            print(f"\n  错误。正确答案是 {correct_letter}")
            print(f"  解析: {q['explanation']}")

        if q["type"] == "vocabulary":
            vocab_total += 1
        else:
            grammar_total += 1
        answered += 1

        input("\n  按 Enter 继续下一题...")

    # 分析
    level = _score_to_level(score)
    strengths, weaknesses = _analyze(vocab_correct, vocab_total,
                                      grammar_correct, grammar_total, answered)

    result = {
        "date": date.today().isoformat(),
        "raw_score": score,
        "level": level,
        "vocabulary_estimate": _estimate_vocabulary(level),
        "strengths": strengths,
        "weaknesses": weaknesses,
    }
    return result


def _score_to_level(score: int) -> int:
    """原始分数 → 等级 1-5"""
    if score <= 30:
        return 1
    if score <= 50:
        return 2
    if score <= 70:
        return 3
    if score <= 85:
        return 4
    return 5


def _estimate_vocabulary(level: int) -> int:
    """根据等级估算词汇量"""
    vocab_data = load_static_json("vocabulary.json")
    return vocab_data["level_estimates"][str(level)]["typical"]


def _analyze(vocab_correct, vocab_total, grammar_correct, grammar_total, answered):
    """分析优劣势"""
    strengths = []
    weaknesses = []

    # 词汇
    if vocab_total > 0:
        vp = vocab_correct / vocab_total
        if vp >= 0.6:
            strengths.append("词汇 (vocabulary)")
        else:
            weaknesses.append("词汇 (vocabulary)")

    # 语法
    if grammar_total > 0:
        gp = grammar_correct / grammar_total
        if gp >= 0.6:
            strengths.append("语法 (grammar)")
        else:
            weaknesses.append("语法 (grammar)")

    return strengths, weaknesses


def display_result(result: dict) -> None:
    """展示评估结果"""
    from .utils import LEVEL_NAMES

    clear_screen()
    print_header("评估结果")
    level = result["level"]
    print(f"  得分:       {result['raw_score']}/100")
    print(f"  等级:       {level} 级 ({LEVEL_NAMES.get(level, '未知')})")
    print(f"  词汇量估算: ~{result['vocabulary_estimate']} 词")

    if result["strengths"]:
        print(f"  优势:       {', '.join(result['strengths'])}")
    if result["weaknesses"]:
        print(f"  薄弱:       {', '.join(result['weaknesses'])}")
    print()
