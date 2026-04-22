---
name: coding-knowledge-init
description: >-
  扫描业务子模块的多个前后端代码仓库，通过交互式引导生成面向 AI Coding 的三层分层专家知识库：基础技术层、业务层、代码仓库层。
  输出结构化的 coding-knowledge/ 目录，每层包含 INDEX.md 索引（控制在 200 行内）和按需加载的详细子文件。
  当用户提到"初始化编码知识库"、"生成 coding 知识库"、"构建代码专家知识"、"AI编码知识初始化"、
  "帮我梳理技术栈和业务架构"、"分析多个代码仓库"、"建立代码仓库知识体系"时使用此 skill。
  即使用户只是说"我有几个代码仓库想让 AI 了解一下"或"帮我把这些项目的知识整理出来方便后续编码"，
  也应该使用这个 skill。本 skill 面向 AI 辅助编码，产出物是让 AI 能像顶级程序员一样理解和编写代码所需的分层知识。
---

## Purpose

要让 AI 像顶级程序员一样在一个业务领域内编写代码，它需要掌握三层知识：

1. **基础技术层** — 公司的技术栈规范、中间件、架构模式、CI/CD 流程等"水下冰山"，这些知识不写在代码里但深刻影响每一行代码的写法
2. **业务层** — 整体业务架构和细分业务领域的领域知识，顶级程序员不仅知道怎么写代码，还知道为什么这样写
3. **代码仓库层** — 每个仓库的代码架构、核心调用链、数据库结构、关键符号索引，编码时能快速定位和准确修改

这三层知识自下而上构建：基础技术层是通用底座，业务层建立在技术层之上提供领域语境，代码仓库层则是实际编码时的精确导航。

## 参考文件导航

本 skill 的详细模板和参考知识存放在 `references/` 目录中，按需读取：

| 文件 | 内容 | 何时读取 |
|------|------|---------|
| `references/templates.md` | 所有输出文件的 markdown 模板 | Phase 3 生成文档时 |
| `references/tech-stack-guide.md` | 各技术栈 JSON 字段→文档的映射指南 | Phase 1.2 读取 scan-result.json 时 |
| `references/phase2-rules.md` | Phase 2 问题触发规则和默认策略 | Phase 2 开始前 |
| `references/agent-prompt-template.md` | 并行合成的子 Agent prompt 模板 | Phase 1.3 启动并行 Agent 时 |
| `references/quality-checks.md` | 覆盖率检查规则、评分卡模板、自动修复策略 | Phase 3.5 第四级校验时 |

---

## 输出目录结构

```
coding-knowledge/
├── config.yaml                       # 项目配置：业务名称、子模块、仓库映射
├── INDEX.md                          # 顶层索引：三层知识概览和导航
├── infra/                            # 第1层：基础技术层
│   ├── INDEX.md
│   ├── tech-stack.md                 # 技术栈规范
│   ├── middleware.md                 # 基础设施与中间件规范
│   ├── app-architecture.md           # 应用选型与分层规范
│   ├── code-quality.md               # 代码质量规范
│   ├── cicd.md                       # CI/CD 平台与流程
│   └── security.md                   # 安全合规规范
├── business/                         # 第2层：业务层
│   ├── INDEX.md
│   ├── overall-architecture.md       # 整体业务架构与服务拓扑
│   ├── glossary.md                   # 业务术语表（术语定义 + 跨系统别名映射）
│   ├── domains/                      # 细分业务架构
│   │   ├── INDEX.md
│   │   └── {domain-name}/
│   │       ├── overview.md           # 领域概述、核心流程
│   │       ├── domain-model.md       # 领域模型与数据关系
│   │       └── cross-service.md      # 跨仓库调用关系
│   └── prd-reference/                # PRD 参考资料（产品语言，不含代码细节）
│       ├── existing-features.md      # 现有功能清单（按业务分类）
│       ├── business-flows.md         # 核心业务流程（含异常处理）
│       ├── user-roles.md             # 角色定义与权限矩阵
│       └── design-patterns.md        # 运营后台菜单结构 + 通用交互模式
├── repos/                            # 第3层：代码仓库层
│   ├── INDEX.md                      # 仓库层索引（含场景→模块路由表）
│   └── {repo-name}/
│       ├── .scan-snapshot.md         # 扫描中间快照（AI编码时无需读取）
│       ├── architecture.md           # 仓库代码架构（含职责边界）
│       ├── codebase-index.md         # 代码索引
│       ├── symbols.md               # 关键类/方法/接口签名索引
│       ├── database-schema.md        # 数据库表结构（有数据库依赖时生成）
│       └── call-chains.md            # 核心业务调用链
└── knowledge-gaps.md                 # 知识完整性检查报告
```

