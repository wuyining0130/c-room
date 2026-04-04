---
name: coding-knowledge-init
description: >-
  扫描业务子模块的多个前后端代码仓库，通过交互式引导生成面向 AI Coding 的三层分层专家知识库：基础技术层、业务层、代码仓库层。
  输出结构化的 coding-knowledge/ 目录，每层包含 INDEX.md 索引（控制在 200 行内）和按需加载的详细子文件。
  当用户提到"初始化编码知识库"、"生成 coding 知识库"、"构建代码专家知识"、"AI编码知识初始化"、
  "帮我梳理技术栈和业务架构"、"分析多个代码仓库"、"建立代码仓库知识体系"时使用此 skill。
  即使用户只是说"我有几个代码仓库想让 AI 了解一下"或"帮我把这些项目的知识整理出来方便后续编码"，
  也应该使用这个 skill。注意与 knowledge-init 的区别：knowledge-init 面向写 PRD，
  本 skill 面向 AI 辅助编码，产出物是让 AI 能像顶级程序员一样理解和编写代码所需的分层知识。
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
│   └── domains/                      # 细分业务架构
│       ├── INDEX.md
│       └── {domain-name}/
│           ├── overview.md           # 领域概述、核心流程
│           ├── domain-model.md       # 领域模型与数据关系
│           └── cross-service.md      # 跨仓库调用关系
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
合同    对外接入      contract_srv             合同对外服务
                      loan_contract_srv        合同对外服务(放款)
        内部收单      e_contract_srv           合同配置&内部收单服务
                      e_contract_task          合同生成调用链路服务
        外部签章      e_seal_srv               合同签章服务
        运营平台      atm_api                  资产运营系统后台(含合同管理)
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
business_name: "合同业务"
domains:
  - name: "对外接入"
    repos:
      - path: "/path/to/contract_srv"
        type: backend
        service_name: "credit.support.contract_srv"
        description: "合同对外服务"
      - path: "/path/to/loan_contract_srv"
        type: backend
        service_name: "credit.support.loan_contract_srv"
        description: "合同对外服务(放款)"
  - name: "内部收单"
    repos:
      - path: "/path/to/e_contract_srv"
        type: backend
        description: "合同配置&内部收单服务"
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
    contract_srv: {status: completed, docs: [".scan-snapshot.md", "architecture.md", "symbols.md", "codebase-index.md", "database-schema.md", "call-chains.md"]}
    e_contract_srv: {status: in_progress, docs: [".scan-snapshot.md"]}
    loan_contract_srv: {status: pending}
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

**子 Agent prompt 模板**（必须严格使用此模板构造 prompt）：

```
你是一个知识库文档生成 Agent。请为以下仓库生成 coding-knowledge 文档。

## 仓库列表
{逐个列出，格式如下}
- 仓库名: contract_srv
  scan-result.json 路径: /path/to/coding-knowledge/scan-data/contract_srv.scan-result.json
  输出目录: /path/to/coding-knowledge/repos/contract_srv/
  技术栈: java

## 生成顺序（严格按此顺序，每个仓库内部也按此顺序）
1. .scan-snapshot.md — 读取 scan-result.json，按快照模板生成
2. database-schema.md — 从 entities + sql_files 提取（无数据库依赖则跳过）
3. symbols.md — 从 controllers + services + repositories + entities 提取
4. call-chains.md — 从 controllers.methods.body_preview + cross_service_calls + mq 合成
5. codebase-index.md — 从 directory_tree + 各层类文件清单合成
6. architecture.md — 综合以上所有文件信息生成概览（必须包含"职责边界"章节）

## 模板获取
先 Read references/templates.md 获取所有输出文件模板。
再 Read references/tech-stack-guide.md 了解 JSON 字段映射。

## symbols.md 质量要求
- 禁止占位描述（不允许 "(多个方法)" 等模糊占位符）
- 每个方法必须有完整签名，从 scan-result.json 的 methods 数组中提取
- 路径必须包含行号（从 methods[].line 提取）
- 按 Controller → Service → Repository/Mapper → Entity 分组
- 总条目 50-100 个核心符号

## architecture.md 职责边界要求
- 必须包含"本服务负责"、"本服务不负责"、"常见误解"三个子章节
- 从 controllers 推断核心职责
- 从 cross_service_calls 推断"不负责"的功能
- 常见误解：如仓库名相似的需要区分

## 输出格式
每个仓库处理完成后输出：
===REPO_COMPLETE===
repo_name: {仓库名}
status: success|failed
docs_generated:
  - .scan-snapshot.md
  - architecture.md
  - symbols.md
  - codebase-index.md
  - database-schema.md
  - call-chains.md
symbols_count: {symbols.md 中的符号总数}
controllers_count: {Controller 数量}
services_count: {Service 数量}
entities_count: {Entity 数量}
cross_service_targets: [appid1, appid2]
mq_topics: [topic1, topic2]
error: {如失败则填写原因}
===END_REPO===

注意：
- 不要使用 AskUserQuestion，所有信息从 scan-result.json 中获取
- 每完成一个仓库就输出 REPO_COMPLETE 块
- 如某个仓库的 scan-result.json 数据为空，标注为空仓库，只生成 architecture.md
```

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
- business/：glossary.md, overall-architecture.md, 每个 domain 的 overview.md
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

这是质量自检的核心——量化评估知识库对实际代码的覆盖程度。覆盖率不足的知识库会导致下游 skill（tech-design、code-gen、code-review）的分析精度下降。

**symbols.md 覆盖率检查**：

