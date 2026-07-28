---
title: "Terminal Agent Environment Synthesis：五篇论文与一条数据生产线"
public: true
description: "一小时 sharing 讲稿：比较 Endless Terminals、TMax、SkillSynth、Terminal-World 与 CLI-Universe 如何生成 task、container、verifier 和 trajectory。"
type: paper-reading
date: 2026-07-28
created_at: 2026-07-28T15:20:00+08:00
paper_title: "Terminal-Agent Environment Synthesis: A Five-Paper Reading Synthesis"
venue: "arXiv reading synthesis"
year: "2026"
status: "read"
category: "Agent Systems"
tags:
  - terminal-agents
  - environment-synthesis
  - data-synthesis
  - verifiable-environments
  - agent-training
source_url: "https://arxiv.org/abs/2601.16443"
---

# Terminal Agent Environment Synthesis：五篇论文与一条数据生产线

## 0. 这场 sharing 想回答什么

这不是一场“谁在 Terminal-Bench 上分数更高”的论文串讲。真正的问题是：

> 如果我们想训练一个 terminal agent，怎样把一句自然语言任务变成一个可启动、可交互、可恢复、可自动打分的环境？

五篇论文恰好给出了五种取舍：

1. **Endless Terminals**：把生成拆成四个阶段，用硬过滤保证 container 可用、测试有效、任务可解。
2. **TMax**：用九个正交轴直接控制多样性与难度，省掉昂贵的 teacher correctness filter，把一部分过滤推迟到 RL rollout。
3. **SkillSynth**：先在 scenario-mediated skill graph 中采样一条最小解题路径，再让 multi-agent harness 实例化任务。
4. **Terminal-World**：把 agent skill 当作同时包含 what / when / how 的合成原语，共同生成 instruction、environment、verifier 与 teacher guideline。
5. **CLI-Universe**：先用真实技术材料把 task blueprint 研究扎实，再用 rubric-gated tests、hint 对照和 fail-to-pass 提高监督密度。

![五篇论文的环境合成路线图](assets/paper-reading/terminal-agent-env-synthesis/five-pipelines-map.svg)

*自制方法地图。五篇工作的差异并不是“pipeline 有几步”，而是把质量预算放在哪里：Endless 和 CLI-Universe 选择生成后的硬过滤，TMax 选择生成吞吐与训练时软过滤，SkillSynth 与 Terminal-World 则先约束技能及轨迹结构。*

---

## 1. 一小时怎么讲

| 时间 | 内容 | 目标 |
|---:|---|---|
| 0–5 min | terminal environment 到底是什么 | 建立统一对象：instruction、initial state、runtime、verifier、trajectory |
| 5–10 min | 五篇论文总览 | 先给路线图，避免逐篇讲完才知道差异 |
| 10–20 min | Endless Terminals | 讲清最朴素、最容易复现的四阶段生产线 |
| 20–31 min | TMax | 重点讲九个采样轴、graded verifier、soft filtering |
| 31–41 min | SkillSynth | 重点讲 scenario-mediated skill graph 与 path sampling |
| 41–51 min | Terminal-World | 重点讲 I/E/V/G 四元组和 generate-verify-repair |
| 51–57 min | CLI-Universe | 重点讲 evidence grounding、hint-conditional、fail-to-pass |
| 57–60 min | 结论与讨论 | 给出可复用的“我们该怎么造环境”设计清单 |

如果现场讨论多，可以压缩每篇的训练结果，只保留一句：

- 环境构造决定 reward 是否可信；
- trajectory 的价值取决于它对应的任务是不是 learnable；
- SFT / RL 是生产线末端，而不是这场 sharing 的主角。

---

## 2. 先统一术语：一个 terminal training environment 包含什么

一个完整训练实例不只是 prompt，而是五件东西：

| 组件 | 作用 | 常见文件/表示 |
|---|---|---|
| Task instruction | 告诉 agent 要达到什么目标 | `task.md`、`instruction` |
| Initial state | 定义开始时有哪些文件、服务、错误状态 | source files、fixtures、filesystem snapshot |
| Runtime | 保证依赖、权限、网络和进程可重放 | Dockerfile、Apptainer `.def`、setup script |
| Verifier | 把终态映射成 reward | pytest、unit tests、protocol checks |
| Trajectory | agent 与环境交互的 action/observation 序列 | shell commands、stdout/stderr、teacher trace |

最关键的是它定义了一个状态转换：

$$
(\text{instruction}, s_0) \xrightarrow{\text{agent actions}} s_T
$$

而 verifier 给出：

$$
r = V(s_T)
$$

如果 $V(s_0)=1$，测试是空的；如果正确解之后仍有 $V(s_T)=0$，测试或环境是错的；如果任务根本不可解，RL 只会看到没有信息量的全零 reward。

因此环境合成的核心不是“生成更多题面”，而是让 instruction、initial state、runtime 和 verifier 共同指向同一个可观察的终态。

---

## 3. 五篇论文放在一张表里

