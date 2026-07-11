#!/usr/bin/env python3
"""
将 Markdown 文件转换为 HTML 并同步到 TAPD 需求单描述字段。

用法:
  # 查看当前需求单描述（预览模式）
  python tapd_sync.py --url <TAPD_URL> --preview

  # 上传 md 文件到需求单
  python tapd_sync.py --url <TAPD_URL> --file <MD_FILE>

  # 跳过确认直接上传
  python tapd_sync.py --url <TAPD_URL> --file <MD_FILE> --yes

环境变量:
  TAPD_ACCESS_TOKEN  TAPD 个人访问令牌（必须）
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
import html as html_module
from html.parser import HTMLParser
from datetime import datetime
from pathlib import Path
from uuid import uuid4

ALLOW_REMOTE_MERMAID = False
MERMAID_JS_PATH = None


def parse_tapd_url(url: str) -> tuple:
    """从 TAPD URL 中提取 workspace_id 和 story_id。

    支持的 URL 格式:
      - https://www.tapd.cn/tapd_fe/{workspace_id}/story/detail/{story_id}
      - https://www.tapd.cn/tapd_fe/my/work?dialog_preview_id=story_{story_id}
      - https://www.tapd.cn/{workspace_id}/prong/stories/view/{story_id}
    """
    # Format 1: /tapd_fe/{workspace_id}/story/detail/{story_id}
    m = re.search(r'tapd\.cn/tapd_fe/(\d+)/stor(?:y|ies)/detail/(\d+)', url)
    if m:
        return m.group(1), m.group(2)

    # Format 2: dialog_preview_id=story_{story_id} (需要从 story_id 推断 workspace_id)
    m = re.search(r'dialog_preview_id=story_(\d+)', url)
    if m:
        story_id = m.group(1)
        wm = re.search(r'tapd\.cn/tapd_fe/(\d+)/', url)
        if wm:
            return wm.group(1), story_id
        # 从 story_id 推断: story_id 格式通常是 11{workspace_id}001{seq}
        if len(story_id) > 12:
            workspace_id = story_id[2:13]
            return workspace_id, story_id
        return None, story_id

    # Format 3: /{workspace_id}/prong/stories/view/{story_id}
    m = re.search(r'tapd\.cn/(\d+)/prong/stories/view/(\d+)', url)
    if m:
        return m.group(1), m.group(2)

    return None, None


def _estimate_mermaid_width(mermaid_code: str) -> int:
    """根据 Mermaid 图表复杂度估算合适的渲染宽度。"""
    lines = [l.strip() for l in mermaid_code.strip().split('\n') if l.strip()]
    edge_lines = sum(1 for l in lines if '-->' in l)
    branches = sum(1 for l in lines if '{' in l and '}' in l and '-->' in l)
    max_label = max((len(l) for l in lines), default=0)

    if edge_lines > 15 or branches > 3 or max_label > 80:
        return 1200  # 复杂图
    elif edge_lines > 8:
        return 900   # 中等图
    else:
        return 600   # 简单线性图


# 全局 Playwright browser 实例，避免每张图都启动一次浏览器
_pw_browser = None
_pw_playwright = None


def _get_playwright_browser():
    """获取或创建 Playwright 浏览器实例（单例）。"""
    global _pw_browser, _pw_playwright
    if _pw_browser is not None:
        return _pw_browser
    try:
        from playwright.sync_api import sync_playwright
        _pw_playwright = sync_playwright().start()
        _pw_browser = _pw_playwright.chromium.launch()
        return _pw_browser
    except Exception:
        return None


def _close_playwright():
    """关闭 Playwright 浏览器。"""
    global _pw_browser, _pw_playwright
    if _pw_browser:
        _pw_browser.close()
        _pw_browser = None
    if _pw_playwright:
        _pw_playwright.stop()
        _pw_playwright = None


def _mermaid_via_playwright(mermaid_code: str) :
    """用 Playwright（本地 Chromium）渲染 Mermaid 为高清 PNG，返回 base64 data URI。

    使用真正的浏览器引擎渲染，字体清晰、布局精准，质量与 TAPD 编辑器内手动粘贴一致。
    """
    import base64 as b64mod

    if not MERMAID_JS_PATH:
        return None
    mermaid_js = Path(MERMAID_JS_PATH)
    if not mermaid_js.is_file():
        print(f"  本地 Mermaid.js 不存在: {mermaid_js}")
        return None
    browser = _get_playwright_browser()
    if not browser:
        return None

    escaped_mermaid = html_module.escape(mermaid_code)
    html = f'''<!DOCTYPE html>
<html><head>
<style>
body {{ margin: 0; padding: 20px; background: white;
       font-family: -apple-system, "Microsoft YaHei", "PingFang SC", "Helvetica Neue", sans-serif; }}
</style>
</head><body>
<pre class="mermaid">
{escaped_mermaid}
</pre>
</body></html>'''

    try:
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.route(re.compile(r"^https?://", re.IGNORECASE), lambda route: route.abort())
        page.set_content(html)
        page.add_script_tag(path=str(mermaid_js))
        page.evaluate("mermaid.initialize({startOnLoad: true, theme: 'default', flowchart: {useMaxWidth: false}})")
        page.evaluate("mermaid.run({querySelector: '.mermaid'})")
        page.wait_for_selector('.mermaid svg', timeout=15000)
        svg = page.query_selector('.mermaid svg')
        img_bytes = svg.screenshot(type="png")
        page.close()

        img_data = b64mod.b64encode(img_bytes).decode('utf-8')
        print(f"    {len(img_bytes)/1024:.0f}KB (Playwright 本地渲染)")
        return f'<p><img src="data:image/png;base64,{img_data}" alt="流程图" style="max-width:100%;" /></p>'
    except Exception as e:
        print(f"  Playwright 渲染失败 ({e})")
        try:
            page.close()
        except Exception:
            pass
        return None


def _mermaid_via_ink(mermaid_code: str) :
    """用 mermaid.ink 远程服务渲染 Mermaid 为 PNG，返回外部链接或 base64 data URI。"""
    import base64 as b64mod

    width = _estimate_mermaid_width(mermaid_code)
    encoded = b64mod.urlsafe_b64encode(mermaid_code.encode()).decode()
    img_url = f'https://mermaid.ink/img/{encoded}?width={width}&type=png'

    # 优先：外部链接
    try:
        req = urllib.request.Request(img_url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print(f"    宽度={width}px (mermaid.ink 外部链接)")
                return f'<p><img src="{img_url}" alt="流程图" style="max-width:100%;" /></p>'
    except Exception as e:
        print(f"  mermaid.ink 外部链接不可用 ({e})，尝试下载...")

    # 回退：base64 内嵌
    try:
        req = urllib.request.Request(img_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=15) as resp:
            img_bytes = resp.read()
            img_data = b64mod.b64encode(img_bytes).decode('utf-8')
            print(f"    宽度={width}px, {len(img_bytes)/1024:.0f}KB (mermaid.ink base64)")
            return f'<p><img src="data:image/png;base64,{img_data}" alt="流程图" style="max-width:100%;" /></p>'
    except Exception as e:
        print(f"  mermaid.ink 渲染失败 ({e})")
        return None


def mermaid_to_img(mermaid_code: str) -> str:
    """将 Mermaid 代码渲染为 PNG 图片标签。

    渲染策略：本地 Mermaid.js + Playwright；失败时默认保留代码块。
    只有用户显式许可时才把源码发送给 mermaid.ink。
    """
    # 优先：Playwright 本地渲染
    result = _mermaid_via_playwright(mermaid_code)
    if result:
        return result

    # 远程渲染会向第三方发送图表源码，仅在用户显式允许时使用。
    if ALLOW_REMOTE_MERMAID:
        result = _mermaid_via_ink(mermaid_code)
        if result:
            return result

    # 兜底：代码块
    print(f"  警告: 所有渲染方式均失败，保留为代码块")
    escaped = mermaid_code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return f'<pre><code class="language-mermaid">{escaped}</code></pre>'


def secure_write(path: Path, content: bytes) -> None:
    """Create a new private file without a world-readable permission window."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


