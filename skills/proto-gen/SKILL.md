---
name: proto-gen
description: >-
  根据 PRD 终稿生成 B 端 HTML 高保真原型，参考项目现有前端组件风格，每个页面独立文件，支持单页微调。
  当用户提到"生成原型"、"做原型"、"画页面"、"出原型"、"HTML 原型"、"页面原型"、
  "把 PRD 变成页面"、"根据需求出个原型"时使用此 skill。
  即使用户只是说"这个需求的页面大概长什么样"，也可以用这个 skill 快速生成可浏览的原型。
type: interactive
theme: pm-artifacts
---

## Purpose

PRD 写好了，但开发和业务方对"页面长什么样"的理解往往不一致。传统做法是用 Figma/Axure 画原型，但对于 B 端后台系统，大量页面都是表格、表单、弹窗的组合——用 HTML 直接生成反而更快，而且可以直接在浏览器中交互。

这个 skill 读取 PRD 和项目前端代码，识别页面列表和交互流程，生成一套可浏览的 HTML 高保真原型。关键设计是：每个页面独立文件，改一个不影响其他；全局样式用 CSS 变量控制，微调风格只需改一个文件；组件样式参考现有前端代码，让原型看起来和正式系统一致。

## 输入

- PRD 文件路径（Markdown 格式，通常是 `prd-craft` 或手写的 PRD 终稿）
- 项目前端代码（用于提取组件样式，非必须）

## 工作流程

### Step 1: 分析 PRD 和前端代码

1. **读取 PRD**：提取以下信息：
   - 功能清单（每个功能对应的页面）
   - 业务流程图（页面间的跳转关系）
   - 需求详情（每个页面的交互说明、表单字段、表格列）
   - 角色权限（不同角色看到的内容差异）
   - 数据模型（表单字段的类型、枚举值、约束）

2. **读取前端代码**（如果存在）：
   - 查找项目中的前端代码目录（通常是 `src/`、`frontend/`、`web/` 等）
   - 读取全局样式文件（如 `variables.css`、`theme.less`、`tailwind.config.js`）提取：
     - 主色调、辅助色
     - 字号体系
     - 间距体系
     - 圆角、阴影等视觉参数
   - 读取常用组件样式（表格、表单、弹窗、按钮、搜索栏、分页器）提取：
     - 表格的表头样式、行高、斑马纹
     - 表单的标签对齐方式、输入框样式
     - 弹窗的宽度、标题栏样式
     - 按钮的颜色、大小层级
   - 如果使用了 UI 框架（Ant Design、Element UI 等），记录框架名和版本，在生成样式时参考其默认风格

3. **如果没有前端代码**：使用中性的 B 端默认风格（类似 Ant Design 默认主题），不会影响原型的生成。

4. **规划页面列表**：基于 PRD 功能清单，列出需要生成的页面：

```
📋 页面规划：

| 页面 | 类型 | 对应功能 | 文件名 |
|------|------|----------|--------|
| {列表页} | table | F-01 | list.html |
| {详情页} | detail | F-02 | detail.html |
| {新建/编辑} | form | F-03 | form.html |
| ... | ... | ... | ... |

共 X 个页面，确认后开始生成。
```

### Step 2: 生成共享样式文件 (styles.css)

这是所有页面的风格基础。使用 CSS 变量控制全局参数，用户只需修改变量值就能调整整体风格。

