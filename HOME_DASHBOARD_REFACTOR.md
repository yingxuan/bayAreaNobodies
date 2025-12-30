# 首页 Dashboard 重构总结

## 一、新首页模块结构说明

### 整体布局原则
- **左侧给判断，右侧给视频深度**
- 所有模块遵循左右结构（桌面端）
- 移动端自动改为上下结构

### 模块列表

1. **今日指标 banner** (TodayCommandBar)
   - 保持不变

2. **今天提醒** (TodayMustDo)
   - 独立模块
   - 显示 3 条必须做的任务

3. **股票资产 + 美股分析视频** (StockAssetsWithVideos)
   - 左 50%：股票资产（总资产、今日涨跌、Top Movers）
   - 右 50%：美股分析视频 carousel
   - 点击模块 → 跳转完整持仓页面

4. **科技 & 新闻 + 科技深度视频** (TechNewsWithVideos)
   - 左 40%：科技 & 美国经济新闻（3-5条短标题列表）
   - 右 60%：科技深度视频 carousel

5. **其他模块**（保持不变）
   - 🍜 吃点好的
   - 🧋 肥宅快乐水
   - 💰 遍地羊毛
   - 🎬 今晚追什么
   - 🗣 北美八卦

### 删除的模块
- ❌ 「科技趋势-硅谷」section（TechTrends）
- ❌ TodayDecisionZone（拆分为独立模块）

## 二、需要新增 / 删除的组件列表

### 新增组件

#### 后端组件
1. **`api/app/routers/youtube_channels.py`** (新建)
   - `/youtube-channels/stock` - 获取美股分析视频
   - `/youtube-channels/tech` - 获取科技深度视频
   - 支持多频道搜索
   - Redis 缓存（6小时）
   - Mock fallback 机制

#### 前端组件
1. **`web/app/components/YouTubeVideoCarousel.tsx`** (新建)
   - 可复用的 YouTube 视频 carousel 组件
   - 支持 `stock` 和 `tech` 两种类型
   - 横向滚动，显示封面/标题/时长/频道名

2. **`web/app/components/StockAssetsWithVideos.tsx`** (新建)
   - 股票资产 + 美股分析视频组合模块
   - 左 50% + 右 50% 布局

3. **`web/app/components/TechNewsWithVideos.tsx`** (新建)
   - 科技 & 新闻 + 科技深度视频组合模块
   - 左 40% + 右 60% 布局

### 修改组件

1. **`web/app/components/StockAssetsCard.tsx`** (修改)
   - 移除 Link 包装（由外层模块处理）
   - 保持原有数据展示逻辑

2. **`web/app/page.tsx`** (修改)
   - 删除 TechTrends 引用
   - 删除 TodayDecisionZone 引用
   - 添加新模块引用

### 删除组件

1. **`web/app/components/TechTrends.tsx`** (删除)
   - 整个「科技趋势-硅谷」section 已移除

2. **`web/app/components/TodayDecisionZone.tsx`** (保留但不再使用)
   - 拆分为独立模块

## 三、YouTube 数据获取方式

### 数据获取策略

**使用 Google Custom Search API**（search 方式）

原因：
- 不需要 YouTube Data API v3（避免配额限制）
- 可以搜索多个频道
- 通过频道名称搜索最新视频

### 实现方式

```python
# 搜索模式
search_query = f'"{channel_name}" site:youtube.com'
search_results = fetch_multiple_pages(
    query=search_query,
    site_domain="youtube.com",
    max_results=max_results * 3,
    date_restrict="d7"  # Last 7 days
)
```

### 频道列表

#### 美股分析频道（Stock Channels）
- 视野环球财经
- 美投讲美股
- 美投侃新闻
- 股市咖啡屋 Stock Cafe
- 老李玩钱

**规则**：
- 每个频道取最新 1 条视频
- 总共最多 5 条视频

#### 科技频道（Tech Channels）
- 硅谷101
- 最强拍档

**规则**：
- 每个频道取最新 3 条视频
- 总共最多 6 条视频
- 按发布时间倒序

### 缓存策略

- **Redis Key**: `youtube:channels:{category}:{channels_str}:{YYYYMMDD}`
- **TTL**: 6 小时
- **Fallback**: Mock 数据

## 四、桌面 / 移动端布局说明

### 模块 1：股票资产 + 美股分析视频

