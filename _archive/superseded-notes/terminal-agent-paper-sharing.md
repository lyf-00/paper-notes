---
title: "终端Agent环境合成：五篇论文的方法对比与设计哲学"
public: false
archived: true
superseded_by: /paper-reading/Terminal-Agent-Environment-Synthesis.html
description: "深度拆解Endless Terminals、TMax、Terminal-World、SkillSynth、CLI-Universe的环境合成pipeline、prompt策略与harness设计"
type: paper-sharing
date: 2026-07-28
created_at: 2026-07-28T15:00:00+08:00
category: "Agent Systems"
tags:
  - terminal-agent
  - environment-synthesis
  - data-generation
  - multi-agent
---

# 终端Agent环境合成：五篇论文的方法对比与设计哲学

> 1小时Paper Sharing · 核心问题：**如何自动合成高质量的终端Agent训练环境？**
>
> 重点：环境合成的Pipeline设计、Prompt策略、Harness架构
> SFT/RL训练结果作为副产品，放在最后

---

## 0. 为什么环境合成是核心问题？（5 min）

### 终端Agent的能力瓶颈

```
模型能力 ↑
    |
    |        ← 我们在这里？
    |
    |
    |___________ 数据天花板 ___________
                  训练数据质量/多样性
```

- 基础模型能力已经很强，但终端Agent性能上不去
- 瓶颈不在模型，在**高质量训练数据稀缺**
- 人工标注成本极高，且难以覆盖长尾场景

### 环境合成 vs 轨迹合成

| 维度 | 轨迹合成 | 环境合成 |
|------|---------|---------|
| 产物 | (state, action, reward)轨迹 | 可执行的完整环境+任务 |
| 灵活性 | 低，路径固定 | 高，同一环境多种解法 |
| 训练方式 | SFT为主 | RL + SFT均可 |
| 难度控制 | 难，依赖教师 | 易，可程序化调节 |

> **环境合成是更底层、更灵活的数据生成范式**

### 环境合成的核心挑战

1. **可执行性**：生成的环境必须真的能跑
2. **难度梯度**：不能太简单也不能无解
3. **多样性**：覆盖足够多的技能和场景
4. **验证可靠**：怎么判断任务是否真的完成了？
5. **成本控制**：LLM调用很贵，怎么提高成功率？

---

## 1. 环境合成的通用框架（10 min）

### 典型Pipeline结构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  任务构思    │ →  │  环境实现    │ →  │  验证过滤    │
│ (Ideation)  │    │ (Realization)│    │ (Validation) │
└─────────────┘    └─────────────┘    └─────────────┘
       ↓                  ↓                  ↓
   头脑风暴            Docker构建         可执行验证
   能力分类            资产准备           难度过滤
   多样性控制          依赖安装           去重
```

### 多智能体Harness设计

几乎所有工作都采用**多智能体协作**的方式：

```
┌─────────────────────────────────────────┐
│              主控制器 / Orchestrator      │
└─────────────┬─────────────┬─────────────┘
              │             │
        ┌─────▼─────┐ ┌─────▼─────┐
        │ 生成Agent  │ │ 验证Agent  │
        │ (Generator)│ │ (Verifier) │
        └─────┬─────┘ └─────┬─────┘
              │             │
        ┌─────▼─────┐ ┌─────▼─────┐
        │ 求解Agent  │ │ 测试Agent  │
        │ (Solver)   │ │ (Tester)   │
        └───────────┘ └───────────┘