| Paper | Seed / 控制变量 | Environment realization | Verification / filtering | Harness | 规模 |
|---|---|---|---|---|---:|
| Endless Terminals | category × complexity × scenario | LLM 生成 initial tests + Docker/Apptainer，失败反馈最多 3 轮 | final tests 初态必须失败；o3 pass@16 > 0 | 自研极简 XML command loop；Docker 用 Harbor，实验用 Apptainer | 3,255 |
| TMax | 9 axes：domain、skill type、primitive skills、persona、language、task/command complexity、fixture、verifier | per-domain base image + per-task delta；单次生成 task/files/tests/image | 只硬保 executability；policy pass rate=0 在 RL 时 soft filter | mini-SWE-agent 风格 Vanillux；Harbor；Apptainer/Podman | 14,600 |
| SkillSynth | skill 的 pre/post scenario graph；path length 1–7 | planner → constructor 生成 instruction、snapshot、container、tests、oracle | oracle execution + rubric judge；verify-repair | multi-agent synthesis harness；评测用 Terminus 2 + Harbor | 3,560 usable |
| Terminal-World | 1K skills + 76 teams + 237 graphs × 4,973 personas | initial files / setup / pytest 各自 GVR，最多 3 轮 | 五维 task judge；文件一致性；setup probing；pytest 初态必须失败 | teacher 为 DeepSeek-V3.2 + Terminus2；shared Debian sandbox | 5,723 |
| CLI-Universe | domain × skill type × capability × engineering pillar，再做 real-world research | pull/adapt 或 synthesize assets；Docker assembly + smoke tests | rubric-gated tests；hint-free fail / hinted pass；strict fail-to-pass | trajectory teacher Kimi-K2.6；评测 Terminus 2 | 6,000 trajectories |

两个容易混淆的数字：

- TMax 的正式名称是 **TMax-15K**，论文给出 **14,600** 个 RL environment instances。
- CLI-Universe 的 **6K** 是最终训练 trajectory 数，不是论文披露的全部候选 environment 数；全流程只有 **33.6%** 候选保留。

---

## 4. Endless Terminals：最清楚的四阶段基线

### 4.1 Pipeline

![Endless Terminals 原论文首页与四阶段 pipeline](assets/paper-reading/terminal-agent-env-synthesis/endless-pipeline-page.png)

*原论文 Figure 1 所在页。四阶段依次是 task description、container setup、completion tests、solution filtering。这张图值得先讲，因为后面四篇的复杂设计都可以看成在这四个位置增加新的控制变量或验证器。*

#### Stage I：Task description + privileged truth

每次 prompt 随机采样三个维度：

- task category：file management、text processing、log analysis、git、database、security 等；
- complexity：单命令到多步 workflow；
- scenario context：developer、DevOps engineer、data analyst 等。

LLM 同时输出：

- 给 agent 看的 task instruction；
- agent 看不到的 privileged truth，包括路径、精确文件内容、期望终态。

这里的关键不是 persona 本身，而是把“公开任务”和“私有验收信息”从一开始分开。

#### Stage II：Initial-state test + container

输入 task description 与 truth，生成：

- `test_initial_state.py`；
- Dockerfile 或 Apptainer definition。

执行闭环：

```text
generate container
→ build
→ run initial-state tests
→ feed build/test error back to LLM
→ retry, at most 3 rounds
→ still failing: discard
```

initial-state tests 检查开始前必须存在的文件、目录、进程或 repository。它们不判断任务是否已经完成，只判断环境能不能开始。

#### Stage III：Final-state tests

第二份测试检查任务完成后的 filesystem / service / computed result。

硬约束：

```text
final tests on initial state = fail
```

这一步消除最常见的 vacuous verifier：测试什么都没检查，初态也会通过。

#### Stage IV：Solution-based filtering

用 o3 对每个任务独立尝试 16 次：

```text
keep(task) iff pass@16 > 0
```

它确认任务至少在当前强模型能力边界内可解，但也引入 teacher ceiling：所有 o3 解不出的任务都被丢弃，其中可能包含正确但更难的任务。

### 4.2 Prompt 和 harness 到底长什么样

论文没有在正文逐字列出生成 prompt，但代码仓公开了主要 prompt 与文件结构。其核心约束是：

- public task 要像用户请求；
- truth 要列清路径、内容和 expected state；
- initial test 只检查 prerequisite，不能检查输出；
- final test 从 truth 构造；
- container build error 会回填给生成模型。

Agent interaction loop 非常小：

```xml
reasoning...
<command>one shell command</command>
```

完成时输出：

```xml
<command>done</command>
```

每轮把 stdout、stderr、exit code 追加回历史。训练最多 16 turns / 16K context；评测可到 64 turns。Docker 路径使用 Harbor，论文主实验使用 persistent Apptainer PTY。

### 4.3 这一篇最值得带走的点

Endless 的设计原则是：

> generator 可以犯错，但每一阶段必须有一个机器可执行的局部验收信号。

它的问题也很直接：

- pass@16 过滤成本高；
- “至少一次成功”确认可解，不保证 verifier 与自然语言完全对齐；
- 任务分布容易像竞赛题，而不像模糊的真实请求；
- 最终数据对强模型偏容易：TMax 后续测得 Gemini-3-Flash 在 Endless 上 pass@1 很高。

---

## 5. TMax：从“多阶段严审”转向“正交轴 + soft filtering”

