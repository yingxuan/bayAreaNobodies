# API 文档

## 本地开发验证

### 前置条件

- FastAPI 服务运行在 `http://localhost:8000`
- Redis 服务运行（可选，用于缓存）
- 无外部网络或 API key 时会自动返回 mock 数据

### 接口列表

#### 1. GET /market/snapshot

获取统一市场快照（包含 BTC、黄金、房贷利率、彩票信息）

**请求示例：**
```bash
curl http://localhost:8000/market/snapshot
```

**响应格式：**
```json
{
  "updatedAt": "2025-01-15T10:30:00.000000+00:00",
  "dataSource": {
    "btc": "live|mock",
    "gold": "live|mock",
    "mortgage": "live|mock",
    "lottery": "live|mock"
  },
  "stale": false,
  "ttlSeconds": 900,
  "btc": {
    "price": 95000,
    "chgPct24h": 1.5,
    "stale": false,
    "ttlSeconds": 600
  },
  "gold": {
    "price": 2650,
    "chgPct24h": 0.2,
    "stale": false,
    "ttlSeconds": 600
  },
  "mortgage30y": {
    "rate": 6.5,
    "weekDate": "2025-01-15",
    "stale": false,
    "ttlSeconds": 43200
  },
  "lottery": {
    "game": "Powerball",
    "jackpot": 33000000,
    "drawDate": "2025-01-15",
    "stale": false,
    "ttlSeconds": 1800
  }
}
```

**字段说明：**
- `updatedAt`: ISO 8601 格式的时间戳，表示整个快照的更新时间（所有字段共享同一时间点）
- `dataSource`: 每个字段的数据源状态（`live` = 实时数据，`mock` = 模拟/缓存数据）
- `stale`: 布尔值，`true` 表示使用了缓存或占位数据（整体快照级别）
- `ttlSeconds`: 缓存 TTL（秒），整体快照和每个字段都有独立的 TTL
- `chgPct24h`: 24小时变化百分比（仅 BTC 和 Gold）

**缓存策略：**
- 整体快照：15 分钟 TTL
- 字段级缓存（last-known-good）：
  - BTC: 10 分钟
  - Gold: 10 分钟
  - Mortgage: 12 小时
  - Lottery: 30 分钟

**降级策略：**
- 如果外部 API 失败，使用 last-known-good 缓存值（标记为 `stale: true`）
- 如果无缓存，返回占位数据（标记为 `dataSource: "mock"` 和 `stale: true`）

---

#### 2. GET /tech/trending

获取科技圈热门新闻（目前支持 Hacker News）

**请求示例：**
```bash
curl "http://localhost:8000/tech/trending?source=hn&limit=12"
```

**查询参数：**
- `source` (可选，默认: `hn`): 数据源，目前仅支持 `hn` (Hacker News)
- `limit` (可选，默认: `12`): 返回条目数，范围 1-50

**响应格式：**
```json
{
  "source": "hn",
  "updatedAt": "2025-01-15T10:30:00.000000+00:00",
  "dataSource": "live|mock",
  "stale": false,
  "ttlSeconds": 600,
  "items": [
    {
      "id": "hn_12345678",
      "title": "Example Tech News Title",
      "url": "https://example.com/article",
      "score": 123,
      "comments": 45,
      "author": "username",
      "createdAt": "2025-01-15T08:00:00.000000+00:00",
      "tags": ["AI", "BigTech"],
      "summary": null
    }
  ]
}
```

**字段说明：**
- `source`: 数据源标识
- `updatedAt`: ISO 8601 格式的时间戳，表示数据获取时间
- `dataSource`: `live` = 实时数据，`mock` = 模拟数据
- `stale`: 布尔值，`true` 表示使用了缓存或降级数据
- `ttlSeconds`: 缓存 TTL（秒），默认 600 秒（10 分钟）
- `items`: 新闻列表，按 `score` 降序排列（稳定排序）
- `items[].tags`: 标签数组，由后端基于 title/url 关键词自动生成（最多 2-3 个）

**缓存策略：**
- TTL: 10 分钟
- 降级：如果 HN Algolia API 失败，返回 3 条 mock 数据

---

## 环境变量

- `REDIS_URL`: Redis 连接 URL（可选，默认: `redis://localhost:6379/0`）
- `NEXT_PUBLIC_API_URL`: 前端 API 基础 URL（默认: `http://localhost:8000`）

## 注意事项

1. **无外部网络时**：所有接口会自动返回 mock 数据，不会抛出 500 错误
2. **无 API key 时**：相关字段会使用占位数据，标记为 `dataSource: "mock"` 和 `stale: true`
3. **缓存一致性**：同一快照的所有字段共享 `updatedAt` 时间戳，确保一致性
4. **Tech Tags 生成**：tags 由后端基于 title/url 关键词自动生成，规则稳定（deterministic），支持：AI、Chips、BigTech、Career、OpenSource、Security、Infra

## 本地开发步骤

### 启动后端（FastAPI）

```bash
# 使用 Docker Compose（推荐）
docker compose up api

# 或直接运行
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 启动前端（Next.js）

```bash
cd web
npm install
npm run dev
```

前端将在 `http://localhost:3000` 启动，后端在 `http://localhost:8000`。

### 环境变量

创建 `.env` 文件（可选，用于真实数据）：

```bash
# 后端
REDIS_URL=redis://localhost:6379/0
GOOGLE_CSE_API_KEY=your_key_here  # 可选
GOOGLE_CSE_ID=your_id_here  # 可选

# 前端
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**注意**：即使不配置 API keys，应用也会正常运行，只是会使用 mock 数据。

