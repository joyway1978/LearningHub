#!/bin/bash

# AI Learning Hub 启动脚本
# 支持启动/停止前后端服务，支持指定端口

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
FRONTEND_PORT=3000
BACKEND_PORT=8000
FRONTEND_DIR="frontend"
BACKEND_DIR="backend"

# PID 文件
PID_DIR=".pids"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
BACKEND_PID_FILE="$PID_DIR/backend.pid"

# 创建 PID 目录
mkdir -p "$PID_DIR"

# 显示帮助信息
show_help() {
    echo -e "${BLUE}AI Learning Hub 启动脚本${NC}"
    echo ""
    echo "用法: ./start.sh [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  start           启动前后端服务（默认）"
    echo "  stop            停止前后端服务"
    echo "  restart         重启前后端服务"
    echo "  status          查看服务状态"
    echo ""
    echo "选项:"
    echo "  -f, --frontend     只操作前端服务"
    echo "  -b, --backend      只操作后端服务"
    echo "  --frontend-port    指定前端端口 (默认: 3000)"
    echo "  --backend-port     指定后端端口 (默认: 8000)"
    echo "  -h, --help         显示帮助信息"
    echo ""
    echo "依赖说明:"
    echo "  启动后端时会自动检查 LibreOffice（用于 Office 文件转换）"
    echo "  如未安装，会提示自动安装"
    echo ""
    echo "示例:"
    echo "  ./start.sh                          # 启动前后端"
    echo "  ./start.sh start -f                 # 只启动前端"
    echo "  ./start.sh start -b                 # 只启动后端"
    echo "  ./start.sh start --frontend-port 3001 --backend-port 8001"
    echo "  ./start.sh stop                     # 停止前后端"
    echo "  ./start.sh stop -f                  # 只停止前端"
    echo "  ./start.sh restart                  # 重启前后端"
    echo "  ./start.sh status                   # 查看服务状态"
}

# 日志输出函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_blue() {
    echo -e "${BLUE}$1${NC}"
}

# LibreOffice Docker 容器名称
LIBREOFFICE_CONTAINER="ai_learning_libreoffice"
LIBREOFFICE_DOCKER_IMAGE="linuxserver/libreoffice:latest"

# 检查 LibreOffice 是否安装
check_libreoffice() {
    # 检查本地安装
    if command -v soffice &> /dev/null; then
        return 0
    elif command -v libreoffice &> /dev/null; then
        return 0
    fi

    return 1
}

# 检查 LibreOffice Docker 容器是否运行
check_libreoffice_docker() {
    if ! command -v docker &> /dev/null; then
        return 1
    fi

    if docker ps -q -f "name=$LIBREOFFICE_CONTAINER" | grep -q .; then
        return 0
    fi

    return 1
}

# 获取操作系统类型
get_os_type() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        Linux*)     echo "linux" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *)          echo "unknown" ;;
    esac
}

# 获取 Linux 发行版
get_linux_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

# 安装 LibreOffice
install_libreoffice() {
    log_blue "=== 安装 LibreOffice ==="
    log_info "LibreOffice 是处理 Office 文件 (PPT、Word、Excel) 的必需依赖"

    local os_type=$(get_os_type)

    case "$os_type" in
        macos)
            log_info "检测到 macOS 系统"
            if command -v brew &> /dev/null; then
                log_info "使用 Homebrew 安装 LibreOffice..."
                log_info "先更新 Homebrew..."
                if ! brew update; then
                    log_warn "Homebrew 更新失败，尝试继续安装..."
                fi
                log_info "安装 LibreOffice 稳定版本..."
                if brew install --cask libreoffice-still; then
                    log_info "LibreOffice 安装成功"
                    # 添加 soffice 到 PATH (如果还没添加)
                    if ! command -v soffice &> /dev/null && [ -d "/Applications/LibreOffice.app/Contents/MacOS" ]; then
                        log_info "请将以下路径添加到 PATH: /Applications/LibreOffice.app/Contents/MacOS"
                        export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"
                    fi
                    return 0
                else
                    log_error "Homebrew 安装失败"
                    return 1
                fi
            else
                log_warn "未检测到 Homebrew，请访问 https://brew.sh 安装"
                return 1
            fi
            ;;

        linux)
            local distro=$(get_linux_distro)
            log_info "检测到 Linux 发行版: $distro"

            case "$distro" in
                ubuntu|debian)
                    log_info "使用 apt-get 安装 LibreOffice..."
                    if sudo apt-get update && sudo apt-get install -y libreoffice; then
                        log_info "LibreOffice 安装成功"
                        return 0
                    else
                        log_error "apt-get 安装失败"
                        return 1
                    fi
                    ;;

                centos|rhel|fedora|rocky|almalinux)
                    log_info "使用 yum/dnf 安装 LibreOffice..."
                    if command -v dnf &> /dev/null; then
                        if sudo dnf install -y libreoffice; then
                            log_info "LibreOffice 安装成功"
                            return 0
                        fi
                    else
                        if sudo yum install -y libreoffice; then
                            log_info "LibreOffice 安装成功"
                            return 0
                        fi
                    fi
                    log_error "yum/dnf 安装失败"
                    return 1
                    ;;

                arch|manjaro)
                    log_info "使用 pacman 安装 LibreOffice..."
                    if sudo pacman -S --noconfirm libreoffice-still; then
                        log_info "LibreOffice 安装成功"
                        return 0
                    else
                        log_error "pacman 安装失败"
                        return 1
                    fi
                    ;;

                *)
                    log_warn "未识别的 Linux 发行版: $distro"
                    return 1
                    ;;
            esac
            ;;

        windows)
            log_warn "Windows 系统请手动安装 LibreOffice"
            log_info "下载地址: https://www.libreoffice.org/download/download/"
            return 1
            ;;

        *)
            log_warn "未识别的操作系统: $(uname -s)"
            return 1
            ;;
    esac
}

