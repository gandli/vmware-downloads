#!/usr/bin/env python3
"""
VMware Download Link Collector
使用 Playwright 获取 VMware 下载链接（支持 JavaScript 渲染）
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# VMware 产品配置
VMWARE_PRODUCTS = {
    "workstation-pro": {
        "name": "VMware Workstation Pro",
        "url": "https://www.vmware.com/info/workstation-pro/evaluation",
        "platforms": ["Windows", "Linux"],
        "description": "行业标准的桌面虚拟化软件",
        "latest_version": "17.5.2",
    },
    "fusion-pro": {
        "name": "VMware Fusion Pro",
        "url": "https://knowledge.broadcom.com/external/article/315638/download-and-install-vmware-fusion.html",
        "platforms": ["macOS"],
        "description": "macOS 上的专业虚拟化软件",
        "latest_version": "13.5.2",
    },
}

# Broadcom 支持门户下载页面
BROADCOM_DOWNLOADS = {
    "workstation-pro": "https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro",
    "fusion-pro": "https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion%20Pro",
}

# VMware 知识库文章（包含下载信息）
VMWARE_KB_ARTICLES = {
    "workstation-pro": "https://knowledge.broadcom.com/external/article/368667/download-and-license-vmware-desktop-hype.html",
    "fusion-pro": "https://knowledge.broadcom.com/external/article/315638/download-and-install-vmware-fusion.html",
}


def get_page_with_playwright(url: str, wait_selector: str = None, timeout: int = 30000) -> str | None:
    """使用 Playwright 获取页面内容（支持 JavaScript 渲染）"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 访问页面
            page.goto(url, wait_until="networkidle", timeout=timeout)

            # 等待特定选择器出现（如果指定）
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=10000)
                except PlaywrightTimeout:
                    print(f"  等待选择器超时: {wait_selector}", file=sys.stderr)

            # 获取页面内容
            content = page.content()
            browser.close()
            return content

    except Exception as e:
        print(f"Playwright 错误: {e}", file=sys.stderr)
        return None