### 核心设计原则

1. **分层按需加载** — 每层有 INDEX.md 索引（≤200 行），AI 先读索引再按需加载详细文件
2. **从代码推断 + 交互补充** — 先自动提取，无法推断的部分生成带选项的问题引导用户补充
3. **扫描快照防丢失** — 每个仓库先生成 `.scan-snapshot.md`，防止上下文压缩丢失信息

---

## 工作流程

### Phase 0: 交互式信息收集

通过引导式对话收集必要信息。

**场景 A — 用户提供了模块/仓库清单表格**（推荐方式）：

用户通常以表格形式提供信息，格式类似：
```
模块    子模块        服务/仓库名              服务描述
交易    订单处理      order_srv                订单核心服务
                      pay_srv                  支付服务
        履约          fulfill_srv              履约&配置服务
                      fulfill_task             履约异步任务服务
        外部对接      channel_srv              渠道对接服务
        运营平台      ops_api                  运营系统后台(含交易管理)
```

解析规则：
- 第一列为业务模块名（作为 `business_name`）
- 第二列为子模块（作为 `domains[].name`）
- 空的模块/子模块列表示沿用上一行的值
- 服务描述直接写入 `config.yaml` 的 `description` 字段，后续生成 architecture.md 职责边界时作为参考
- 如用户提供了 git 仓库地址，按以下逻辑处理：
  1. 询问用户仓库是否已 clone 到本地，如已 clone 则获取本地路径
  2. 如未 clone，询问用户希望 clone 到哪个目录（默认 `~/repos/{business_name}/`）
  3. 自动执行 `git clone <url> <target_dir>/<repo_name>`（并行 clone 加速）
  4. clone 完成后将本地路径写入 config.yaml

直接解析为 `config.yaml`，跳过交互问答。

**场景 B — 用户只给了仓库路径，信息不完整**：

**第一轮**：业务名称、子模块划分、各子模块对应仓库路径、每个仓库的一句话描述
**第二轮**：每个仓库所属子模块、前后端类型、是否有共享公共仓库

**场景 C — 单仓库**：简化，只需确认业务名称和仓库类型。

将信息保存到 `coding-knowledge/config.yaml`：

```yaml
business_name: "交易业务"
domains:
  - name: "订单处理"
    repos:
      - path: "/path/to/order_srv"
        type: backend
        service_name: "trade.order_srv"
        description: "订单核心服务"
      - path: "/path/to/pay_srv"
        type: backend
        service_name: "trade.pay_srv"
        description: "支付服务"
  - name: "履约"
    repos:
      - path: "/path/to/fulfill_srv"
        type: backend
        description: "履约&配置服务"
shared_repos:
  - path: "/path/to/common-lib"
    type: library
```

#### 进度恢复机制

整个流程开始前，检查 `coding-knowledge/.progress.yaml`：

- **存在** → 读取进度，向用户展示摘要，询问"从断点继续？还是重新开始？"
- **不存在** → 正常执行，Phase 1 开始时创建

```yaml
started_at: "2026-04-03T10:00:00"
current_phase: "phase_1"
phase_0: {status: completed, config_yaml: true}
phase_1:
  status: in_progress
  scan_script_done: true
  batch_index: 2           # 当前处理到第几批（大规模场景）
  repos:
    order_srv: {status: completed, docs: [".scan-snapshot.md", "architecture.md", "symbols.md", "codebase-index.md", "database-schema.md", "call-chains.md"]}
    fulfill_srv: {status: in_progress, docs: [".scan-snapshot.md"]}
    pay_srv: {status: pending}
phase_2: {status: pending, user_answers: {}}
phase_3: {status: pending, repos: {}, business_done: false, infra_done: false}
phase_4: {status: pending}
phase_5: {status: pending}
```

**更新规则**：
- 每个仓库开始时标记 `in_progress`，完成后标记 `completed` 并记录已生成的文件列表
- Phase 2 用户的每个回答立即写入 `user_answers`
- 断点恢复时：跳过 `completed` 的仓库，`in_progress` 的重新处理
- 全部完成后删除 `.progress.yaml`

