# 🚀 VQA Arcade 公网部署清单（腾讯云轻量 + Docker）

> 目标：把完整 7 算法 VQA 稳定部署到公网，7×24 可访问，不依赖本地 Mac 开机。

---

## 一、选购服务器

### 推荐配置（够用且不浪费）

| 项目 | 推荐值 | 原因 |
|------|--------|------|
| 产品 | 腾讯云轻量应用服务器 | 性价比高，含流量包，学生有优惠 |
| CPU | 2 核 | torch CPU 推理最低要求 |
| 内存 | **4 GB**（最低）/ 8 GB（推荐） | torch + opencv + 4 个模型加载约用 2.5GB，4G 够跑但紧张 |
| 系统盘 | 60 GB SSD | 镜像约 2.5GB + 模型 354MB + 上传文件，60G 富余 |
| 系统 | **Ubuntu 22.04 LTS** | Docker 兼容性最好 |
| 价格 | 约 ¥24-90/月（看配置/地域） | 学生认证有额外优惠 |
| 地域 | 广州/上海/北京任选 | 国内访问快 |

**⚠️ 别选 2GB 内存**：torch 加载模型后会 OOM（内存溢出），VSFA/VMAF 会直接崩。

### 选购地址
- 腾讯云轻量：https://console.cloud.tencent.com/lighthouse
- 学生优惠：https://cloud.tencent.com/act/campus

---

## 二、首次配置服务器（约 10 分钟）

买完后会拿到 **公网 IP**（如 `43.136.xxx.xxx`）和 root 密码。SSH 登录：

```bash
ssh root@<你的公网IP>
```

### 1. 装 Docker

```bash
# 一键装 Docker + docker-compose 插件
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

# 启动并设开机自启
systemctl enable --now docker

# 验证
docker --version
docker compose version
```

### 2. 配置防火墙（开放 5100 端口）

腾讯云控制台 → 轻量服务器 → 防火墙 → 添加规则：
- 协议：TCP
- 端口：5100
- 来源：0.0.0.0/0（所有人可访问）

或命令行：
```bash
# 服务器内（如 ufw）
ufw allow 5100/tcp
```

---

## 三、部署项目（约 5 分钟，不含构建时间）

### 方式 A：从 GitHub 拉取（推荐，代码最新）

```bash
# 装个 git（Ubuntu 22.04 一般自带）
apt update && apt install -y git

# 克隆项目
git clone https://github.com/Kevin-XX/vqa-arcade.git
cd vqa-arcade
```

### ⚠️ 关键：模型文件不在 git 里（.gitignore 排除了）

模型文件 354MB，需要单独上传。**两个办法二选一**：

**办法 1（推荐）：本地 scp 上传**
```bash
# 在你的 Mac 本地执行
cd /Users/kevin/Documents/视觉质量评估
scp -r vqa/algos/*.pth root@<服务器IP>:/root/vqa-arcade/vqa/algos/
```

**办法 2：用云盘/对象存储中转**（如果 scp 太慢）
- 把模型传到腾讯云 COS
- 服务器 `wget` 下载

### 3. 启动！

```bash
cd /root/vqa-arcade
./deploy.sh
# 或手动: docker compose up -d --build
```

首次构建约 5-10 分钟（装 torch 慢），后续重启秒级。

### 4. 验证

```bash
# 服务器内
curl http://localhost:5100/api/health

# 应返回: {"status":"ok","algorithms":["PSNR","SSIM","VMAF",...]}
```

公网访问：`http://<服务器公网IP>:5100`

---

## 四、（可选）绑定域名 + HTTPS

如果想要 `vqa.你的域名.com` 而非裸 IP：

### 1. 买域名 + 备案
- 国内服务器要域名访问需备案（腾讯云控制台有备案入口，约 7 工作日）
- 急用可先裸 IP 访问，备案下来再绑域名

### 2. DNS 解析
域名解析加一条 A 记录：`vqa → 服务器公网IP`

### 3. Nginx 反代 + Let's Encrypt HTTPS

```bash
apt install -y nginx certbot python3-certbot-nginx

# 配置反代
cat > /etc/nginx/sites-available/vqa <<'EOF'
server {
    listen 80;
    server_name vqa.你的域名.com;
    client_max_body_size 200M;        # 允许大文件上传
    proxy_read_timeout 300s;          # 算法长超时(5分钟)
    proxy_send_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:5100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # 流式响应支持
        proxy_buffering off;
        proxy_cache off;
    }
}
EOF

ln -s /etc/nginx/sites-available/vqa /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 申请 HTTPS 证书(自动续期)
certbot --nginx -d vqa.你的域名.com
```

---

## 五、日常运维命令

```bash
cd /root/vqa-arcade

./deploy.sh status      # 查状态
./deploy.sh logs        # 实时日志
./deploy.sh restart     # 重启
./deploy.sh stop       # 停止

# 更新代码
git pull && ./deploy.sh restart

# 查资源占用
docker stats vqa-arcade
```

---

## 六、成本与稳定性总结

| 项 | 数值 |
|----|------|
| 一次性 | 域名约 ¥10-70/年（可选） |
| 月费 | 服务器 ¥24-90/月（看配置） |
| 稳定性 | ⭐⭐⭐⭐⭐（7×24，重启自动恢复） |
| 完整功能 | ✅ 7 算法全可用 |
| 答辩当天 | 100% 可靠，不依赖任何本地设备 |

---

## 七、故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| `docker compose` 命令不存在 | 旧版 Docker | 用 `docker-compose`（带横杠）或升级 |
| 容器启动后立刻退出 | 模型文件没挂载进去 | 检查 `vqa/algos/*.pth` 是否存在 |
| `/api/health` 返回 degraded | torch 没装好 | `docker compose logs` 看错误 |
| 公网访问超时 | 防火墙没开 5100 | 腾讯云控制台加防火墙规则 |
| VSFA 报 OOM | 内存不够 | 升级到 8GB 内存配置 |
| 上传大文件失败 | Nginx body 限制 | 检查 `client_max_body_size` |
