# 「今天吃什么」智能卡片升级总结

## A) 新增 / 修改的文件列表

### 新增文件
1. **api/app/services/food_today_service.py** (新增)
   - `fetch_today_pick()`: 获取今天的餐厅和推荐菜品
   - `select_restaurant_for_today()`: 基于日期确定性随机选择餐厅
   - `get_restaurant_dish()`: 从 Google Places reviews 提取菜品信息
   - `extract_dish_from_reviews()`: 从评论中提取菜品名称
   - `get_mock_today_pick()`: Mock 数据降级

2. **web/app/components/TodayEatCard.tsx** (新增)
   - 专门的"今天吃什么"卡片组件
   - 显示餐厅名、推荐菜品、菜品图片
   - 点击直接跳转到 Google Maps

### 修改文件
3. **api/app/routers/food.py** (修改)
   - 新增 `GET /food/today-pick` 端点
   - 导入 `food_today_service`

4. **web/app/components/TodayBrief.tsx** (修改)
   - 导入 `TodayEatCard` 组件
   - 移除旧的 food entry 逻辑
   - 在 Entry Cards grid 中使用 `TodayEatCard`

## B) /food/today-pick API 的 curl 示例

### 请求示例
```bash
curl -X GET "http://localhost:8000/food/today-pick?city=cupertino" \
  -H "Accept: application/json"
```

### 响应示例（Google Places 成功）
```json
{
  "city": "cupertino",
  "date": "2025-12-29",
  "restaurant": {
    "name": "Home Eat 汉家宴",
    "googlePlaceId": "ChIJxxxx",
    "googleMapsUrl": "https://maps.google.com/?q=place_id:ChIJxxxx",
    "rating": 4.7
  },
  "dish": {
    "name": "招牌红烧肉",
    "image": "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=xxx&key=xxx"
  },
  "dataSource": "google_places",
  "stale": false,
  "ttlSeconds": 86400,
  "updatedAt": "2025-12-29T20:00:00.000000+00:00"
}
```

### 响应示例（Mock 降级）
```json
{
  "city": "cupertino",
  "date": "2025-12-29",
  "restaurant": {
    "name": "川味轩",
    "googlePlaceId": "",
    "googleMapsUrl": "https://maps.google.com/?q=川味轩+cupertino",
    "rating": 4.5
  },
  "dish": {
    "name": "宫保鸡丁",
    "image": ""
  },
  "dataSource": "mock",
  "stale": true,
  "ttlSeconds": 86400,
  "updatedAt": "2025-12-29T20:00:00.000000+00:00"
}
```

## C) Card 的最终文案示例

### 卡片展示结构
```
┌─────────────────────────────────┐
│ 🍜 今天吃什么                   │
│                                 │
│ Home Eat 汉家宴                 │
│ (大号字体)                      │
│                                 │
│ 招牌红烧肉                      │
│ (粗体)                          │
│                                 │
│ [菜品图片 16:9]                 │
│                                 │
│ ⭐ 4.7 · Cupertino              │
│ (小字灰色)                      │
│                                 │
│ 已帮你选好，点开直接导航        │
│ (小字灰色)                      │
└─────────────────────────────────┘
```

### 点击行为
- 点击整个卡片 → `window.open(googleMapsUrl, '_blank')`
- 直接打开 Google Maps 的该餐厅页面
- 不进入站内详情页

## D) 核心功能实现

### 1. 确定性随机选择
- **规则**: `seed = hash(city + YYYY-MM-DD)`
- **结果**: 同一天所有用户看到相同餐厅
- **变化**: 不同天会变化

### 2. 菜品提取逻辑
- **优先级 1**: 从 Google Places reviews 提取（关键词匹配：红烧肉、宫保鸡丁、麻婆豆腐等）
- **优先级 2**: 从评论中的"推荐"、"必点"、"招牌"等关键词提取
- **降级**: 如果无法提取，使用"招牌菜"

### 3. 图片获取
- **优先级 1**: Google Places 的第二张照片（通常是菜品，第一张是餐厅外观）
- **优先级 2**: 餐厅封面图
- **降级**: 无图片

### 4. 缓存策略
- **Redis Key**: `food:today:{city}:{YYYY-MM-DD}`
- **TTL**: 24 小时（86400 秒）
- **分布式锁**: 防止缓存击穿

## E) 降级策略

1. **Google Places API 不可用**
   - 返回 mock 餐厅和菜品
   - `dataSource: "mock"`, `stale: true`

2. **无法提取菜品名**
   - 使用"招牌菜"作为兜底

3. **图片缺失**
   - 使用餐厅封面图
   - 如果仍缺失，不显示图片

4. **数据库无中餐馆**
   - 返回 mock 数据

5. **API 异常**
   - 永不返回 500
   - 始终返回 mock 数据

## F) 验收标准

✅ **同一天多次刷新结果一致**
- 使用日期作为随机 seed
- Redis 缓存 24 小时

✅ **不同天结果变化**
- 每天使用不同的 date string 作为 seed

✅ **点击卡片直接打开 Google Maps**
- `window.open(googleMapsUrl, '_blank')`
- 不进入站内详情页

✅ **用户无需再"选餐厅"**
- 直接显示餐厅名和推荐菜品
- 点击即可导航

✅ **中文优先**
- 餐厅名：中文优先
- 菜品名：中文（允许"招牌菜"兜底）
- 无英文描述性句子

## G) 技术实现细节

### 后端 Service
- **确定性随机**: 使用 `hashlib.md5(city + date)` 生成 seed
- **菜品提取**: 关键词匹配（30+ 常见中餐菜品）
- **Google Places**: 使用 `place/details` API 获取 reviews 和 photos
- **缓存**: Redis 24 小时 TTL，带分布式锁

### 前端组件
- **独立组件**: `TodayEatCard` 独立于 `BriefItemCard`
- **图片处理**: `onError` 隐藏加载失败的图片
- **点击行为**: 直接 `window.open` Google Maps URL
- **加载状态**: 显示"加载中..."占位

### 数据流
1. 前端请求 `/food/today-pick?city=cupertino`
2. 后端检查 Redis 缓存
3. 如果无缓存：
   - 从数据库获取所有中餐馆
   - 使用日期 seed 随机选择
   - 调用 Google Places API 获取菜品信息
   - 缓存结果 24 小时
4. 返回餐厅 + 菜品 + Google Maps URL
5. 前端渲染卡片，点击跳转 Google Maps