---

### Phase 1: 代码扫描与知识合成

分两步：先用 Python 脚本批量提取结构化数据（秒级），再由 LLM 读取 JSON 合成文档。

#### 1.1 运行扫描脚本

使用 `scripts/scan-repo.py` 和 `scripts/batch-scan.sh` 批量扫描，生成 `scan-result.json`。

```bash
# 单仓库
python3 scripts/scan-repo.py /path/to/repo --output-dir coding-knowledge/scan-data/

# 批量扫描
bash scripts/batch-scan.sh /path/to/repos coding-knowledge/scan-data/
```

**脚本自动检测技术栈**：Java（pom.xml/build.gradle）、Go（go.mod）、PHP（composer.json）、前端（package.json+vue/react）、Node.js（package.json+express/nestjs）、Python（requirements.txt/pyproject.toml）。

**降级策略 — 脚本失败时**：

如果 scan-repo.py 执行失败（Python 环境缺失、权限问题、脚本 bug 等），按以下策略降级：

1. **单个仓库失败**：记录失败原因到 `.progress.yaml`，对该仓库回退到 LLM 直接扫描模式：
   - 用 Grep 搜索关键注解/文件模式定位核心类
   - 用 Read 读取源码提取方法签名
   - 直接生成 `.scan-snapshot.md`（跳过 JSON 中间步骤）
   - 在 `knowledge-gaps.md` 标注"该仓库为 LLM 直接扫描，信息完整度可能低于脚本扫描"

2. **批量扫描全部失败**（如 Python3 不可用）：
   - 告知用户脚本环境问题，询问是否继续以 LLM 直接扫描模式运行
   - 如用户同意，按仓库数量评估：≤5 个仓库直接扫描，>5 个建议用户先解决环境问题
   - LLM 直接扫描时，每仓库按 references/tech-stack-guide.md 中的字段清单 Grep/Read

3. **部分仓库失败**：成功的用 JSON，失败的用 LLM 直接扫描，两种模式的产出合并进同一知识库

#### 1.2 LLM 读取 JSON 合成文档

读取 `references/tech-stack-guide.md` 了解各技术栈的字段映射，然后读取每个仓库的 `scan-result.json`，合成以下文件（按此顺序，有依赖关系）：

1. `.scan-snapshot.md` — 基础数据，所有后续文件依赖它
2. `database-schema.md` — call-chains 需引用表结构（无数据库则跳过）
3. `symbols.md` — call-chains 需引用方法签名
4. `call-chains.md` — 依赖 2 和 3
5. `codebase-index.md` — 综合索引
6. `architecture.md` — 综合概览，必须包含"职责边界"章节

生成文件时读取 `references/templates.md` 获取对应模板。

#### 1.3 并行合成策略

**当仓库数量 >= 3 时，使用 Agent 工具并行合成文档。**

- **单仓库**：直接在主流程中读取 JSON 合成全套文档
- **3+ 仓库**：每 5-8 个仓库一批，启动并行 Agent

**大规模场景管理**（仓库 > 15 个）：

| 规模 | 分批策略 | 并行 Agent 数 | 检查点 |
|------|---------|-------------|--------|
| 3-15 个仓库 | 单批处理 | 2-3 个 Agent，每个 5-8 仓库 | 批次完成后更新 .progress.yaml |
| 16-30 个仓库 | 分 2 批 | 每批 2-3 个 Agent | 每批完成后更新 .progress.yaml，汇总中间结果 |
| 31-50 个仓库 | 分 3-4 批 | 每批 2-3 个 Agent | 每批完成后更新 .progress.yaml，检查 context 剩余 |
| 50+ 仓库 | 分 5+ 批 | 每批 2-3 个 Agent | 每批完成后强制 Re-read .progress.yaml 刷新状态 |

**每批处理流程**：
1. 读取 `.progress.yaml` 确认当前批次
2. 启动并行 Agent 处理本批仓库
3. 解析所有 `===REPO_COMPLETE===` 块
4. 更新 `.progress.yaml`（batch_index + 各仓库状态）
5. 如非最后一批，继续下一批

**context 保护**：每完成一批后，Re-read `.progress.yaml` 和已完成仓库的关键摘要（跨服务调用目标、MQ topics），释放本批的详细数据。

