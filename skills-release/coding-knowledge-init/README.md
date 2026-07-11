# coding-knowledge-init

一个 Claude Code Skill，扫描你的代码仓库，自动生成面向 AI 编码的三层专家知识库。

装上它之后，AI 写代码时不再是"只看得见当前文件的新手"，而是"了解整个业务架构、知道每个服务职责边界、能精准定位代码的老员工"。

## 解决什么问题

AI 辅助编码最大的瓶颈不是代码能力，而是**上下文**：
- 不知道公司用什么中间件、什么规范 → 写出不符合规范的代码
- 不理解业务术语和流程 → 改错地方、漏改关联模块
- 不了解服务间调用关系 → 不知道改动会影响谁

这个 Skill 一次性解决这三层问题。

## 生成什么

```
coding-knowledge/
├── infra/          ← 技术栈规范、中间件、代码质量标准（公司级）
├── business/       ← 业务架构、术语表、领域模型、跨服务调用（业务级）
├── repos/          ← 每个仓库的架构、符号索引、调用链、数据库结构（代码级）
└── INDEX.md        ← 三层知识导航入口
```

生成后自动配置 CLAUDE.md，AI 编码时按需加载对应层级的知识，不占多余 context。

## 安装

将 `coding-knowledge-init/` 整个目录复制到 `~/.claude/skills/` 下：

```bash
cp -r coding-knowledge-init ~/.claude/skills/
```

需要 Python 3 环境（用于代码扫描脚本）。

## 使用

### 第一步：准备输入

先整理好你负责的业务模块和仓库清单，格式如下：

```
模块      子模块          服务                                    git仓库                                                     服务描述
交易      订单处理        trade.order_srv                         https://git.xxx.com/.../order-srv                           订单核心服务
                          trade.pay_srv                           https://git.xxx.com/.../pay_srv                             支付服务
                          trade.order_qry                         https://git.xxx.com/.../order_qry                           订单查询服务
          履约            trade.fulfill_srv                       https://git.xxx.com/.../fulfill_srv                         履约&配置服务
                          trade.fulfill_task                      https://git.xxx.com/.../fulfill_task                        履约异步任务服务
          渠道对接        trade.channel_srv                       https://git.xxx.com/.../channel-srv                         渠道对接服务
                          trade.notify_proxy                      https://git.xxx.com/.../notify_proxy                        通知代理服务
          运营平台        trade.ops_api                           https://git.xxx.com/.../ops-api                             运营系统后台(含交易管理)
```

关键信息：
- **模块 / 子模块** — 业务如何划分（AI 需要知道哪些服务属于同一业务域）
- **服务名** — 每个服务的标识
- **git 仓库地址** — 代码在哪里（已 clone 到本地的填本地路径，未 clone 的填 git 地址，Skill 会自动 clone）
- **服务描述** — 一句话说明这个服务干什么（AI 理解职责边界的关键输入）

### 第二步：在 Claude Code 中运行

把整理好的表格直接粘贴给 Claude Code：

```
帮我初始化编码知识库。

业务模块和仓库信息如下：

模块    子模块        服务                              git仓库                                       服务描述
交易    订单处理      order_srv                         https://git.xxx.com/.../order-srv               订单核心服务
                      pay_srv                           https://git.xxx.com/.../pay_srv                 支付服务
        履约          fulfill_srv                       https://git.xxx.com/.../fulfill_srv              履约&配置服务
                      fulfill_task                      https://git.xxx.com/.../fulfill_task             履约异步任务服务
        渠道对接      channel_srv                       https://git.xxx.com/.../channel-srv              渠道对接服务
        运营平台      ops_api                           https://git.xxx.com/.../ops-api                  运营系统后台(含交易管理)
```

如果仓库已 clone 到本地，也可以直接给本地路径，不需要 git 地址。

然后 Skill 会：
1. **自动 clone**（如需要）+ **扫描**所有仓库（Python 脚本，秒级完成）
2. **问你几个问题**补充代码里看不到的信息（CI/CD 流程、业务规则等）
3. **生成三层知识库**，包含精确到行号的符号索引
4. **自检验证**确保知识质量

全程约 20-25 分钟（11 个仓库规模）。

## 生成后的效果

**之前**（没有知识库）：
```
你：帮我改一下合同签章的逻辑
AI：请问支付相关的代码在哪个文件？（开始盲目搜索...）
```

**之后**（有知识库）：
```
你：帮我改一下支付回调的逻辑
AI：（自动读取 INDEX.md → 场景路由表定位到 pay_srv →
     读 symbols.md 找到 PayCallbackController.handleCallback():78 →
     读 call-chains.md 了解完整链路 → 精准修改）
```

## 支持的技术栈

Java/Spring、Go、PHP、Vue/React、Node.js (Express/NestJS)、Python (Django/Flask/FastAPI)

自动检测，无需手动配置。

## 更新知识库

代码有变更后：

```
代码更新了，帮我刷新知识库
```

Skill 会通过 git diff 智能判断哪些仓库和文档需要更新，不会全量重跑。

## 常见问题

**Q: 扫描脚本报错怎么办？**
Skill 有降级策略，脚本失败的仓库会自动回退到 AI 直接扫描模式，不会阻塞整个流程。

**Q: 仓库很多（50+）会不会超时？**
不会。脚本扫描 50 个仓库 < 3 分钟，AI 合成阶段自动分批并行处理，带进度检查点，中断可恢复。

**Q: 生成的知识库准确吗？**
Skill 内置三级质量校验：文件完整性检查 → 行号准确性抽查 → 跨文件一致性检查。此外还有可用性验证环节，用实际编码场景测试知识库是否真的能用。

**Q: 和 gen-project-doc 有什么区别？**
gen-project-doc 侧重单仓库的 CLAUDE.md + docs/，适合单项目场景。本 Skill 侧重多仓库多服务的三层分层知识体系，适合复杂业务领域的 AI 编码。两者可互补。
