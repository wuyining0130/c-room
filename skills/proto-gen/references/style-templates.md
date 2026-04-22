## CSS 变量与组件样式

### 全局 CSS 变量

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

如果从前端代码中提取到了实际的样式参数，用提取到的值替换上述默认值。

### 组件样式参考

样式文件还应包含以下常用组件的样式定义（以下为关键组件的参考实现，生成时以此为基础扩展）：

```css
/* ===== 表格 ===== */
.table-container { width: 100%; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; background: var(--color-bg-white); }
th { background: #fafafa; font-weight: 500; text-align: left; padding: 12px 16px; border-bottom: 1px solid var(--color-border); }
td { padding: 12px 16px; border-bottom: 1px solid #f0f0f0; }
tr:hover td { background: #fafafa; }

/* ===== 表单 ===== */
.form-group { display: flex; align-items: flex-start; margin-bottom: var(--spacing-lg); }
.form-label { width: 120px; min-width: 120px; text-align: right; padding-right: 12px; line-height: 32px; color: var(--color-text); }
.form-label .required { color: var(--color-danger); margin-right: 4px; }
.form-control { flex: 1; min-width: 0; }
input[type="text"], input[type="number"], input[type="date"], select, textarea {
  width: 100%; height: 32px; padding: 4px 11px; border: 1px solid var(--color-border);
  border-radius: var(--border-radius); font-size: var(--font-size-base); outline: none;
}
input:focus, select:focus, textarea:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(24,144,255,0.2); }
textarea { height: auto; min-height: 64px; }

/* ===== 按钮 ===== */
.btn { display: inline-flex; align-items: center; height: 32px; padding: 0 15px; border: 1px solid var(--color-border); border-radius: var(--border-radius); cursor: pointer; font-size: var(--font-size-base); background: var(--color-bg-white); }
.btn-primary { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.btn-primary:hover { background: var(--color-primary-hover); border-color: var(--color-primary-hover); }
.btn-danger { color: var(--color-danger); border-color: var(--color-danger); }

/* ===== 弹窗 ===== */
.modal-mask { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 1000; }
.modal-mask.active { display: flex; align-items: center; justify-content: center; }
.modal { background: var(--color-bg-white); border-radius: var(--border-radius); width: 520px; max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid var(--color-border); }
.modal-body { padding: 24px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 10px 24px; border-top: 1px solid var(--color-border); }

/* ===== 搜索栏 ===== */
.search-bar { display: flex; flex-wrap: wrap; gap: var(--spacing-md); padding: var(--spacing-md); background: var(--color-bg-white); border-radius: var(--border-radius); margin-bottom: var(--spacing-md); }
.search-bar .search-item { display: flex; align-items: center; gap: 8px; }
.search-bar .search-item label { white-space: nowrap; color: var(--color-text-secondary); }
.search-actions { display: flex; gap: 8px; margin-left: auto; }

/* ===== 分页器 ===== */
.pagination { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 16px 0; }
.pagination .page-info { color: var(--color-text-secondary); font-size: var(--font-size-sm); }

/* ===== 状态标签 ===== */
.tag { display: inline-block; padding: 0 8px; font-size: var(--font-size-sm); line-height: 22px; border-radius: 2px; }
.tag-success { color: var(--color-success); background: #f6ffed; border: 1px solid #b7eb8f; }
.tag-warning { color: var(--color-warning); background: #fffbe6; border: 1px solid #ffe58f; }
.tag-danger { color: var(--color-danger); background: #fff2f0; border: 1px solid #ffccc7; }
.tag-default { color: var(--color-text-secondary); background: #fafafa; border: 1px solid var(--color-border); }
.tag-processing { color: var(--color-primary); background: #e6f7ff; border: 1px solid #91d5ff; }

/* ===== 面包屑 ===== */
.breadcrumb { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.breadcrumb a { color: var(--color-text-secondary); text-decoration: none; }
.breadcrumb a:hover { color: var(--color-primary); }
.breadcrumb .separator { margin: 0 8px; }

/* ===== 卡片 ===== */
.card { background: var(--color-bg-white); border-radius: var(--border-radius); box-shadow: var(--shadow-card); padding: var(--spacing-lg); margin-bottom: var(--spacing-md); width: 100%; }
.card-title { font-size: var(--font-size-lg); font-weight: 500; margin-bottom: var(--spacing-md); }

/* ===== 操作栏 ===== */
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-md); }
```

生成 styles.css 时以上述为基础，根据实际页面需求扩展（如 Tab 切换、描述列表等）。如果从前端代码中提取到了实际样式参数，替换对应的值。

## HTML 骨架与页面类型模板

### HTML 骨架

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

### 页面类型模板

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
