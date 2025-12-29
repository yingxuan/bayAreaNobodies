# 首页与 Risk 模块产品级升级 - 交付总结

## A) 修改/新增文件列表

### 前端文件
1. **web/app/components/TodayBrief.tsx** (修改)
   - 更新资产显示格式：`Total Assets: $X | Today: +$Y (+Z%)`
   - 优化解读型文案生成逻辑（回答"So-what"）

2. **web/app/lib/risk.ts** (修改)
   - 更新 RiskItem schema，添加 `why`, `deadline`, `category` 字段
   - 更新 `getRiskItems()` 调用新 API endpoint
   - 增强 `isValidRisk()` 验证逻辑

3. **web/app/lib/riskSeeds.ts** (新增)
   - Mock 种子库，包含 10 条合规的通用提醒
   - 每日轮换逻辑（基于 day of year）

4. **web/app/components/RiskPageContent.tsx** (修改)
   - 显示新字段：`why`, `deadline`, `category`
   - 增强错误处理（永不抛出）

5. **web/app/risk/page.tsx** (修改)
   - 更新标题和描述为"今日提醒"

### 后端文件
6. **api/app/services/risk_service.py** (新增)
   - Gemini AI 集成（3-5 秒超时）
   - Redis 缓存（12 小时 TTL）
   - Mock 种子库降级策略
   - JSON 校验和字段长度验证

7. **api/app/routers/risk.py** (新增)
   - `GET /risk/today?city=cupertino` endpoint
   - 永不返回 500，始终降级到 mock

8. **api/main.py** (修改)
   - 注册 risk router

## B) /risk/today API 完整文档

### 请求示例
```bash
curl "http://localhost:8000/risk/today?city=cupertino"
```

### 查询参数
- `city` (可选，默认: `cupertino`): 城市名称
  - 支持：`cupertino`, `sunnyvale`, `san-jose`, `palo-alto`, `mountain-view` 等湾区城市
  - 不支持的城市会 fallback 到 `cupertino`（不返回 400）

### 响应示例 A：Gemini 成功（dataSource="gemini", stale=false）
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

### 响应示例 B：Mock 降级（dataSource="mock", stale=true）
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

### 字段说明
- `updatedAt`: ISO 8601 格式时间戳（必须）
- `dataSource`: `gemini` | `cache` | `mock`（必须）
- `stale`: 布尔值，`true` 表示使用了过期缓存或降级数据（必须）
- `ttlSeconds`: 缓存 TTL（秒），默认 43200（必须）
- `items`: 数组，最多 3 条（必须）
- `items[].deadline`: `YYYY-MM-DD` 格式或 `null`（必须）
- `disclaimer`: 免责声明字符串（必须）

## C) 首页资产数字出现位置说明

### Before（修改前）
- TodayBrief 财务结论卡：显示"总资产 $X | 今日 +$Y (+Z%) | 解读文案"
- HomePortfolioSection Header：显示"今日 +$Y (+Z%)"（已删除）

### After（修改后）
- **TodayBrief 财务结论卡（首屏唯一）**：
  - 第一行：`Total Assets: $X`
  - 第二行：`Today: +$Y (+Z%)`
  - 第三行：解读型文案（回答是否需要行动）
- **HomePortfolioSection Header**：
  - 只显示：`💼 我的资产 | 展开查看持仓`
  - 不显示任何 $ 或 %
- **HomePortfolioSection 展开后**：
  - 显示总资产、持仓表等（深入层，不算重复）

### 验收结果
✅ 首页首屏能看到 `Total Assets: $X` 和 `Today: +$Y (+Z%)`  
✅ 未展开 Portfolio 时，资产数字只出现一次（TodayBrief 大卡）  
✅ Portfolio Header 不显示任何数字

## D) Redis Key / TTL / 降级策略

### Redis Key 格式
```
risk:today:{city}:{YYYY-MM-DD}
```
示例：`risk:today:cupertino:2025-12-29`

### TTL
- **缓存 TTL**: 12 小时（43200 秒）
- **锁 TTL**: 30 秒（防止 cache stampede）

### 缓存与降级执行顺序（必须按此顺序）

1. **Redis Cache 命中** → 直接返回
   - Key: `risk:today:{city}:{YYYY-MM-DD}`
   - 如果存在且 age < 12h → 返回（`dataSource: "cache"`, `stale: false`）
   - 如果过期但存在 → 返回（`dataSource: "cache"`, `stale: true`）

2. **Cache Miss → 调用 Gemini**
   - 超时：3-5 秒
   - 成功 → 写入 Redis cache（12h TTL）并返回（`dataSource: "gemini"`）
   - 失败 → 降级到步骤 3

3. **Gemini 失败但有 last-known-good Cache** → 返回过期缓存
   - `dataSource: "cache"`, `stale: true`

4. **全部失败 → Mock 种子库**（最终降级）
   - 基于 day of year 轮换（1-2 条）
   - 始终可用，永不失败
   - `dataSource: "mock"`, `stale: true`