### 5.1 九个轴怎样组成任务

![TMax 九轴 compositional data pipeline](assets/paper-reading/terminal-agent-env-synthesis/tmax-pipeline-page.png)

*原论文 Figure 2 所在页。左侧九个轴先组成 task signature，Gemini-3-Pro 再一次性实例化 source files、Dockerfile、unit tests 和 instruction。最关键的变化是：TMax 不做昂贵的 teacher solvability validation。*

TMax 的九个采样轴：

| Axis | Cardinality / 示例 | 控制什么 |
|---|---|---|
| Domain | 9：security、SWE、file ops、data querying… | 主题覆盖 |
| Skill type | 每个 domain 4–7 类 | 知识类型 |
| Primitive skills | 每个 domain 20–40；每题采 3–5 个 | 组合能力 |
| Persona | 每个 domain 6–18 个 | 使用场景 |
| Language | Python、C、Bash、C++、Rust、Go、multi-language、any | 实现分布 |
| Task complexity | short / moderate / complex / intricate | workflow 长度 |
| Command complexity | bash-only / bash+code / bash+code+services | action space |
| Fixture | text、image、audio、video、binary、vendored package、multi-service | 输入形态 |
| Verifier | exact text、metric、adversarial、fuzz、multi-protocol | reward 形态 |

它的采样并非简单笛卡尔积。代码里还做了：

- language weighted sampling，Python 仍占最高权重；
- 每题随机选 3–5 个 primitive skills；
- real-software scenario anchor 以约 0.35 概率注入；
- `rl_v2` 对 intricate task、非 legacy fixture 和 verifier 做上采样；
- 任何新型 fixture/verifier 任务路由到预装 OCR、ffmpeg、binutils、科学计算库的 `base_intricate` image。

### 5.2 Prompt contract

TMax 代码公开的 task generator prompt 可以压缩成下面这份 field contract：

```text
System:
  role = domain-specific task builder
  requirements = challenging, programmatically verifiable, self-contained, realistic
  output = <task> public instruction </task>
           <truth> privileged verification data </truth>

User:
  skill_type
  primary_language
  3–5 primitive_skills
  task_complexity
  command_complexity
  persona/scenario
  optional real-software anchor
  verifier_kind
  fixture_kind
```

`<truth>` 不是简单答案字符串，而必须声明：

- exact paths；
- setup 前应存在的对象；
- agent 应创建的对象；
- 对 derived value 的可复现计算过程；
- verifier-specific parameters。

例如：

- `metric_threshold`：metric 公式、reference、threshold、output path；
- `adversarial_corpus`：evil/clean corpus 路径、双向 pass criterion、entry point；
- `fuzz_equivalence`：oracle path、input distribution、N、agent executable；
- `multi_protocol`：host:port、protocol request/response、credentials。

然后独立生成：

1. initial-state pytest；
2. final-state pytest；
3. per-task Apptainer definition；
4. build + smoke test。

公开实现默认 task prompt `temperature=1.0`，initial/final test prompt `temperature=0.6`，每次最多 2,048 tokens。

### 5.3 Graded verifier 为什么比 exact text 更重要

TMax 不只问“最终文件是否一字不差”，而是把难度做进 verifier：

| Verifier | 例子 | 难度旋钮 |
|---|---|---|
| `exact_text` | 文件等于参考答案 | 无 |
| `metric_threshold` | SSIM ≥ 0.95、speedup ≥ 1.3× | threshold |
| `adversarial_corpus` | 恶意样本全拦截、正常样本全保留 | corpus size / pass rate |
| `fuzz_equivalence` | 随机 N 个输入与 oracle bit-exact 一致 | N / input distribution |
| `multi_protocol` | HTTP/TCP/gRPC/SMTP 真实请求正确 | protocol / condition 数 |

这比单纯增加 prompt 长度更可靠，因为它直接改变 reward surface。

### 5.4 为什么 TMax 敢跳过 teacher filter

TMax 只要求：

```text
container builds + tests execute
```

它不在数据生成时证明：

```text
a strong teacher can solve the task
```

理由是训练时每个 prompt 会有一组 rollout；如果 policy 对这个任务全部失败，group reward 标准差为零，不产生有效梯度，于是直接在 RL batching 阶段过滤。

这是一种非常不同的成本分配：

```text
Endless: generation-time hard filtering
TMax:    training-time soft filtering
```

优点是便宜、吞吐高；风险是 container 可执行不等于 task 与 verifier 语义正确，错误环境仍可能消耗 rollout compute。

### 5.5 Harness

TMax 使用 mini-SWE-agent 风格的 **Vanillux2Agent**：

- bash tool schema；
- submit marker；
- tool-format error recovery；
- output truncation；
- 在 Harbor active environment 里执行。

训练基础设施是 open-instruct + vLLM，sandbox backend 使用 Podman 或 Apptainer；公开 Harbor 数据也可跑在 Docker 或 Daytona。论文还比较了自身 harness、OpenHands、mini-SWE-agent、Terminus-2，说明 RL gain 能跨 harness 转移，但最好分数仍出现在训练时相近的 harness。

---

## 6. SkillSynth：不只控制 task diversity，还控制 trajectory diversity

