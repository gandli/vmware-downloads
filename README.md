# VMware 下载链接

自动收集的 VMware 下载链接。最后更新: 2026-05-30 01:41 UTC

## 产品列表

### VMware Workstation Pro

- **平台**: Windows, Linux
- **说明**: 行业标准的桌面虚拟化软件
- **最新版本**: 17.5.2
- **产品页面**: [VMware Workstation Pro](https://www.vmware.com/info/workstation-pro/evaluation)
- **Broadcom 下载**: [下载页面](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro)
- **安装指南**: [KB 文章](https://knowledge.broadcom.com/external/article/368667/download-and-license-vmware-desktop-hype.html)
- **直接下载链接**:
  - [https://support.broadcom.com/](https://support.broadcom.com/)
- **状态**: available

### VMware Fusion Pro

- **平台**: macOS
- **说明**: macOS 上的专业虚拟化软件
- **最新版本**: 13.5.2
- **产品页面**: [VMware Fusion Pro](https://knowledge.broadcom.com/external/article/315638/download-and-install-vmware-fusion.html)
- **Broadcom 下载**: [下载页面](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion%20Pro)
- **安装指南**: [KB 文章](https://knowledge.broadcom.com/external/article/315638/download-and-install-vmware-fusion.html)
- **直接下载链接**:
  - [https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion)
  - [https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro)
  - [https://knowledge.broadcom.com/external/article/315638/download-and-install-vmware-fusion.html](https://knowledge.broadcom.com/external/article/315638/download-and-install-vmware-fusion.html)
- **状态**: available

## 如何下载

VMware 产品现在由 Broadcom 管理。下载步骤：

1. 访问 [Broadcom 支持门户](https://support.broadcom.com)
2. 注册/登录免费账号
3. 导航到 VMware 产品下载页面
4. 选择产品版本和平台
5. 同意条款后下载

> **提示**: 自 2024 年 5 月起，VMware Workstation Pro 和 Fusion Pro 对个人使用免费。

## 本地运行

```bash
# 安装依赖
uv pip install -r requirements.txt

# 安装 Playwright 浏览器
python -m playwright install chromium

# 运行收集脚本
python scripts/collect_vmware_links.py
```

## License

本项目仅供学习用途。VMware 产品受其自身许可条款约束。