**先 Read `references/agent-prompt-template.md` 获取完整的子 Agent prompt 模板**，严格使用该模板构造 prompt。模板包含仓库列表格式、生成顺序、质量要求、输出格式等完整规范。

**主 Agent 解析子 Agent 输出**：提取 `cross_service_targets` 和 `mq_topics` 用于 Phase 3 生成 cross-service.md，更新 `.progress.yaml`。

---

### Phase 2: 交互式知识补充

先 Read `references/phase2-rules.md` 获取完整的触发规则表。

基于 scan-result.json 和 .scan-snapshot.md，按规则自动生成补充问题。每轮 3-5 个问题，分 2-3 轮进行。三轮问题：
1. **基础技术层（必问）** — CI/CD、代码规范、跨服务规范、MQ 规范、数据库规范、安全规范
2. **业务层（动态生成）** — 仓库职责边界、跨服务调用场景、相似 Entity 区分、枚举含义、核心流程
3. **补充确认（可选）** — 对置信度 low 的推断向用户确认

使用 AskUserQuestion 展示问题，每个回答立即写入 `.progress.yaml`。用户可随时选择"全部跳过"。

---

### Phase 3: 知识库生成

基于扫描快照和用户补充信息，生成完整的三层知识库。先 Read `references/templates.md` 获取所有模板。

**生成顺序（严格按此顺序，文件之间有依赖）**：

```
3.1 repos/ 层（如 Phase 1 Agent 已完成则跳过，仅做质量检查）
    ① .scan-snapshot.md → ② database-schema.md → ③ symbols.md
    → ④ call-chains.md → ⑤ codebase-index.md → ⑥ architecture.md

3.2 business/ 层（依赖 repos/ 的跨服务信息）
    ① glossary.md → ② overall-architecture.md
    → ③ domains/{domain}/overview.md → ④ domain-model.md → ⑤ cross-service.md
    → ⑥ prd-reference/existing-features.md → ⑦ business-flows.md
    → ⑧ user-roles.md → ⑨ design-patterns.md

3.3 infra/ 层（依赖 Phase 2 用户补充 + repos/ 技术栈信息）
    生成顺序不敏感，可并行

3.4 INDEX.md 文件（最后生成）
    ① repos/INDEX.md（含场景路由表 + 同名/易混淆模块区分）
    ② business/INDEX.md → ③ business/domains/INDEX.md
    ④ infra/INDEX.md → ⑤ 顶层 INDEX.md
```

#### 3.5 完整性自检与质量校验

生成所有文件后，执行 **四级校验**：

**第一级：文件存在性检查**
- 每个 repo 目录：.scan-snapshot.md, architecture.md（含"职责边界"章节）, codebase-index.md, symbols.md（无占位描述）, database-schema.md（有数据库时）, call-chains.md
- business/：glossary.md, overall-architecture.md, 每个 domain 的 overview.md, prd-reference/ 下的 existing-features.md, business-flows.md, user-roles.md, design-patterns.md
- infra/：tech-stack.md, middleware.md（有中间件时）
- repos/INDEX.md：包含"场景路由表"，多仓库时包含"同名/易混淆模块区分"
- 所有 INDEX.md ≤ 200 行

**第二级：内容准确性抽查**（每仓库 2-3 项）
- symbols.md 行号验证：随机 3 个 Controller 方法，Read 源码验证行号（±5 行）
- call-chains.md 方法引用：检查引用的方法名在 symbols.md 中有对应
- database-schema.md 字段：与 scan-result.json 中 entities.fields 对比

**第三级：交叉一致性检查**
- 术语一致性：glossary.md 覆盖核心 Entity class_name
- 跨服务一致性：cross-service.md 与各仓库 .scan-snapshot.md 的跨服务调用一致
- INDEX.md 导航完整性：路径指向实际存在的文件

**第四级：覆盖率与完整性量化评估**

**Read `references/quality-checks.md` 获取完整的覆盖率检查规则、评分卡模板和自动修复策略。** 这是质量自检的核心——量化评估知识库对实际代码的覆盖程度，检查 symbols.md 覆盖率（Controller ≥90%、Service ≥80%、Entity ≥80%）和 call-chains.md 完整性（跨服务调用 ≥90%、MQ topic 100%、双向一致 100%），不合格时自动修复。

