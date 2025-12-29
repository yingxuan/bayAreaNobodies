# 「羊毛专区」修复总结

## A) 修改的组件文件列表

1. **web/app/lib/i18n.ts** (修改)
   - 新增 `extractProductName()`: 从标题中提取商品名
   - 新增 `getSourceName()`: 获取来源名称（Amazon, Target等）
   - 新增 `generateDealProductName()`: 生成商品名（提取或来源+类别）
   - 新增 `getDealImageUrl()`: 获取图片URL（带类别兜底图）
   - 新增 `getDealExternalUrl()`: 获取外部链接（带平台首页降级）
   - 修改 `getDealCategory()`: 增强类别判断（补充 care/supplement 等）

2. **web/app/components/HomeSections.tsx** (修改)
   - 重写 `HomeDealsSection` 组件
   - 新增图片显示（1:1 aspect ratio）
   - 新增商品名显示（类别 + 来源 + 商品名）
   - 修改点击行为（直接外跳，不进入站内详情页）

## B) Before / After 羊毛卡示例

### Before（修复前）
```
┌─────────────────────────────┐
│ [无图片]                    │
│ 日用品                      │
│ 可省约 $7.80（可叠加优惠）  │
│ 可省 $7.80                  │
│ 无需门槛                    │
└─────────────────────────────┘
点击 → /deals/unknown/xxx-123 (404)
```

### After（修复后）
```
┌─────────────────────────────┐
│ [图片 1:1] 日用品 · Amazon  │
│ Amazon 日用品优惠            │
│ 可省 $7.80                  │
│ 可省约 $7.80（可叠加优惠）   │
│ 无需门槛                    │
└─────────────────────────────┘
点击 → https://www.amazon.com/gp/goldbox (直接外跳)
```

## C) 点击行为说明

### 站内路由（已移除）
- ❌ `/deals/[source]/[slug]-[id]` - 不再使用（避免404）

### 外跳行为（新实现）
1. **优先使用 `source_url`**
   - 如果 deal 有 `source_url` → 直接打开该URL
   - 示例：`https://www.amazon.com/dp/B08XXX`

2. **降级到平台首页**
   - 如果没有 `source_url`，根据 `source` 字段判断：
     - Amazon → `https://www.amazon.com/gp/goldbox`
     - Target → `https://www.target.com/c/deals/-/N-5xtg6`
     - Walmart → `https://www.walmart.com/cp/deals`
     - Costco → `https://www.costco.com/warehouse-deals.html`
   - 其他来源 → 尝试从 source 提取域名，否则使用 Amazon 首页

3. **永不404**
   - 所有卡片点击都有有效的外部链接
   - 使用 `window.open(url, '_blank')` 新标签页打开

## D) 核心修复点

### 1. 商品名解析（是什么）
- **提取逻辑**: 从 title 中移除 "Save $X on", "X% off" 等促销短语
- **降级策略**: 如果无法提取 → 使用 "来源 + 类别 + 优惠"
- **显示格式**: `[类别] · [来源]` + `[商品名]`

### 2. 图片补齐（必须有图）
- **优先级 1**: 使用 `deal.image_url`（如果存在）
- **优先级 2**: 使用类别兜底图（SVG data URI）
  - 食品/零食: 灰色背景 + "食品零食"文字
  - 日用品: 灰色背景 + "日用品"文字
  - 其他类别: 对应类别占位图
- **图片规格**: 1:1 aspect ratio, object-fit: cover
- **错误处理**: `onError` 时显示灰色占位图

### 3. 点击行为修复（消灭404）
- **移除站内路由**: 不再使用 `/deals/[source]/[slug]-[id]`
- **直接外跳**: 使用 `source_url` 或平台首页
- **新标签页**: `window.open(url, '_blank')`
- **降级保证**: 始终有有效链接，永不404

## E) 验收标准

✅ **每个卡片用户知道"这是什么"**
- 显示类别 + 来源 + 商品名
- 示例：`日用品 · Amazon` + `Amazon 日用品优惠`

✅ **每个卡片都有图片**
- 使用 `image_url` 或类别兜底图
- 1:1 比例，左侧显示

✅ **任意卡片点击后不出现404**
- 直接外跳到 `source_url` 或平台首页
- 新标签页打开

✅ **用户不需要再猜这是食品还是日用品**
- 类别标签清晰显示
- 商品名包含类别信息

## F) 技术实现细节

### 商品名提取算法
```typescript
// 移除促销短语
"Save $7.80 on select items" 
→ "select items" (太短，降级)
→ "Amazon 日用品优惠"
```

### 图片降级链
```
deal.image_url 
→ 类别占位图 (SVG data URI)
→ 灰色占位图 (onError)
```

### 外跳URL生成
```
deal.source_url 
→ 平台首页 (根据 source)
→ Amazon 首页 (最终降级)
```

## G) 卡片布局结构

```
┌─────────────────────────────┐
│ [图片] │ 类别 · 来源         │
│ 80x80  │ 商品名（主标题）      │
│        │ 可省 $X.XX（绿色）   │
│        │ 折扣信息（小字）     │
│        │ 限时/囤货/门槛       │
└─────────────────────────────┘
```