### 6.1 为什么随机拼 skills 不够

假设从技能池随机抽：

```text
OCR + Kubernetes + PDF table extraction + TLS certificate
```

LLM 也许能写出一个题面，但四个技能未必形成因果 workflow。最终 constructor 常把它们降级成并列 checklist，实际解题路径仍很短。

SkillSynth 的核心变化是把 skill 表成状态转换：

$$
\kappa: \sigma_{\text{pre}} \rightarrow \sigma_{\text{post}}
$$

其中：

- scenario 是某一决策点的环境语义状态；
- skill 是把一个 scenario 转成下一个 scenario 的多步 workflow。

### 6.2 Skill graph construction

![SkillSynth 的 skill graph construction pipeline](assets/paper-reading/terminal-agent-env-synthesis/skillsynth-graph-page.png)

*原论文 Figure 3 所在页。raw skills 先过滤，再为每个 skill 推断 pre/post scenarios；scenario 经聚类去重后，pre-cluster 与 post-cluster 做语义对齐，最后才得到可以采样 path 的 graph。这里的 scenario node 是连接不同 skill 的关键中介。*

数据源来自 ClawHub 与 public GitHub skills，先过滤：

1. 可在 Linux terminal 执行；
2. 是结构化 workflow，不只是 prompt engineering；
3. 没有 adversarial / jailbreak 行为；
4. 输出 deterministic、objectively verifiable。

之后分五步：

1. **Scenario inference**：输入 skill 的 Markdown、code、examples，推断多个 pre/post scenarios。
2. **Scenario dedup**：embedding 后两阶段聚类；Louvain coarse buckets + complete-linkage agglomerative clustering。
3. **Cross-skill alignment**：每个 post scenario 检索最相似的 1,000 个 pre scenarios，再由 LLM 判断兼容性；反向再做一次。
4. **Scenario merge**：把兼容的 pre/post 合成统一 node。
5. **Triple filter**：再次判断 `(scenario, skill, scenario)` 是否真是有效转换。

最终图规模：

- 82,073 scenario nodes；
- 57,214 skill-labeled transitions；
- 6,251 connected components；
- giant component 覆盖 85.6% nodes；
- median degree 2，max degree 752。

### 6.3 Path sampling

采样 path：

$$
\mathcal{P}=(\sigma_0,\kappa_1,\sigma_1,\ldots,\kappa_L,\sigma_L), \quad 1 \le L \le 7
$$

不使用 uniform random walk，因为 hub scenario 会被重复访问。SkillSynth 维护：

- scenario visit count $\nu(\sigma)$；
- skill usage count $\mu(\kappa)$。

采样概率与历史频次成反比：

$$
p(\sigma)\propto(\nu(\sigma)+1)^{-1},\qquad
p(\kappa)\propto(\mu(\kappa)+1)^{-1}
$$

同一路径中不重复 scenario 或 skill，保证 monotone progression。这样控制的是训练轨迹中最低必要技能序列，而不只是题目关键词的覆盖率。

### 6.4 Multi-agent synthesis harness

每条 path 变成五类产物：

1. natural-language instruction；
2. initial filesystem snapshot；
3. containerized environment；
4. verification scripts；
5. oracle solution。

Harness 分工：

```text
skill-graph path
→ planner：sub-objectives + expected outputs
→ constructor：materialize all task artifacts
→ oracle execution check
→ rubric judge:
     instruction ↔ tests alignment
     instruction self-containedness
→ failed: diagnostic feedback → constructor repair
```

一轮运行从 3,721 paths 得到 3,560 usable tasks。平均 repair 2.31 cycles、11 tool calls；721 个首轮失败任务被修回。论文没有在主文明确写出允许的最大 repair cycles/tool calls 数值，因此分享时不要自行补数字。

### 6.5 Prompt 披露边界

论文公开了：

- graph construction 的准则；
- trajectory → scenario/skill 的抽取 prompt；
- embedding query 格式。

它没有完整公开 planner / constructor 的逐字 task synthesis prompt。因此可以复述 artifact schema 与 verify-repair control flow，但不能声称拿到了完整可复现 prompt。

### 6.6 Harness 与评测

- task synthesis：自研 multi-agent harness；
- task difficulty：Hy3 Preview 每题尝试 3 次；
- evaluation agent：Terminus 2；
- orchestration：Harbor；
- 128 个并发 Docker environments。

---

## 7. Terminal-World：skill 同时生成 I / E / V / G

### 7.1 为什么 agent skill 适合当 synthesis primitive

Terminal-World 认为一个好的 skill 天然包含：

- **what**：最终要完成什么；
- **when**：需要哪些输入、前置状态和适用条件；
- **how**：典型执行步骤、工具和 failure modes。

这三部分分别可以派生：

```text
what → instruction
when → environment blueprint
how  → execution guideline
```

所以不必先生成题面，再事后“给题面配一个 container”。

### 7.2 四阶段 pipeline

#### Stage A：Skill collection

从 ClawHub / SkillMP 收集 10,000 skills：

1. rule filter：去掉 terminal-irrelevant skills，剩 8,520；
2. LLM filter：terminal applicability 与 content richness 都必须 3/3，剩 3,025；
3. popularity filter：取下载量前 1,000，覆盖 12 categories / 63 subcategories。

