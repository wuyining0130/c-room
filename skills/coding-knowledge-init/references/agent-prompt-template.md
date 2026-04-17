# 子 Agent Prompt 模板

并行合成时，必须严格使用此模板构造子 Agent 的 prompt：

```
你是一个知识库文档生成 Agent。请为以下仓库生成 coding-knowledge 文档。

## 仓库列表
{逐个列出，格式如下}
- 仓库名: order_srv
  scan-result.json 路径: /path/to/coding-knowledge/scan-data/order_srv.scan-result.json
  输出目录: /path/to/coding-knowledge/repos/order_srv/
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