#### 桌面端（lg:）
```
┌─────────────────────────────────────────┐
│ 📈 股票资产                              │
├──────────────────┬──────────────────────┤
│ 股票资产 (50%)   │ 美股分析视频 (50%)    │
│                  │                      │
│ 总资产           │ [视频1] [视频2] ...   │
│ 今日涨跌         │                      │
│ Top Movers       │                      │
└──────────────────┴──────────────────────┘
```

**实现**:
```tsx
<div className="lg:grid lg:grid-cols-2 lg:gap-6">
  <div className="mb-4 lg:mb-0">
    <StockAssetsCard />
  </div>
  <div>
    <YouTubeVideoCarousel category="stock" />
  </div>
</div>
```

#### 移动端（< lg）
```
┌─────────────────────┐
│ 📈 股票资产          │
├─────────────────────┤
│ 股票资产             │
│ 总资产               │
│ 今日涨跌             │
│ Top Movers          │
├─────────────────────┤
│ 美股分析视频         │
│ [视频1] [视频2] ...  │
└─────────────────────┘
```

**实现**:
- 自动上下排列（`mb-4` 间距）
- 视频 carousel 横向滚动

### 模块 2：科技 & 新闻 + 科技深度视频

#### 桌面端（lg:）
```
┌─────────────────────────────────────────┐
│ 🧠 科技 & 新闻                          │
├──────────────┬──────────────────────────┤
│ 新闻 (40%)   │ 科技深度视频 (60%)        │
│              │                          │
│ • 新闻1      │ [视频1] [视频2] [视频3]   │
│ • 新闻2      │ [视频4] [视频5] [视频6]   │
│ • 新闻3      │                          │
│ • 新闻4      │                          │
│ • 新闻5      │                          │
│              │                          │
│ 查看更多 →    │                          │
└──────────────┴──────────────────────────┘
```

**实现**:
```tsx
<div className="lg:grid lg:grid-cols-5 lg:gap-6">
  <div className="lg:col-span-2 mb-4 lg:mb-0">
    {/* News list */}
  </div>
  <div className="lg:col-span-3">
    <YouTubeVideoCarousel category="tech" limit={6} />
  </div>
</div>
```

#### 移动端（< lg）
```
┌─────────────────────┐
│ 🧠 科技 & 新闻       │
├─────────────────────┤
│ 新闻列表             │
│ • 新闻1              │
│ • 新闻2              │
│ • 新闻3              │
│ 查看更多 →           │
├─────────────────────┤
│ 科技深度视频         │
│ [视频1] [视频2] ...  │
└─────────────────────┘
```

**实现**:
- 自动上下排列（`mb-4` 间距）
- 视频 carousel 横向滚动

## 五、全局约束执行

### ✅ 禁止营销式 subtitle
- 不使用"今天值得你花 X 分钟"
- 不使用"不该错过"
- 不使用"推荐""建议"等词

### ✅ 禁止 AI 生成冗长总结
- 新闻列表只显示标题 + 来源
- 不展开正文
- 不生成 AI 解读

### ✅ 首页只提供入口
- 不做内容解读
- 点击跳转原文或详情页
- 视频直接跳转 YouTube

### ✅ 视频模块统一为 carousel
- 所有视频模块使用 `YouTubeVideoCarousel`
- 横向滚动
- 统一样式和交互

### ✅ 移动端自动改为上下结构
- 使用 Tailwind CSS Grid
- `lg:` 前缀控制桌面端布局
- 移动端自动堆叠

## 六、API 数据结构

### 美股分析视频 API

**Endpoint**: `GET /youtube-channels/stock?limit_per_channel=1`

**响应**:
```json
{
  "items": [
    {
      "videoId": "dQw4w9WgXcQ",
      "title": "美股最新分析：科技股走势",
      "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
      "duration": "15:30",
      "channelTitle": "视野环球财经",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
  ],
  "channels": ["视野环球财经", "美投讲美股", ...],
  "total": 5,
  "dataSource": "youtube"
}
```

### 科技视频 API

**Endpoint**: `GET /youtube-channels/tech?limit_per_channel=3`

**响应**:
```json
{
  "items": [
    {
      "videoId": "jNQXAC9IVRw",
      "title": "硅谷最新动态：AI 芯片竞争",
      "thumbnail": "https://img.youtube.com/vi/jNQXAC9IVRw/mqdefault.jpg",
      "duration": "20:15",
      "channelTitle": "硅谷101",
      "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    }
  ],
  "channels": ["硅谷101", "最强拍档"],
  "total": 6,
  "dataSource": "youtube"
}
```

## 七、部署状态

✅ 后端 API 已创建
✅ 前端组件已创建
✅ 路由已注册
✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看重构后的首页 Dashboard。