```

**常见角色分工**：
- **Generator**：生成任务描述、环境配置、测试用例
- **Solver**：尝试解决任务，验证可解性
- **Verifier**：检查结果是否正确
- **Tester**：编写测试用例，自动化验证
- **Critic / Reviewer**：质量评估、多样性检查

### Prompt策略演进

| 策略 | 特点 | 代表工作 |
|------|------|---------|
| 单轮生成 | 一次prompt生成完整任务 | 早期工作 |
| 迭代细化 | 多轮对话逐步完善 | CLI-Universe |
| Rubric门控 | 按检查清单逐项验证 | TMax, CLI-Universe |
| 辩论/对抗 | 两个agent互相挑错 | SkillSynth |
| 自举/自演化 | 用已生成的任务生成新任务 | Endless Terminals |

---

## 2. 五篇论文的环境合成详解（35 min）

### 2.1 Endless Terminals：四阶段Pipeline开山之作

**论文**：Endless Terminals: Scaling Terminal RL with Automatic Environment Generation
**时间**：Jan 2026
**地位**：终端环境合成的奠基性工作

#### Pipeline：四个阶段

```
Stage 1          Stage 2          Stage 3          Stage 4
Seed Task    →  Environment   →  Environment  →  RL Training
Curation        Generation       Validation
```

#### Stage 1: Seed Task Curation（种子任务精选）

- **人工精选** 50 个种子任务
- 覆盖主要领域：文件操作、文本处理、系统管理等
- 每个任务包含：任务描述、初始环境、验证脚本

**为什么需要种子任务？**
- 冷启动问题：从零开始生成质量不稳定
- 提供"风格锚点"：让LLM知道什么是好的终端任务
- 控制分布：确保生成的任务在有用的范围内

#### Stage 2: Environment Generation（环境生成）

**Prompt策略**：Few-shot + 模板化

```
你是一个终端任务设计专家。请根据以下种子任务，
生成一个新的、类似但不同的终端任务。

种子任务示例：
[任务描述]
[初始环境]
[验证方法]

要求：
1. 任务必须可以在Linux终端中完成
2. 必须有明确的成功/失败判断标准
3. 难度适中，需要5-15步操作
4. 不能与种子任务完全相同

新任务：
```

**生成内容**：
- 任务描述（自然语言）
- Dockerfile / 环境配置
- 初始文件系统状态
- 验证脚本（bash / python）

#### Stage 3: Environment Validation（环境验证）

**三层验证**：

1. **语法验证**：Dockerfile能build吗？脚本有语法错误吗？
2. **可执行验证**：环境能启动吗？验证脚本能运行吗？
3. **可解性验证**：用一个agent尝试解决，能解出来吗？

**过滤漏斗**：
```
100%  生成的候选
 ↓
 ~60% 语法/构建通过
 ↓
 ~40% 可执行验证通过
 ↓
 ~30% 可解性验证通过
```

#### Harness设计

```
Generator Agent ──→ Environment ──→ Solver Agent
                      ↓
                   Verifier Script
