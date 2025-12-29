# 「羊毛专区」产品级升级总结

## A) 修改/新增文件列表

### 新增文件
1. **web/app/lib/dealImage.ts** (新增)
   - `getDealImage()`: 统一图片选择函数，带类别兜底图

2. **web/app/lib/dealFormat.ts** (新增)
   - `getDealCategoryCN()`: 获取中文分类（快餐/食品/日用品等）
   - `getDealTitleCN()`: 生成中文标题（保留品牌名）
   - `getDealSaveText()`: 生成省钱文本（只生成一次，不重复）
   - `getDealBadges()`: 生成标签（最多2个）

3. **api/app/services/food_deals_service.py** (新增)
   - `fetch_food_deals()`: 使用 Google CSE 抓取快餐优惠
   - `parse_deal_from_result()`: 解析 CSE 结果为 deal 对象
   - `extract_image_from_result()`: 从 CSE 结果提取图片
   - Mock 数据：Burger King, Subway, McDonald's

4. **api/app/routers/deals_food.py** (新增)
   - `GET /deals/food`: 获取快餐优惠接口

5. **web/public/images/deals/.gitkeep** (新增)
   - 占位图片目录（需要添加实际图片文件）

### 修改文件
6. **web/app/components/HomeSections.tsx** (修改)
   - 重写 `HomeDealsSection` 组件
   - 合并 food deals 和 retail deals
   - 使用新的格式化函数（去重）
   - 使用新的图片处理（强制有图）
   - 修复点击行为（外跳，不404）

7. **web/next.config.js** (修改)
   - 添加图片域名白名单（Amazon, Slickdeals, 快餐品牌等）

8. **api/main.py** (修改)
   - 注册 `deals_food` router

## B) /deals/food 的 curl 示例

### 成功响应（CSE）
```bash
curl -X GET "http://localhost:8000/deals/food?city=cupertino&limit=10" \
  -H "Accept: application/json"
```

**响应示例：**
```json
{
  "items": [
    {
      "id": "food-123456",
      "title": "Burger King BOGO Deal",
      "description": "Buy one Whopper, get one free...",
      "url": "https://www.burgerking.com/promotions",
      "source": "burgerking.com",
      "category": "food_fast",
      "imageUrl": "https://example.com/image.jpg",
      "saveAmount": null,
      "code": null
    }
  ],
  "total": 1,
  "city": "cupertino",
  "dataSource": "cse"
}
```

### Mock 降级响应
```json
{
  "items": [
    {
      "id": "mock-bk-bogo",
      "title": "Burger King BOGO Whopper Deal",
      "description": "Buy one Whopper, get one free with coupon code",
      "url": "https://www.burgerking.com/promotions",
      "source": "burgerking.com",
      "category": "food_fast",
      "imageUrl": null,
      "saveAmount": null,
      "code": null
    },
    {
      "id": "mock-subway",
      "title": "Subway $5 Footlong Deal",
      "description": "Limited time $5 footlong sandwiches",
      "url": "https://www.subway.com/en-us/promotions",
      "source": "subway.com",
      "category": "food_fast",
      "imageUrl": null,
      "saveAmount": "5.00",
      "code": null
    },
    {
      "id": "mock-mcd",
      "title": "McDonald's App Deal - Free Fries",
      "description": "Download app and get free fries with purchase",
      "url": "https://www.mcdonalds.com/us/en-us/deals.html",
      "source": "mcdonalds.com",
      "category": "food_fast",
      "imageUrl": null,
      "saveAmount": null,
      "code": null
    }
  ],
  "total": 3,
  "city": "cupertino",
  "dataSource": "mock"
}
```

## C) 首页羊毛卡片最终字段映射说明

### 卡片结构（去重后）
```
┌─────────────────────────────────┐
│ [图片 80x80] │ [快餐]            │
│              │ Burger King 买一送一│
│              │ 可省 $X（绿色大字） │
│              │ [需 Clip] [BOGO]  │
│              │ burgerking.com    │
└─────────────────────────────────┘
```

