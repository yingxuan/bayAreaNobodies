# 发布前文档与稳定性收尾 - 完成总结

## A) 新增/修改的文档文件列表

1. **API_DOCS.md** (修改)
   - 新增 `/risk/today` API 完整文档
   - 包含两个完整 JSON 示例（Gemini 成功 / Mock 降级）
   - 添加环境变量说明
   - 添加缓存与降级顺序说明
   - 添加 AI Safety & Validation 说明
   - 添加 City 参数规则

2. **UPGRADE_SUMMARY.md** (修改)
   - 补充 `/risk/today` API 完整示例（两个 JSON）
   - 明确缓存与降级执行顺序
   - 添加 AI Safety & Validation 章节
   - 添加环境变量清单
   - 添加 City 参数规则
   - 添加发布前自测 Checklist

3. **RELEASE_CHECKLIST.md** (新增)
   - 本文档，用于发布前检查

## B) /risk/today 的两个 JSON 示例

### 示例 A：Gemini 成功（dataSource="gemini", stale=false）
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

### 示例 B：Mock 降级（dataSource="mock", stale=true）
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

## C) 环境变量清单

### 后端环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `GEMINI_API_KEY` | 否 | - | 用于 `/risk/today` AI 生成。缺失时自动降级为 mock，不应抛 500 |
| `REDIS_URL` | 否 | `redis://localhost:6379/0` | 用于缓存。缺失时功能仍可用，但无缓存 |
| `GOOGLE_CSE_API_KEY` | 否 | - | 用于 Powerball 和 Gold 的 CSE fallback |
| `GOOGLE_CSE_ID` | 否 | - | Google Custom Search Engine ID |
| `DAILY_CSE_BUDGET` | 否 | `10000` | 每日 CSE 配额限制 |
| `FINNHUB_API_KEY` | 否 | - | 用于 Gold、BTC、S&P 500 的实时数据 |

### 前端环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `NEXT_PUBLIC_API_URL` | 否 | `http://localhost:8000` | 前端 API 基础 URL。生产环境需设置为实际 API 地址 |

## D) 缓存与降级顺序摘要（1-2 行）

**执行顺序**：Redis Cache（12h TTL）→ Gemini API（3-5s 超时）→ Last-known-good Cache → Mock 种子库。所有步骤失败时自动降级，永不返回 500。

## E) 发布前自测 Checklist（3 条）

1. ✅ **无 GEMINI_API_KEY 时测试**：`/risk/today` 应返回 `dataSource: "mock"`，不应抛 500
2. ✅ **Redis 不可用时测试**：应直接使用 Gemini 或 mock，不应抛 500
3. ✅ **首页资产显示验证**：首屏能看到 `Total Assets: $X` 和 `Today: +$Y (+Z%)`，且未展开 Portfolio 时只出现一次

---

## 文件定位确认

✅ **UPGRADE_SUMMARY.md** - 存在，已更新  
✅ **API_DOCS.md** - 存在，已更新  
✅ **api/app/routers/risk.py** - 存在  
✅ **api/app/services/risk_service.py** - 存在  
✅ **web/app/lib/risk.ts** - 存在  
✅ **web/app/lib/riskSeeds.ts** - 存在  

所有文件已确认存在，文档已补齐。