# 检查并安装 LibreOffice
check_and_install_libreoffice() {
    log_blue "=== 检查 LibreOffice ==="

    if check_libreoffice; then
        log_info "LibreOffice 已就绪"
        if command -v soffice &> /dev/null; then
            log_info "本地 soffice 路径: $(which soffice)"
        elif command -v libreoffice &> /dev/null; then
            log_info "本地 libreoffice 路径: $(which libreoffice)"
        fi
        return 0
    fi

    log_warn "LibreOffice 未安装"
    log_info "LibreOffice 是 Office 文件上传功能的必需依赖"
    echo ""

    # 尝试本地安装
    log_blue "是否自动安装 LibreOffice 到本地系统? (Y/n)"
    read -r response

    if [[ -z "$response" || "$response" =~ ^[Yy]$ ]]; then
        if install_libreoffice; then
            return 0
        else
            echo ""
            log_error "自动安装失败，请手动安装"
            show_libreoffice_install_guide
            return 1
        fi
    else
        log_warn "跳过 LibreOffice 安装"
        show_libreoffice_install_guide
        return 1
    fi
}

# 启动 LibreOffice Docker 容器
start_libreoffice_docker() {
    log_blue "=== 启动 LibreOffice Docker 容器 ==="

    if ! command -v docker &> /dev/null; then
        log_error "未安装 Docker，无法使用 Docker 模式"
        return 1
    fi

    # 检查容器是否已存在
    if docker ps -a -q -f "name=$LIBREOFFICE_CONTAINER" | grep -q .; then
        log_info "LibreOffice 容器已存在，正在启动..."
        if docker start "$LIBREOFFICE_CONTAINER"; then
            log_info "LibreOffice Docker 容器启动成功"
            return 0
        else
            log_error "启动现有容器失败"
            return 1
        fi
    else
        log_info "创建并启动 LibreOffice Docker 容器..."
        if docker run -d \
            --name "$LIBREOFFICE_CONTAINER" \
            --restart unless-stopped \
            -v /tmp/libreoffice-convert:/tmp/libreoffice-convert \
            "$LIBREOFFICE_DOCKER_IMAGE" \
            tail -f /dev/null; then
            log_info "LibreOffice Docker 容器启动成功"
            return 0
        else
            log_error "创建容器失败"
            return 1
        fi
    fi
}

# 停止 LibreOffice Docker 容器
stop_libreoffice_docker() {
    if check_libreoffice_docker; then
        log_info "停止 LibreOffice Docker 容器..."
        docker stop "$LIBREOFFICE_CONTAINER" >/dev/null 2>&1 || true
        log_info "LibreOffice Docker 容器已停止"
    fi
}

# 显示 LibreOffice 安装指导
show_libreoffice_install_guide() {
    echo ""
    log_blue "=== LibreOffice 安装指导 ==="
    echo ""
    echo "LibreOffice 是 Office 文件 (PPT、Word、Excel) 上传功能的必需依赖"
    echo ""
    echo "安装方式:"
    echo ""
    echo "本地安装:"
    local os_type=$(get_os_type)
    case "$os_type" in
        macos)
            echo "   # 使用 Homebrew (推荐):"
            echo "   brew update"
            echo "   brew install --cask libreoffice-still"
            echo ""
            echo "   # 或者从官网下载安装包:"
            echo "   https://www.libreoffice.org/download/download/"
            ;;
        linux)
            local distro=$(get_linux_distro)
            case "$distro" in
                ubuntu|debian)
                    echo "   sudo apt-get update"
                    echo "   sudo apt-get install libreoffice"
                    ;;
                centos|rhel|fedora)
                    echo "   sudo yum install libreoffice"
                    echo "   # 或使用 dnf:"
                    echo "   sudo dnf install libreoffice"
                    ;;
                arch|manjaro)
                    echo "   sudo pacman -S libreoffice-still"
                    ;;
                *)
                    echo "   请参考您的发行版文档安装 LibreOffice"
                    ;;
            esac
            ;;
        windows)
            echo "   请从官网下载安装程序:"
            echo "   https://www.libreoffice.org/download/download/"
            ;;
        *)
            echo "   请访问 https://www.libreoffice.org/download/download/"
            ;;
    esac
    echo ""
    log_info "安装完成后，请重新运行启动脚本"
    echo ""
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 查找进程 ID
find_pid() {
    local port=$1
    lsof -Pi :"$port" -sTCP:LISTEN -t 2>/dev/null || echo ""
}