class _VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.images = []
        self.hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style"}:
            self.hidden_depth += 1
        if tag.lower() == "img":
            image = dict(attrs)
            alt = image.get("alt") or ""
            self.images.append({"alt": re.sub(r"\s+", " ", alt).strip(), "src": (image.get("src") or "").strip()})
            if alt:
                self.parts.append(alt)

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data):
        if not self.hidden_depth:
            self.parts.append(data)


def normalized_visible_text(html: str) -> str:
    """Normalize HTML to the user-visible text TAPD must preserve."""
    parser = _VisibleTextParser()
    parser.feed(html)
    parser.close()
    return re.sub(r"\s+", " ", html_module.unescape(" ".join(parser.parts))).strip()


def normalized_content_contract(html: str) -> dict:
    """Return text plus image semantics that must survive TAPD sanitization."""
    parser = _VisibleTextParser()
    parser.feed(html)
    parser.close()
    text = re.sub(r"\s+", " ", html_module.unescape(" ".join(parser.parts))).strip()
    return {"text": text, "images": parser.images}


def md_to_html(md_content: str) -> str:
    """将 Markdown 转换为 HTML，去掉 YAML frontmatter，预渲染 Mermaid 图表。"""
    try:
        import markdown
    except ImportError:
        print("错误: 缺少 Python 依赖 markdown。")
        print(f"请确认后执行: {sys.executable} -m pip install markdown")
        raise SystemExit(2)

    # 去掉 YAML frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', md_content, flags=re.DOTALL)

    # 去掉文档开头的第一个 H1 标题（TAPD 需求单本身有标题，无需重复）
    content = re.sub(r'^\s*#\s+[^\n]+\n+', '', content)

    # 预渲染 Mermaid 代码块（在 markdown 转换前处理）
    mermaid_count = 0

    def replace_mermaid(match):
        nonlocal mermaid_count
        mermaid_count += 1
        code = match.group(1).strip()
        print(f"  渲染 Mermaid 图表 #{mermaid_count}...")
        return mermaid_to_img(code)

    content = re.sub(
        r'```mermaid\s*\n(.*?)```',
        replace_mermaid,
        content,
        flags=re.DOTALL
    )

    if mermaid_count > 0:
        print(f"  共渲染 {mermaid_count} 个 Mermaid 图表")
        _close_playwright()

    # 确保有序/无序列表前有空行，否则 markdown 库不会解析为 <ol>/<ul>
    content = re.sub(r'([^\n])\n((\d+\.|\-|\*)\s)', r'\1\n\n\2', content)

    # 连续的 **标签：** 行之间加 trailing spaces 使 Markdown 产生 <br>
    # 需要循环应用，因为正则匹配不重叠（A\nB\nC 第一次匹配 A\nB，B\nC 被跳过）
    # 用 (?<!  ) 负向前瞻确保不会重复添加 trailing spaces（避免无限循环）
    prev = None
    while prev != content:
        prev = content
        content = re.sub(r'(\*\*[^*]+：\*\*\s*.+?)(?<!  )\n(\*\*[^*]+：\*\*)', r'\1  \n\2', content)

    html = markdown.markdown(content, extensions=['tables', 'fenced_code', 'toc'])
    # 松散列表会产生 <li><p>...</p></li>，去掉 <p> 包裹改为紧凑格式避免行距过大
    html = re.sub(r'<li>\s*<p>(.*?)</p>\s*</li>', r'<li>\1</li>', html, flags=re.DOTALL)
    return html


