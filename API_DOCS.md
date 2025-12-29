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
    "price": 2650.1,
    "chgPct24h": 0.2,
    "sourceUrl": "https://finnhub.io",
    "stale": false,
    "ttlSeconds": 600
  },
  "sp500": {
    "price": 5234.56,
    "chgPct24h": 0.15,
    "stale": false,
    "ttlSeconds": 300
  },
  "mortgage30y": {
    "rate": 6.5,
    "weekDate": "2025-01-15",
    "stale": false,
    "ttlSeconds": 43200
  },
  "lottery": {
    "game": "Powerball",
    "jackpot": 1080000000,
    "drawDate": "2026-01-06",
    "sourceUrl": "https://powerball.com",
    "stale": false,
    "ttlSeconds": 1800
  }
}
```

**字段说明：**
- `updatedAt`: ISO 8601 格式的时间戳，表示整个快照的更新时间（所有字段共享同一时间点）
- `dataSource`: 每个字段的数据源状态（`live` = 实时数据，`google_cse` = Google CSE 抓取，`mock` = 模拟/缓存数据）
- `stale`: 布尔值，`true` 表示使用了缓存或占位数据（整体快照级别）
- `ttlSeconds`: 缓存 TTL（秒），整体快照和每个字段都有独立的 TTL
- `chgPct24h`: 24小时变化百分比（仅 BTC、Gold、S&P 500）
- `sourceUrl`: 数据来源 URL（Gold 和 Lottery 字段）
- `drawDate`: 下次开奖日期（YYYY-MM-DD 格式，仅 Lottery 字段）

**缓存策略：**
- 整体快照：15 分钟 TTL
- 字段级缓存（last-known-good）：
  - S&P 500: 5 分钟
  - BTC: 10 分钟
  - Gold: 10 分钟
  - Mortgage: 12 小时
  - Lottery: 30 分钟

**数据源优先级：**
- **Gold**: Finnhub API → yfinance → Google CSE → last-known-good → mock
- **Powerball**: Google CSE（多查询策略，信任域名加权）→ last-known-good → mock
- **BTC**: Finnhub API → yfinance → crypto_service → last-known-good → mock
- **S&P 500**: yfinance (^GSPC) → Finnhub (SPY) → last-known-good → mock

**降级策略：**
- 如果外部 API 失败，使用 last-known-good 缓存值（标记为 `stale: true`）
- 如果无缓存，返回占位数据（标记为 `dataSource: "mock"` 和 `stale: true`）
- 所有异常不会抛出 500 错误，而是返回 mock/placeholder 数据
- 使用 Redis 锁（30秒）防止缓存击穿

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

#### 3. GET /risk/today

获取今日风险提醒（湾区码农今天应该注意什么）

**请求示例：**
```bash
curl "http://localhost:8000/risk/today?city=cupertino"
```

**查询参数：**
- `city` (可选，默认: `cupertino`): 城市名称，支持：`cupertino`, `sunnyvale`, `san-jose` 等湾区城市。不支持的城市会 fallback 到 `cupertino`。

**响应格式（Gemini 成功）：**
```json
{
  "updatedAt": "2025-12-29T20:30:00.000000+00:00",
  "dataSource": "gemini",
  "stale": false,
  "ttlSeconds": 43200,
  "items": [
    {
      "id": "gemini-1",
      "title": "检查是否已收到所有 1099 表格",
      "why": "1 月底是 1099 表格发放截止日期，缺失表格可能影响报税",
      "who": "有投资账户、银行利息或副业收入的湾区码农",
      "action": "检查邮箱和账户通知，确认已收到所有 1099 表格",
      "deadline": "2025-01-31",
      "severity": "high",
      "category": "tax"
    },
    {
      "id": "gemini-2",
      "title": "Tax-loss harvesting 需注意 wash sale 规则",
      "why": "30 天内买卖相同或相似证券会触发 wash sale，损失不能抵税",
      "who": "正在进行 tax-loss harvesting 的投资者",
      "action": "检查最近 30 天的交易记录，避免重复买入相同证券",
      "deadline": null,
      "severity": "med",
      "category": "tax"
    }
  ],
  "disclaimer": "本信息仅供参考，不构成税务、投资或法律建议。请咨询专业人士获取个性化建议。"
}
```

**响应格式（Mock 降级）：**
```json
{
  "updatedAt": "2025-12-29T20:30:00.000000+00:00",
  "dataSource": "mock",
  "stale": true,
  "ttlSeconds": 43200,
  "items": [
    {
      "id": "seed-1099",
      "title": "检查是否已收到所有 1099 表格",
      "why": "1 月底是 1099 表格发放截止日期，缺失表格可能影响报税",
      "who": "有投资账户、银行利息或副业收入的湾区码农",
      "action": "检查邮箱和账户通知，确认已收到所有 1099 表格",
      "deadline": "2025-01-31",
      "severity": "high",
      "category": "tax"
    },
    {
      "id": "seed-wash-sale",
      "title": "Tax-loss harvesting 需注意 wash sale 规则",
      "why": "30 天内买卖相同或相似证券会触发 wash sale，损失不能抵税",
      "who": "正在进行 tax-loss harvesting 的投资者",
      "action": "检查最近 30 天的交易记录，避免重复买入相同证券",
      "deadline": null,
      "severity": "med",
      "category": "tax"
    }
  ],
  "disclaimer": "本信息仅供参考，不构成税务、投资或法律建议。请咨询专业人士获取个性化建议。"
}
```

**字段说明：**
- `updatedAt`: ISO 8601 格式的时间戳，表示数据更新时间
- `dataSource`: `gemini` = AI 生成，`cache` = Redis 缓存，`mock` = Mock 种子库
- `stale`: 布尔值，`true` 表示使用了过期缓存或降级数据
- `ttlSeconds`: 缓存 TTL（秒），默认 43200 秒（12 小时）
- `items`: 提醒列表，最多 3 条
- `items[].id`: 唯一标识符
- `items[].title`: 标题（≤40 字符）
- `items[].why`: 事实背景（≤80 字符）
- `items[].who`: 适用人群（≤40 字符）
- `items[].action`: 可执行行动（≤80 字符）
- `items[].deadline`: 截止日期（YYYY-MM-DD 格式或 `null`）
- `items[].severity`: 严重程度（`low` | `med` | `high`）
- `items[].category`: 分类（`tax` | `finance` | `work` | `legal` | `life`）
- `disclaimer`: 免责声明（所有响应必须包含）

**缓存与降级策略：**

执行顺序（优先级从高到低）：
1. **Redis Cache 命中** → 直接返回（`dataSource: "cache"`, `stale: false`）
   - Key: `risk:today:{city}:{YYYY-MM-DD}`
   - TTL: 12 小时（43200 秒）
   - 如果缓存过期但存在 → 返回（`stale: true`）

2. **Cache Miss → 调用 Gemini**
   - 超时：3-5 秒
   - 成功 → 写入 Redis cache 并返回（`dataSource: "gemini"`）
   - 失败 → 降级到步骤 3

3. **Gemini 失败但有 last-known-good Cache** → 返回过期缓存（`dataSource: "cache"`, `stale: true`）

4. **全部失败 → Mock 种子库**（最终降级）
   - 基于 day of year 轮换（1-2 条）
   - 始终可用，永不失败
   - `dataSource: "mock"`, `stale: true`

**AI Safety & Validation：**
- Gemini 必须输出严格 JSON（无 markdown 代码块）
- JSON parse 失败 → 直接降级到 mock
- 字段缺失/超长 → 截断或丢弃该条（保留有效项）
- 出现违法/规避税务/个性化投资建议 → 丢弃并降级
- 所有返回必须包含 `disclaimer` 字段
- 永不因 AI 异常返回 500（始终降级到 mock）

**错误处理：**
- Gemini API 失败 → 自动降级到 mock
- JSON 解析失败 → 自动降级到 mock
- 字段验证失败 → 过滤无效项，返回有效项
- Redis 不可用 → 直接使用 Gemini 或 mock
- 所有错误 → 永不返回 500，始终返回有效响应

**City 参数规则：**
- 支持的 city slug：`cupertino`, `sunnyvale`, `san-jose`, `palo-alto`, `mountain-view` 等湾区城市
- 不支持的城市 → fallback 到 `cupertino`（不返回 400）
- 所有 city 参数都会传递给 Gemini prompt，但实际生成内容为通用提醒（不依赖 city）

---

## 环境变量

### 后端环境变量

- `REDIS_URL`: Redis 连接 URL（可选，默认: `redis://localhost:6379/0`）
  - 用于缓存 `/risk/today` 和 `/market/snapshot` 数据
  - 缺失时：功能仍可用，但无缓存（直接调用 Gemini 或返回 mock）

- `GEMINI_API_KEY`: Google Gemini API Key（可选）
  - 用于 `/risk/today` 的 AI 生成功能
  - **缺失时**：`/risk/today` 自动降级为 mock 种子库，**不应抛 500**
  - 获取方式：https://makersuite.google.com/app/apikey

- `GOOGLE_CSE_API_KEY`: Google Custom Search API Key（可选）
  - 用于 Powerball 和 Gold 的 CSE fallback

- `GOOGLE_CSE_ID`: Google Custom Search Engine ID（CX）（可选）

- `DAILY_CSE_BUDGET`: 每日 CSE 配额限制（默认: 10000）

- `FINNHUB_API_KEY`: Finnhub API Key（可选）
  - 用于 Gold、BTC、S&P 500 的实时数据

### 前端环境变量

- `NEXT_PUBLIC_API_URL`: 前端 API 基础 URL（默认: `http://localhost:8000`）
  - 用于前端调用后端 API
  - 生产环境需设置为实际 API 地址

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

