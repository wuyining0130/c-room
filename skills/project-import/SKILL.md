---
name: project-import
description: >-
  从 TAPD 链接或 Git 仓库地址一键导入项目资料到本地标准目录。用户只需粘贴链接，skill 自动识别类型、检测凭证、引导配置、拉取资料并整理归档。
  当用户提到"拉取项目资料"、"导入需求"、"克隆代码"、"把 TAPD 的需求拉到本地"、粘贴了 tapd.cn 链接或 git 仓库地址时，使用此 skill。
---

## Purpose

产品经理和开发在启动 AI 辅助工作流时，第一步往往是把项目的需求文档和代码拉到本地。这个过程涉及 TAPD 凭证配置、Git Token 申请、API 命令拼装等繁琐步骤。

这个 skill 把这些步骤封装成"粘贴链接 → 自动处理"的体验：用户不需要记任何命令格式，只需要提供链接，skill 负责识别、检查、拉取、整理。

## 交互流程

按以下顺序引导用户，每一步确认后再进入下一步。

### Step 1: 接收链接并识别类型

询问用户："请粘贴你要导入的链接（TAPD 页面链接、Git 仓库地址，或者文档链接）。可以一次粘贴多个。"

根据链接内容自动识别类型：

**TAPD 链接识别规则：**

匹配 `tapd.cn` 域名下的 URL，从中提取 workspace_id 和实体信息。

URL 模式：`https://www.tapd.cn/tapd_fe/{workspace_id}/{entity_type}/detail/{entity_id}`

示例：`https://www.tapd.cn/tapd_fe/12345678/story/detail/1112345678001256446`

从 URL 中提取：
- `workspace_id`：路径中 `tapd_fe/` 后面的数字（如 `12345678`）
- `entity_type`：`story` → stories, `bug` → bug
- `entity_id`：`detail/` 后面的数字（如 `1112345678001256446`）

**Git 仓库链接识别规则：**

匹配以下模式之一：
- 包含 `.git` 后缀的 URL
- `git@` 开头的 SSH 地址
- 包含 `gitlab` 或 `github` 的 URL
- 用户明确说明是 Git 仓库

**其他链接：**

如果链接不属于以上两类，提示用户确认链接类型，或作为文档链接处理。

识别完成后，向用户确认："识别到以下内容：[列出识别结果]。是否正确？"

### Step 2: 检测凭证并引导配置

根据识别到的链接类型，检查对应凭证是否已配置。

**TAPD 凭证检测：**

检查环境变量 `TAPD_ACCESS_TOKEN` 是否存在：

```bash
echo "${TAPD_ACCESS_TOKEN:+已配置}" || echo "未配置"
```

如果未配置，引导用户：

1. 告知用户："TAPD 需要一个访问令牌才能拉取数据。"
2. 指引获取方式："登录 TAPD → 右上角头像 → 个人设置 → 安全与认证 → 创建个人访问令牌"
3. 指引配置方式："在终端执行以下命令（或添加到 ~/.zshrc 持久化）："
   ```bash
   export TAPD_ACCESS_TOKEN="你的令牌"
   ```
4. 配置完成后，用一个简单的 API 调用验证令牌是否有效：
   ```bash
   python scripts/tapd.py get_user_participant_projects
   ```
   如果返回项目列表则凭证有效。如果报错，提示用户检查令牌。

**Git 凭证检测（GitLab 私有部署）：**

尝试对目标仓库执行 `git ls-remote` 检测访问权限：

```bash
git ls-remote --exit-code <仓库地址> HEAD 2>&1
```

如果失败，引导用户：

1. 告知用户："Git 仓库需要 Personal Access Token 才能访问。"
2. 指引获取方式："登录 GitLab → Settings → Access Tokens → 创建一个具有 `read_repository` 权限的令牌"
3. 指引配置方式——推荐使用 Git 凭证存储，避免每次输入：
   ```bash
   git config --global credential.helper store
   # 然后在克隆时输入一次用户名和 Token 即可
   ```

凭证检测通过后，告知用户："凭证检测通过，可以开始拉取。"

### Step 3: 选择拉取范围并执行

根据链接类型提供不同的范围选项。

**TAPD 需求拉取：**

当用户粘贴的是需求详情链接时，直接拉取该条需求，无需额外选择。

如果用户需要拉取更多需求，可以：
1. **继续粘贴更多链接**——逐条拉取
2. **按关键词搜索拉取**——用户提供关键词，模糊匹配
3. **拉取项目下全部需求**——拉取 workspace 下所有需求（超过 100 条时提醒用户）

执行拉取时调用 tapd skill 的脚本。tapd.py 脚本位于 tapd skill 目录下，路径为：
`~/.claude/skills/tapd/scripts/tapd.py`