def extract_version_from_text(text: str) -> str | None:
    """从文本中提取版本号"""
    # 匹配 VMware 版本号模式（如 17.5.2, 13.5.0 等）
    patterns = [
        # 匹配 "VMware Workstation 17 Pro" 或 "VMware Fusion 13 Pro"
        r"VMware\s+Workstation\s+(\d+)(?:\s+Pro)?",
        r"VMware\s+Fusion\s+(\d+)(?:\s+Pro)?",
        # 匹配完整版本号如 17.5.2
        r"VMware\s+Workstation\s+(?:Pro\s+)?(\d+\.\d+(?:\.\d+)?)",
        r"VMware\s+Fusion\s+(?:Pro\s+)?(\d+\.\d+(?:\.\d+)?)",
        # 通用版本号模式
        r"Version\s+(\d+\.\d+(?:\.\d+)?)",
        r"v(\d+\.\d+(?:\.\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            version = match.group(1)
            # 如果只匹配到主版本号（如 17），添加 .0
            if version.isdigit():
                return f"{version}.0"
            return version

    return None


def extract_download_links(html: str, base_url: str = "") -> list[dict]:
    """从 HTML 中提取下载链接"""
    links = []

    # 匹配各种下载链接模式
    patterns = [
        # 直接下载链接
        r'href=["\']([^"\']*\.(?:exe|dmg|tar\.gz|bundle|iso|zip))["\']',
        # Broadcom 支持门户链接
        r'href=["\']([^"\']*support\.broadcom\.com[^"\']*)["\']',
        # VMware 下载链接
        r'href=["\']([^"\']*vmware\.com[^"\']*download[^"\']*)["\']',
        # 通用下载按钮
        r'href=["\']([^"\']*(?:download|get|try)[^"\']*)["\']',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            if match.startswith("/"):
                match = base_url + match
            if match not in [l["url"] for l in links]:
                links.append({"url": match, "type": "download"})

    return links


def check_vmware_product(product_key: str) -> dict:
    """检查 VMware 产品页面获取下载信息"""
    product = VMWARE_PRODUCTS[product_key]
    result = {
        "product": product["name"],
        "key": product_key,
        "platforms": product["platforms"],
        "description": product["description"],
        "product_url": product["url"],
        "broadcom_downloads": BROADCOM_DOWNLOADS.get(product_key, ""),
        "kb_article": VMWARE_KB_ARTICLES.get(product_key, ""),
        "checked_at": datetime.utcnow().isoformat(),
        "status": "unknown",
        "version": product.get("latest_version", "unknown"),
        "download_links": [],
    }

    print(f"正在检查 {product['name']}...")

    # 获取产品页面
    html = get_page_with_playwright(product["url"])
    if not html:
        result["status"] = "unreachable"
        return result

    result["status"] = "available"

    # 尝试从页面提取版本信息（如果预定义版本不存在）
    if result["version"] == "unknown":
        version = extract_version_from_text(html)
        if version:
            result["version"] = version
            print(f"  从页面找到版本: {version}")
    else:
        print(f"  使用预定义版本: {result['version']}")

    # 提取下载链接
    download_links = extract_download_links(html, "https://www.vmware.com")
    result["download_links"] = download_links

    if download_links:
        print(f"  找到 {len(download_links)} 个下载链接")
    else:
        print("  未找到直接下载链接，需要通过 Broadcom 支持门户下载")

    return result


def save_to_json(results: list[dict], output_path: Path) -> None:
    """保存结果到 JSON 文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "collected_at": datetime.utcnow().isoformat(),
                "products": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"已保存 JSON 到 {output_path}")


def generate_readme(results: list[dict], readme_path: Path) -> None:
    """生成 README.md"""
    lines = [
        "# VMware 下载链接",
        "",
        f"自动收集的 VMware 下载链接。最后更新: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## 产品列表",
        "",
    ]

    for result in results:
        lines.append(f"### {result['product']}")
        lines.append("")
        lines.append(f"- **平台**: {', '.join(result['platforms'])}")
        lines.append(f"- **说明**: {result['description']}")

        if result.get("version"):
            lines.append(f"- **最新版本**: {result['version']}")

        lines.append(f"- **产品页面**: [{result['product']}]({result['product_url']})")

        if result.get("broadcom_downloads"):
            lines.append(f"- **Broadcom 下载**: [下载页面]({result['broadcom_downloads']})")

        if result.get("kb_article"):
            lines.append(f"- **安装指南**: [KB 文章]({result['kb_article']})")

        # 列出找到的下载链接
        if result.get("download_links"):
            lines.append("- **直接下载链接**:")
            for link in result["download_links"][:3]:  # 最多显示 3 个
                lines.append(f"  - [{link['url']}]({link['url']})")

        lines.append(f"- **状态**: {result['status']}")
        lines.append("")

    lines.extend(
        [
            "## 如何下载",
            "",
            "VMware 产品现在由 Broadcom 管理。下载步骤：",
            "",
            "1. 访问 [Broadcom 支持门户](https://support.broadcom.com)",
            "2. 注册/登录免费账号",
            "3. 导航到 VMware 产品下载页面",
            "4. 选择产品版本和平台",
            "5. 同意条款后下载",
            "",
            "> **提示**: 自 2024 年 5 月起，VMware Workstation Pro 和 Fusion Pro 对个人使用免费。",
            "",
            "## 本地运行",
            "",
            "```bash",
            "# 安装依赖",
            "uv pip install -r requirements.txt",
            "",
            "# 安装 Playwright 浏览器",
            "python -m playwright install chromium",
            "",
            "# 运行收集脚本",
            "python scripts/collect_vmware_links.py",
            "```",
            "",
            "## License",
            "",
            "本项目仅供学习用途。VMware 产品受其自身许可条款约束。",
        ]
    )

    readme_path.parent.mkdir(parents=True, exist_ok=True)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"已生成 README 到 {readme_path}")


def main() -> int:
    """主函数"""
    print("VMware 下载链接收集器")
    print("=" * 50)

    # 收集所有产品信息
    results = []
    for product_key in VMWARE_PRODUCTS:
        result = check_vmware_product(product_key)
        results.append(result)

    # 确定输出路径
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    json_path = repo_root / "data" / "vmware_downloads.json"
    readme_path = repo_root / "README.md"

    # 保存结果
    save_to_json(results, json_path)
    generate_readme(results, readme_path)

    # 打印摘要
    print("\n" + "=" * 50)
    print("收集摘要:")
    for result in results:
        status = "[OK]" if result["status"] == "available" else "[FAIL]"
        version = f" v{result['version']}" if result.get("version") else ""
        print(f"  {status} {result['product']}{version}: {result['status']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
