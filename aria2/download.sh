#!/bin/bash
# VMware 下载脚本（使用 aria2）

# 检查 aria2 是否安装
if ! command -v aria2c &> /dev/null; then
    echo "错误: 未安装 aria2"
    echo "请先安装 aria2:"
    echo "  macOS: brew install aria2"
    echo "  Ubuntu/Debian: sudo apt install aria2"
    echo "  Windows: scoop install aria2 或 choco install aria2"
    exit 1
fi

# 下载目录
DOWNLOAD_DIR="./vmware-downloads"
mkdir -p "$DOWNLOAD_DIR"

# 使用 aria2 下载
echo "开始下载 VMware 产品..."
aria2c --dir="$DOWNLOAD_DIR" --file-allocation=none \
  --connect-timeout=30 --retry-wait=5 --max-tries=3 \
  -i vmware-workstation-pro.aria2

echo "下载完成！"