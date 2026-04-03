---
name: knowledge-init
description: >-
  扫描项目代码和需求文档，生成面向"产品需求生成"的结构化知识库。输出 prd-knowledge/ 目录，
  聚焦业务语义、产品上下文、用户角色、业务流程等面向写 PRD 的信息。
  与 coding-knowledge-init 互补：本 skill 面向写 PRD（业务视角），coding-knowledge-init 面向写代码（实现视角）。
  当用户提到"生成知识库"、"初始化知识库"、"构建项目知识库"、"分析项目代码和需求"、"为后续写PRD做准备"时，使用此 skill。
  即使用户只是说"帮我了解一下这个项目"，也应该考虑使用。
---

## Purpose

在用 AI 辅助写产品需求之前，需要让 AI 充分理解现有项目。随便生成的知识库往往是"给人看的百科全书"——什么都有但后续写 PRD 时不知道怎么用。

这个 skill 生成的知识库是**面向"写 PRD"这个下游任务优化的结构化上下文**。每份文件不仅记录事实，还说清楚"这个信息在写需求时怎么用"。这样后续调用 `prd-draft` 等 skill 时，AI 能精准利用这些知识，而不是在海量信息中迷失。

## 与 coding-knowledge 的关系

项目有两套知识库，各司其职：

| | prd-knowledge/（本 skill 产出） | coding-knowledge/（coding-knowledge-init 产出） |
|--|------|------|
| **面向任务** | 写 PRD、做需求评审 | 写代码、做 code review |
| **信息视角** | 业务语义——"系统做什么、为谁做" | 代码实现——"代码怎么写、调用链怎么走" |
| **架构信息** | 模块职责、技术栈概览 | 精确的类名/方法签名/行号 |
| **数据模型** | 业务实体、字段含义、实体关系 | 真实 DDL、索引、字符集 |
| **接口信息** | 接口用途、业务功能映射 | 方法签名、参数类型、调用链 |
| **下游 skill** | prd-draft、prd-review、proto-gen | tech-design、code-gen、code-review |

**关键原则**：
- 两套知识库**不合并**——粒度和视角不同，合并会导致信息过载
- `tech-design` 是桥梁——同时读取两套知识库，把产品需求翻译为技术方案
- 如果 `coding-knowledge/` 已存在，本 skill 在扫描代码时可以引用其中的架构概览作为辅助，但**产出物仍聚焦业务语义**——不需要在 prd-knowledge 里重复精确的方法签名和 DDL

## 项目根目录定义

**项目根目录**是 `{project_name}/` 目录，即 `sources/` 的父目录。所有系列 skill 共享这个约定：
- `prd-knowledge/` 生成在项目根目录下
- `coding-knowledge/` 生成在项目根目录下
- `requirements/` 生成在项目根目录下
- 其他 skill 引用"项目根目录"时，均指此目录

判断优先级：
1. 如果当前工作目录下存在 `sources/` 目录，则当前目录即为项目根目录
2. 如果当前工作目录下存在 `prd-knowledge/` 目录，则当前目录即为项目根目录
3. 否则，使用当前工作目录

详见 `conventions` skill 中的完整约定。

## 前置条件

需要一个包含项目资料的目录，通常是 `project-import` skill 生成的 `sources/` 目录：

```
{project_name}/
└── sources/
    ├── tapd-requirements/    # TAPD 需求文档
    │   ├── raw/              # JSON 原始数据
    │   └── docs/             # Markdown 可读版
    ├── codebase/             # 项目代码
    └── docs/                 # 其他文档
```

如果用户的项目资料不是这个结构，也没关系——skill 会自动识别目录中的代码文件和文档文件。

## 工作流程

按以下 4 个阶段依次执行。每个阶段完成后简要告知用户进度。

### Phase 1: 扫描项目结构

扫描 `sources/` 目录（或用户指定的目录），识别以下信息：

**代码层面（业务语义视角，不追求代码级精度）：**
- **技术栈**：语言、框架、构建工具（通过 package.json、pom.xml、go.mod、requirements.txt 等识别）
- **模块结构**：目录组织方式、各模块的业务职责（通过目录名和入口文件推断）
- **数据模型**：ORM 模型定义中的业务实体和字段含义（重点关注"这个实体代表什么业务对象"，而非精确的字段类型和索引——那是 coding-knowledge 的职责）
- **API 接口**：路由定义和接口用途（重点关注"这个接口做什么业务操作"，而非方法签名和参数类型）
- **前端页面**：页面组件、路由配置、用户可见的功能入口

