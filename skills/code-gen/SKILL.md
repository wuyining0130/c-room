---
name: code-gen
description: >-
  根据技术方案 + PRD + 原型 + 编码知识库，在目标代码仓库中生成可直接提交的业务实现代码。
  不是生成脚手架，而是生成完整的 Controller、Service、Mapper、Entity、前端页面组件等业务代码。
  当用户提到"生成代码"、"写代码"、"实现技术方案"、"按技术方案写代码"、"代码生成"、
  "把技术方案变成代码"、"帮我实现这个需求"、"根据设计文档写代码"时使用此 skill。
  即使用户只是说"tech-design 写好了，接下来呢"或"开始开发吧"，也应该用这个 skill。
---

## Purpose

技术方案写好了，下一步是写代码。传统做法是开发自己读技术方案、翻现有代码、一个文件一个文件地写。问题是：技术方案中已经明确了接口设计、DDL、改动范围和任务拆解，但开发还要手动把这些信息翻译成代码——这个过程高度重复且容易出错（参数名拼错、接口路径不一致、遗漏某个服务的改动）。

这个 skill 读取技术方案、PRD、原型和编码知识库，按照技术方案中的任务拆解，在目标仓库中直接生成/修改代码文件。它不是生成"脚手架"或"模板代码"——而是生成包含完整业务逻辑的实现代码，可以直接提交 CR。

**核心能力在于深度利用 coding-knowledge**：通过编码知识库中的符号索引、调用链、DDL、代码规范，生成的代码在命名风格、分层结构、异常处理方式上与项目现有代码保持一致——看起来像项目老员工写的，而不是外包交付的。

## 输入

- `requirements/{模块名}/tech-design.md`（主要输入，包含接口设计、DDL、任务拆解、改动范围）
- `requirements/{模块名}/prd-draft.md`（验收标准、业务规则、边界条件）
- `requirements/{模块名}/prototype/`（前端页面结构参考）
- `coding-knowledge/`（**核心参考**——代码风格、架构模式、符号索引、调用链、DDL 模式、代码规范）
- 目标代码仓库路径（用户指定，或从 tech-design 的改动范围中提取）

## 工作流程

### Phase 0: 读取输入、构建上下文

#### 0.1 读取 tech-design.md

提取以下信息，作为后续生成的权威源：
- 改动影响范围（涉及哪些仓库、哪些文件需要新增/修改）
- 接口设计（API 清单、请求参数、响应结构、错误码）
- 数据库变更（DDL）
- 开发任务拆解（T-01, T-02... 含依赖关系）
- 交互时序图（服务间调用关系）
- 复用接口参数说明（区分参数和行为差异）

#### 0.2 读取 prd-draft.md

提取以下信息，用于确保业务逻辑完整：
- 功能清单和验收标准（确保生成的代码覆盖每个功能点）
- 业务规则和边界条件（确保代码中有相应的校验逻辑）
- 错误处理要求（具体的错误提示文案）

#### 0.3 深度读取 coding-knowledge（核心步骤）

这是 code-gen 与普通 AI 代码生成最大的差异。不是"读一下了解大概"，而是**按代码层逐层提取具体的编码模式**。

**第一层：基础规范（必读）**

读取 `coding-knowledge/infra/` 下的文件，提取全局编码约束：
- `code-quality.md` → 命名规范（驼峰 vs 下划线、前缀后缀约定）、注释风格、异常处理模式、日志规范
- 其他基础设施规范 → 中间件使用方式（MQ 生产消费模式、缓存操作方式）

**第二层：仓库架构（按涉及仓库读取）**

对 tech-design 中列出的每个仓库，读取 `coding-knowledge/repos/{repo}/` 下的文件：