```

- **单Generator + 单Solver**的简单架构
- 验证主要靠**脚本**而非LLM judge
- 没有复杂的多轮辩论或审查

#### 关键数据

| 指标 | 数值 |
|------|------|
| 种子任务 | 50个 |
| 生成任务 | ~10,000个 |
| 最终保留 | 3,255个 |
| 保留率 | ~30% |
| 平均生成成本 | ~$0.5/任务 |

#### 意义与局限

**意义**：
- 首次证明终端环境可以自动合成
- 建立了"生成→验证→过滤"的基本范式
- 验证了RL+合成环境的有效性

**局限**：
- 多样性有限，容易偏离种子任务分布
- 验证比较粗糙，主要靠脚本
- 没有显式的技能/难度控制

---

### 2.2 TMax：组合式采样 + 多维验证器

**论文**：TMax: Compositional Data Generation for Terminal Agents
**时间**：Jun 2026
**核心思想**：**正交维度组合采样**，从"随机生成"到"可控合成"

#### 核心创新：9轴正交采样

不是随机生成任务，而是从**9个正交维度**组合采样：

```
┌─────────────────────────────────────────────────┐
│                 9个采样轴                         │
├──────────┬──────────┬──────────┬─────────────────┤
│ Domain   │ Skill    │ Primitive│ Persona        │
│ (9种)    │ Type     │ Skill    │ (6-18/domain)  │
│          │ (4-7/    │ (20-40/  │                 │
│          │ domain)  │ domain)  │                 │
├──────────┼──────────┼──────────┼─────────────────┤
│ Language │ Task     │ Command  │ Fixture        │
│ (8种)    │ Complex. │ Complex. │ (7种)          │
│          │ (4级)    │ (3级)    │                 │
├──────────┼──────────┴──────────┴─────────────────┤
│ Verifier │                                        │
│ (5种)    │                                        │
└──────────┴────────────────────────────────────────┘
```

**每个轴的具体选项**：

| 轴 | 选项示例 |
|----|---------|
| Domain | software_engineering, system_admin, data_processing, security, scientific_computing... |
| Skill Type | algorithmic, systems, configuration, shell_scripting, cryptography... |
| Fixture | text_only, image, audio, video, stripped_binary, vendored_package, multi_service_compose |
| Verifier | exact_text, metric_threshold, adversarial_corpus, fuzz_equivalence, multi_protocol |

> **组合爆炸**：9个轴 → 理论可生成 **百万级** 独特任务

#### 采样策略

不是均匀采样，而是**分层采样**：

1. 先按Domain分层，确保每个领域都有覆盖
2. 每个Domain内，按Skill Type × Complexity做网格采样
3. 其他维度随机采样，增加多样性
4. 去重：避免生成过于相似的任务

**Prompt模板**：
```
请生成一个终端任务，满足以下规格：

领域：{domain}
技能类型：{skill_type}
难度：{task_complexity}
命令复杂度：{command_complexity}
用户角色：{persona}
自然语言：{language}
环境资产类型：{fixture}
验证方式：{verifier}

任务描述：
[详细描述任务目标]

初始环境：
[描述需要的文件、工具、配置]

验证方法：
[根据{verifier}设计验证方案]
```

> 从"自由生成"到"按规格生成"——**可控性大幅提升**

#### 5种验证器（Verifier）

| 验证器 | 原理 | 适用场景 |
|--------|------|---------|
| `exact_text` | 输出文本精确匹配 | 文件内容、字符串处理 |
| `metric_threshold` | 数值指标达到阈值 | 性能优化、准确率 |
| `adversarial_corpus` | 对抗测试集测试 | 鲁棒性、安全性 |
| `fuzz_equivalence` | 模糊测试等价性 | 编译器、解析器 |
| `multi_protocol` | 多协议交叉验证 | 网络服务、API |

**为什么需要多种验证器？**
- 单一验证器容易被reward hacking
- 不同类型的任务需要不同的验证方式
- 多验证器交叉验证更可靠

#### Harness设计

```
┌─────────────────────────────────────────┐
│          Sampler (采样器)                │
│  从9个轴组合采样任务规格                   │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────▼───────────────────────────┐
│          Generator (生成器)              │
│  按规格生成任务描述+环境配置               │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────▼───────────────────────────┐
│     Verifier Suite (验证器套件)          │
│  exact / metric / adversarial / fuzz...  │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────▼───────────────────────────┐
│       Solver Agent (求解验证)            │
│  确认任务可解且难度合适                   │
└─────────────────────────────────────────┘
```

**特点**：
- **Sampler + Generator**分离：规格和实现解耦
- **程序化验证为主**：5种验证器都是代码
- LLM主要用于**生成**，验证尽量自动化

#### 关键数据

| 指标 | 数值 |
|------|------|
| 采样轴数 | 9个 |
| 生成环境数 | ~20,000 |
| 最终保留 | 14,600 |
| 保留率 | ~73% |
| 验证器种类 | 5种 |

> 保留率比Endless Terminals高很多，因为**规格化生成**减少了无效候选

---

### 2.3 Terminal-World：Agent Skills 驱动的环境合成

**论文**：Terminal-World: Agent-Skill-Driven Environment Synthesis for Terminal Agents
**时间**：May 2026
**核心思想**：**以技能为核心**组织环境合成，而非以任务为核心

#### 核心概念：Skill Taxonomy（技能分类法）

```
Level 1: Domain (领域)
  └── Level 2: Skill Family (技能族)
        └── Level 3: Primitive Skill (原子技能)
              └── Level 4: Skill Variant (技能变体)