再扩展：

- 同 subcategory 的 composition relation → 76 skill teams；
- 跨 subcategory 的 composition graph → 237 skill graphs；
- 全部 flatten 成统一 `skill.md`。

#### Stage B：Task generation

每个 skill/team/graph 与 FinePersonas 中一个 persona 配对。只有 pair 合理才生成：

$$
(\mathcal{I},\mathcal{E},\mathcal{V},\mathcal{G})
$$

- $\mathcal{I}$：instruction；
- $\mathcal{E}$：initial files + setup steps；
- $\mathcal{V}$：evaluation criteria；
- $\mathcal{G}$：给 teacher 的 execution guideline。

五维 judge 每一项都必须至少 4/5：

1. instruction quality；
2. closed-world solvability；
3. blueprint completeness；
4. guideline quality；
5. evaluation-criteria quality。

#### Stage C：Environment building

最终 sandbox 有三类 artifact：

```text
F       initial files
B_env   setup script
T_test  pytest verifier
```

每类 artifact 都走统一 GVR：

$$
x^{(0)}=\mathrm{Generate}(\cdot),\quad
x^{(t+1)}=\mathrm{Repair}(x^{(t)},\mathrm{Verify}(x^{(t)}))
$$

最多 3 个 repair iterations。

Initial files 按 generation mode 路由到三类 agent：

- `llm_direct`：直接生成文本/代码；
- `local_tool`：用 Python 等本地工具生成二进制或复杂 artifact；
- `remote_fetch`：search / fetch / download 外部资产。

File verifier 同时检查：

- internal correctness：格式与描述一致；
- external consistency：跨文件 path、schema、reference 一致。

Setup 使用 shared Debian 13 sandbox + per-task setup script，而非每题一个 Docker image。env verifier 不只看 exit code，还生成 probing commands 检查 package import、CLI availability、directory 与版本。

Pytest verifier 必须：

- 可执行，无 syntax/import error；
- 在 pre-execution initial state 全部失败；
- 只检查 agent 产生的结果，不重复检查已验证的 initial files。

#### Stage D：Trajectory collection

DeepSeek-V3.2 + Terminus2 接收：

```text
instruction I + execution guideline G + history H
```

rollout 后运行 pytest。论文保留成功与失败 trajectories；SFT 前从模型输入中移除 guideline，让 student 学 terminal interaction，而不是依赖隐式提示。

### 7.3 Prompt 为什么值得展示

Terminal-World 附录把 prompt 拆得非常细。分享时建议展示三张“prompt contract”而不是贴满整页文字。

**Task generation prompt**

```text
Inputs:
  Agent Skill
  Persona

Output JSON:
  pair_relevance
  task_title
  instruction
  initial_files[{generation_mode, filepath, description}]
  setup_steps[]
  evaluation_criteria[]
```

Relevance check 很重要：persona 与 skill 不相关时输出 `UNRELATED_PAIR`，而不是强行编故事。

**Environment setup prompt**

```text
Inputs:
  base environment specification
  instruction (context only)
  blueprint
  pre-seeded files

Output:
  bash commands for dependency/runtime setup only

Negative constraints:
  do not create application code
  do not solve the task
  do not overwrite pre-seeded assets
```

**Pytest verifier prompt**

```text
Inputs:
  instruction
  evaluation criteria
  initial text files
  initial asset metadata
  validated paths

Output JSON:
  system_packages[]
  python_packages[]
  helper_files[]
  test_outputs_py
```

其中最关键的 prompt engineering 不是角色描述，而是**scope isolation**：file agent 只造文件、env agent 只装环境、verifier 只验终态、teacher 才解题。

### 7.4 数据与成本

- 5,723 tasks；
- 4,973 personas；
- 3,723 single-skill + 1,000 team-skill + 1,000 graph-skill；
- 平均 2.25 initial files；
- 104 file types；
- 平均 4.27 pytest tests；
- 平均 trajectory 13.44 steps / 18,176 tokens；
- 6,884 accepted task specs → 5,723 executable envs，construction success 83.1%；
- pipeline 总成本约 \$999.59，约 \$0.17 / trajectory。

---

## 8. CLI-Universe：把监督密度放在第一位

### 8.1 三阶段 pipeline

![CLI-Universe 三阶段 pipeline](assets/paper-reading/terminal-agent-env-synthesis/cli-universe-pipeline-page.png)

*原论文 Figure 1 所在页。Step 1 不是直接写题，而是 taxonomy anchor → evidence-guided research → blueprint；Step 3 又把 test agent 与 solution agent 分开，最后要求 initial fail、solution pass。*

#### Stage 1：Task blueprint construction

候选任务由四维 anchor 定义：

| Dimension | 问题 |
|---|---|
| Domain | 任务发生在哪个技术领域 |
| Skill type | 难点依赖什么专业知识 |
| Capability | 希望触发 exploration、recovery、planning 等哪种行为 |
| Engineering pillar | 新功能、debug、deployment、systems programming 等哪类工作 |

然后 research agent 搜索：

- repositories；
- official docs；
- issue discussions；
- tutorials；
- usage examples。