```css
/* ===== 全局 CSS 变量 ===== */
:root {
  /* 颜色体系 */
  --color-primary: #1890ff;        /* 主色 */
  --color-primary-hover: #40a9ff;  /* 主色悬停 */
  --color-success: #52c41a;
  --color-warning: #faad14;
  --color-danger: #ff4d4f;
  --color-text: #333;              /* 正文色 */
  --color-text-secondary: #999;    /* 辅助文字 */
  --color-border: #d9d9d9;
  --color-bg: #f5f5f5;             /* 页面背景 */
  --color-bg-white: #fff;          /* 卡片背景 */

  /* 字号体系 */
  --font-size-sm: 12px;
  --font-size-base: 14px;
  --font-size-lg: 16px;
  --font-size-title: 20px;

  /* 间距体系 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  /* 圆角 */
  --border-radius: 4px;

  /* 阴影 */
  --shadow-card: 0 2px 8px rgba(0,0,0,0.08);

  /* 布局尺寸 */
  --sidebar-width: 200px;
  --header-height: 48px;
}

/* ===== 基础重置 ===== */
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 100%; height: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: var(--font-size-base); color: var(--color-text); }

/* ===== 核心布局（必须严格遵守，不得覆盖） ===== */
.layout { display: flex; height: 100vh; width: 100%; overflow: hidden; }
.sidebar { width: var(--sidebar-width); min-width: var(--sidebar-width); height: 100vh; overflow-y: auto; background: #001529; color: #fff; }
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
.header { height: var(--header-height); min-height: var(--header-height); display: flex; align-items: center; padding: 0 var(--spacing-lg); background: var(--color-bg-white); border-bottom: 1px solid var(--color-border); }
.content { flex: 1; overflow-y: auto; padding: var(--spacing-lg); background: var(--color-bg); }
```

**布局规则（生成页面时必须遵守）**：
- 每个页面的 HTML 结构必须是 `.layout > .sidebar + .main > .header + .content`
- `.main` 用 `flex: 1; min-width: 0` 撑满侧边栏右侧的全部剩余空间，**禁止给 .main 或 .content 设置 max-width 或固定宽度**
- 内容区 `.content` 内部可以放卡片容器，但卡片也应 `width: 100%`，不要用 `max-width` 限制

如果从前端代码中提取到了实际的样式参数，用提取到的值替换上述默认值。

样式文件还应包含以下常用组件的样式定义：
- **布局**：侧边栏 + 顶栏 + 内容区的经典 B 端布局
- **表格**：表头、行、斑马纹、操作列
- **表单**：标签 + 输入框布局、必填标记、校验提示
- **弹窗**：遮罩、弹窗容器、标题栏、底部按钮
- **按钮**：主要/次要/危险/禁用状态
- **搜索栏**：搜索条件 + 搜索/重置按钮
- **分页器**：页码、每页条数、总数
- **标签/状态**：不同颜色的状态标签
- **面包屑**：页面层级导航
- **消息提示**：成功/失败/警告提示条

### Step 3: 逐页生成 HTML

每个页面一个独立的 HTML 文件，必须使用以下骨架结构：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{页面标题} - {模块名}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="layout">
    <div class="sidebar">
      <!-- 侧边栏导航，当前页高亮，链接到其他页面 -->
    </div>
    <div class="main">
      <div class="header">
        <!-- 面包屑 / 页面标题 -->
      </div>
      <div class="content">
        <!-- 页面主体内容 -->
      </div>
    </div>
  </div>