```

**示例**：
```
System Administration
  ├── Process Management
  │     ├── ps/top 监控
  │     ├── kill/nice 控制
  │     └── systemd 服务管理
  └── File System
        ├── 权限管理
        ├── 挂载/卸载
        └── 磁盘配额
```

#### 核心创新：Skill Teams & Skill Graphs

**Skill Team（技能组合）**：
- 一个任务不是用一个技能，而是**一组技能的组合**
- 例如："部署Web服务" = Git操作 + Docker命令 + 配置文件编辑 + 网络调试

**Skill Graph（技能图）**：
- 技能之间有依赖关系和组合关系
- 用图结构来控制任务的技能多样性和难度

```
Skill A ──→ Skill B ──→ Skill C
   \         /
    └──→ Skill D ──→ Skill E
```

#### 环境合成Pipeline

```
Stage 1               Stage 2                Stage 3
Skill Graph    →    Skill Team        →    Environment
Construction        Sampling               Synthesis
(构建技能图)         (采样技能组合)          (合成环境)
```

**Stage 1: Skill Graph Construction**
- 人工定义 + LLM辅助构建技能分类法
- 标注技能之间的依赖关系、前置条件
- 每个技能有：名称、描述、难度、相关命令

**Stage 2: Skill Team Sampling**
- 从技能图中采样一个连通子图作为Skill Team
- 控制大小（3-8个技能）和难度
- 确保技能之间有逻辑关联，不是随机拼凑

**Stage 3: Environment Synthesis**
- 给定Skill Team，生成一个需要用到所有这些技能的任务
- 生成环境配置和初始状态
- 生成验证脚本

**Prompt策略**：Skill-grounded Generation

```
请设计一个终端任务，要求必须使用以下技能：

技能列表：
1. {skill_1_name}: {skill_1_description}
2. {skill_2_name}: {skill_2_description}
3. {skill_3_name}: {skill_3_description}

技能依赖关系：
{skill_dependency_graph}

要求：
- 任务必须自然地融合所有列出的技能
- 不能有技能是多余的
- 难度适中，需要10-20步完成
- 有明确的验证标准

任务描述：
...
```

#### Harness设计

```
┌─────────────────────────────────────────┐
│        Skill Graph (知识库)              │
│  技能分类法 + 依赖关系                    │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────▼───────────────────────────┐
│        Skill Team Sampler                │
│  从图中采样连通子图                        │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────▼───────────────────────────┐
│        Environment Generator             │
│  基于技能组合生成环境                      │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────▼───────────────────────────┐
│     Skill Coverage Checker               │
│  验证任务确实用到了所有技能                │
└─────────────────────────────────────────┘
```

**特殊之处**：
- **技能是一等公民**，任务是技能的载体
- 有专门的**技能覆盖率检查**：确保任务真的用到了指定技能
- 可以精确控制每个技能的训练样本数

#### 关键数据

| 指标 | 数值 |
|------|------|
| 技能总数 | ~500个 |
| 技能族 | ~50个 |
| 训练环境数 | 5,723 |
| 平均技能数/任务 | 4.2个 |
| 平均步数 | 13.44步 |

---

### 2.4 SkillSynth：场景中介的技能图 + 多智能体Harness

**论文**：SkillSynth: Scenario-Mediated Skill Graph for Terminal Agent Training
**机构**：腾讯混元团队
**时间**：Apr 2026
**核心思想**：**场景（Scenario）作为技能组合的中介**，多智能体协作生成

#### 核心创新：Scenario-Mediated Skill Graph

**为什么需要场景？**
- 纯技能组合可能不自然（"为什么我要同时用grep和docker？"）
- 场景提供了**上下文合理性**：在XX场景下，自然需要A+B+C技能

**三层结构**：
```
场景 (Scenario)
    ↓ 介导
