# 首页信息架构重排 - 变更总结

## 一、目标
将首页最核心的 4 类信息做成两个紧凑的 Row（7/5 左文右视频），彻底消除空白和混乱。

## 二、最终页面结构

```
Home (page.tsx)
├── (1) CompactTopBar - 紧凑指标条（S&P/Gold/BTC/ARM/Powerball）
├── (2) TodayAlertBar - 今日提醒
├── (3) StockRow - 股票资产 Row（7/5 布局）
│   ├── 左（col-span-7）: StockSummaryCard
│   │   ├── 总资产：$X
│   │   ├── 今日涨跌：+$Y (+Z%)
│   │   ├── Top Movers（5 个 pill）
│   │   └── 一句话中文结论
│   └── 右（col-span-5）: YouTubeCarousel（美股分析视频）
│       └── 横向滚动 5 个视频卡
│
├── (4) TechRow - 科技新闻 Row（7/5 布局）
│   ├── 左（col-span-7）: TechCatalystNewsCard
│   │   ├── 3 条中文结论型新闻
│   │   ├── 每条：标题 + 来源/时间 + 影响 ticker pills
│   │   └── 轻分割线分隔
│   └── 右（col-span-5）: YouTubeCarousel（科技新闻解读视频）
│       └── 横向滚动 5 个视频卡
│
└── (5-9) 其他原有模块（保持不变）
    ├── PlaceCarousel（中餐）
    ├── PlaceCarousel（奶茶）
    ├── DealsCarousel
    ├── EntertainmentCarousel
    └── GossipCarousel
```

## 三、新增文件

### 前端组件
1. **`web/app/components/home/StockSummaryCard.tsx`**
   - 股票资产总结卡片（左 7）
   - 显示：总资产、今日涨跌、Top Movers、一句话结论
   - 数据来源：`GET /portfolio/db-summary`

2. **`web/app/components/home/TechCatalystNewsCard.tsx`**
   - 影响科技股要闻卡片（左 7）
   - 显示：3 条中文结论型新闻
   - 数据来源：`GET /tech/trending?source=hn&limit=4`
   - 使用 `generateWhatItMeans` 和 `extractChineseConclusion` 生成中文结论

3. **`web/app/components/home/YouTubeCarousel.tsx`**
   - 可复用的 YouTube 视频轮播组件（右 5）
   - 支持 stock 和 tech 两种类别
   - 固定高度：`min-h-[220px]`（桌面端）
   - 数据来源：`GET /youtube-channels/stock` 或 `/youtube-channels/tech`

4. **`web/app/components/home/StockRow.tsx`**
   - 股票资产 Row 容器
   - 7/5 布局：StockSummaryCard + YouTubeCarousel

5. **`web/app/components/home/TechRow.tsx`**
   - 科技新闻 Row 容器
   - 7/5 布局：TechCatalystNewsCard + YouTubeCarousel

### 工具文件
6. **`web/app/lib/i18nZh.ts`**
   - 简单英文到中文映射工具
   - `translateToChinese()`: 翻译常见术语
   - `extractChineseConclusion()`: 从英文标题提取中文结论

### 占位页面
7. **`web/app/videos/stocks/page.tsx`**
   - 美股分析视频页面占位（避免 404）

8. **`web/app/videos/tech/page.tsx`**
   - 科技新闻解读视频页面占位（避免 404）

9. **`web/app/portfolio/page.tsx`**
   - 重定向到 `/wealth`（避免 404）

## 四、修改文件

1. **`web/app/page.tsx`**
   - 替换 `StockAssetsWithVideos` → `StockRow`
   - 替换 `TechNewsWithVideos` → `TechRow`
   - 保持其他模块不变

## 五、关键样式点

### 布局
- **桌面端**：`lg:grid-cols-12`，左 7（`lg:col-span-7`），右 5（`lg:col-span-5`）
- **移动端**：自动堆叠（`grid-cols-1`），左在上右在下
- **Row 容器**：`gap-4`，左右等高（使用 `flex` 确保高度一致）

### 卡片样式
- **统一风格**：`rounded-xl border bg-white shadow-sm hover:shadow-md`
- **Header 高度**：`min-h-[44px]`（确保左右对齐）
- **紧凑间距**：`space-y-2`，`p-4`

### 视频 Carousel
- **固定高度**：`min-h-[220px]`（桌面端），`min-h-[200px]`（移动端）
- **横向滚动**：`overflow-x-auto scrollbar-hide`
- **视频卡尺寸**：`w-36`，缩略图 `h-20`
- **标题限制**：`line-clamp-2`

### 新闻列表
- **标题限制**：`line-clamp-2`（最多 2 行）
- **分割线**：`border-b border-gray-100`（最后一项无分割线）
- **Ticker Pills**：`bg-blue-50 text-blue-700`，最多 3 个

## 六、数据流

### StockSummaryCard
```
GET /portfolio/db-summary
  → total_value, day_gain, day_gain_percent, holdings[]
  → 计算 Top Movers（按绝对值排序）
  → 生成一句话结论（基于涨跌和 Top Movers）
```

### TechCatalystNewsCard
```
GET /tech/trending?source=hn&limit=4
  → items[] (title, title_cn, tags, url)
  → generateWhatItMeans() 或 extractChineseConclusion()
  → 过滤英文标题，提取影响 tickers
  → 显示 3 条中文结论型新闻
```

### YouTubeCarousel
```
GET /youtube-channels/stock?limit_per_channel=1
  → items[] (videoId, title, thumbnail, duration, channelTitle, url)
  → 显示 5 个视频卡（横向滚动）
```

## 七、约束遵守情况

✅ **桌面端布局**：`grid-cols-12`，左 7 右 5  
✅ **移动端堆叠**：自动改为 `grid-cols-1`  
✅ **紧凑设计**：固定高度、限制条数、无废话副标题  
✅ **中文优先**：所有可见文本中文，英文仅作为补充  
✅ **无 404**：所有链接都有对应页面（占位或真实）  
✅ **统一高度**：左右卡片等高（使用 `flex` 和 `h-full`）  
✅ **视觉饱满**：右侧 carousel 填满区域，固定高度

## 八、测试要点

1. **桌面端**：检查 7/5 布局是否正确，左右是否等高
2. **移动端**：检查是否自动堆叠，carousel 是否可横滑
3. **数据加载**：检查所有 API 调用是否正常，fallback 是否生效
4. **链接跳转**：检查所有 "更多 →" 链接是否正常（无 404）
5. **中文显示**：检查所有新闻标题是否为中文结论型
6. **视频播放**：检查视频点击是否正常跳转到 YouTube

## 九、后续优化建议

1. **后端 API**：考虑新增 `/tech/catalysts` endpoint，专门返回影响科技股的中文结论型新闻
2. **视频数据**：如果有 YouTube API key，可以替换 Google CSE 搜索，获取更准确的视频数据
3. **缓存优化**：考虑在客户端缓存视频数据，减少重复请求
4. **响应式优化**：进一步优化移动端视频卡尺寸和间距

