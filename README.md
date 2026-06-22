# CET Planner — 四六级复习规划小程序

一个基于命令行的 **CET-4/6 智能复习规划工具**。通过入学测评了解你的英语水平，自动生成个性化的多周复习计划，支持每日任务追踪和进度可视化。

## ✨ 功能特性

- **🎯 入学测评** — 25 道分层抽题（词汇 60% + 语法 40%，难度 1-5 梯度分布），估算词汇量和强弱项
- **📋 智能规划** — 根据目标（四级/六级）、当前水平、可用天数自动生成多周复习计划
- **📊 每日任务** — 词汇（新词 + 复习）+ 每日轮换技能训练（听力/阅读/写作/翻译）+ 周日综合回顾
- **📈 进度追踪** — 任务完成打卡、连续学习天数、词汇增长曲线（sparkline）、周报/总报告
- **⚡ 强度自适应** — 可用时间少于推荐周期时自动压缩计划（最高 2.5x 强度）
- **💾 纯本地存储** — 所有数据以 JSON 格式存储，无需网络，无需数据库
- **🖥️ 全中文界面** — 终端交互全部中文化

## 📦 环境要求

- **Python 3.9+**（仅依赖标准库，无需安装第三方包）

## 🚀 快速开始

```bash
# 进入项目目录
cd cet_planner

# 启动新手向导（测评 + 生成计划）
python -m cet_planner start

# 或直接指定参数
python -m cet_planner start --name 小明 --exam cet6 --days 90
```

首次运行会引导你完成：
1. 填写姓名、目标考试（CET-4 / CET-6）
2. 完成 25 道英语水平测评题
3. 自动生成个性化复习计划

## 📖 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `start` | 新手向导：测评 → 生成计划 | `python -m cet_planner start` |
| `assess` | 重新测评水平 | `python -m cet_planner assess` |
| `today` | 查看今日任务列表 | `python -m cet_planner today` |
| `done` | 标记任务完成 | `python -m cet_planner done 1` |
| `undo` | 撤销已完成任务 | `python -m cet_planner undo 1` |
| `week` | 查看指定周计划 | `python -m cet_planner week 2` |
| `progress` | 查看总体进度 | `python -m cet_planner progress` |
| `report` | 生成详细学习报告 | `python -m cet_planner report` |
| `adjust` | 调整可用学习天数 | `python -m cet_planner adjust --days 60` |
| `info` | 查看个人信息和计划 | `python -m cet_planner info` |

### 可选参数

| 参数 | 说明 |
|------|------|
| `--name <姓名>` | 设置用户姓名 |
| `--exam <cet4\|cet6>` | 设置目标考试 |
| `--days <天数>` | 设置可用学习天数 |
| `--version` | 显示版本号 |

## 📁 项目结构

```
cet_planner/
├── __init__.py            # 包信息 (v1.0.0)
├── __main__.py            # python -m 入口
├── main.py                # CLI 主入口，命令路由
├── models.py              # 数据模型（dataclass + enum）
├── assessment.py          # 测评引擎：抽题、答题、评分
├── plan_generator.py      # 复习计划生成器
├── storage.py             # JSON 持久化层
├── utils.py               # 工具函数（日期、终端输出、sparkline）
├── data/                  # 静态数据
│   ├── questions.json     # 题库（词汇 + 语法）
│   ├── templates.json     # 学习计划模板
│   └── vocabulary.json    # 词汇量配置
└── user_data/             # 用户数据（运行时生成）
    ├── profile.json       # 用户档案
    ├── plan.json          # 学习计划
    ├── tasks.json         # 任务列表
    └── progress.json      # 进度记录
```

## 🔄 数据流

```
用户输入 → assessment.py（测评）
           ↓
      profile.json（用户档案）
           ↓
   plan_generator.py（生成计划）
           ↓
      plan.json + tasks.json
           ↓
   每日交互：today → done/undo → progress.json
           ↓
      progress / report（可视化反馈）
```

## 🧪 运行测试

```bash
python test_cet.py
```

测试覆盖：题库加载、分层抽题、评分逻辑、档案存取、计划生成、压缩排期、任务标记、进度记录等 12 项。

## 🛠️ 技术栈

- **语言：** Python 3.9+
- **依赖：** 零第三方库，纯标准库
- **存储：** 本地 JSON 文件（原子写入，防数据损坏）
- **界面：** 终端 CLI，全中文交互

---

> 💡 规划逻辑参考四六级考试大纲设计，建议每天投入 1-2 小时，坚持执行计划效果最佳。
