# YouTube 娱乐模块升级总结

## 一、模块定义

### 模块名称
🎬 今晚追什么

### 副标题
来自 YouTube · 最新电视剧 / 综艺

### 位置
- 放在「遍地羊毛」之后
- 「北美八卦」之前

## 二、新增/修改的组件列表

### 后端组件

1. **`api/app/routers/entertainment.py`** (新建)
   - 新增 `/entertainment/youtube` API 端点
   - 支持 `type=tv` (电视剧) 和 `type=variety` (综艺)
   - 使用 Google Custom Search 搜索 YouTube 视频
   - 支持 Redis 缓存（12小时）
   - Mock fallback 机制

2. **`api/main.py`** (修改)
   - 添加 `entertainment` router 注册

### 前端组件

1. **`web/app/components/EntertainmentCarousel.tsx`** (重构)
   - 从 yfsp.tv 改为 YouTube
   - 支持 TV 和 Variety 两种类型
   - 移动端优先唤起 YouTube App
   - 保持与餐厅/奶茶 carousel 一致的样式

## 三、新 API 字段说明

### 请求参数

**Endpoint**: `GET /entertainment/youtube`

**Query Parameters**:
- `type` (string, optional): `tv` (电视剧) 或 `variety` (综艺)，默认 `tv`
- `limit` (int, optional): 返回数量，默认 12，范围 1-20

**示例**:
```
GET /entertainment/youtube?type=tv&limit=8
GET /entertainment/youtube?type=variety&limit=8
```

### 响应结构

```json
{
  "items": [
    {
      "videoId": "dQw4w9WgXcQ",
      "title": "最新电视剧推荐 2024",
      "title_cn": "最新电视剧推荐 2024",
      "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
      "channelTitle": "电视剧频道",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "type": "tv"
    }
  ],
  "type": "tv",
  "total": 8,
  "dataSource": "youtube"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `videoId` | string | YouTube 视频 ID（必需） |
| `title` | string | 视频标题（英文/原始） |
| `title_cn` | string | 视频标题（中文，可选） |
| `thumbnail` | string | 视频缩略图 URL（medium quality: mqdefault.jpg） |
| `channelTitle` | string | 频道名称 |
| `url` | string | YouTube 视频完整 URL |
| `type` | string | 类型：`tv` 或 `variety` |

## 四、数据来源（YouTube）

### 搜索策略

1. **搜索词 1**: "最新电视剧" + `site:youtube.com`
2. **搜索词 2**: "最新综艺" + `site:youtube.com`

### 每个搜索词
- 取前 6-8 条视频（根据 `limit` 参数）
- 只保留有效视频（有 videoId 和 thumbnail）
- 去重（按 videoId）

### 后端实现

- **API**: `/entertainment/youtube?type=tv|variety`
- **搜索服务**: 使用 `app.services.google_search.fetch_multiple_pages`
- **缓存**: Redis key `entertainment:youtube:{type}:{YYYYMMDD}`，TTL 12小时
- **Fallback**: Mock 数据（当 Google CSE 不可用时）

## 五、UI / 交互要求

### Carousel 形式
- ✅ 横向滑动（与餐厅/奶茶 carousel 一致）
- ✅ 支持"换一批"（重新随机）
- ✅ 保持一致的样式和布局

### Card 结构
- ✅ 视频封面图（必需，使用 `mqdefault.jpg`）
- ✅ 中文标题（最多 2 行，超出截断 `line-clamp-2`）
- ✅ 一行小字（频道名，`line-clamp-1`）

### 点击行为
- ✅ 点击整卡 → 打开 YouTube 视频（新 tab）
- ✅ 移动端优先唤起 YouTube App（使用 `vnd.youtube:` scheme）

### 移动端优化

```typescript
// 移动端优先唤起 YouTube App
if (isMobile) {
  const appUrl = `vnd.youtube:${video.videoId}`
  window.location.href = appUrl
  // Fallback to web after short delay
  setTimeout(() => {
    window.open(youtubeUrl, '_blank')
  }, 500)
} else {
  window.open(youtubeUrl, '_blank')
}
```

## 六、内容克制要求

- ✅ 不展示长描述
- ✅ 不做播放页
- ✅ 首页只做"发现 + 跳转"
- ✅ 保持简洁，只显示标题和频道名

## 七、首页插入位置说明

### 当前顺序（`web/app/page.tsx`）

```tsx
{/* (1) 今日指标 banner */}
<TodayCommandBar />