def tapd_api(method: str, endpoint: str, params: dict = None) -> dict:
    """调用 TAPD API。"""
    token = os.environ.get('TAPD_ACCESS_TOKEN')
    if not token:
        print("错误: 未设置 TAPD_ACCESS_TOKEN 环境变量")
        print("请在终端执行: export TAPD_ACCESS_TOKEN='你的令牌'")
        print("获取方式: TAPD → 右上角头像 → 个人设置 → 安全与认证 → 创建个人访问令牌")
        sys.exit(1)

    base_url = "https://api.tapd.cn"
    url = f"{base_url}/{endpoint}"

    if method == 'GET' and params:
        url += '?' + urllib.parse.urlencode(params)
        data = None
    elif method == 'POST' and params:
        data = urllib.parse.urlencode(params).encode('utf-8')
    else:
        data = None

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    if data:
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"TAPD API 错误 ({e.code}): {body}")
        sys.exit(1)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"TAPD 网络错误: {e}")
        sys.exit(1)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"TAPD 响应解析失败: {e}")
        sys.exit(1)


def get_story(workspace_id: str, story_id: str) -> dict:
    """获取需求单信息。"""
    result = tapd_api('GET', 'stories', {
        'workspace_id': workspace_id,
        'id': story_id
    })
    if result.get('status') == 1 and result.get('data'):
        return result['data'][0]['Story']
    print(f"错误: 未找到需求单 (workspace={workspace_id}, id={story_id})")
    print(f"API 返回: {json.dumps(result, ensure_ascii=False)}")
    sys.exit(1)