- `architecture.md` → **包结构和分层约定**。新建文件时据此确定放在哪个包下、类名如何命名。特别注意"本服务不负责"的描述——避免把不属于该服务的逻辑写进去
- `symbols.md` → **现有类和方法的签名索引**。这是"风格学习"的入口——从中找到同类型的现有实现（如现有的 Controller、Service），后续 Phase 1 会据此 Read 完整源码
- `database-schema.md` → **现有表的真实 DDL**。新建表时参考字段命名转换规则（如 `create_time` vs `createdAt`）、索引命名规范（如 `idx_` 前缀）、字符集和引擎设定
- `call-chains.md` → **实际的跨服务调用代码**。如果 tech-design 涉及跨服务调用，从这里找到项目实际使用的调用方式（Feign Client？RestTemplate？WebClient？gRPC stub？），以及错误处理和超时配置的写法

**第三层：业务域（按需读取）**

如果 tech-design 涉及跨服务协作，读取 `coding-knowledge/business/domains/{domain}/`：
- `cross-service.md` → 跨仓库调用关系和数据流向

#### 0.4 风格学习（关键步骤）

从 symbols.md 中定位 **2-3 个同类型的现有实现文件**，用 Read 工具读取完整源码。目的是学习项目的编码模式，而非仅看签名。

具体做法：

| 待生成的代码层 | 从 symbols.md 找到的参考对象 | 学习要点 |
|---------------|--------------------------|---------|
| Entity/Model | 同仓库现有的 Entity 类 | 注解使用方式、字段命名转换、基类继承、审计字段处理 |
| Mapper/Repository | 同仓库现有的 Mapper/Repository | MyBatis XML vs 注解、自定义查询方法的命名模式、分页实现 |
| Service | 同仓库现有的 Service 类 | 事务注解用法、异常抛出方式、依赖注入风格（构造器 vs @Autowired） |
| Controller | 同仓库现有的 Controller 类 | 统一返回值包装、参数校验注解、权限注解、Swagger 注解风格 |
| 前端 API 层 | 同项目现有的 API 文件 | axios 封装方式、请求/响应拦截、错误处理 |
| 前端页面 | 同项目现有的列表页/表单页 | 组件库用法、状态管理方式、搜索条件布局 |

**风格学习的产出是一份隐式的"编码清单"**——不需要输出给用户，但在 Phase 2 生成每一行代码时都要遵循。比如：
- "这个项目的 Controller 都用 `@RestController` + `@RequestMapping`，不用 `@Controller` + `@ResponseBody`"
- "Service 层的异常统一用 `throw new BusinessException(ErrorCode.XXX)` 而不是返回 error code"
- "所有查询方法都叫 `listXxx`/`getXxx`，不叫 `queryXxx`/`findXxx`"

### Phase 1: 生成计划（向用户确认）

**必须在写任何代码之前向用户展示计划并获得确认。**

基于 Phase 0 的分析结果，输出一份结构化的生成计划：

```
## 代码生成计划

### 代码风格参考
- 后端参考：{从 symbols.md 定位到的参考 Controller/Service 文件路径}
- 前端参考：{从现有页面定位到的参考组件路径}
- 编码规范：{coding-knowledge/infra/code-quality.md 中的关键约束}

### 后端（{仓库名}）
| 序号 | 操作 | 文件路径 | 说明 | 对应任务 |
|------|------|----------|------|----------|
| 1 | 新增 | {从 architecture.md 推导的准确包路径}/XxxEntity.java | 新增实体类 | T-01 |
| 2 | 新增 | {包路径}/XxxMapper.java | 新增 Mapper 接口 | T-01 |
| 3 | 修改 | {从 symbols.md 定位的准确文件路径}:L{行号} | 新增方法 createXxx() | T-02 |
| 4 | 新增 | {包路径}/XxxController.java | 新增 CRUD 接口 | T-03 |

### 前端（{仓库名}）
| 序号 | 操作 | 文件路径 | 说明 | 对应任务 |
|------|------|----------|------|----------|
| 1 | 新增 | src/api/xxx.js | API 调用层 | T-05 |
| 2 | 新增 | src/pages/xxx/index.vue | 列表页面（参考 prototype/list.html） | T-05 |
| 3 | 新增 | src/pages/xxx/form.vue | 新增/编辑表单 | T-05 |

### 数据库
- 执行 tech-design 中的 DDL（已参考 database-schema.md 确认风格一致）

### 注意事项
- {需要用户确认的事项}
```