技能图 (Skill Graph)
    ↓ 展开
任务轨迹 (Task Trajectory)
```

**示例**：
```
场景："线上服务故障排查"
  ↓
技能组合：日志查询(grep/awk) + 进程管理(ps/kill)
         + 网络诊断(curl/netstat) + 配置检查
  ↓
任务："服务响应变慢，找出原因并修复"
```

#### 多智能体Harness设计

这是五篇论文中**最复杂的多智能体架构**：

```
┌─────────────────────────────────────────────────────┐
│                   Orchestrator                       │
│              (总调度 / 流程控制)                      │
└──┬──────────┬──────────┬──────────┬──────────┬──────┘
   │          │          │          │          │
┌──▼───┐  ┌───▼───┐  ┌──▼───┐  ┌───▼───┐  ┌───▼───┐
│Scenario│  │Skill  │  │Env   │  │Solver│  │Critic │
│Designer│  │Graph  │  │Gen   │  │Agent │  │Agent  │
│(场景   │  │Builder│  │(环境 │  │(求解 │  │(评审  │
│ 设计师)│  │(技能图)│  │ 生成)│  │ 者)  │  │ 者)  │
└───────┘  └───────┘  └──────┘  └───────┘  └───────┘
```

**各角色职责**：

| 角色 | 职责 | Prompt特点 |
|------|------|-----------|
| **Scenario Designer** | 设计真实可信的场景背景 | 强调真实性、合理性 |
| **Skill Graph Builder** | 为场景构建技能依赖图 | 技能分解、依赖分析 |
| **Env Generator** | 生成具体环境和任务 | 详细、可执行 |
| **Solver Agent** | 尝试解决任务，生成轨迹 | 探索式、多轮交互 |
| **Critic Agent** | 评审质量、多样性、难度 | 批判性、checklist式 |

#### 环境合成Pipeline

```
Stage 1           Stage 2            Stage 3           Stage 4
Scenario    →   Skill Graph    →  Environment   →  Trajectory
Design          Construction       Generation      Generation
(场景设计)       (技能图构建)        (环境生成)       (轨迹生成)
     ↓                ↓                 ↓                ↓
  场景描述         技能依赖图        Docker环境       完整解轨迹
  背景故事         技能列表         初始状态         验证结果
