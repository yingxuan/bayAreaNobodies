# 开发环境指南

## 问题：为什么每次都要重新部署才能看到 UI 更新？

**原因**：你在使用**生产环境**（`docker-compose.prod.yml`），它：
- 构建静态文件（`npm run build`）
- 运行生产服务器（`node server.js`）
- **没有代码热重载**
- 代码更改需要重新构建镜像

## 解决方案：使用开发环境

### 方案 1：Docker 开发环境（推荐）

使用 `docker-compose.yml`（开发配置），它支持**热重载**：

```bash
# 停止生产环境
docker compose -f docker-compose.prod.yml down

# 启动开发环境
docker compose up --build

# 或者后台运行
docker compose up -d --build
```

**开发环境特点**：
- ✅ 自动热重载（保存文件后立即看到更新）
- ✅ 支持 Fast Refresh（React 组件状态保持）
- ✅ 代码挂载到容器（`./web:/app`）
- ✅ 开发模式错误提示更详细

**访问**：
- 前端：http://localhost:3000
- API：http://localhost:8000/docs

### 方案 2：本地开发（不通过 Docker）

如果你想在本地直接运行前端（更快，但需要本地 Node.js）：

```bash
cd web

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
```

**注意**：需要确保后端 API 在运行（Docker 或本地）。

### 方案 3：混合模式（前端本地 + 后端 Docker）

```bash
# 1. 只启动后端服务（Docker）
docker compose up postgres redis api

# 2. 在另一个终端，本地运行前端
cd web
npm install
npm run dev
```

## 开发工作流

### 日常开发

1. **启动开发环境**：
   ```bash
   docker compose up
   ```

2. **修改代码**：
   - 编辑 `web/app/**/*.tsx` 文件
   - 保存后，浏览器**自动刷新**（无需重启）

3. **查看日志**：
   ```bash
   docker compose logs -f web
   ```

### 部署到生产

开发完成后，使用生产环境：

```bash
# 停止开发环境
docker compose down

# 启动生产环境
docker compose -f docker-compose.prod.yml up -d --build
```

## 常见问题

### Q: 修改后没有自动刷新？

**检查**：
1. 确认使用的是 `docker-compose.yml`（不是 `.prod.yml`）
2. 检查容器日志：`docker compose logs web`
3. 确认文件已保存
4. 尝试硬刷新浏览器（Ctrl+Shift+R 或 Cmd+Shift+R）

### Q: 开发环境启动慢？

**优化**：
- 使用本地开发（方案 2），跳过 Docker 构建
- 或者只启动需要的服务：`docker compose up web api`

### Q: 端口被占用？

**解决**：
```bash
# 检查端口占用
netstat -ano | findstr :3000  # Windows
lsof -i :3000                 # Mac/Linux

# 修改 docker-compose.yml 中的端口映射
ports:
  - "3001:3000"  # 改为 3001
```

## 开发环境 vs 生产环境对比

| 特性 | 开发环境 (`docker-compose.yml`) | 生产环境 (`docker-compose.prod.yml`) |
|------|--------------------------------|--------------------------------------|
| 热重载 | ✅ 支持 | ❌ 不支持 |
| 构建时间 | 快（无需构建） | 慢（需要构建） |
| 错误提示 | 详细 | 精简 |
| 性能 | 较慢 | 优化 |
| 代码挂载 | ✅ 是 | ❌ 否 |
| 适用场景 | 开发调试 | 生产部署 |

## 推荐配置

**开发时**：使用 `docker-compose.yml`
**部署时**：使用 `docker-compose.prod.yml`

这样可以：
- 开发时享受热重载，快速迭代
- 部署时使用优化后的生产构建