**计划中的文件路径必须是精确路径**——不是猜测的路径，而是从 architecture.md（包结构）和 symbols.md（现有文件位置）推导出的。对于修改现有文件的操作，标注行号。

用户确认后才开始 Phase 2。

### Phase 2: 按依赖顺序生成代码

**生成原则**：按依赖关系从底层到上层生成，确保引用关系正确。每个文件生成后立即写入。

#### 后端生成顺序

按 Entity → Mapper/Repository → Service → Controller → 配置/其他 的顺序：

**1. Entity/Model 层**

- 根据 tech-design 的 DDL 生成实体类
- **从 Phase 0.4 学到的模式**：字段注解方式（JPA `@Column` 还是 MyBatis-Plus `@TableField`）、基类继承（是否有 `BaseEntity`）、审计字段（`createTime`/`updateTime` 如何处理）、逻辑删除字段
- **从 database-schema.md 参考**：字段命名转换规则（数据库 `create_time` → Java `createTime` 的具体方式，有些项目用 `@TableField("create_time")`，有些靠全局配置自动转换）

**2. Mapper/Repository 层**

- 根据 Entity 生成对应的数据访问接口
- **从 Phase 0.4 学到的模式**：MyBatis XML vs 注解、是否继承 `BaseMapper<T>`、自定义查询方法的命名规则、分页的实现方式（PageHelper？MyBatis-Plus IPage？）
- 包含 tech-design 中提到的自定义查询方法

**3. Service 层**

- 实现业务逻辑，对应 tech-design 中每个接口的处理流程
- **从 Phase 0.4 学到的模式**：事务注解用法（`@Transactional` 的传播级别习惯）、异常处理方式（自定义 BusinessException？统一 ErrorCode 枚举？）、依赖注入风格（构造器注入 vs `@Autowired`）、日志打印习惯
- **从 PRD 验收标准推导校验逻辑**：每个验收条件对应一个校验分支
- **跨服务调用**：从 call-chains.md 中找到项目实际使用的调用方式，照搬其代码模式（而不是自己发明一种新的调用方式）

**4. Controller 层**

- 接口路径、参数、响应结构严格按照 tech-design 的接口设计
- **从 Phase 0.4 学到的模式**：统一返回值包装类（`Result<T>`？`ResponseEntity<T>`？）、参数校验注解（`@Valid` + JSR 303 还是手动校验）、权限注解（`@PreAuthorize`？自定义 `@Permission`？）、Swagger/OpenAPI 注解风格
- 错误码使用 tech-design 定义的业务错误码

**5. 配置/其他**

- MQ Consumer/Producer（如 tech-design 涉及）——从 call-chains.md 中找到现有 MQ 代码的写法
- 菜单/权限配置文件（如需要）
- 新增的常量/枚举类

#### 前端生成顺序

按 API 调用层 → 路由配置 → 页面组件 的顺序：

**1. API 调用层**

- 根据 tech-design 的接口清单生成 API 方法
- **从 Phase 0.4 学到的模式**：axios 封装方式（统一 request 函数？各 API 独立文件？）、请求/响应拦截处理
- 方法名和参数名与 tech-design 的接口编号对应

**2. 路由配置**

- 新增页面的路由注册
- 参考现有路由文件的组织方式

**3. 页面组件**

- **参考 prototype/ 的页面结构**：原型中的表格列顺序、搜索条件布局、弹窗结构直接指导组件代码
- 使用项目实际技术栈的组件库（从 coding-knowledge 或 package.json 确定是 Element UI / Ant Design / 自研组件等）
- 表格列定义从 tech-design 的接口响应字段推导
- 表单字段和校验规则从 tech-design 的接口请求参数推导