```

**Stage 1: Scenario Design**
- Scenario Designer生成场景描述
- 包含：背景故事、用户角色、目标、约束
- 要求：真实、有代入感、不是"假任务"

**Stage 2: Skill Graph Construction**
- Skill Graph Builder分析场景需要的技能
- 构建技能依赖图
- 标注：前置技能、核心技能、可选技能

**Stage 3: Environment Generation**
- Env Generator根据场景+技能图生成环境
- 生成：任务描述、Dockerfile、初始文件、验证脚本
- 多轮迭代：Critic评审，Generator修改

**Stage 4: Trajectory Generation**
- Solver Agent在环境中求解
- 生成完整的交互轨迹
- Critic评审轨迹质量

**Critic的评审Checklist**：
```
□ 场景是否真实可信？
□ 技能列表是否完整且必要？
□ 环境是否可执行？
□ 任务难度是否合适？
□ 验证方法是否可靠？
□ 轨迹是否自然，不是"作弊"解法？
□ 是否有多样性，不与已有任务重复？
```

#### 辩论机制（Debate）

Generator和Critic会进行**多轮辩论**：
1. Generator生成初版
2. Critic指出问题
3. Generator修改
4. Critic再次评审
5. ...直到通过或达到最大轮次

> 类似"红队/蓝队"对抗，提高最终质量

#### 关键数据

| 指标 | 数值 |
|------|------|
| 场景数 | 82,073 |
| 过滤后技能数 | 57,214 |
| LLM验证桥梁 | 185,529 |
| 最终验证任务 | 3,560 |
| Oracle通过率 | 95.7% |
| 平均辩论轮次 | 3-5轮 |

---

### 2.5 CLI-Universe：Inside-out设计 + 证据引导细化 ⭐

**论文**：CLI-Universe: Towards Verifiable Task Synthesis Engine for Terminal Agents
**时间**：Jun 2026
**地位**：当前环境合成的**最高水平**，数据效率最高

#### 核心哲学：Inside-out vs Outside-in

| 维度 | Outside-in | Inside-out |
|------|-----------|------------|
| 起点 | 现有工件（仓库、文档） | 能力定义 |
| 方法 | 改造已有内容 | 从能力出发构建 |
| 质量 | 参差不齐 | 设计即有质量保证 |
| 覆盖 | 表面广 | 能力维度精确控制 |
| 代表 | TerminalTraj, Nemotron | CLI-Universe |

> **从"有什么做什么"到"要什么造什么"**

#### 三阶段Pipeline

```
┌─────────────────────────────────────────────────────┐
│ 阶段一：任务蓝图构建 (Task Blueprint Construction)    │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │能力分类法 │→│证据引导深度   │→│蓝图形成与    │   │
│  │采样组合  │  │研究          │  │验证          │   │
│  └──────────┘  └──────────────┘  └──────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ 阶段二：环境实现 (Environment Realization)           │
│  ┌──────────┐  ┌──────────────┐                     │
│  │资产物化  │→│环境组装(Docker)│                     │
│  └──────────┘  └──────────────┘                     │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ 阶段三：测试构建与可执行过滤                          │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │测试构建  │→│Hint条件过滤   │→│Fail-to-Pass  │   │
│  │(Rubric)  │  │              │  │检查          │   │
│  └──────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────┘
```

#### 阶段一：任务蓝图构建

**1. 任务候选规范（Task Candidate Specification）**

四维能力分类法采样：

| 维度 | 数量 | 说明 |
|------|------|------|
| Domain（领域） | 17个 | 应用领域 |
| Skill Type（技能类型） | 8种 | 专业技术知识类型 |
| Capability（能力） | 11种 | 推理行为类型 |
| Engineering Pillar（工程支柱） | 6种 | 工作形式 |

**采样策略**：
- 先选Domain，再从该Domain的Skill Type池中选
- Capability和Pillar可以跨Domain组合
- 组合评分：创造性、技术基础、可行性
- 高分候选进入下一阶段

**2. 证据引导细化（Evidence-Guided Refinement）** ⭐

这是CLI-Universe最独特的设计！

**问题**：纯LLM生成的任务容易"想当然"，技术细节不准确
**解决**：让研究agent先搜索真实技术材料，再基于证据生成任务

```
抽象任务想法
    ↓
研究agent搜索真实材料：
  - GitHub仓库
  - 官方文档
  - Issue讨论
  - 教程博客
  - StackOverflow问答
    ↓
逐步将证据融入任务规范
  - 具体工具/版本
  - 真实的失败模式
  - 具体的输入输出契约
  - 已知的坑和边界情况
    ↓
充分grounded的任务规范
```

**Prompt策略**：迭代式研究+细化

```
第1轮：
"针对{task_idea}，搜索相关的技术资料，列出3个最相关的
开源项目/文档，并总结关键技术点。"

第2轮：
"基于找到的资料，细化任务描述，确保每个技术细节都有
依据。标注哪些信息来自哪个来源。"

第3轮：
"检查任务的可行性，列出可能的失败模式和边界情况。"