**需求文档层面：**
- **已有需求清单**：从 TAPD Markdown 文件中提取需求标题和描述
- **业务术语**：反复出现的专有名词和概念
- **用户角色**：文档中提到的用户类型和权限

**如果 `coding-knowledge/` 已存在**，可以直接引用以下信息而非重新从代码扫描：
- 仓库级 `architecture.md` 中的模块职责概览
- `business/` 目录中的业务领域划分
- 但注意：只取业务语义层面的信息，不搬运代码级细节

扫描时优先读取以下文件（而非逐行扫描所有代码）：
- 配置文件和入口文件（了解技术栈和模块划分）
- 模型定义文件（了解业务实体）
- 路由/Controller 文件（了解接口功能）
- 页面级组件和路由配置（了解用户可见功能）
- 需求文档的标题和描述段落（了解业务语义）

### Phase 2: 提取业务语义

基于 Phase 1 的扫描结果，深入提取：

- **业务规则**：代码中的校验逻辑、状态流转、权限控制等隐含的业务规则
- **用户角色与权限**：谁能做什么，角色之间的区别
- **数据流向**：数据从哪里来、经过哪些处理、到哪里去（业务视角，非代码调用链）
- **现有交互模式**：列表页/详情页/表单/弹窗等已有的 UI 模式
- **业务流程**：核心操作的完整流程（如"创建→审核→发布"）

### Phase 3: 生成结构化知识库

在项目根目录下创建 `prd-knowledge/` 目录，生成以下文件：

#### 文件清单

| 文件 | 内容 | 对需求生成的价值 |
|------|------|------------------|
| `architecture.md` | 技术栈、模块划分、部署结构、依赖关系 | 写 PRD 时判断技术可行性，预估开发复杂度 |
| `business-glossary.md` | 业务术语定义和关系 | 确保 PRD 用语与现有系统一致，避免歧义 |
| `user-roles.md` | 用户角色、权限矩阵、角色间关系 | 写用户故事时精确定义"谁"，设计权限时参考现有模式 |
| `data-model.md` | 核心实体、字段含义、关系、约束 | 设计新功能的数据结构时避免与现有模型冲突 |
| `existing-features.md` | 现有功能清单（按模块组织） | 了解系统全貌，避免重复建设，发现可复用的功能 |
| `api-inventory.md` | 接口清单（URL、方法、用途描述） | 新需求可以复用哪些接口，需要新增哪些 |
| `design-patterns.md` | 已有交互模式和 UI 组件 | 新页面设计时保持交互一致性，复用已有组件 |
| `business-flows.md` | 核心业务流程图（用 Mermaid 语法） | 理解系统运转逻辑，新功能如何嵌入现有流程 |

**与 coding-knowledge 的产出对比**：
- `architecture.md`：本 skill 侧重"模块做什么业务"，coding-knowledge 侧重"代码怎么分层、类怎么组织"
- `data-model.md`：本 skill 侧重"这个实体代表什么、字段业务含义"，coding-knowledge 的 `database-schema.md` 侧重"DDL、索引、字段类型"
- `api-inventory.md`：本 skill 侧重"接口做什么业务操作"，coding-knowledge 的 `symbols.md` 侧重"方法签名、参数类型、行号"

#### 每个文件的结构模板

每个知识库文件遵循统一的结构：

```markdown
# {文件标题}

> 最后更新: {timestamp}
> 信息来源: {sources/ 下的哪些文件}

## 对需求生成的价值

{1-2 句话说明这份文件在后续写 PRD 时怎么用}

## 内容

{主体内容}

## 信息来源

{列出分析了哪些文件得出的结论}
```

#### business-flows.md 格式示例

业务流程用 Mermaid 流程图语法，方便渲染和理解：

```markdown
## 知识条目管理流程

​```mermaid
flowchart TD
    A[创建知识条目] --> B{审核}
    B -->|通过| C[发布]
    B -->|驳回| D[退回修改]
    D --> A
    C --> E[上线可用]
    E --> F{需要更新?}
    F -->|是| G[编辑] --> B
    F -->|否| E
