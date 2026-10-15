# 代码生成报告模板

在 `requirements/{模块名}/` 目录下生成 `{模块名}代码生成报告.md`：

```markdown
---
title: "{模块名} — 代码生成报告"
tech_design_version: "{tech-design 版本}"
tech_design_path: "{实际读取的技术方案路径}"
prd_path: "{实际读取的 PRD 路径}"
prd_version: "{PRD 版本}"
prototype_path: "{原型路径或 null}"
prototype_prd_version: "{原型依据的 PRD 版本或 null}"
knowledge_baseline: "{各仓库 last_scanned_commit/source-verified 摘要}"
repo_baseline: "{各仓库写入前 HEAD 与工作区状态摘要}"
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

## 7. 验证结果

| 仓库 | 检查项 | 命令 | 结果 | 说明 |
|------|--------|------|------|------|
| {仓库} | 单元测试/类型检查/lint/构建 | `{实际命令}` | 通过/失败/未执行 | {关键结果或原因} |

## 8. 实际 Diff 核对

{计划文件与实际 git status/diff 的一致性、计划外变更、未跟踪文件}
```