{/* (2-4) 今日决策区 */}
<TodayDecisionZone />

{/* (5) 🍜 吃点好的 */}
<PlaceCarousel ... />

{/* (6) 🧋 肥宅快乐水 */}
<PlaceCarousel ... />

{/* (7) 💰 遍地羊毛 */}
<DealsCarousel />

{/* (8) 🎬 今晚追什么 */}
<EntertainmentCarousel />  // ← 这里

{/* (9) 🗣 北美八卦 */}
<GossipCarousel />
```

### 位置确认
- ✅ 放在「遍地羊毛」之后
- ✅ 「北美八卦」之前

## 八、后续如何扩展到 Mobile App

### 数据结构通用性

1. **API 响应结构**
   - 已标准化为 `{ items, type, total, dataSource }`
   - 字段清晰，易于 Mobile App 解析

2. **视频信息完整**
   - `videoId`: 可用于直接打开 YouTube App
   - `thumbnail`: 可用于显示封面
   - `url`: 可用于 WebView fallback

### Mobile App 集成建议

#### 1. Widget / Dashboard
```swift
// iOS Swift 示例
struct YouTubeVideoCard: View {
    let video: YouTubeVideo
    
    var body: some View {
        VStack {
            AsyncImage(url: video.thumbnail)
            Text(video.title_cn ?? video.title)
                .lineLimit(2)
            Text(video.channelTitle)
                .font(.caption)
        }
        .onTapGesture {
            // Open YouTube App
            if let url = URL(string: "vnd.youtube:\(video.videoId)") {
                UIApplication.shared.open(url)
            }
        }
    }
}
```

#### 2. Notification
- 可以推送"今晚追什么"推荐
- 包含视频标题、缩略图、直接跳转链接

#### 3. 数据同步
- 使用相同的 API 端点
- 缓存策略一致（12小时）
- 支持离线查看（缓存最近一次结果）

### API 兼容性

- ✅ RESTful API，易于 Mobile App 调用
- ✅ 支持 JSON 响应
- ✅ 错误处理完善（Mock fallback）
- ✅ 缓存机制（减少 API 调用）

## 九、技术实现细节

### 后端搜索逻辑

1. **Google Custom Search**
   - 使用 `fetch_multiple_pages` 获取多页结果
   - 限制最近 7 天（`date_restrict="d7"`）
   - 去重（按 videoId）

2. **视频 ID 提取**
   - 支持 `youtube.com/watch?v=VIDEO_ID`
   - 支持 `youtu.be/VIDEO_ID`
   - 验证 videoId 有效性

3. **缩略图生成**
   - 使用 YouTube 标准缩略图 URL
   - 格式：`https://img.youtube.com/vi/{videoId}/mqdefault.jpg`
   - Medium quality (320x180)

### 前端渲染逻辑

1. **数据获取**
   - 并行请求 TV 和 Variety 两种类型
   - 合并结果，去重
   - 限制显示 12 条

2. **错误处理**
   - API 失败时静默处理（不显示错误）
   - 空结果时不显示模块

3. **性能优化**
   - 图片懒加载（浏览器默认）
   - 缩略图错误时使用 fallback SVG

## 十、验收检查

### ✅ 功能完整性
- [x] 后端 API 正常工作
- [x] 前端组件正确渲染
- [x] 点击跳转到 YouTube
- [x] 移动端优先唤起 App
- [x] "换一批"功能正常

### ✅ 内容质量
- [x] 显示最新电视剧/综艺
- [x] 视频封面清晰
- [x] 标题中文优先
- [x] 频道名显示正确

### ✅ 用户体验
- [x] 加载状态显示
- [x] 空状态处理
- [x] 错误处理
- [x] 响应式布局

### ✅ 性能
- [x] Redis 缓存生效
- [x] API 响应时间合理
- [x] 前端渲染流畅

## 十一、部署状态

✅ 后端 API 已创建
✅ 前端组件已重构
✅ 路由已注册
✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看新的「🎬 今晚追什么」模块。

