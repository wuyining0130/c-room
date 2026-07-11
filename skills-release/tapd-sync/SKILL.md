---
name: tapd-sync
description: >-
  将 Markdown 文档同步到 TAPD 需求单。读取本地 md 文件，转换为 HTML，通过 TAPD API 更新需求单描述字段。
  当用户提到"上传到 TAPD"、"同步到 TAPD"、"更新 TAPD 需求单"、"把 md 传到 TAPD"、
  "把 PRD 更新到 TAPD"、"同步需求单"时使用此 skill。
  用户粘贴了 tapd.cn 链接并提到上传/同步/更新文档时，也应该触发。
---

## Purpose

PRD、技术方案等文档在本地用 Markdown 编写后，需要同步到 TAPD 需求单供团队协作。手动复制粘贴会丢失格式，而且每次更新都要重复操作。

这个 skill 把"读取 md → 转 HTML → 调 TAPD API 更新描述"封装成一条命令，用户只需提供文件路径和 TAPD 链接。

## 前置条件

需要配置 `TAPD_ACCESS_TOKEN` 环境变量。如果未配置，引导用户：

1. 登录 TAPD → 右上角头像 → 个人设置 → 安全与认证 → 创建个人访问令牌
2. 在终端执行（或添加到 `~/.zshrc` 持久化）：
   ```bash
   export TAPD_ACCESS_TOKEN="你的令牌"
   ```

## 工作流程

### Step 1: 收集输入

需要两个信息：
- **Markdown 文件路径**：要上传的文档（如 `prd-draft.md`、`tech-design.md`）
- **TAPD 需求单 URL**：用户粘贴的 TAPD 链接

支持的 TAPD URL 格式：
- `https://www.tapd.cn/tapd_fe/{workspace_id}/story/detail/{story_id}`
- `https://www.tapd.cn/tapd_fe/my/work?dialog_preview_id=story_{story_id}`
- `https://www.tapd.cn/{workspace_id}/prong/stories/view/{story_id}`

### Step 2: 确认并执行

1. 先做依赖预检；缺少依赖时列出安装命令并获得用户许可，不在上传流程中静默安装
2. 用 `--preview` 查看目标需求单信息，确认是正确的需求单
3. 将目标需求单当前标题、描述和获取时间保存到本地备份文件 `requirements/{模块名}/tapd-backup/{story_id}-{timestamp}.json`（无法判断模块时保存到 Markdown 同目录的 `tapd-backup/`）
4. 生成本地 HTML 预览并报告字符数、Mermaid 渲染方式和降级情况
5. 告知用户当前描述会被覆盖，获得确认
6. 执行上传；上传后重新读取需求单，核对标题及规范化后的完整可见文本是否一致

### 脚本调用

脚本位于此 skill 目录下的 `scripts/tapd_sync.py`。

```bash
# 预览需求单
python scripts/tapd_sync.py --url "<TAPD_URL>" --preview

# 上传（会提示确认）
python scripts/tapd_sync.py --url "<TAPD_URL>" --file "<MD_FILE>"

# 跳过确认直接上传（用户已在对话中确认时使用）
python scripts/tapd_sync.py --url "<TAPD_URL>" --file "<MD_FILE>" --yes --accept-concurrency-risk
```

如果 URL 中无法自动解析 workspace_id，使用 `--workspace-id` 手动指定。

### Step 3: 输出结果

上传成功后告知用户：
1. 需求单名称
2. 描述字段的字符数变化
3. TAPD 链接（方便用户直接点击查看）

## 技术细节

### Markdown → HTML

- TAPD 需求单描述字段底层是 HTML，Markdown 需要先转为 HTML 才能正确渲染
- 转换使用 Python `markdown` 库，支持表格、代码块、目录等扩展
- YAML frontmatter 会被自动去除

### Mermaid 流程图处理

TAPD 需求单描述字段不支持原生 Mermaid 渲染（仅 TAPD Markdown Wiki 页面支持），因此脚本会将 Mermaid 代码块预渲染为 PNG 图片。

**渲染策略**：

1. **Playwright 本地渲染（优先）**：用户提供本地 `mermaid.min.js` 并传入 `--mermaid-js <path>`；脚本用本地 Chromium 渲染，并拦截页面发起的所有 HTTP(S) 请求，防止图表中的外部资源间接联网。
2. **代码块（默认兜底）**：本地渲染不可用时保留为 `<pre><code>`，避免将合同、接口或架构图内容发送给第三方。
3. **mermaid.ink 远程渲染（显式许可）**：只有用户明确同意并传入 `--allow-remote-mermaid` 时使用。

**本地渲染依赖**：需要 Playwright、Chromium 和用户提供的本地 Mermaid.js。未提供任一项时默认保留代码块；远程回退必须获得用户许可。

**为什么不用 SVG**：TAPD 的 HTML 清洗器会剥离 SVG 中的 `<foreignObject>` 元素，而 Mermaid 用 foreignObject 渲染文字，导致图表文字和连线全部丢失。

### 上传行为

- 上传操作会**覆盖**需求单现有描述，TAPD 有变更历史可回退
- TAPD 当前接口不支持条件更新。脚本会在上传前再次读取以检测确认窗口内的修改，但最终检查与 POST 之间仍有极短竞态窗口；交互模式需再次确认风险，`--yes` 模式必须同时传入 `--accept-concurrency-risk`

## Python 依赖

脚本不会自动修改 Python 环境。缺少依赖时退出并显示安装命令，经用户确认后再安装：

```bash
pip3 install markdown playwright
playwright install chromium
```

Playwright 用于本地高清 Mermaid 渲染（可选）。未安装或未传入本地 Mermaid.js 时保留代码块，不自动调用远程服务。

## 与其他 skill 的关系

通常在 prd-draft 或 tech-design 生成文档后使用，将本地 Markdown 产出物同步到 TAPD 供团队查看。

## Common Pitfalls

**忘记确认覆盖**：上传会替换需求单现有描述。脚本默认提示确认并说明并发竞态；仅在用户已明确接受该风险时使用 `--yes --accept-concurrency-risk`。

**未保存原描述**：上传前必须保存本地 JSON 备份；即使 TAPD 有历史记录，也不能把远端历史作为唯一回滚手段。

**URL 解析失败**：部分 TAPD URL 格式中 workspace_id 不在路径里（如 `dialog_preview_id` 格式），需要用 `--workspace-id` 手动指定。

**Mermaid 未渲染**：默认不会联网下载 Mermaid.js。需要图片时，安装 Playwright 和 Chromium，并用 `--mermaid-js` 指向本地 `mermaid.min.js`；只有确认可向第三方发送源码时才使用 `--allow-remote-mermaid`。
