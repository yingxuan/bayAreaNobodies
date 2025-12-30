# 首页重构总结：湾区码农每日决策台

## 一、修改/新增文件清单

### 修改文件：
1. **`web/app/page.tsx`**
   - 完全重构，按 1-9 顺序排列模块
   - 移除 HomeOverview、EntryCards
   - 新增所有新组件引用

2. **`web/app/components/TodayCommandBar.tsx`**
   - 标题中文化："今日指标" → "📊 今天市场发生了什么"

3. **`web/app/lib/hotTopics.ts`**
   - 标签中文化："Market" → "S&P 500"，"Gold" → "黄金"

4. **`web/app/components/FinancialStatusCard.tsx`**
   - 标题更新："💰 财务状态" → "📈 股票资产"（保留作为备用）

5. **`web/app/components/TodayMustDo.tsx`**
   - 标题更新："✅ 今天必须做的 3 件事" → "✅ 今天提醒"
   - 新增"换一批"按钮
   - 显示 why + action（两行）

### 新增文件：
1. **`web/app/components/StockAssetsCard.tsx`**
   - (2) 股票资产组件
   - 显示：总资产、今日涨跌、Top Movers
   - 整卡可点击跳转 /wealth

2. **`web/app/components/NewsDigestCard.tsx`**
   - (3) 科技行业 & 美国经济新闻
   - 高密度、中文优先、少而精

3. **`web/app/components/CarouselSection.tsx`**
   - 通用 carousel 外壳组件
   - 支持标题、副标题、换一批、查看更多

4. **`web/app/components/PlaceCarousel.tsx`**
   - (5-6) 中餐/奶茶 carousel
   - 支持 geolocation，fallback 到 Cupertino
   - 随机排序 + 换一批

5. **`web/app/components/DealsCarousel.tsx`**
   - (7) 遍地羊毛 carousel
   - 修复图片为空问题（使用 getDealImage）
   - 去重（按 title+source）
   - 点击外链（修复 404）

6. **`web/app/components/EntertainmentCarousel.tsx`**
   - (8) 打发时间 carousel
   - 预留 yfsp.tv API 接口

7. **`web/app/components/GossipCarousel.tsx`**
   - (9) 北美八卦 carousel
   - 使用现有 /feeds/gossip 接口

## 二、首页最终渲染树（按 1→9）

```
Home (page.tsx)
├── (1) TodayCommandBar - 📊 今天市场发生了什么
│   ├── S&P 500
│   ├── 黄金
│   ├── BTC
│   ├── CA Jumbo ARM
│   └── Powerball
│
├── (2) StockAssetsCard - 📈 股票资产
│   ├── 总资产：$X
│   ├── 今日涨跌：+$Y (+Z%)
│   ├── Top Movers (3条)
│   └── 点击跳转 /wealth
│
├── (3) NewsDigestCard - 📰 科技行业 & 美国经济新闻
│   ├── Item 1: 标题 + 摘要 + 影响
│   └── Item 2: 标题 + 摘要 + 影响
│
├── (4) TodayMustDo - ✅ 今天提醒
│   ├── Item 1: 标题 + why + action + deadline
│   ├── Item 2: 标题 + why + action + deadline
│   ├── Item 3: 标题 + why + action + deadline
│   └── 换一批按钮
│
├── (5) PlaceCarousel - 🍜 吃点好的
│   └── 横向滚动卡片（中餐馆）
│
├── (6) PlaceCarousel - 🧋 肥宅快乐水
│   └── 横向滚动卡片（奶茶店）
│
├── (7) DealsCarousel - 💰 遍地羊毛
│   └── 横向滚动卡片（deals）
│
├── (8) EntertainmentCarousel - 🎬 打发时间
│   └── 横向滚动卡片（yfsp.tv，待实现）
│
└── (9) GossipCarousel - 🗣 北美八卦
    └── 横向滚动卡片（一亩三分地）
```

## 三、新 API 路径与返回字段

### 已使用现有 API：
1. **`GET /portfolio/db-summary`**
   - 返回：`total_value`, `day_gain`, `day_gain_percent`, `holdings[]`
   - 用途：股票资产卡

2. **`GET /tech/trending?source=hn&limit=2`**
   - 返回：`items[]` (title, title_cn, summary, summary_cn, impact_cn, url)
   - 用途：科技新闻

3. **`GET /risk/today-actions?city=cupertino&refresh=1`**
   - 返回：`items[]` (title, why, action, deadline, severity)
   - 用途：今天提醒

4. **`GET /food/restaurants?cuisine_type={chinese|boba}&limit=12`**
   - 返回：`restaurants[]` (name, rating, photo_url, google_maps_url, distance_miles)
   - 用途：中餐/奶茶 carousel

5. **`GET /deals/food?city=cupertino&limit=12`**
   - 返回：`items[]` (title, description, imageUrl, externalUrl, sourceUrl)
   - 用途：羊毛 carousel

6. **`GET /feeds/deals?limit=12`**
   - 返回：`coupons[]` (title, description, url, code)
   - 用途：羊毛 carousel（补充）