研究结果被编译进 blueprint：

- `Instruction.md`；
- internal `Hint.md`；
- environment checklist；
- validation target；
- concrete I/O contract；
- known failure modes 与工具约束。

如果技术材料不足、工具不可得或约束冲突，候选直接丢弃。

#### Stage 2：Environment realization

Asset strategy 有两条路：

```text
pull & adapt:
  repository / docs / dataset / config / logs
  → normalize / inject controlled fault / rescope

synthesize:
  no suitable external asset
  → controlled variants with known ground truth
  → generate verification metadata
```

之后打包 Docker：

- pinned dependencies；
- environment variables；
- services / permissions；
- fixed filesystem paths；
- inter-component references；
- smoke tests：install、service startup、layout、reachability。

#### Stage 3：Test construction + executable filtering

Test agent 根据 realized environment 与 validation target 生成测试，并按 rubric 迭代：

- correctness；
- determinism；
- edge-case coverage。

Solution agent 看 internal hint，生成成功 trajectory。

随后两层最有辨识度的过滤：

**Hint-conditional**

```text
without hint → fail
with hint    → pass
```

它不是只证明“任务可解”，而是要求 teacher supervision 对成功有实际增量。

**Fail-to-pass**

```text
tests(initial environment) = fail
tests(after hinted solution) = pass
```

最终只有 33.6% 候选留存。

![CLI-Universe 各阶段证据与候选留存](assets/paper-reading/cli-universe/source-filtering-evidence.png)

*原论文 Figure 2 的关键面板。作者不是只报告最终淘汰率，而是给每个阶段绑定可观察证据：research refinement 提升 solver turns、blueprint review 提高人类/模型接受率、合成 tests 与 Terminal-Bench 2 ground truth 对齐，最终五层过滤保留 33.6%。*

### 8.2 Prompt 和 harness 的披露边界

CLI-Universe 论文描述了 agent roles、artifact fields、rubric 与过滤逻辑，但没有公开逐字 prompt appendix，也没有公开生成代码。因此可以准确讲：

- prompt 输入包含 taxonomy anchor / realized env / validation target / internal hint；
- test 与 solution agent 角色隔离；
- trajectory teacher 是 Kimi-K2.6；
- benchmark evaluation 使用 Terminus 2、200 turns、avg@4；
- Codex + GPT-5.4 被用于 test semantic agreement 和 error analysis judge。

但不能声称：

- 知道 research agent 的完整 system prompt；
- 知道每轮 refinement 的精确 stop condition；
- 知道所有 synthesis agents 的温度、token budget 与 retry count；
- production harness 就是 Terminus 2。论文只明确说 Terminus 2 用于主要评测。

### 8.3 为什么这篇适合收尾

Endless 只问“强模型能否至少解出一次”；CLI-Universe 多问了一层：

> 这条成功 trajectory 是否真的提供了没有它就得不到的监督？

hint-free fail / hinted pass 是一个很强的 training-value filter。它可能丢掉本来就容易但仍有用的任务，也依赖 hint 的质量；但它让最终 6K trajectory 的监督密度明显高于“只要成功就收”。

![CLI-Universe 的组件消融、模型扩展与数据效率](assets/paper-reading/cli-universe/source-ablation-scaling.png)

*原论文 Figure 3。移除 asset strategy、query rubric 或 test rubric 都会降低结果，说明收益不是某一个 verifier 独立带来的；同一 6K 数据对 8B、14B、32B 的增益随模型容量扩大，也提示高密度环境监督没有在小规模数据处立即饱和。*

---

## 9. 五篇工作的真正分歧

### 9.1 Hard filtering vs soft filtering

| 路线 | 何时丢弃 | 优点 | 代价 |
|---|---|---|---|
| Endless | build/test 后 + teacher pass@16 | 数据进入 RL 前已知可解 | 16 次 teacher rollout 成本高；teacher ceiling |
| TMax | build 失败才硬丢；zero-pass 在 RL batch 丢 | 生成吞吐高，容易扩到 15K | 坏 verifier 可能消耗训练算力 |
| SkillSynth | oracle + rubric，失败可 repair | instruction/tests/path 三者更一致 | harness 复杂；LLM judge 仍可能共偏 |
| Terminal-World | 每个 artifact 都 GVR + 五维 judge | 错误定位细，repair yield 高 | agent 数多，prompt/interface 维护成本高 |
| CLI-Universe | research、blueprint、smoke、test、hint、fail2pass 多门 | supervision density 高 | 66.4% 淘汰，单位成功样本成本可能高 |

![CLI-Universe 的质量漏斗](assets/paper-reading/cli-universe/quality-funnel.svg)

*自制质量漏斗。它把 CLI-Universe 的核心设计压缩成一句话：最终 6K 不是任意成功对话，而是经过能力锚定、证据研究、环境实现、test/solution 隔离与 fail-to-pass 后留下的监督单元。*

### 9.2 Diversity 到底指什么

五篇论文的“多样性”不是一回事：

- Endless：task category / complexity / scenario 的**题面多样性**；
- TMax：九个采样轴与分布平衡的**组合多样性**；
- SkillSynth：minimal workflow path 的**trajectory diversity**；
- Terminal-World：skill/team/graph × persona 与 104 file types 的**语义和环境多样性**；
- CLI-Universe：真实 evidence / constraints / failure modes 的**技术情境多样性**。