def update_story_description(workspace_id: str, story_id: str, html: str) -> dict:
    """更新需求单描述字段。"""
    result = tapd_api('POST', 'stories', {
        'workspace_id': workspace_id,
        'id': story_id,
        'description': html
    })
    if result.get('status') == 1:
        return result['data']['Story']
    print(f"错误: 更新失败")
    print(f"API 返回: {json.dumps(result, ensure_ascii=False)}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='将 Markdown 同步到 TAPD 需求单')
    parser.add_argument('--url', required=True, help='TAPD 需求单 URL')
    parser.add_argument('--file', help='Markdown 文件路径')
    parser.add_argument('--preview', action='store_true', help='仅预览当前需求单信息')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认直接上传')
    parser.add_argument('--workspace-id', help='手动指定 workspace_id（URL 无法自动解析时使用）')
    parser.add_argument('--backup-dir', help='原描述和 HTML 预览的保存目录，默认位于 Markdown 同目录的 tapd-backup/')
    parser.add_argument('--allow-remote-mermaid', action='store_true', help='允许将 Mermaid 源码发送到 mermaid.ink 远程渲染')
    parser.add_argument('--mermaid-js', help='本地 mermaid.min.js 路径；仅使用本地文件，不从 CDN 加载')
    parser.add_argument('--accept-concurrency-risk', action='store_true', help='确认接受 TAPD 无条件更新接口在最终检查后仍有极短并发覆盖窗口')
    args = parser.parse_args()
    global ALLOW_REMOTE_MERMAID, MERMAID_JS_PATH
    ALLOW_REMOTE_MERMAID = args.allow_remote_mermaid
    MERMAID_JS_PATH = args.mermaid_js

    # 解析 TAPD URL
    workspace_id, story_id = parse_tapd_url(args.url)
    if args.workspace_id:
        workspace_id = args.workspace_id
    if not workspace_id or not story_id:
        print(f"错误: 无法从 URL 解析出 workspace_id 和 story_id")
        print(f"URL: {args.url}")
        print(f"解析结果: workspace_id={workspace_id}, story_id={story_id}")
        print("请使用 --workspace-id 参数手动指定")
        sys.exit(1)

    # 获取当前需求单
    story = get_story(workspace_id, story_id)
    current_desc_len = len(story.get('description') or '')
    print(f"需求单: {story['name']}")
    print(f"当前描述: {current_desc_len} 字符")

    if args.preview:
        print(f"\nworkspace_id: {workspace_id}")
        print(f"story_id: {story_id}")
        print(f"状态: {story.get('status', 'unknown')}")
        return

    # 读取并转换 Markdown
    if not args.file:
        print("错误: 需要指定 --file 参数")
        sys.exit(1)

    file_path = os.path.expanduser(args.file)
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '-' + uuid4().hex[:8]
    backup_dir = Path(os.path.expanduser(args.backup_dir)) if args.backup_dir else Path(file_path).resolve().parent / 'tapd-backup'
    backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup_dir.chmod(0o700)
    backup_path = backup_dir / f'{story_id}-{timestamp}.json'
    backup_payload = json.dumps({
        'workspace_id': workspace_id,
        'story_id': story_id,
        'name': story.get('name'),
        'description': story.get('description') or '',
        'backed_up_at': datetime.now().isoformat(timespec='seconds'),
        'source_file': str(Path(file_path).resolve()),
    }, ensure_ascii=False, indent=2).encode('utf-8')
    secure_write(backup_path, backup_payload)
    print(f"原描述备份: {backup_path}")

    html_content = md_to_html(md_content)
    print(f"Markdown: {len(md_content)} 字符 → HTML: {len(html_content)} 字符")
    preview_path = backup_dir / f'{story_id}-{timestamp}-preview.html'
    secure_write(preview_path, html_content.encode('utf-8'))
    print(f"HTML 预览: {preview_path}")

    # 确认
    if not args.yes:
        print(f"\n即将覆盖需求单描述 ({current_desc_len} → {len(html_content)} 字符)")
        confirm = input("确认上传? [y/N] ")
        if confirm.lower() != 'y':
            print("已取消")
            return

    # 检测读取到最终确认之间的修改；TAPD 接口无条件更新，无法消除随后 POST 前的竞态窗口。
    latest = get_story(workspace_id, story_id)
    if (latest.get('description') or '') != (story.get('description') or ''):
        print("错误: 确认期间需求单描述已被其他人更新，已停止上传。请重新预览、备份并确认。")
        sys.exit(1)
    if args.yes and not args.accept_concurrency_risk:
        print("错误: --yes 模式还需显式传入 --accept-concurrency-risk；TAPD API 不支持条件更新。")
        sys.exit(1)
    if not args.yes:
        print("注意: TAPD API 不支持条件更新。最终检查后到上传前仍存在极短并发覆盖窗口。")
        confirm = input("接受该风险并立即上传? [y/N] ")
        if confirm.lower() != 'y':
            print("已取消")
            return

    # 上传
    updated = update_story_description(workspace_id, story_id, html_content)
    verified = get_story(workspace_id, story_id)
    new_len = len(verified.get('description', '') or '')
    verified_html = verified.get('description', '') or ''
    expected_contract = normalized_content_contract(html_content)
    verified_contract = normalized_content_contract(verified_html)
    expected_images = expected_contract["images"]
    verified_images = verified_contract["images"]
    text_matches = verified_contract["text"] == expected_contract["text"]
    image_count_matches = len(verified_images) == len(expected_images)
    image_alts_match = [item["alt"] for item in verified_images] == [item["alt"] for item in expected_images]
    image_sources_valid = all(item["src"] for item in verified_images)
    content_matches = text_matches and image_count_matches and image_alts_match and image_sources_valid
    if verified.get('name') != story.get('name') or not content_matches:
        print("错误: 上传后的需求单核对失败，请使用本地备份检查或恢复")
        print(f"可见文本长度: 预期 {len(expected_contract['text'])}，远端 {len(verified_contract['text'])}；全文一致: {text_matches}")
        print(f"图片: 预期 {len(expected_images)}，远端 {len(verified_images)}；顺序/alt一致: {image_alts_match}；src有效: {image_sources_valid}")
        print(f"备份文件: {backup_path}")
        sys.exit(1)
    print(f"\n上传成功")
    print(f"需求单: {verified['name']}")
    print(f"描述长度: {current_desc_len} → {new_len} 字符")
    print(f"已核对远端标题、规范化完整可见文本及图片完整性；原描述备份: {backup_path}")


if __name__ == '__main__':
    main()