### 字段映射
- **categoryCN**: `getDealCategoryCN(deal)` → "快餐" | "食品/零食" | "日用品" | "服饰" | "精选优惠"
- **titleCN**: `getDealTitleCN(deal)` → "Burger King 买一送一" | "Subway $5 优惠" | "Amazon 日用品优惠"
- **saveText**: `getDealSaveText(deal)` → "可省 $7.80" | "买一送一" | null（只出现一次）
- **badges**: `getDealBadges(deal)` → ["需 Clip", "BOGO"] | ["无门槛", "折扣"]（最多2个）
- **image**: `getDealImage(deal)` → { src: "https://...", isFallback: false } | { src: "/images/deals/food.png", isFallback: true }
- **url**: `deal.url || deal.source_url || deal.sourceUrl || deal.externalUrl || getDealExternalUrl(...)`

### 去重规则
- ❌ 旧：`可省 $7.80` 在标题、副标题、正文重复出现
- ✅ 新：`可省 $7.80` 只出现一次（绿色大字）
- ❌ 旧：`可省约 $7.80（可叠加优惠）` + `可省 $7.80` 重复
- ✅ 新：`Burger King 买一送一`（标题）+ `可省 $X`（唯一一次）

## D) 自测说明

### 1. 图片是否出现
- **检查点**：首页羊毛专区所有卡片都有图片
- **验证方法**：
  - 打开首页，滚动到"羊毛专区"
  - 检查每个卡片左侧是否有图片（80x80）
  - 如果外链图片 403/404，应该自动回退到类别兜底图
  - 不应该出现灰色空块

### 2. 点击是否 404
- **检查点**：任意卡片点击都不进入 404
- **验证方法**：
  - 点击每个羊毛卡片
  - 应该在新标签页打开外部链接（Burger King、Subway 等官网）
  - 或打开 `/deals` 页面（如果 URL 无效）
  - 不应该进入 `/deals/[source]/[slug]` 导致 404

### 3. 是否包含 BK/Subway
- **检查点**：羊毛专区能看到至少 2 条快餐优惠
- **验证方法**：
  - 打开首页，查看"羊毛专区"
  - 应该看到至少 2 条带有"快餐"标签的卡片
  - 卡片标题应包含 "Burger King"、"Subway"、"McDonald's" 等品牌名
  - 卡片点击应跳转到对应品牌官网

### 4. 信息去重
- **检查点**：同一金额/信息不重复出现
- **验证方法**：
  - 检查每个卡片，"可省 $X" 只出现一次（绿色大字）
  - 标题和副标题不重复显示相同信息
  - 标签（badges）最多 2 个，不重复

## E) 技术实现细节

### 图片处理流程
1. 优先级查找：`imageUrl` → `image` → `thumbnail` → `ogImage` → `photoUrl` → `media[0].url`
2. 验证：必须是 `http://` 或 `https://` 开头
3. 类别兜底：根据 `category` 返回 `/images/deals/{category}.png`
4. 错误处理：`onError` 时切换到类别兜底图

### 去重逻辑
- `getDealSaveText()`: 只生成一次省钱文本，不在标题中重复
- `getDealTitleCN()`: 生成简洁标题，不包含金额信息
- `getDealBadges()`: 最多 2 个标签，不重复

### Food Deals 数据流
1. 前端并行请求：`/feeds/deals` + `/deals/food`
2. 合并结果：优先 food deals（至少 2 条），然后 retail deals
3. 后端 CSE 搜索：7 个查询（Burger King, Subway, McDonald's 等）
4. 解析结果：提取品牌、优惠类型、图片
5. 缓存：Redis 6 小时 TTL

### 点击行为
- 优先级：`deal.url` → `deal.source_url` → `deal.sourceUrl` → `deal.externalUrl` → `getDealExternalUrl()`
- 验证：必须是 `http://` 或 `https://` 开头
- 降级：如果 URL 无效，打开 `/deals` 页面

## F) 占位图片说明

需要在 `web/public/images/deals/` 目录下添加以下图片文件：
- `food.png` - 食品/快餐占位图
- `household.png` - 日用品占位图
- `snack.png` - 零食占位图
- `deal.png` - 默认占位图
- `finance.png` - 金融占位图

**临时方案**：当前使用 SVG data URI 作为占位，但建议替换为实际图片文件以获得更好的视觉效果。