### 错误处理
- Gemini API 失败 → 自动降级到 mock
- JSON 解析失败 → 自动降级到 mock
- 字段验证失败 → 过滤无效项，返回有效项
- Redis 不可用 → 直接使用 Gemini 或 mock
- 所有错误 → 永不返回 500，始终返回有效响应

### AI Safety & Validation（必须遵守）

**Gemini 输出校验规则：**
- Gemini 必须输出严格 JSON（无 markdown 代码块）
- JSON parse 失败 → 直接降级到 mock
- 字段缺失/超长 → 截断或丢弃该条（保留有效项）
  - `title` > 40 字符 → 丢弃
  - `why` > 80 字符 → 丢弃
  - `who` > 40 字符 → 丢弃
  - `action` > 80 字符 → 丢弃
- 出现违法/规避税务/个性化投资建议 → 丢弃并降级
- 所有返回必须包含 `disclaimer` 字段
- 永不因 AI 异常返回 500（始终降级到 mock）

**合规要求：**
- 所有提醒必须是通用提醒，不提供个性化建议
- 不要求用户提供隐私信息
- 不涉及违法或规避税务的行为
- 所有内容必须包含免责声明

## E) 最终 Gemini Prompt 文本

### System Prompt
```
你是生活与合规提醒助手。只能提供面向大众的通用提醒，不提供个性化税务/投资/法律建议。输出必须是严格 JSON，不要 markdown，不要多余文字。最多 3 条。
```

### User Prompt
```
今天是 {YYYY-MM-DD}，地区：湾区 {city}（California）。
请给湾区码农今天应该注意的 1–3 件事。
偏好：报税节点、tax-loss harvesting 的通用注意事项、RSU/401k/保险/合规。
每条必须包含 title/why/who/action/deadline/severity/category。
不要给个性化建议，不要要求隐私信息。

输出格式（严格 JSON 数组）：
[
  {
    "id": "unique-id",
    "title": "标题（≤40字）",
    "why": "事实背景（≤80字）",
    "who": "适用人群（≤40字）",
    "action": "可执行行动（≤80字）",
    "deadline": "YYYY-MM-DD 或 null",
    "severity": "low|med|high",
    "category": "tax|finance|work|legal|life"
  }
]
```

## 验收标准检查清单

- ✅ 首页首屏显示：`Total Assets: $X` 和 `Today: +$Y (+Z%)`
- ✅ 未展开 Portfolio 时，资产数字只出现一次
- ✅ `/risk/today` 在无 Gemini key / 无外网时不 500
- ✅ AI 输出为严格 JSON，失败自动降级
- ✅ 风险内容"像今天该注意什么"，不是泛泛而谈
- ✅ Mock 种子库可独立长期使用
- ✅ 所有 AI 输出经过 JSON 校验和字段长度验证
- ✅ 免责声明在所有响应中显示
- ✅ 前端组件永不抛出错误，始终显示有效状态

## 技术细节

### 环境变量

**后端必需：**
- `GEMINI_API_KEY`（可选）
  - 用于 `/risk/today` 的 AI 生成功能
  - **缺失时**：自动降级为 mock 种子库，**不应抛 500**
  - 获取方式：https://makersuite.google.com/app/apikey

- `REDIS_URL`（可选，默认: `redis://localhost:6379/0`）
  - 用于缓存 `/risk/today` 数据
  - 缺失时：功能仍可用，但无缓存（直接调用 Gemini 或返回 mock）

**前端必需：**
- `NEXT_PUBLIC_API_URL`（默认: `http://localhost:8000`）
  - 用于前端调用后端 API
  - 生产环境需设置为实际 API 地址

### 依赖
- `google-generativeai==0.3.2`（已在 requirements.txt 中，非新增）

### 数据库
- 无 schema 变更
- 无新表创建

### 缓存
- Redis（已存在）
- Key: `risk:today:{city}:{YYYY-MM-DD}`
- TTL: 12 小时（43200 秒）

### API 端点
- `GET /risk/today?city=cupertino`
- 响应时间：< 5 秒（Gemini）或 < 100ms（cache/mock）
- 永不返回 500

### City 参数规则
- 支持的 city slug：`cupertino`, `sunnyvale`, `san-jose`, `palo-alto`, `mountain-view` 等湾区城市
- 不支持的城市 → fallback 到 `cupertino`（不返回 400）
- 所有 city 参数都会传递给 Gemini prompt，但实际生成内容为通用提醒（不依赖 city）

---

## 发布前自测 Checklist

1. ✅ **无 GEMINI_API_KEY 时测试**：`/risk/today` 应返回 `dataSource: "mock"`，不应抛 500
2. ✅ **Redis 不可用时测试**：应直接使用 Gemini 或 mock，不应抛 500
3. ✅ **首页资产显示验证**：首屏能看到 `Total Assets: $X` 和 `Today: +$Y (+Z%)`，且未展开 Portfolio 时只出现一次