...直到足够详细
```

**效果验证**：
- 求解轮次：5.34 → 18.43（**3.45×**）
- 通过率：68.2% → 54.9%（**-13.3 pt**）

> 不是延长轨迹，而是**真正提高了难度和真实性**！

**3. 蓝图形成与验证**

每个细化后的候选被编译为**蓝图**，包含：
- 用户面指令（user-facing instruction）
- 内部hint（internal hint）：用于参考解决方案
- 环境清单（environment checklist）

**Rubric验证**：
- 基于检查清单逐项验证
- 验证者：人类 + LLM双盲
- 接受率：人类72%→91%，LLM75%→93%

#### 阶段二：环境实现

**1. 资产物化（Asset Materialization）**

获取所需资产：
- 源仓库、文档、数据集、配置文件、服务日志
- 从公开资源获取，然后适配
- 适配方式：标准化格式、注入故障、调整参数、限定范围
- 没有合适外部资产时，从头合成

**2. 环境组装（Environment Assembly）**

打包为Docker镜像：
- 依赖、运行时配置、固定版本
- 资产放置到指定位置
- 连接组件间引用
- 自包含，可复现

**Smoke Test验证**：
- 依赖安装成功？
- 服务启动正确？
- 文件系统布局符合预期？
- 基本端到端可达性？

#### 阶段三：测试构建与可执行过滤

**1. 测试构建（Test Construction）**

测试agent构建任务特定测试：
- 生成候选测试套件
- 迭代检查 against test-case rubrics
- 覆盖：正确性、确定性、边界情况
- 细化或替换直到稳定

**验证质量**：
- 官方解决方案通过合成测试：91%
- Agent-as-judge语义匹配：88%

**2. Hint-Conditional Filtering**

```
有hint尝试 → 成功 ✓
无hint尝试 → 失败 ✗
                ↓
          保留这个任务！
```

**为什么这样过滤？**
- 过滤掉太简单的任务（没hint也能解）
- 确保hint提供了有意义的监督信号
- 保证训练数据的"教学价值"

**3. Fail-to-Pass Filtering** ⭐

```
初始环境 → 测试失败 ✓
执行解决方案后 → 测试通过 ✓
                        ↓
                  保留这个任务！
```

**双向验证**：
- 正向：解决方案真的能解决问题
- 反向：初始状态确实有问题
- 排除：测试平凡通过的空洞任务
- 排除：未真正达到目标的假解决方案

#### 整体过滤漏斗

```
100%  所有候选
 ↓ -30%
 70%  Idea Filtered（想法过滤）
 ↓ -14%
 56%  Blueprint Validated（蓝图验证）
 ↓ -14%
 42%  Environment Built（环境构建成功）
 ↓ -8.4%
 33.6%  Verified Tasks（最终保留）
```

> **约2/3被过滤，只保留1/3！** 严苛的质量控制

#### Harness设计

```
┌─────────────────────────────────────────────────────┐
│                  Orchestrator                        │
└──┬──────────┬──────────┬──────────┬──────────┬──────┘
   │          │          │          │          │
