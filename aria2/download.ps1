# VMware 下载脚本（使用 aria2）

# 检查 aria2 是否安装
if (-not (Get-Command aria2c -ErrorAction SilentlyContinue)) {
    Write-Error "错误: 未安装 aria2"
    Write-Host "请先安装 aria2:"
    Write-Host "  scoop install aria2"
    Write-Host "  choco install aria2"
    Write-Host "  winget install aria2"
    exit 1
}

# 下载目录
$DOWNLOAD_DIR = ".\vmware-downloads"
New-Item -ItemType Directory -Force -Path $DOWNLOAD_DIR | Out-Null

# 使用 aria2 下载
Write-Host "开始下载 VMware 产品..."
aria2c --dir="$DOWNLOAD_DIR" --file-allocation=none `
  --connect-timeout=30 --retry-wait=5 --max-tries=3 `
  -i vmware-workstation-pro.aria2

Write-Host "下载完成！"