#### 每个文件的生成流程

1. 如果是**新增文件**：
   - 确认目标目录存在（用 `ls` 检查）
   - 用 Write 工具创建
2. 如果是**修改文件**：
   - 先用 Read 读取完整文件内容
   - 用 Edit 精确修改（不重新格式化周边代码）
3. 生成后立即写入文件系统（不攒到最后一起写）

### Phase 3: 生成报告

在 `requirements/{模块名}/` 目录下生成 `code-gen-report.md`：

```markdown
---
title: "{模块名} — 代码生成报告"
tech_design_version: "{tech-design 版本}"
date: "{生成日期}"
---

# {模块名} — 代码生成报告

## 1. 生成概览

| 仓库 | 新增文件 | 修改文件 | 对应任务 |
|------|---------|---------|---------|
| {仓库名} | {N} 个 | {M} 个 | T-01 ~ T-03 |

## 2. 编码风格参考

| 代码层 | 参考的现有文件 | 学习到的关键模式 |
|--------|-------------|----------------|
| Controller | {文件路径} | 统一返回 Result<T>，使用 @Valid 校验 |
| Service | {文件路径} | 构造器注入，BusinessException 异常处理 |
| Entity | {文件路径} | 继承 BaseEntity，@TableField 注解 |

## 3. 文件清单

### {仓库名}

#### 新增文件
| 文件路径 | 说明 | 对应 tech-design 任务 |
|----------|------|----------------------|
| src/.../XxxEntity.java | 新增实体 | T-01 |

#### 修改文件
| 文件路径 | 修改内容 | 对应 tech-design 任务 |
|----------|----------|----------------------|
| src/.../XxxService.java | 新增 createXxx() 方法 | T-02 |

## 4. 需求覆盖检查

| PRD 功能 | 接口编号 | 代码文件 | 验收标准覆盖 |
|----------|---------|---------|------------|
| F-01 | API-01, API-02 | XxxController.java | 全部覆盖 |
| F-02 | API-03 | XxxService.java | 部分覆盖（Q-01 待确认项未实现） |

## 5. 未覆盖项

{tech-design 中有但本次未生成的任务，及原因}

## 6. 注意事项

{需要开发者手动处理的事项，如：}
- 配置中心需要新增的配置项
- 需要手动执行的 DDL
- 需要人工确认的业务逻辑
- coding-knowledge 中发现的与 tech-design 不一致之处
```

### Phase 4: 输出总结

生成完成后告知用户：
1. 代码生成报告位置
2. 新增/修改的文件数量（按仓库统计）
3. 对应的 tech-design 任务覆盖情况
4. 需要手动处理的事项
5. 建议用 `/code-review` 审查生成的代码

## 输出目录

```
requirements/{模块名}/
├── prd-draft.md              ← PRD 终稿（输入）
├── review/                   ← prd-review 产出
├── prototype/                ← proto-gen 产出
├── tech-design.md            ← tech-design 产出（输入）
└── code-gen-report.md        ← 本 skill 产出
```

实际代码变更直接写入目标仓库目录（不在 requirements/ 下）。

## 与其他 skill 的关系

```
coding-knowledge-init                         ← 第零步：项目地图
  生成 coding-knowledge/
        ↓ (参考)
project-import → knowledge-init → prd-draft → prd-review → proto-gen
                                                                ↓
                                              tech-design → code-gen → code-review
                                                             ↑
                                                     coding-knowledge/
                                                     (深度利用)
```