讲到这里可以问听众：

> 如果 task title 不同，但 solver 永远执行 `cat → python script → save answer`，这算多样吗？

SkillSynth 对这个问题的回答最直接：不算，必须控制 path 中出现的 scenario-skill pairs。

### 9.3 Per-task image vs shared sandbox

两种工程路线：

**Per-task image**

- Endless、TMax、CLI-Universe；
- isolation 强；
- 环境更接近 artifact；
- build/storage 成本高。

**Shared sandbox + per-task setup**

- Terminal-World；
- base environment 复用，启动更快；
- 需要非常严格的 setup scope 与 fresh-state contract；
- shared base 的工具分布可能成为隐藏先验。

SkillSynth 生成 containerized environment，但论文更关注 synthesis harness，而非镜像缓存策略。

### 9.4 Verifier 不是最后补的一段 pytest

![Terminal environment verifier 的可靠性阶梯](assets/paper-reading/terminal-agent-env-synthesis/verifier-ladder.svg)

*自制 verifier 阶梯。只检查文件存在很容易制造假阳性；逐步加入行为 invariant、deterministic edge cases、fail-to-pass、instruction alignment 与 graded criteria，reward 才越来越接近用户真正要求的状态转换。*

可靠 verifier 至少要满足：

1. **Initial-state negative**：初态不能通过；
2. **Solved-state positive**：oracle / reference solution 后必须通过；
3. **Instruction alignment**：不能检查用户没要求的限制；
4. **Non-vacuity**：不能只检查文件存在；
5. **Determinism**：重跑结果稳定；
6. **Robustness**：尽量检查行为或 invariant，而非脆弱的全文相等；
7. **No trace inspection**：只看环境终态，不看 agent 自述；
8. **Useful resolution**：能产生 binary 或 graded learning signal。

TMax 的 graded verifier 与 CLI-Universe 的 fail-to-pass 可以组合：前者改善 reward resolution，后者保证 state transition 有效。

---

## 10. 如果我们自己搭一条 pipeline

我会采用下面的混合方案：

### Phase 1：Coverage planning

从 TMax 学：

- domain / skill / persona / language / task complexity / command complexity；
- fixture 与 verifier 独立采样；
- 对最终 corpus 做 entropy-based balance audit。

从 SkillSynth 学：

- skill 要有 pre/post scenarios；
- path 采样做 inverse-frequency weighting；
- 不允许随机 skills 只形成并列 checklist。

### Phase 2：Blueprint

从 Terminal-World 与 CLI-Universe 学：

```yaml
instruction: public user request
initial_files:
  - path
  - generation_mode
  - reproduction_spec
setup_steps:
evaluation_criteria:
internal_hint:
expected_intermediate_states:
skill_path:
evidence:
```

在生成环境之前做：

- persona-skill relevance；
- closed-world solvability；
- instruction/evaluation alignment；
- evidence availability；
- safety / license / network constraints。

### Phase 3：Artifact generation

按 artifact 类型路由：

- text/code → LLM direct；
- image/audio/binary/data → deterministic local tool；
- real package/docs → pinned remote fetch；
- dependencies/services → environment agent。

每个 agent 只有一个 scope，避免一个模型同时造题、造答案、造测试而发生 shared hallucination。

### Phase 4：Executable QA

最低门槛：

```text
build/setup success
initial probes pass
final verifier runs
final verifier(initial) fails
oracle solution executes
final verifier(solved) passes
```

再加：

- repeated-run determinism；
- instruction ↔ verifier rubric judge；
- edge-case mutation test；
- no hidden network dependency；
- timeout and resource budget；
- test leakage scan。

### Phase 5：Difficulty calibration

不要只用“solver turns 多”定义困难。建议同时记录：

- strong-model pass@k；
- pass@k curve slope；
- median commands / unique commands；
- failure recovery count；
- verifier partial score；
- wall-clock / resource usage；
- minimal skill path length。

Learnable band 可以定义为：

```text
not pass@k = 1.0
not pass@k = 0.0
```

而不是把所有最难任务直接投入 RL。

### Phase 6：Trajectory collection

建议保留三种 rollout：

- unguided success；
- guided success；
- informative failure。

并记录：

- environment version；
- agent harness version；
- model / sampling config；
- command / observation；
- verifier output；
- terminal reason；
- hint visibility。

这样之后才能判断 gain 来自 task、harness、teacher 还是 training recipe。

---

## 11. Sharing 时可以现场展示的三个例子

### Example A：空测试

```python
def test_output_exists():
    assert Path("/app/output.json").exists()
```

问题：agent 写 `{}` 也能过。改成：

```python
def test_output_contract():
    data = json.loads(Path("/app/output.json").read_text())
    assert set(data) == {"summary", "records"}
    assert len(data["records"]) == EXPECTED_COUNT
    assert recompute_summary(data["records"]) == data["summary"]
```

对应论文：Terminal-World 的 verifier prompt 与 CLI-Universe 的 rubric-gated tests。

### Example B：随机 skill composition