对每个仓库，从 scan-result.json（或通过 Grep 扫描源码）获取实际的类/方法数量，与 symbols.md 中记录的条目对比：

| 检查维度 | 计算方式 | 合格线 | 不合格后果 |
|----------|---------|--------|-----------|
| Controller 覆盖率 | symbols.md 中 Controller 数 / 仓库实际 Controller 数 | ≥ 90% | tech-design 无法精确定位接口，改动范围分析降级为推测 |
| Service 覆盖率 | symbols.md 中 Service 数 / 仓库实际 Service 数 | ≥ 80% | code-gen 风格学习缺少参考，生成代码风格可能不一致 |
| Repository/Mapper 覆盖率 | symbols.md 中 Repo/Mapper 数 / 仓库实际数 | ≥ 70% | code-gen 数据访问层生成缺少模式参考 |
| Entity 覆盖率 | symbols.md 中 Entity 数 / 仓库实际 Entity 数 | ≥ 80% | database-schema 与代码的映射关系不完整 |
| 方法签名完整度 | 有完整签名的方法数 / symbols.md 中总方法数 | 100% | 禁止出现"(多个方法)"等占位描述 |

检查方式：
1. 从 scan-result.json 的 `controllers`、`services`、`repositories`、`entities` 数组获取实际数量
2. 如果 scan-result.json 不可用，用 Grep 搜索实际代码：
   - Controller：`@RestController|@Controller` (Java)、`func.*Handler` (Go)、`class.*Controller` (PHP/Python)
   - Service：`@Service` (Java)、`type.*Service struct` (Go)
   - Entity：`@Entity|@Table` (JPA)、`@TableName` (MyBatis-Plus)、`CREATE TABLE` (SQL)
3. 对比 symbols.md 中各分组的条目数

**call-chains.md 完整性检查**：

| 检查维度 | 计算方式 | 合格线 | 不合格后果 |
|----------|---------|--------|-----------|
| 跨服务调用覆盖 | call-chains.md 中记录的跨服务调用数 / scan-result.json 中 cross_service_calls 总数 | ≥ 90% | tech-design 调用链追踪遗漏中间层服务 |
| MQ topic 覆盖 | call-chains.md 中记录的 MQ topic 数 / scan-result.json 中 mq.topics 总数 | 100% | 异步链路遗漏导致改动范围不完整 |
| 调用链双向一致 | A 仓库记录"调用 B"，B 仓库应记录"被 A 调用" | 100% | cross-service.md 调用关系矛盾 |
| 入口链路覆盖 | 有完整调用链的 Controller 方法数 / 核心 Controller 方法总数 | ≥ 60% | code-review 无法验证跨服务调用模式一致性 |

检查方式：
1. 从各仓库 scan-result.json 的 `cross_service_calls` 数组提取所有跨服务调用目标
2. 与 call-chains.md 中记录的调用关系逐一对比
3. 从 scan-result.json 的 `mq` 部分提取所有 producer/consumer topic，与 call-chains.md 对比
4. 双向检查：如果仓库 A 的 call-chains.md 记录了对仓库 B 的调用，检查仓库 B 的 call-chains.md 或 cross-service.md 中是否有对应的被调用记录

**生成质量评分卡**：

检查完成后，在 `knowledge-gaps.md` 中生成质量评分卡：

```markdown
## 质量评分卡

### 按仓库评分

| 仓库 | symbols 覆盖率 | call-chains 完整性 | 综合评级 | 影响 |
|------|---------------|-------------------|---------|------|
| contract_srv | C:95% S:88% R:75% E:90% | 跨服务:92% MQ:100% | ✅ 合格 | — |
| e_contract_srv | C:80% S:60% R:50% E:70% | 跨服务:70% MQ:80% | ⚠️ 不足 | tech-design 定位精度下降 |
| loan_srv | C:100% S:90% R:80% E:85% | 跨服务:100% MQ:100% | ✅ 优秀 | — |

> C=Controller S=Service R=Repository E=Entity

### 全局评分

| 维度 | 得分 | 说明 |
|------|------|------|
| symbols.md 总覆盖率 | {加权平均}% | 按仓库代码量加权 |
| call-chains.md 完整性 | {加权平均}% | 按跨服务调用数量加权 |
| 调用链双向一致性 | {百分比}% | 不一致的调用对数量 |
| **综合评级** | ✅ 可用 / ⚠️ 建议补充 / ❌ 需要重新扫描 | |

### 评级标准

- ✅ **可用**：所有仓库 symbols 覆盖率 ≥ 合格线，call-chains 完整性 ≥ 90%
- ⚠️ **建议补充**：部分仓库低于合格线，列出具体补充建议
- ❌ **需要重新扫描**：核心仓库严重不足（Controller 覆盖率 < 70%），建议重新运行扫描
```

**不合格时的自动修复**：

- symbols.md 覆盖率不足：自动 Grep 查找遗漏的类，Read 源码提取方法签名，补充到 symbols.md
- call-chains.md 遗漏跨服务调用：从 scan-result.json 提取遗漏的调用关系，补充到 call-chains.md
- MQ topic 遗漏：从 scan-result.json 补充遗漏的 topic
- 双向不一致：在两侧都补充缺失的调用关系记录
- 自动修复后重新计算评分，更新评分卡

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

**用户输入**："我负责合同业务，下面有4个子模块，代码仓库都在 /path/repos/ 下面，帮我初始化编码知识库"

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

**用户输入**："帮我分析 ~/projects/contract_srv，建立编码知识库"

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