7. **`GET /feeds/gossip?limit=12`**
   - 返回：`articles[]` (title, title_cn, url, source, engagement, created_at)
   - 用途：八卦 carousel

### 待实现 API（后端）：
1. **`GET /entertainment/yfsp/latest?type=movie|tv&limit=12`**
   - 返回：`items[]` (title, title_cn, poster, type, status, url)
   - 用途：打发时间 carousel
   - 状态：前端已预留，后端待实现

2. **`GET /news/economy?limit=2`**（可选）
   - 返回：`items[]` (title, title_cn, summary, impact, source, time)
   - 用途：美国经济新闻（补充到 NewsDigestCard）
   - 状态：可选，当前使用 tech news 作为占位

## 四、已修复的体验痛点

### ✅ 1. 英文过多 → 中文化
- **TodayCommandBar**：标题和标签全部中文化
- **Tech News**：优先显示 `title_cn`，fallback 到 `title`
- **Deals**：使用 `getDealReadableTitle` 生成中文标题
- **Gossip**：优先显示 `title_cn`，来源名称中文化（一亩三分地、华人网）

### ✅ 2. 内容冗余 → 去冗余
- **Tech News**：从三部分长文改为高密度单条（标题 + 摘要 + 影响）
- **Today Must Do**：只显示必要字段（标题 + why + action + deadline）
- **Deals**：去重逻辑（按 title+source 归一）

### ✅ 3. 点击 404 → 修复链接
- **DealsCarousel**：点击直接外链（`externalUrl` > `sourceUrl` > `url`）
- **PlaceCarousel**：点击直接打开 Google Maps（`google_maps_url`）
- **GossipCarousel**：点击直接外链到原帖（`url`）
- **StockAssetsCard**：整卡和 Top Movers 行都跳转 `/wealth`（不 404）

### ✅ 4. 图片为空 → 修复 fallback
- **DealsCarousel**：使用 `getDealImage()` 统一处理，有完整 fallback 链
- **PlaceCarousel**：使用 `photo_url`，失败显示占位符
- **所有卡片**：统一使用 SVG data URI 作为最终 fallback

## 五、设计原则执行情况

### A. "数字只出现一次"
- ✅ 市场数字（S&P/BTC/Gold/ARM/Powerball）只在 (1) TodayCommandBar 出现
- ✅ 个人资产数字只在 (2) StockAssetsCard 出现
- ✅ 不重复显示

### B. 中文优先
- ✅ Tech/Deals/Gossip 标题优先显示中文
- ✅ 英文作为 fallback 或小字显示
- ⚠️ 后端翻译功能待完善（当前依赖现有 `title_cn` 字段）

### C. 信息密度
- ✅ 每个 section 只展示决策所需字段
- ✅ Tech News 从长文改为高密度单条
- ✅ 避免冗余模板

### D. 卡片统一
- ✅ 所有 carousel card 都有：图片、标题、关键信息、CTA
- ✅ 统一使用 CarouselSection 外壳

### E. 可拓展到 mobile
- ✅ 所有 section 都是独立组件
- ✅ Carousel 使用横向滚动，适合 mobile swipe
- ✅ 组件结构可复用

## 六、待完善功能

### 后端接口待实现：
1. **`/entertainment/yfsp/latest`**
   - 抓取 yfsp.tv 最新列表
   - 翻译片名（Gemini）
   - 缓存 TTL

2. **`/news/economy`**（可选）
   - 美国经济/宏观新闻聚合
   - 可使用 Gemini daily brief 或 RSS

### 翻译功能待完善：
1. **后端翻译服务**
   - `translate_en_to_zh(text)` 函数
   - 使用 Gemini API
   - Redis 缓存

2. **Tech News 翻译**
   - 当前依赖现有 `title_cn` 字段
   - 需要后端自动翻译未翻译的标题

### 其他优化：
1. **Geolocation 优化**
   - 当前有 fallback，但可优化用户体验提示

2. **图片加载优化**
   - 可考虑使用 `next/image` 的优化功能

3. **Carousel 性能**
   - 大量卡片时可考虑虚拟滚动

## 七、部署状态

✅ 所有前端组件已创建
✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看重构后的首页。

## 八、验收检查

### ✅ 首页顺序正确（1→9）
- (1) 今日指标 banner
- (2) 股票资产
- (3) 科技行业 & 美国经济新闻
- (4) 今天提醒
- (5) 吃点好的
- (6) 肥宅快乐水
- (7) 遍地羊毛
- (8) 打发时间
- (9) 北美八卦

### ✅ 中文化完成
- 所有面向用户的文案尽量中文化
- 英文内容作为 fallback 或次要信息

### ✅ 信息密度高
- 每个 section 紧凑，无大块空白
- 只显示决策所需字段

### ✅ 链接不 404
- 所有点击行为都有明确的跳转目标
- Deals/Places/Gossip 都外链或内链正确

### ✅ 图片有 fallback
- 所有图片都有可靠的 fallback 机制
- 使用 SVG data URI 作为最终 fallback

