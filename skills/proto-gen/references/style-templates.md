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
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; position: relative; }

/* ===== 页面视图切换 ===== */
.page-view { display: none; flex-direction: column; height: 100%; width: 100%; overflow: hidden; }
.page-view.active { display: flex; }
.page-view .header { height: var(--header-height); min-height: var(--header-height); display: flex; align-items: center; padding: 0 var(--spacing-lg); background: var(--color-bg-white); border-bottom: 1px solid var(--color-border); }
.page-view .content { flex: 1; overflow-y: auto; padding: var(--spacing-lg); background: var(--color-bg); }
```

如果从前端代码中提取到了实际的样式参数，用提取到的值替换上述默认值。

### 组件样式参考

`<style>` 中还应包含以下常用组件的样式定义（以下为关键组件的参考实现，生成时以此为基础扩展）：

```css
/* ===== 侧边栏 ===== */
.sidebar-title { padding: 16px 20px; font-size: var(--font-size-lg); font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sidebar-menu { list-style: none; padding: 8px 0; }
.sidebar-menu li a { display: block; padding: 10px 20px; color: rgba(255,255,255,0.65); text-decoration: none; font-size: var(--font-size-base); transition: all 0.2s; cursor: pointer; }
.sidebar-menu li a:hover { color: #fff; background: rgba(255,255,255,0.08); }
.sidebar-menu li a.active { color: #fff; background: var(--color-primary); }
.sidebar-section { padding: 12px 20px 6px; font-size: var(--font-size-sm); color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 1px; }

/* ===== 表格 ===== */
.table-container { width: 100%; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; background: var(--color-bg-white); }
th { background: #fafafa; font-weight: 500; text-align: left; padding: 12px 16px; border-bottom: 1px solid var(--color-border); white-space: nowrap; }
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
.btn { display: inline-flex; align-items: center; height: 32px; padding: 0 15px; border: 1px solid var(--color-border); border-radius: var(--border-radius); cursor: pointer; font-size: var(--font-size-base); background: var(--color-bg-white); transition: all 0.2s; gap: 6px; }
.btn:hover { border-color: var(--color-primary); color: var(--color-primary); }
.btn-primary { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.btn-primary:hover { background: var(--color-primary-hover); border-color: var(--color-primary-hover); color: #fff; }
.btn-sm { height: 24px; padding: 0 8px; font-size: var(--font-size-sm); }
.btn-link { border: none; background: none; color: var(--color-primary); padding: 0; height: auto; cursor: pointer; text-decoration: none; }
.btn-link:hover { color: var(--color-primary-hover); }
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

/* ===== 快速跳转栏（header 右侧） ===== */
.quick-nav { display: flex; gap: 6px; align-items: center; }
.quick-nav .qn-item { display: inline-flex; align-items: center; padding: 0 10px; height: 26px; font-size: 12px; border-radius: 13px; cursor: pointer; transition: all 0.15s; white-space: nowrap; background: #f5f5f5; color: #666; border: 1px solid #e8e8e8; }
.quick-nav .qn-item:hover { background: #e6f7ff; color: #096dd9; border-color: #91d5ff; }
.quick-nav .qn-item.qn-active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
```

生成 `<style>` 块时以上述为基础，根据实际页面需求扩展（如 Tab 切换、描述列表等）。如果从前端代码中提取到了实际样式参数，替换对应的值。

## HTML 骨架

单文件原型使用以下骨架结构：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{模块名} - 原型</title>
  <style>
    /* 全局 CSS 变量 + 组件样式（全部内联） */
  </style>
</head>
<body>
  <div class="layout">
    <div class="sidebar">
      <div class="sidebar-title">{模块名}</div>
      <ul class="sidebar-menu">
        <li><a class="active" onclick="showPage('index')">首页概览</a></li>
        <li><a onclick="showPage('list')">列表页</a></li>
        <li><a onclick="showPage('detail')">详情页</a></li>
        <li><a onclick="showPage('form')">表单页</a></li>
      </ul>
    </div>
    <div class="main">
      <!-- 动态 Header：左侧面包屑 + 右侧快速跳转栏 -->
      <div class="header" id="pageHeader" style="justify-content: space-between;"></div>

      <div class="content">
        <!-- 首页概览 -->
        <div class="page-view active" id="page-index">
          <!-- 页面列表卡片 + 业务流程概览 -->
        </div>

        <!-- 列表页 -->
        <div class="page-view" id="page-list">
          <!-- 搜索栏 + 表格 + 分页 -->
        </div>

        <!-- 更多页面视图... -->
      </div>
    </div>
  </div>

  <script>
    // 快速跳转栏 HTML（所有页面共用，showPage 渲染到 header 右侧）
    var quickNav = '<div class="quick-nav">' +
      '<span class="qn-item" data-page="index" onclick="showPage(\'index\')">概览</span>' +
      '<span class="qn-item" data-page="list" onclick="showPage(\'list\')">F-01 列表页</span>' +
      '<span class="qn-item" data-page="form" onclick="showPage(\'form\')">F-02 表单页</span>' +
      '</div>';

    // 每个页面的面包屑（header 左侧）
    var breadcrumbs = {
      index: '<div style="font-weight:500;">{模块名} — 原型导航</div>',
      list:  '<div class="breadcrumb">列表页</div>',
      form:  '<div class="breadcrumb">表单页</div>'
    };

    function showPage(pageId) {
      // 切换页面视图
      document.querySelectorAll('.page-view').forEach(el => el.classList.remove('active'));
      var target = document.getElementById('page-' + pageId);
      if (target) target.classList.add('active');
      // 更新侧边栏高亮
      document.querySelectorAll('.sidebar-menu a').forEach(el => el.classList.remove('active'));
      var nav = document.querySelector('.sidebar-menu a[onclick*="' + pageId + '"]');
      if (nav) nav.classList.add('active');
      // 更新 header：左侧面包屑 + 右侧快速跳转栏
      document.getElementById('pageHeader').innerHTML = (breadcrumbs[pageId] || '') + quickNav;
      // 高亮当前页的快速跳转按钮
      document.querySelectorAll('.quick-nav .qn-item').forEach(el => {
        el.classList.toggle('qn-active', el.getAttribute('data-page') === pageId);
      });
    }
    showPage('index');
  </script>
</body>
</html>
```

**严格要求**：
- HTML 结构必须是 `.layout > .sidebar + .main`，`.main` 中包含多个 `.page-view`
- 不得在 `<style>` 中覆盖 `.layout`、`.sidebar`、`.main` 的核心布局属性
- 侧边栏导航使用 `onclick="showPage('xxx')"` 而非 `href` 链接
- 默认显示的页面视图添加 `.active` 类
- 每个 `.page-view` 内部必须包含 `.header` + `.content`

## 页面类型模板

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
- 嵌入在触发它的页面视图中
- 点击按钮弹出，点击关闭/遮罩收起
