# 生产环境部署指南

本文档详细说明如何将 AI Learning Platform 部署到生产环境。

## 目录

- [环境准备](#环境准备)
- [安全注意事项](#安全注意事项)
- [部署步骤](#部署步骤)
- [SSL证书配置](#ssl证书配置)
- [备份策略](#备份策略)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)

## 环境准备

### 系统要求

- **操作系统**: Ubuntu 22.04 LTS 或 CentOS 8+
- **CPU**: 至少 2 核
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 50GB 可用空间
- **网络**: 公网IP，开放端口 80, 443, 3000, 8000

### 软件要求

- Docker >= 20.10
- Docker Compose >= 2.0
- Nginx (用于反向代理和SSL)
- Git

### 安装Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 安全注意事项

### 1. 修改默认密码

**生产环境必须修改以下默认值：**

```bash
# .env 文件
MYSQL_ROOT_PASSWORD=your-secure-root-password-here
MYSQL_PASSWORD=your-secure-db-password-here
MINIO_ROOT_PASSWORD=your-secure-minio-password-here
SECRET_KEY=your-very-long-and-secure-jwt-secret-key-at-least-32-characters
```

### 2. 生成强密码

```bash
# 生成32位随机密码
openssl rand -base64 32

# 生成64位JWT密钥
openssl rand -base64 64
```

### 3. 禁用调试模式

```bash
# .env 文件
DEBUG=false
ENVIRONMENT=production
```

### 4. 配置允许的跨域来源

```bash
# .env 文件 - 只允许你的域名
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## 部署步骤

### 1. 克隆代码

```bash
cd /opt
git clone <your-repository-url> ai-learning-platform
cd ai-learning-platform
```

### 2. 配置环境变量

```bash
cp .env.example .env
nano .env
```

生产环境配置示例：

```env
# MySQL Configuration
MYSQL_ROOT_PASSWORD=your-secure-root-password
MYSQL_DATABASE=ai_learning
MYSQL_USER=app_user
MYSQL_PASSWORD=your-secure-db-password

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your-secure-minio-password
MINIO_BUCKET_NAME=materials

# Backend Configuration
SECRET_KEY=your-very-long-jwt-secret-key-min-32-chars-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=https://yourdomain.com

# Frontend Configuration
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
API_URL=http://backend:8000

# Environment
DEBUG=false
ENVIRONMENT=production
```

### 3. 启动服务

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 检查状态
docker-compose ps
```

### 4. 配置Nginx反向代理

安装Nginx：

```bash
sudo apt update
sudo apt install nginx
```

创建配置文件 `/etc/nginx/sites-available/ai-learning`：

```nginx
# HTTP -> HTTPS 重定向
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# 前端服务
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# API服务
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 文件上传大小限制
        client_max_body_size 500M;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/ai-learning /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL证书配置

### 使用 Let's Encrypt (推荐)

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# 自动续期测试
sudo certbot renew --dry-run
```

### 手动配置SSL证书

如果你有商业SSL证书：

```bash
# 上传证书文件到服务器
sudo mkdir -p /etc/nginx/ssl
sudo cp your_certificate.crt /etc/nginx/ssl/
sudo cp your_private.key /etc/nginx/ssl/
sudo chmod 600 /etc/nginx/ssl/*

# 更新Nginx配置中的证书路径
# 然后重启Nginx
sudo systemctl restart nginx
```

## 备份策略

### 1. 数据库备份

创建备份脚本 `/opt/ai-learning-platform/scripts/backup-db.sh`：

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="ai_learning"
DB_USER="root"
DB_PASS="your-root-password"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
docker exec ai_learning_mysql mysqldump -u$DB_USER -p$DB_PASS $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# 保留最近30天的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

设置定时任务：

```bash
chmod +x /opt/ai-learning-platform/scripts/backup-db.sh

# 编辑crontab
crontab -e

# 添加每日凌晨2点备份
0 2 * * * /opt/ai-learning-platform/scripts/backup-db.sh >> /var/log/db-backup.log 2>&1
```

### 2. MinIO数据备份

创建备份脚本 `/opt/ai-learning-platform/scripts/backup-minio.sh`：

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/minio"
DATE=$(date +%Y%m%d_%H%M%S)
MINIO_DATA="/var/lib/docker/volumes/ai-learning-platform_minio_data/_data"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份MinIO数据
tar czf $BACKUP_DIR/minio_backup_$DATE.tar.gz -C $MINIO_DATA .

# 保留最近30天的备份
find $BACKUP_DIR -name "minio_backup_*.tar.gz" -mtime +30 -delete

echo "MinIO backup completed: minio_backup_$DATE.tar.gz"
```

### 3. 完整系统备份

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/full"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/opt/ai-learning-platform"

mkdir -p $BACKUP_DIR

# 备份项目代码和配置
tar czf $BACKUP_DIR/full_backup_$DATE.tar.gz \
    -C $PROJECT_DIR \
    --exclude='*/node_modules' \
    --exclude='*/__pycache__' \
    --exclude='*/.git' \
    .

# 保留最近7天的完整备份
find $BACKUP_DIR -name "full_backup_*.tar.gz" -mtime +7 -delete

echo "Full backup completed: full_backup_$DATE.tar.gz"
```

### 4. 备份恢复

```bash
# 恢复数据库
gunzip < backup_20240101_120000.sql.gz | docker exec -i ai_learning_mysql mysql -uroot -p ai_learning

# 恢复MinIO数据
docker-compose down
tar xzf minio_backup_20240101_120000.tar.gz -C /var/lib/docker/volumes/ai-learning-platform_minio_data/_data
docker-compose up -d
```

## 监控和日志

### 1. 查看服务日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
```

### 2. 设置日志轮转

Docker日志配置已在 `docker-compose.yml` 中设置：

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 3. 系统监控

安装监控工具：

```bash
# 安装 htop 和 iotop
sudo apt install htop iotop

# 查看容器资源使用
docker stats
```

### 4. 健康检查

```bash
# 后端健康检查
curl https://api.yourdomain.com/health

# 数据库健康检查
curl https://api.yourdomain.com/api/v1/health/db
```

## 故障排除

### 服务无法启动

```bash
# 查看详细日志
docker-compose logs --tail=100 backend

# 检查端口占用
sudo netstat -tlnp | grep -E '3000|8000|3306|9000'

# 重启服务
docker-compose restart
```

### 数据库连接问题

```bash
# 检查MySQL状态
docker-compose ps mysql
docker-compose logs mysql

# 进入MySQL容器
docker-compose exec mysql mysql -uroot -p

# 检查用户权限
SHOW GRANTS FOR 'app_user'@'%';
```

### 文件上传失败

```bash
# 检查MinIO状态
docker-compose ps minio
docker-compose logs minio

# 检查存储桶
docker-compose exec backend python -c "from app.core.storage import minio_client; print(minio_client.bucket_exists())"
```

### 性能优化

1. **MySQL优化**

创建 `mysql/my.cnf`：

```ini
[mysqld]
innodb_buffer_pool_size = 1G
max_connections = 200
query_cache_size = 64M
```

2. **Nginx优化**

```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 4096;
client_body_buffer_size 128k;
client_max_body_size 500M;
```

## 更新部署

```bash
cd /opt/ai-learning-platform

# 拉取最新代码
git pull origin main

# 重新构建
docker-compose build

# 无停机更新
docker-compose up -d

# 检查状态
docker-compose ps
```

## 安全加固

### 1. 防火墙配置

```bash
# 允许必要端口
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. 禁用root登录

```bash
# 编辑 SSH 配置
sudo nano /etc/ssh/sshd_config

# 设置
PermitRootLogin no
PasswordAuthentication no

# 重启 SSH
sudo systemctl restart sshd
```

### 3. 定期安全更新

```bash
# 设置自动更新
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

---

**注意**: 部署完成后，请立即测试所有功能，确保系统正常运行。