如有缺失或不一致，**立即修正**。

---

### Phase 4: 知识完整性检查

生成 `knowledge-gaps.md`，包含：
- 各层完整度百分比和关键缺失
- 仓库扫描完整度矩阵
- 按优先级分类的待补充项（P0 阻塞性 / P1 建议 / P2 锦上添花）
- 下一步建议

模板详见 `references/templates.md`。

---

### Phase 4.5: 知识库可用性验证（可选但推荐）

生成完知识库后，用 1-2 个典型编码场景快速验证 AI 能否真正用好这些知识。

**验证方法**：

从 config.yaml 中选择一个核心仓库，设计 2 个模拟场景：

**场景 1 — 代码定位验证**：
```
假设你收到需求："修改 {从 glossary.md 中选一个核心术语} 的 {从 call-chains.md 中选一个流程} 逻辑"。
1. 从 repos/INDEX.md 的场景路由表定位到目标仓库
2. 从 symbols.md 找到具体的类和方法
3. 验证：symbols.md 中的路径和行号是否能直接定位到正确的源码位置？
```

**场景 2 — 跨服务理解验证**：
```
假设你要修改一个涉及跨服务调用的功能。
1. 从 business/domains/{domain}/cross-service.md 了解调用关系
2. 从各仓库的 call-chains.md 了解完整链路
3. 验证：是否能清楚知道改动的影响范围（上游谁调你，你调用了谁）？
```

**执行方式**：
- 实际 Read 对应的知识库文件，走一遍定位流程
- 如果在任何步骤卡住（INDEX.md 没有覆盖这个场景、symbols.md 缺少关键方法、cross-service.md 遗漏调用关系），立即修正
- 验证通过后在 knowledge-gaps.md 末尾追加验证记录

**验证记录格式**：
```markdown
## 可用性验证

| 场景 | 结果 | 发现的问题 | 是否已修正 |
|------|------|-----------|-----------|
| 代码定位: {具体场景} | PASS/FAIL | {问题描述} | YES/NO |
| 跨服务理解: {具体场景} | PASS/FAIL | {问题描述} | YES/NO |
```

---

### Phase 5: 生成顶层 INDEX.md 与 CLAUDE.md 集成

#### 5.1 生成顶层 INDEX.md

生成 `coding-knowledge/INDEX.md`，模板见 `references/templates.md`。

#### 5.2 自动生成 CLAUDE.md 知识库加载规则

在项目根目录创建或追加 `CLAUDE.md`（如已存在则在末尾追加知识库章节），让 Claude Code 在编码时自动使用知识库：

```markdown
## AI Coding 知识库

本项目配置了分层编码知识库，位于 `coding-knowledge/` 目录。

### 使用方式

**先读 `coding-knowledge/INDEX.md` 的意图路由表**，按你的具体意图直达所需文件。一个任务通常只需 2-3 个文件，不要全量加载。

典型路径：
- **明确的修改任务** → INDEX.md 意图路由表 → 目标仓库的 `symbols.md` → `call-chains.md`
- **写 PRD** → `business/prd-reference/existing-features.md` + `business-flows.md`
- **探索性任务**（可行性分析、影响评估、问题排查）→ INDEX.md "需要广泛理解时" 章节，按场景加载更多文件
- **意图不在路由表里** → INDEX.md "路由表匹配不上时" 章节，通过关键词搜索或业务域缩小范围

### 不要读的文件

- `repos/{repo}/.scan-snapshot.md` — 扫描中间数据，日常编码无需读取

### 注意事项

- 行号可能因代码变更而偏移，以实际代码为准
- 置信度标记为 `low` 的信息来自推断，使用前建议验证
- **业务描述必须用代码验证**：`business/` 层是产品语言，会省略查询条件、数据维度等实现细节。回答"系统现在具体怎么做的"时，必须去 `repos/` 层定位源码确认，不能只凭业务描述下结论
- 如需更新知识库，运行 coding-knowledge-init skill
```

**CLAUDE.md 生成规则**：
- 如果项目根目录没有 `CLAUDE.md`，创建新文件
- 如果已存在 `CLAUDE.md`，检查是否已有"AI Coding 知识库"章节：
  - 有 → 替换该章节内容
  - 无 → 在文件末尾追加
- 不修改 `CLAUDE.md` 中的其他内容

---

## 增量更新