- **前置**：`tech-design` 的技术方案是主要输入；`coding-knowledge-init` 的编码知识库是核心参考
- **后续**：生成的代码变更由 `code-review` 审查
- **与 tech-design 的关系**：tech-design 定义"做什么"（接口设计、DDL、任务拆解），code-gen 执行"怎么做"（生成实际代码）。tech-design 中的接口编号（API-XX）和任务编号（T-XX）是 code-gen 的直接索引
- **与 coding-knowledge 的关系**：coding-knowledge 是 code-gen 的"编码导师"——
  - `symbols.md` 告诉你项目里有什么类、方法，去哪里找同类型参考
  - `architecture.md` 告诉你新代码放在哪个包、遵循什么分层
  - `database-schema.md` 告诉你建表用什么风格
  - `call-chains.md` 告诉你跨服务调用怎么写
  - `infra/code-quality.md` 告诉你必须遵守什么规范
  - 没有 coding-knowledge 也能生成代码，但效果从"老员工写的"降级为"实习生写的"

## 生成原则

**风格一致性是第一优先级**：生成的代码必须看起来像项目现有代码的自然延伸。做法不是"读一下规范然后凭感觉"，而是：
1. 从 symbols.md 找到同类型的现有实现文件
2. Read 完整源码，提取编码模式
3. 新代码严格复刻这些模式——同样的注解组合、同样的方法命名、同样的异常处理方式

**tech-design 是权威源**：接口路径、参数名、响应结构、错误码以 tech-design 为准，不自行发挥。如果觉得 tech-design 有问题（如参数类型不合理），在报告的"注意事项"中标注，但代码仍按 tech-design 生成。

**coding-knowledge 是编码导师**：遇到"这里应该怎么写"的问题时，第一反应是查 coding-knowledge，不是凭通用知识猜测。比如：
- "这个项目的分页怎么实现？" → 查 symbols.md 中的分页相关方法
- "跨服务调用用什么方式？" → 查 call-chains.md
- "异常怎么抛？" → 查 code-quality.md 和参考 Service 的实现

**不破坏现有代码**：修改现有文件时，只在必要的位置添加/修改代码，不重新格式化或重构周边代码。用 Edit 工具精确修改，不用 Write 覆盖整个文件。

**业务逻辑要完整**：不是只生成方法签名和 TODO 注释，而是生成包含完整业务逻辑的代码。校验规则从 PRD 的验收标准推导，处理流程从 tech-design 的时序图推导。

**分批生成，及时写入**：按 Phase 2 的顺序逐文件生成，每个文件生成后立即写入。不要攒到最后一起输出——中途如果出错，已写入的文件不受影响。

## Common Pitfalls

**跳过风格学习直接生成**：不 Read 项目中现有的 Controller 就生成新的 Controller，结果用了完全不同的注解组合和返回值包装。Phase 0.4 的风格学习不能省略。

**只看 symbols.md 不读源码**：symbols.md 只有签名索引，看不到方法体内的编码模式（事务怎么用、异常怎么抛、日志怎么打）。必须 Read 2-3 个参考文件的完整源码。

**接口参数与 tech-design 不一致**：tech-design 写的是 `knowledgeType`，代码里写成了 `knowledge_type` 或 `type`。必须严格按照 tech-design 的参数名。

**遗漏修改文件**：tech-design 说要修改 3 个文件，code-gen 只改了 2 个。Phase 1 的计划清单必须完整覆盖 tech-design 的改动范围。

**前端代码不参考原型**：prototype/ 中的页面结构是 PRD 的可视化表达，前端代码应该参考原型的布局和组件结构，而不是自己重新设计页面。

**只生成签名不写实现**：生成的 Service 方法体里全是 `// TODO: implement`。这个 skill 的价值就在于生成完整的业务逻辑实现，而非留白让开发自己填。

**忽略 coding-knowledge 中的"不负责"标注**：architecture.md 中写了"本服务不负责 XXX"，但代码里把这个逻辑写进去了。生成代码前要检查服务的职责边界。

**跨服务调用方式不一致**：项目现有代码用 Feign Client 调用其他服务，生成的代码却用了 RestTemplate。必须从 call-chains.md 或参考代码中学习实际的调用方式。