拉取单条需求：
```bash
python ~/.claude/skills/tapd/scripts/tapd.py get_stories_or_tasks \
  --workspace_id {workspace_id} \
  --entity_type stories \
  --id {entity_id}
```

按关键词搜索拉取：
```bash
python ~/.claude/skills/tapd/scripts/tapd.py get_stories_or_tasks \
  --workspace_id {workspace_id} \
  --entity_type stories \
  --name "%关键词%"
```

**Git 仓库拉取：**

提供选项：
1. **克隆完整仓库**——`git clone <url>`
2. **只克隆最新版本**（浅克隆）——`git clone --depth 1 <url>`，节省时间和空间
3. **克隆指定分支**——`git clone -b <branch> <url>`

推荐默认使用浅克隆，因为 AI 分析代码通常不需要完整历史。

### Step 4: 整理到标准目录并生成导入摘要

所有拉取的资料整理到以下目录结构：

```
{project_name}/
└── sources/
    ├── tapd-requirements/          # TAPD 需求
    │   ├── raw/                    # 原始 JSON 数据
    │   │   ├── story_{id}.json
    │   │   └── ...
    │   └── docs/                   # Markdown 可读版
    │       ├── story_{id}.md
    │       └── ...
    ├── codebase/                   # Git 代码仓库
    │   └── {repo_name}/
    └── docs/                       # 其他文档
        └── ...
```

**TAPD 需求转 Markdown 格式：**

每条需求生成一个 Markdown 文件，格式如下：

```markdown
# {需求标题}

- **ID**: {id}
- **状态**: {status}
- **优先级**: {priority}
- **创建人**: {creator}
- **处理人**: {owner}
- **迭代**: {iteration}
- **创建时间**: {created}

## 需求描述

{description 内容，HTML 转 Markdown}

## 验收标准

{如有}
```

**生成 import-summary.md：**

拉取完成后，在 `{project_name}/` 根目录生成导入摘要：

```markdown
# 项目资料导入摘要

## 导入时间
{timestamp}

## TAPD 需求
- **项目 ID**: {workspace_id}
- **拉取范围**: {全量/迭代X/指定需求}
- **需求数量**: {count} 条
- **需求列表**:
  | ID | 标题 | 状态 | 优先级 |
  |----|------|------|--------|
  | ... | ... | ... | ... |

## 代码仓库
- **仓库地址**: {git_url}
- **分支**: {branch}
- **克隆方式**: {完整/浅克隆}

## 目录结构
{tree 命令输出}

## 下一步建议
使用 `knowledge-init` skill 基于这些资料生成项目知识库。
```

## 多链接批量处理

用户可以一次粘贴多个链接。处理逻辑：
1. 逐个识别所有链接的类型
2. 按类型分组（TAPD / Git / 其他）
3. 统一检测所有需要的凭证
4. 确认后批量执行拉取
5. 所有资料整理到同一个项目目录下

## 项目名称确定

按以下优先级确定项目名称：
1. 用户主动指定
2. Git 仓库名（如果有）
3. TAPD 项目名（通过 `get_workspace_info` 获取）
4. 询问用户

## 常见问题处理

**TAPD 令牌过期：** API 返回 401 时，提示用户重新生成令牌并更新环境变量。

**Git 克隆超时：** 建议用户检查网络/代理配置，或改用浅克隆。

**需求量过大：** 超过 100 条时提醒用户，建议按迭代分批拉取。

**链接无法识别：** 请用户确认链接类型，或手动指定是 TAPD / Git / 文档。

## Examples

### Example 1: 粘贴单条 TAPD 需求链接

**用户输入：**
"帮我把这个需求拉下来 https://www.tapd.cn/tapd_fe/12345678/story/detail/1112345678001256446"

**Skill 行为：**
1. 识别为 TAPD 需求链接，提取 workspace_id=12345678, entity_id=1112345678001256446
2. 检测 TAPD_ACCESS_TOKEN → 已配置 → 跳过引导
3. 提供范围选项，用户选"只拉这一条"
4. 执行拉取，保存 JSON + Markdown，生成 import-summary.md

### Example 2: 粘贴 Git 仓库 + 多条 TAPD 链接

**用户输入：**
"把这个项目的代码和需求都拉下来：
git@gitlab.example.com:myteam/myproject.git
https://www.tapd.cn/tapd_fe/12345678/story/detail/1112345678001256446
https://www.tapd.cn/tapd_fe/12345678/story/detail/1112345678001256789"

**Skill 行为：**
1. 识别三个链接：1 个 Git SSH 地址 + 2 条 TAPD 需求链接
2. 分别检测 Git 和 TAPD 凭证
3. Git: 推荐浅克隆 → TAPD: 逐条拉取两条需求
4. 统一整理到同一项目目录，生成 import-summary.md
