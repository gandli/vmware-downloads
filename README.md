# VMware Download Links

自动收集 VMware Workstation 和 Fusion 下载链接。

> 通过 GitHub Actions 每日自动更新

## 产品列表

| 产品 | 平台 | 下载链接 |
|------|------|----------|
| VMware Workstation Pro | Windows/Linux | [下载](https://www.vmware.com/go/getworkstation-pro) |
| VMware Workstation Player | Windows/Linux | [下载](https://www.vmware.com/go/getworkstation-player) |
| VMware Fusion Pro | macOS | [下载](https://www.vmware.com/go/getfusion-pro) |
| VMware Fusion Player | macOS | [下载](https://www.vmware.com/go/getfusion-player) |

## 说明

- VMware 下载需要 Broadcom 账号（免费注册）
- 下载链接会跳转到 VMware Customer Connect 门户
- 本仓库通过 GitHub Actions 自动更新

## 本地运行

```bash
# 使用 uv 安装依赖
uv pip install -r requirements.txt

# 运行收集脚本
python scripts/collect_vmware_links.py
```

## License

本项目仅供学习用途。VMware 产品受其自身许可条款约束。