┌──▼───┐  ┌───▼───┐  ┌──▼───┐  ┌───▼───┐  ┌───▼───┐
│Research│  │Blueprint│  │Env   │  │Test  │  │Solver│
│Agent   │  │Validator│  │Builder│ │Agent │  │Agent │
│(研究   │  │(蓝图    │  │(环境  │  │(测试  │  │(求解  │
│ agent) │  │ 验证者) │  │ 构建) │  │ 构建) │  │ 者)  │
└───────┘  └───────┘  └──────┘  └───────┘  └───────┘
```

**特点**：
- **Research Agent**是独特角色：负责搜索真实证据
- 验证是**多阶段、多层次**的：蓝图→环境→测试→求解
- 大量使用**Rubric（检查清单）**而非主观判断

---

## 3. 横向对比与设计哲学（8 min）

### 3.1 Pipeline结构对比

| 论文 | 阶段数 | 核心阶段 | 过滤强度 |
|------|--------|---------|---------|
| Endless Terminals | 4 | 生成+验证 | 弱（~30%保留） |
| TMax | 3 | 采样+生成+验证 | 中（~73%保留） |
| Terminal-World | 3 | 技能图+采样+生成 | 中 |
| SkillSynth | 4 | 场景+技能图+环境+轨迹 | 强（多轮辩论） |
| CLI-Universe | 3 | 蓝图+环境+测试 | 最强（~33.6%保留） |

> **注意**：保留率低不一定是坏事——CLI-Universe保留率最低，但数据质量最高

### 3.2 多样性控制策略

| 论文 | 控制方式 | 粒度 |
|------|---------|------|
| Endless Terminals | 种子任务引导 | 粗 |
| TMax | 9轴正交采样 | 细 |
| Terminal-World | 技能图采样 | 中 |
| SkillSynth | 场景+技能图 | 中细 |
| CLI-Universe | 四维能力分类法 | 最细 |

### 3.3 验证机制对比

| 论文 | 验证方式 | 自动化程度 | 可靠性 |
|------|---------|-----------|--------|
| Endless Terminals | 脚本验证+solver | 高 | 中 |
| TMax | 5种程序化验证器 | 最高 | 高 |
| Terminal-World | 技能覆盖检查+脚本 | 中高 | 中高 |
| SkillSynth | Critic评审+辩论 | 中 | 中高 |
| CLI-Universe | Rubric+Fail-to-Pass | 高 | 最高 |

### 3.4 Harness复杂度对比

```
简单 ←────────────────────────────────────→ 复杂

Endless    TMax    Terminal-   SkillSynth   CLI-Universe
Terminals          World

1-2个agent  3个agent  3-4个agent  5个agent    5个agent
            (sampler)            (辩论机制)   (research)
```

### 3.5 设计哲学的演进

```
第一代：随机生成 + 简单过滤
  ↓  "怎么保证多样性？"
第二代：结构化采样 + 多验证器
  ↓  "怎么保证技能覆盖？"
第三代：技能图驱动 + 场景中介
  ↓  "怎么保证真实性？"
第四代：证据引导 + 多阶段Rubric验证
```

**核心趋势**：
1. **从"量"到"质"**：越来越重视单条数据的质量
2. **从"生成"到"验证"**：验证环节的比重越来越大
3. **从"单agent"到"多agent"**：角色分工越来越细
4. **从"内省"到"外证"**：从LLM自己想，到搜索真实证据

---

## 4. 总结与未来方向（2 min）

### 关键洞察

1. **验证比生成更重要**：好的验证器是质量的生命线
2. **结构化 > 随机性**：可控采样比随机生成效率高得多
3. **真实性是瓶颈**：LLM生成的任务容易"想当然"，需要真实证据grounding
4. **多智能体协作有效**：角色分工、辩论机制都能提升质量
5. **Inside-out是趋势**：从能力定义出发，比从现有工件改造更精准

### 开放问题

- **可扩展性**：现在还是几千几万的规模，能到百万级吗？
- **难度控制**：怎么精确控制任务难度，形成平滑梯度？
- **自动课程学习**：能不能让环境自动适配agent当前水平？
- **多模态环境**：GUI + Terminal混合环境怎么合成？
- **自我进化**：Agent能不能自己生成训练环境，迭代提升？

### 一句话总结

> **终端环境合成已经从"能生成"进化到"生成得好、生成得准、生成得真"，但距离"生成得又多又好又便宜"还有很长的路要走。**

---

## Q&A

> 感谢聆听！欢迎讨论 🎉

**参考论文**：
- [Endless Terminals (2026.01)](https://arxiv.org/abs/2601.16443)
- [TMax (2026.06)](https://arxiv.org/abs/2606.23321)
- [Terminal-World (2026.05)](https://arxiv.org/abs/2605.20876)
- [SkillSynth (2026.04)](https://arxiv.org/abs/2604.25727)
- [CLI-Universe (2026.06)](https://arxiv.org/abs/2606.22883)
