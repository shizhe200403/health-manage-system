#!/bin/bash

# 本地构建前端并上传到服务器的脚本
# 避免在服务器上进行耗时的 npm install 和 build，直接同步 dist

set -e

echo "🔨 开始在本地构建前端..."

# 进入前端目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

cd "$FRONTEND_DIR"

# 检查 Node.js 版本
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

echo "📦 安装依赖..."
npm ci --no-audit --no-fund

echo "🏗️  构建生产版本..."
npm run build

echo "✅ 本地构建完成!"

# 询问是否上传到服务器
read -p "是否立即上传到服务器? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -z "$SERVER_IP" ]; then
        read -p "请输入服务器IP (默认: 121.41.102.152): " server_ip
        server_ip=${server_ip:-121.41.102.152}
    else
        server_ip=$SERVER_IP
    fi

    echo "📤 上传构建文件到服务器..."

    # 在服务器上创建临时目录
    ssh root@$server_ip "mkdir -p /tmp/frontend-dist"

    # 上传 dist 目录
    scp -r "$FRONTEND_DIR/dist" root@$server_ip:/tmp/frontend-dist/

    echo "🔄 在服务器上部署..."
    ssh root@$server_ip << 'ENDSSH'
cd /root/health-manage-system

# 同步最新 dist 到宿主机目录，供 frontend 容器直接挂载使用
rm -rf frontend/dist
mkdir -p frontend/dist
cp -r /tmp/frontend-dist/dist/. frontend/dist/

# 清理临时文件
rm -rf /tmp/frontend-dist

# 重建并重启 frontend，使挂载生效
docker compose -p health-manage-system --env-file .env.production -f docker-compose.prod.yml up -d --force-recreate frontend

echo "✅ 部署完成!"
ENDSSH

    echo "🎉 前端已成功部署到服务器!"
else
    echo "💡 提示: 构建文件在 frontend/dist/ 目录"
    echo "   你可以手动上传到服务器的 /root/health-manage-system/frontend/dist/ 目录"
fi