如果 `coding-knowledge/` 目录已存在且用户要求更新：

### 智能增量更新（基于 git diff）

```bash
# 1. 获取自上次生成以来的变更文件
git diff --name-only {上次生成的 commit hash} HEAD

# 2. 确定受影响的仓库
#    变更文件路径 → 所属仓库 → 标记为需要更新
```

**更新策略**：

| 变更类型 | 更新范围 | 操作 |
|---------|---------|------|
| 某仓库内 Controller/Service 变更 | 该仓库的 symbols.md, call-chains.md | 重新运行 scan-repo.py → 重新合成受影响文件 |
| 新增/删除 Entity | 该仓库的 database-schema.md + business/glossary.md | 重新扫描 + 更新术语表 |
| 新增仓库 | 完整扫描新仓库 + 更新所有 INDEX.md | 全量处理新仓库 + 增量更新索引 |
| 跨服务调用变更 | 相关仓库的 call-chains.md + cross-service.md | 重新提取跨服务关系 |
| 配置文件变更 | infra/ 层相关文件 | 重新合成受影响的 infra 文件 |

**增量更新流程**：
1. 读取 `config.yaml` 获取已有配置
2. 运行 `git diff --name-only` 获取变更文件清单
3. 映射变更文件到仓库和文档类型
4. 仅对受影响的仓库重新运行 `scan-repo.py`
5. 仅重新合成受影响的文档
6. 更新所有受影响的 INDEX.md
7. 在更新的文件元数据中标注更新原因和时间

**无法使用 git diff 时**（非 git 仓库或用户未提供基准 commit）：
- 对所有仓库重新运行 `scan-repo.py`，对比新旧 scan-result.json
- 只更新有差异的文档

---

## 注意事项

**扫描性能**：数据提取由 Python 脚本完成（每仓库 2-5 秒），50 个仓库 < 3 分钟。LLM 只需读取 JSON 合成文档，通过并行 Agent 进一步加速。

**信息时效性**：代码仓库层的知识会随代码变化而过期。建议在大需求开发前使用增量更新刷新相关仓库索引。

**隐私与安全**：如发现硬编码密钥/密码，在知识库中标注文件路径但不记录具体值，在 knowledge-gaps.md 中作为安全风险提出。

**生成代码识别**：跳过自动生成的代码（MyBatis Generator、Protobuf、Swagger Codegen）。检查 `@Generated` 注解或 `AUTO-GENERATED` 注释。

**context 保护**：每生成 2-3 个文档后 Re-read `.scan-snapshot.md` 刷新上下文。大规模场景每批处理完后 Re-read `.progress.yaml`。

---

## Examples

### Example 1: 多仓库完整初始化

**用户输入**："我负责交易业务，下面有4个子模块，代码仓库都在 /path/repos/ 下面，帮我初始化编码知识库"

**Skill 行为**：
1. Phase 0: 用户已提供信息，生成 config.yaml
2. Phase 1.1: 运行 `batch-scan.sh`（秒级），如失败则降级到 LLM 直接扫描
3. Phase 1.2-1.3: 并行 Agent 读取 JSON 合成文档，每批 5-8 仓库
4. Phase 2: Read phase2-rules.md → 基于扫描结果生成问题
5. Phase 3: Read templates.md → 生成三层知识库
6. Phase 3.5: 三级质量校验
7. Phase 4: 生成 knowledge-gaps.md
8. Phase 4.5: 可用性验证（模拟编码场景）
9. Phase 5: 生成顶层 INDEX.md + 更新 CLAUDE.md

### Example 2: 单仓库快速初始化

**用户输入**："帮我分析 ~/projects/order_srv，建立编码知识库"

**Skill 行为**：
1. 简化 Phase 0: 确认业务名称和仓库类型
2. Phase 1.1: 运行 `scan-repo.py`（无需 Agent）
3. Phase 1.2: 直接合成全套文档
4. Phase 2-5: 正常执行，业务层多为推断
5. 生成 CLAUDE.md 集成规则

### Example 3: 增量更新

**用户输入**："代码有更新，帮我刷新知识库"

**Skill 行为**：
1. 读取 config.yaml 和 knowledge-gaps.md
2. 运行 git diff 确定变更范围
3. 仅重新扫描和合成受影响的仓库和文件
4. 更新 INDEX.md 和 CLAUDE.md
