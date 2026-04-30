# 第四级质量校验：覆盖率与完整性量化评估

这是质量自检的核心——量化评估知识库对实际代码的覆盖程度。覆盖率不足的知识库会导致下游 skill（tech-design、code-gen、code-review）的分析精度下降。

## symbols.md 覆盖率检查

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

## call-chains.md 完整性检查

| 检查维度 | 计算方式 | 合格线 | 不合格后果 |
|----------|---------|--------|-----------|
| 跨服务调用覆盖 | call-chains.md 中记录的跨服务调用数 / scan-result.json 中 cross_service_calls 总数 | ≥ 90% | tech-design 调用链追踪遗漏中间层服务 |
| MQ topic 覆盖 | call-chains.md 中记录的 MQ topic 数 / scan-result.json 中 mq.topics 总数 | 100% | 异步链路遗漏导致改动范围不完整 |
| 调用链双向一致 | A 仓库记录"调用 B"，B 仓库应记录"被 A 调用" | 100% | overall-architecture.md 调用关系矛盾 |
| 入口链路覆盖 | 有完整调用链的 Controller 方法数 / 核心 Controller 方法总数 | ≥ 60% | code-review 无法验证跨服务调用模式一致性 |

检查方式：
1. 从各仓库 scan-result.json 的 `cross_service_calls` 数组提取所有跨服务调用目标
2. 与 call-chains.md 中记录的调用关系逐一对比
3. 从 scan-result.json 的 `mq` 部分提取所有 producer/consumer topic，与 call-chains.md 对比
4. 双向检查：如果仓库 A 的 call-chains.md 记录了对仓库 B 的调用，检查仓库 B 的 call-chains.md 中是否有对应的被调用记录

## 质量评分卡

检查完成后，在 `knowledge-gaps.md` 中生成质量评分卡：

```markdown
## 质量评分卡

### 按仓库评分

| 仓库 | symbols 覆盖率 | call-chains 完整性 | 综合评级 | 影响 |
|------|---------------|-------------------|---------|------|
| order_srv | C:95% S:88% R:75% E:90% | 跨服务:92% MQ:100% | ✅ 合格 | — |
| fulfill_srv | C:80% S:60% R:50% E:70% | 跨服务:70% MQ:80% | ⚠️ 不足 | tech-design 定位精度下降 |
| pay_srv | C:100% S:90% R:80% E:85% | 跨服务:100% MQ:100% | ✅ 优秀 | — |

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

## 不合格时的自动修复

- symbols.md 覆盖率不足：自动 Grep 查找遗漏的类，Read 源码提取方法签名，补充到 symbols.md
- call-chains.md 遗漏跨服务调用：从 scan-result.json 提取遗漏的调用关系，补充到 call-chains.md
- MQ topic 遗漏：从 scan-result.json 补充遗漏的 topic
- 双向不一致：在两侧都补充缺失的调用关系记录
- 自动修复后重新计算评分，更新评分卡