```text
skills = [OCR, nginx config, SQL aggregation]
```

差的任务：分别 OCR、改 nginx、跑 SQL，三段互不相干。

好的 path：

```text
scanned invoices
--OCR--> normalized text records
--load--> SQLite database
--aggregate--> monthly totals
--serve--> local HTTP report
```

对应论文：SkillSynth 的 scenario-mediated skill graph。

### Example C：binary reward 太粗

任务：优化图像压缩。

差 verifier：

```text
compressed.png exists → 1
```

更好的 verifier：

```text
SSIM >= 0.95
size <= 0.60 × original
dimensions unchanged
```

对应论文：TMax `metric_threshold`。再叠加 CLI-Universe：

```text
initial state fails
hint-guided solution passes
```

---

## 12. 最后五分钟的结论

### 结论一：环境才是 agent RL 的 supervision unit

自然语言 task 只是入口。真正被训练的是：

```text
state → action → observation → state transition → executable reward
```

### 结论二：多样性必须在多个层级测

至少分开：

- instruction diversity；
- environment / fixture diversity；
- verifier diversity；
- minimal skill-path diversity；
- actual trajectory diversity。

### 结论三：过滤位置决定成本结构

- 生成时硬过滤：成功样本贵，但进入训练的数据干净；
- 训练时软过滤：环境便宜，但 rollout 可能浪费；
- 最现实的系统可能是分层门槛：便宜静态检查 → 少量 oracle → policy-side soft filter。

### 结论四：prompt 最重要的是 interface contract

可复现的 prompt 不只是“你是一个资深工程师”，而是：

- 输入字段是什么；
- 输出 schema 是什么；
- agent scope 是什么；
- negative constraints 是什么；
- error feedback 如何回流；
- stop / retry / discard 条件是什么。

### 结论五：不要把 SFT / RL 指标当成环境质量的唯一证据

最终 benchmark gain 受到 teacher、student、harness、turn budget、训练算法与数据混合共同影响。环境质量应该先用自身的：

- build rate；
- fail-to-pass rate；
- instruction-test agreement；
- determinism；
- difficulty distribution；
- trajectory coverage；
- unit cost；

来审计。

![Terminal agent 失败模式归因示意](assets/paper-reading/cli-universe/source-failure-attribution.png)

*原论文 Figure 5。即使是前沿模型，很多失败也发生在“没有正确验证是否完成”，而不是完全不会执行。这正是为什么 environment synthesis 必须把 verifier 视为训练对象的一部分，而不是数据生产线末端的附属脚本。*

---

## 13. 讨论问题

1. o3 pass@16 全失败的 task，是坏任务，还是超出当前 teacher 能力的好任务？
2. TMax 把 zero-pass task 推到 RL 时过滤，节省了生成成本，但会浪费多少 rollout compute？
3. skill graph 控制了预期 minimal path，agent 实际 trajectory 偏离这条 path 时，应该视为 diversity 还是 noise？
4. hint-free fail / hinted pass 会不会偏向“只有特定解法”的任务？
5. shared sandbox 与 per-task image，哪个更容易发生 hidden dependency leakage？
6. verifier 与 task 由同一模型家族生成时，怎样发现 shared misconception？
7. failed trajectories 应该用于 SFT、RL、preference learning，还是只做 error mining？

---

## 14. Prompt / code / harness 复现索引

| Paper | Prompt availability | Code / harness availability | 分享时应怎样表述 |
|---|---|---|---|
| Endless Terminals | 论文描述结构；代码仓公开 generation scripts | 公开；Apptainer + Harbor + SkyRL | 可以讲具体文件与 3-round / pass@16 |
| TMax | 公开代码含 task、initial/final test、fixture/verifier prompt | 公开；Vanillux2Agent、Harbor、open-instruct | 可以展示 field contract 与关键 prompt 片段 |
| SkillSynth | 公开 graph/trajectory extraction prompts；未完整公开 constructor prompt | 论文公开 harness 结构 | 讲 schema 与 control flow，不声称完整复现 |
| Terminal-World | 论文附录 D 给出完整分角色 prompt templates | 论文给 Terminus2 JSON prompt 与 shared sandbox 规格 | 最适合讲 prompt decomposition |
| CLI-Universe | 未公开逐字 prompt | 未公开 synthesis implementation；评测用 Terminus 2 | 明确“论文级流程可知，实现参数未披露” |

---

## 参考资料

- [Endless Terminals: Scaling RL Environments for Terminal Agents](https://arxiv.org/abs/2601.16443)
- [Endless Terminals code](https://github.com/kanishkg/endless-terminals)
- [TMax: A Simple Recipe for Terminal Agents](https://arxiv.org/abs/2606.23321)
- [TMax code and data-generation prompts](https://github.com/hamishivi/tmax)
- [Toward Scalable Terminal Task Synthesis via Skill Graphs (SkillSynth)](https://arxiv.org/abs/2604.25727)
- [Terminal-World: Scaling Terminal-Agent Environments via Agent Skills](https://arxiv.org/abs/2605.20876)
- [CLI-Universe: Towards Verifiable Task Synthesis Engine for Terminal Agents](https://arxiv.org/abs/2606.22883)