</body>
</html>
```

**严格要求**：
- HTML 结构必须是 `.layout > .sidebar + .main > .header + .content`，不得嵌套额外的容器层
- 不得在 `<style>` 标签中覆盖 `.layout`、`.sidebar`、`.main`、`.header`、`.content` 的布局属性
- 侧边栏导航必须包含所有页面的 `<a>` 链接，当前页用 `.active` 类标记

每个文件：
- 引用共享的 `styles.css`
- 侧边栏的导航菜单高亮当前页面，其他页面可点击跳转
- 使用真实的示例数据（不是 lorem ipsum），基于 PRD 中的数据模型生成
- 表单字段的类型和约束与 PRD 数据模型一致
- 包含基本的交互效果（用纯 JS 实现，不依赖外部库）：
  - 弹窗的打开/关闭
  - 表格行的选中
  - 表单的展开/收起
  - Tab 切换
  - 搜索栏的展开/收起

#### 页面类型模板

**列表页 (table)**：
- 页面标题 + 面包屑
- 搜索栏（基于 PRD 中的筛选条件）
- 操作按钮区（新建、批量操作等）
- 数据表格（列基于 PRD 数据模型，填充 5-8 行示例数据）
- 分页器
- 操作列（查看、编辑、删除等，基于 PRD 权限矩阵）

**详情页 (detail)**：
- 面包屑导航
- 基础信息卡片
- 关联信息 Tab
- 操作按钮（编辑、删除、状态变更等）

**表单页 (form)**：
- 面包屑导航
- 表单字段（类型、必填、校验提示与 PRD 一致）
- 底部按钮（提交、取消）
- 如果字段较多，分组展示

**弹窗 (modal)**：
- 不单独生成文件，嵌入在触发它的页面中
- 点击按钮弹出，点击关闭/遮罩收起

### Step 4: 生成导航入口页 (index.html)

```html
<!-- index.html 结构 -->
- 项目名称和模块名称
- 页面列表（带缩略描述，点击跳转到对应页面）
- 业务流程概览（展示页面间的流转关系）
- 角色说明（不同角色的权限差异）
```

### Step 5: 输出结构

```
requirements/{模块名}/prototype/
├── index.html          ← 导航入口
├── styles.css          ← 共享样式（CSS 变量在这里改）
├── list.html           ← 列表页
├── detail.html         ← 详情页
├── form.html           ← 表单页
└── ...                 ← 其他页面
```

### Step 6: 输出总结

生成完成后告知用户：
1. 原型文件位置
2. 共生成了多少个页面
3. 如何查看：`open requirements/{模块名}/prototype/index.html`
4. 如何微调：
   - 调整全局风格：修改 `styles.css` 中的 CSS 变量
   - 调整单个页面：直接编辑对应的 HTML 文件，不影响其他页面
5. 样式参考来源（从前端代码提取 / 使用默认风格）

## 生成原则

**保真度优先于花哨**：B 端原型的价值在于让业务方和开发看到"页面大概长这样"，而不是做得多好看。优先保证：字段完整、布局合理、交互逻辑正确。

**真实数据优于占位符**：表格和表单中使用基于 PRD 数据模型的真实示例数据（如"张三"、"2024-03-15"、"审核通过"），而不是"测试数据1"、"xxx"这类占位文字。让原型看起来像一个正在使用的系统。

**独立性优于 DRY**：每个 HTML 文件是完全独立的（除了引用 styles.css），即使这意味着侧边栏等公共部分在每个文件中重复。这样修改一个页面时不需要担心影响其他页面，也方便单独发给业务方确认某个页面。

**纯 HTML/CSS/JS**：不依赖任何外部框架或 CDN。原型文件可以直接用浏览器打开，不需要任何构建工具或网络连接。这保证了原型的便携性——可以打包发邮件、放到共享文件夹。

**组件一致性**：同一套原型中的表格、表单、按钮等组件保持视觉一致。不要一个页面的按钮是圆角的，另一个页面的是直角的。统一在 styles.css 中定义。

## 与其他 skill 的关系

```
coding-knowledge-init → prd-draft → prd-review → proto-gen
                                                      ↑
                                           PRD 终稿作为输入
```

- **前置**：`prd-draft` 或 `prd-review` 产出的 PRD 终稿
- **辅助**：`coding-knowledge/business/prd-reference/design-patterns.md` 提供现有交互模式参考

## Common Pitfalls

**布局不撑满全屏**：最常见的问题。原因通常是：给 `.main` 或 `.content` 设了 `max-width`、用了 `margin: 0 auto` 居中、或在 `.layout` 外面多套了一层容器。必须严格使用 styles.css 中定义的核心布局类，不要在页面内用 `<style>` 覆盖布局属性。

**一个文件塞所有页面**：多页面合并到一个 HTML 文件会导致难以维护和单独微调。每页一个文件是刻意的设计选择。

**依赖外部资源**：不要引用 CDN 上的字体、图标库或 CSS 框架。原型要能在离线环境下打开。如果需要图标，用 Unicode 字符或 SVG 内联。

**过度交互**：原型不需要实现完整的前端逻辑（如真正的表单校验、数据提交、API 调用）。只需要最基本的交互效果（弹窗开关、Tab 切换等）让业务方能理解操作流程即可。

**忽略 PRD 中的数据模型**：表格的列名、表单的字段名应该与 PRD 数据模型严格一致，而不是自己编一套。这是原型和 PRD 之间的桥梁。