​```

**触发角色**: 运营人员
**关键状态**: 草稿 → 审核中 → 已发布 → 已下线
**业务规则**: 发布后修改需要重新审核
```

### Phase 4: 自检完整性

生成知识库后，对每个文件进行完整性自检，生成 `prd-knowledge/knowledge-gaps.md`：

```markdown
# 知识库完整性检查报告

> 生成时间: {timestamp}
> 整体完整度: {百分比估算}

## 信息充分的部分
- [x] architecture.md — 技术栈和模块结构清晰
- [x] data-model.md — 核心实体和关系完整

## 信息不足的部分

### user-roles.md
- **缺失**: 角色的具体权限边界不明确
- **建议**: 提供后台管理系统的角色配置截图或权限表
- **影响**: 写 PRD 时可能遗漏权限相关的需求

### business-flows.md
- **缺失**: "审核"环节的具体规则（谁审核、审核标准）
- **建议**: 提供审核相关的需求文档或访谈业务方
- **影响**: 涉及审核的新需求可能设计不完整

## 下一步建议
1. 补充以上缺失信息后，重新运行 `knowledge-init` 更新知识库
2. 如果信息已经足够，可以使用 `prd-draft` skill 开始撰写新需求
3. 如果后续需要生成技术方案或代码，建议运行 `coding-knowledge-init` 生成编码知识库——它提供精确的方法签名、DDL、调用链等代码级信息，是 `tech-design` 和 `code-gen` 的重要输入
```

## 增量更新

如果 `prd-knowledge/` 目录已存在，skill 会：
1. 读取现有知识库内容
2. 对比 `sources/` 中是否有新增或变更的文件
3. 只更新受影响的知识库文件，而非全量重建
4. 在每个更新的文件中标注 `[UPDATED]` 和更新原因

## 输出目录结构

```
{project_name}/
├── sources/                    # 原始资料（不动）
├── prd-knowledge/              # 本 skill 产出（面向写 PRD）
│   ├── architecture.md
│   ├── business-glossary.md
│   ├── user-roles.md
│   ├── data-model.md
│   ├── existing-features.md
│   ├── api-inventory.md
│   ├── design-patterns.md
│   ├── business-flows.md
│   └── knowledge-gaps.md       # 完整性检查报告
└── coding-knowledge/           # coding-knowledge-init 产出（面向写代码，独立生成）
```

## Examples

### Example 1: 知识库运营后台项目

**用户输入：**
"我已经用 project-import 拉取了知识库运营后台的代码和需求文档，帮我生成项目知识库"

**Skill 行为：**
1. Phase 1: 扫描 sources/codebase/ 发现 Vue3 + Node.js 项目，识别出知识管理、分类管理、FAQ 管理等模块
2. Phase 2: 从 TAPD 需求文档中提取"知识条目"、"FAQ"、"坐席"等业务术语，识别"运营人员"和"坐席"两个角色
3. Phase 3: 生成 8 个知识库文件
4. Phase 4: 自检发现 user-roles.md 中缺少坐席的具体权限范围，标注在 knowledge-gaps.md；建议运行 coding-knowledge-init 获取代码级信息

### Example 2: 只有代码没有需求文档

**用户输入：**
"帮我分析一下 ~/projects/my-app 这个项目，生成知识库"

**Skill 行为：**
1. 发现 sources/ 目录不存在，直接扫描 ~/projects/my-app
2. 只从代码中提取信息，需求文档相关部分标注为"无数据"
3. knowledge-gaps.md 会重点标注：缺少业务需求文档，建议用 project-import 拉取

## Common Pitfalls

**只扫描代码不看需求文档：** 代码能告诉你"系统做了什么"，但需求文档告诉你"为什么这样做"。两者结合才能生成有用的知识库。

**知识库文件过长：** 每个文件控制在可快速浏览的长度。如果 api-inventory.md 超过 500 行，按模块拆分为子文件。

**术语不一致：** business-glossary.md 中定义的术语，在其他文件中要保持一致使用。

**与 coding-knowledge 职责混淆：** 本 skill 的产出是给写 PRD 用的，不需要精确到方法签名和 DDL 字段类型。如果发现自己在写精确的代码级信息，说明越界了——那是 coding-knowledge-init 的职责。保持"业务语义"视角：实体"代表什么"比字段"是什么类型"更重要。