# 保存 PID
save_pid() {
    local pid=$1
    local file=$2
    echo "$pid" > "$file"
}

# 读取 PID
read_pid() {
    local file=$1
    if [ -f "$file" ]; then
        cat "$file"
    else
        echo ""
    fi
}

# 检查进程是否运行
is_running() {
    local pid=$1
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# 启动后端服务
start_backend() {
    log_blue "=== 启动后端服务 ==="

    # 检查后端端口
    if check_port "$BACKEND_PORT"; then
        local existing_pid=$(find_pid "$BACKEND_PORT")
        log_warn "后端端口 $BACKEND_PORT 已被占用 (PID: $existing_pid)"
        log_warn "请先停止现有服务或使用其他端口"
        return 1
    fi

    # 检查 LibreOffice
    check_and_install_libreoffice || true

    # 进入后端目录
    cd "$BACKEND_DIR"

    log_info "启动 FastAPI 服务..."
    log_info "端口: $BACKEND_PORT"
    log_info "地址: http://localhost:$BACKEND_PORT"

    # 启动后端（后台运行）
    nohup python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "$BACKEND_PORT" \
        --reload \
        > "../$PID_DIR/backend.log" 2>&1 &

    local backend_pid=$!
    cd ..

    # 保存 PID
    save_pid "$backend_pid" "$BACKEND_PID_FILE"

    # 等待服务启动
    local retries=0
    local max_retries=30
    while ! check_port "$BACKEND_PORT"; do
        if [ $retries -ge $max_retries ]; then
            log_error "后端服务启动超时"
            return 1
        fi
        sleep 1
        ((retries++))
    done

    log_info "后端服务已启动 (PID: $backend_pid)"
    return 0
}

# 启动前端服务
start_frontend() {
    log_blue "=== 启动前端服务 ==="

    # 检查前端端口
    if check_port "$FRONTEND_PORT"; then
        local existing_pid=$(find_pid "$FRONTEND_PORT")
        log_warn "前端端口 $FRONTEND_PORT 已被占用 (PID: $existing_pid)"
        log_warn "请先停止现有服务或使用其他端口"
        return 1
    fi

    # 进入前端目录
    cd "$FRONTEND_DIR"

    log_info "启动 Next.js 服务..."
    log_info "端口: $FRONTEND_PORT"
    log_info "地址: http://localhost:$FRONTEND_PORT"

    # 设置前端端口
    export PORT="$FRONTEND_PORT"

    # 启动前端（后台运行）
    nohup npm run dev \
        > "../$PID_DIR/frontend.log" 2>&1 &

    local frontend_pid=$!
    cd ..

    # 保存 PID
    save_pid "$frontend_pid" "$FRONTEND_PID_FILE"

    # 等待服务启动
    local retries=0
    local max_retries=30
    while ! check_port "$FRONTEND_PORT"; do
        if [ $retries -ge $max_retries ]; then
            log_error "前端服务启动超时"
            return 1
        fi
        sleep 1
        ((retries++))
    done

    log_info "前端服务已启动 (PID: $frontend_pid)"
    return 0
}

# 停止后端服务
stop_backend() {
    log_blue "=== 停止后端服务 ==="

    local pid=$(read_pid "$BACKEND_PID_FILE")
    local stopped=false

    # 尝试通过 PID 停止
    if [ -n "$pid" ] && is_running "$pid"; then
        log_info "正在停止后端服务 (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 2
        if is_running "$pid"; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        stopped=true
    fi

    # 尝试通过端口查找并停止
    local port_pid=$(find_pid "$BACKEND_PORT")
    if [ -n "$port_pid" ]; then
        log_info "正在停止端口 $BACKEND_PORT 的进程 (PID: $port_pid)..."
        kill "$port_pid" 2>/dev/null || true
        sleep 1
        if kill -0 "$port_pid" 2>/dev/null; then
            kill -9 "$port_pid" 2>/dev/null || true
        fi
        stopped=true
    fi

    if [ "$stopped" = true ]; then
        log_info "后端服务已停止"
    else
        log_warn "后端服务未运行"
    fi

    # 清除 PID 文件
    rm -f "$BACKEND_PID_FILE"
}

# 停止前端服务
stop_frontend() {
    log_blue "=== 停止前端服务 ==="

    local pid=$(read_pid "$FRONTEND_PID_FILE")
    local stopped=false

    # 尝试通过 PID 停止
    if [ -n "$pid" ] && is_running "$pid"; then
        log_info "正在停止前端服务 (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 2
        if is_running "$pid"; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        stopped=true
    fi

    # 尝试通过端口查找并停止
    local port_pid=$(find_pid "$FRONTEND_PORT")
    if [ -n "$port_pid" ]; then
        log_info "正在停止端口 $FRONTEND_PORT 的进程 (PID: $port_pid)..."
        kill "$port_pid" 2>/dev/null || true
        sleep 1
        if kill -0 "$port_pid" 2>/dev/null; then
            kill -9 "$port_pid" 2>/dev/null || true
        fi
        stopped=true
    fi

    if [ "$stopped" = true ]; then
        log_info "前端服务已停止"
    else
        log_warn "前端服务未运行"
    fi

    # 清除 PID 文件
    rm -f "$FRONTEND_PID_FILE"
}

# 显示服务状态
show_status() {
    log_blue "=== 服务状态 ==="

    # 检查后端
    local backend_pid=$(read_pid "$BACKEND_PID_FILE")
    local backend_port_pid=$(find_pid "$BACKEND_PORT")
    if [ -n "$backend_port_pid" ]; then
        log_info "后端服务: ${GREEN}运行中${NC} (PID: $backend_port_pid, 端口: $BACKEND_PORT)"
    else
        log_warn "后端服务: ${RED}未运行${NC}"
    fi

    # 检查前端
    local frontend_pid=$(read_pid "$FRONTEND_PID_FILE")
    local frontend_port_pid=$(find_pid "$FRONTEND_PORT")
    if [ -n "$frontend_port_pid" ]; then
        log_info "前端服务: ${GREEN}运行中${NC} (PID: $frontend_port_pid, 端口: $FRONTEND_PORT)"
    else
        log_warn "前端服务: ${RED}未运行${NC}"
    fi
}

# 主函数
main() {
    local command="start"
    local run_frontend=false
    local run_backend=false

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            start|stop|restart|status)
                command="$1"
                shift
                ;;
            -f|--frontend)
                run_frontend=true
                shift
                ;;
            -b|--backend)
                run_backend=true
                shift
                ;;
            --frontend-port)
                FRONTEND_PORT="$2"
                shift 2
                ;;
            --backend-port)
                BACKEND_PORT="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 如果没有指定特定服务，默认启动/停止所有
    if [ "$run_frontend" = false ] && [ "$run_backend" = false ]; then
        run_frontend=true
        run_backend=true
    fi

    # 执行命令
    case $command in
        start)
            log_blue "================================"
            log_blue "  AI Learning Hub 启动脚本"
            log_blue "================================"
            echo ""

            if [ "$run_backend" = true ]; then
                start_backend
                echo ""
            fi

            if [ "$run_frontend" = true ]; then
                start_frontend
                echo ""
            fi

            log_blue "================================"
            log_info "服务启动完成！"
            echo ""
            log_info "前端地址: http://localhost:$FRONTEND_PORT"
            log_info "后端地址: http://localhost:$BACKEND_PORT"
            log_info "API 文档: http://localhost:$BACKEND_PORT/docs"
            echo ""
            log_info "日志文件:"
            log_info "  - 后端: $PID_DIR/backend.log"
            log_info "  - 前端: $PID_DIR/frontend.log"
            echo ""
            log_info "停止服务: ./start.sh stop"
            log_blue "================================"
            ;;

        stop)
            log_blue "================================"
            log_blue "  停止服务"
            log_blue "================================"
            echo ""

            if [ "$run_frontend" = true ]; then
                stop_frontend
                echo ""
            fi

            if [ "$run_backend" = true ]; then
                stop_backend
                echo ""
            fi

            log_info "服务已停止"
            log_blue "================================"
            ;;

        restart)
            log_blue "================================"
            log_blue "  重启服务"
            log_blue "================================"
            echo ""

            # 先停止
            if [ "$run_frontend" = true ]; then
                stop_frontend
            fi
            if [ "$run_backend" = true ]; then
                stop_backend
            fi

            sleep 2
            echo ""

            # 再启动
            if [ "$run_backend" = true ]; then
                start_backend
                echo ""
            fi
            if [ "$run_frontend" = true ]; then
                start_frontend
                echo ""
            fi

            log_info "服务重启完成！"
            log_blue "================================"
            ;;

        status)
            show_status
            ;;
    esac
}

# 运行主函数
main "$@"
