# Phase 2 问题生成规则

本文件定义 Phase 2 交互式知识补充的触发条件和问题模板。必须严格按规则生成问题，不要自由发挥。

---

## 第一轮：基础技术层（必问）

| 触发条件 | 生成的问题 | 目标文件 |
|---------|-----------|---------|
| 任何仓库存在 | "CI/CD 用什么平台？发布流程是怎样的？（如：Jenkins/GitLab CI + 灰度/全量发布）" | infra/cicd.md |
| 任何仓库存在 | "代码规范有哪些强制要求？（如：必须 code review、禁止直接操作数据库、提交前跑单元测试）" | infra/code-quality.md |
| 检测到跨服务调用（cross_service_calls 非空） | "跨服务调用有什么规范？（如：RPC 框架选型、超时配置、降级策略）" | infra/middleware.md |
| 检测到 MQ（mq 非空） | "消息队列使用有什么规范？（如：topic 命名规则、消息幂等要求、消费重试策略）" | infra/middleware.md |
| 检测到数据库（entities 或 sql_files 非空） | "数据库使用有什么规范？（如：分库分表策略、读写分离、慢查询阈值）" | infra/middleware.md |
| 任何仓库存在 | "安全合规方面有哪些强制要求？（如：敏感数据加密、接口鉴权方式、日志脱敏）" | infra/security.md |

## 第二轮：业务层（根据扫描结果动态生成）

| 触发条件 | 生成的问题 | 目标文件 |
|---------|-----------|---------|
| 每个 domain 下有多个仓库 | "在 {domain} 领域中，{仓库A} 和 {仓库B} 的职责边界是什么？什么场景走 A 什么场景走 B？" | business/domains/{domain}/overview.md |
| cross_service_calls 中发现调用关系 | "{仓库A} 调用了 {仓库B} 的 {接口}，这个调用的完整业务场景是什么？" | business/domains/{domain}/cross-service.md |
| 多个仓库的 entities 中有相似命名 | "{仓库A} 和 {仓库B} 都有 {类似Entity名}，它们是同一个概念吗？还是不同的业务含义？" | business/glossary.md |
| 检测到枚举（enums 非空） | "以下枚举值的业务含义是什么？{列出代码中值名不够自解释的枚举}" | business/glossary.md |
| 每个 domain | "{domain} 的核心业务流程是什么？（如：从用户发起到最终完成的完整链路）" | business/domains/{domain}/overview.md |

## 第三轮：补充确认（可选，仅在有不确定项时触发）

| 触发条件 | 生成的问题 | 目标文件 |
|---------|-----------|---------|
| architecture.md 中职责边界标注了置信度 low | "我推断 {仓库} 不负责 {功能}，这个判断对吗？有什么常见误解？" | repos/{repo}/architecture.md |
| glossary.md 中有推断的术语 | "以下术语的定义我是从代码推断的，请确认或修正：{术语列表}" | business/glossary.md |

---

## 问题展示和回答规则

- 使用 AskUserQuestion 工具展示问题，提供 2-3 个选项 + Other 自由输入
- 用户每回答一个问题，**立即写入 `.progress.yaml` 的 `phase_2.user_answers`**
- 用户选择"跳过/不确定"的问题，标记为 `skipped`，在 knowledge-gaps.md 中记录为待补充
- 用户选择"全部跳过后续问题"时立即结束 Phase 2，进入 Phase 3

## 默认策略（用户不回答时）

| 信息类别 | 默认处理 | 置信度标注 |
|---------|---------|-----------|
| CI/CD 流程 | 不生成 infra/cicd.md，在 knowledge-gaps.md 标记为 P1 | — |
| 代码规范 | 从代码模式推断基础规范（如检测到 checkstyle 配置则提取） | low |
| 跨服务规范 | 从代码中提取实际用法（如超时配置值），标注为推断 | medium |
| 业务流程 | 从 call-chains 推断流程大纲，标注"待用户确认" | low |
| 术语定义 | 从 Entity/枚举名推断，标注"待用户确认" | low |
| 职责边界 | 从 Controller 和 cross_service_calls 推断 | medium |
