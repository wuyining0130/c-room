---
name: tapd-sync
description: >-
  将 Markdown 文档同步到 TAPD 需求单。读取本地 md 文件，转换为 HTML，通过 TAPD API 更新需求单描述字段。
  当用户提到"上传到 TAPD"、"同步到 TAPD"、"更新 TAPD 需求单"、"把 md 传到 TAPD"、
  "把 PRD 更新到 TAPD"、"同步需求单"时使用此 skill。
  用户粘贴了 tapd.cn 链接并提到上传/同步/更新文档时，也应该触发。
type: interactive
theme: pm-artifacts
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

1. 先用 `--preview` 查看目标需求单信息，确认是正确的需求单
2. 告知用户当前描述会被覆盖（显示字符数变化），获得确认
3. 执行上传

### 脚本调用

脚本位于此 skill 目录下的 `scripts/tapd_sync.py`。

```bash
# 预览需求单
python scripts/tapd_sync.py --url "<TAPD_URL>" --preview

# 上传（会提示确认）
python scripts/tapd_sync.py --url "<TAPD_URL>" --file "<MD_FILE>"

# 跳过确认直接上传（用户已在对话中确认时使用）
python scripts/tapd_sync.py --url "<TAPD_URL>" --file "<MD_FILE>" --yes
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

**渲染策略（三级回退）**：

1. **Playwright 本地渲染（优先，最佳质量）**：用 Playwright 启动本地 Chromium，加载 Mermaid.js CDN 渲染为 SVG，再截图为 PNG。中文字体清晰（使用系统字体）、布局精准（真实浏览器引擎），质量与 TAPD 编辑器内手动粘贴一致。输出为 base64 data URI，TAPD 会提取到自己的 CDN 托管。
2. **mermaid.ink 远程渲染（回退）**：用 `mermaid.ink` 服务端渲染。优先生成外部直链（TAPD 直接加载不压缩），不可用时下载为 base64 内嵌。质量不如本地渲染（中文字体差、布局可能拥挤）。
3. **代码块（兜底）**：渲染完全失败时保留为 `<pre><code>` 格式

**Playwright 依赖**：需要 `pip3 install playwright && playwright install chromium`。如果未安装 Playwright，自动回退到 mermaid.ink。

**为什么不用 SVG**：TAPD 的 HTML 清洗器会剥离 SVG 中的 `<foreignObject>` 元素，而 Mermaid 用 foreignObject 渲染文字，导致图表文字和连线全部丢失。

### 上传行为

- 上传操作会**覆盖**需求单现有描述，TAPD 有变更历史可回退
- 脚本默认会提示确认，在对话中用户已明确同意时可用 `--yes` 跳过

## Python 依赖

脚本会自动安装缺失的依赖，也可以手动预装：

```bash
pip3 install markdown playwright
playwright install chromium
```

Playwright 用于本地高清 Mermaid 渲染（可选，未安装时自动回退到 mermaid.ink 远程渲染）。

## 与其他 skill 的关系

```
prd-draft / tech-design → tapd-sync → TAPD 需求单
```

- 通常在 prd-draft 或 tech-design 生成文档后使用
- 将本地 Markdown 产出物同步到 TAPD 供团队查看

## Common Pitfalls

**忘记确认覆盖**：上传会替换需求单现有描述。脚本默认会提示确认，在对话中用户已明确同意时可用 `--yes` 跳过。

**URL 解析失败**：部分 TAPD URL 格式中 workspace_id 不在路径里（如 `dialog_preview_id` 格式），需要用 `--workspace-id` 手动指定。

**Mermaid 图片模糊**：如果 Playwright 未安装导致回退到 mermaid.ink，中文字体和布局质量会明显下降。建议安装 Playwright（`pip3 install playwright && playwright install chromium`）获得最佳渲染效果。
