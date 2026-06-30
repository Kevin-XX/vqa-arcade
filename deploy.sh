#!/usr/bin/env bash
# ============================================================
#  VQA Arcade —— 一键部署脚本
#  本地验证 / 云服务器通用
#  用法:
#    chmod +x deploy.sh
#    ./deploy.sh              # 构建并启动
#    ./deploy.sh stop         # 停止
#    ./deploy.sh logs         # 看日志
#    ./deploy.sh restart      # 重启
#    ./deploy.sh status       # 查状态
# ============================================================
set -e

COMPOSE="docker compose"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

case "${1:-up}" in
  up|build|"")
    echo "🔨 构建镜像并启动..."
    $COMPOSE up -d --build
    echo ""
    echo "⏳ 等待服务就绪..."
    for i in $(seq 1 30); do
      if curl -s -m 2 -o /dev/null http://localhost:5100/api/health 2>/dev/null; then
        echo "✅ 服务已就绪"
        echo "   本地: http://localhost:5100"
        echo "   公网: 绑定域名或用 IP:5100"
        $COMPOSE ps
        exit 0
      fi
      sleep 2
    done
    echo "❌ 30 秒内未就绪, 查日志:"
    $COMPOSE logs --tail 30
    exit 1
    ;;
  stop|down)
    echo "🛑 停止服务..."
    $COMPOSE down
    ;;
  logs)
    $COMPOSE logs -f --tail 50
    ;;
  restart)
    $COMPOSE restart
    echo "✅ 已重启"
    ;;
  status|ps)
    $COMPOSE ps
    ;;
  *)
    echo "用法: $0 {up|stop|logs|restart|status}"
    exit 1
    ;;
esac
