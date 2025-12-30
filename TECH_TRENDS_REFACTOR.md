# 科技趋势模块重构总结

## 一、模块定义

### 模块标题
🧠 科技趋势 · 硅谷

### 副标题（可选）
数据来源：YouTube · 硅谷101
（如果视觉显得多余，可完全移除）

### 位置
- 放在「今晚追什么」之后
- 「北美八卦」之前

## 二、新组件或重构组件说明

### 后端组件

1. **`api/app/routers/tech_trends.py`** (新建)
   - 新增 `/tech-trends/channel` API 端点
   - 新增 `/tech-trends/context` API 端点
   - 使用 Google Custom Search 搜索 YouTube 频道视频
   - 支持 Redis 缓存（6小时）
   - Mock fallback 机制

2. **`api/main.py`** (修改)
   - 添加 `tech_trends` router 注册

### 前端组件

1. **`web/app/components/TechTrends.tsx`** (新建)
   - 左侧：Context Panel（背景说明）
   - 右侧：Video Carousel（视频列表）
   - 响应式布局（桌面端左右，移动端上下）
   - 工具型设计，无营销语言

## 三、Mock / API 数据结构

### 视频 API

**Endpoint**: `GET /tech-trends/channel?channel=硅谷101&limit=5`

**响应结构**:
```json
{
  "items": [
    {
      "videoId": "dQw4w9WgXcQ",
      "title": "硅谷最新动态：AI 芯片竞争加剧",
      "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
      "publishedAt": "2024-01-15T10:00:00",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
  ],
  "channel": "硅谷101",
  "total": 5,
  "dataSource": "youtube"
}
```

### Context API

**Endpoint**: `GET /tech-trends/context`

**响应结构**:
```json
{
  "context": {
    "background": "硅谷科技公司近期动态涉及AI芯片、云计算和人才市场变化。",
    "points": [
      "AI芯片竞争持续，NVIDIA、AMD等公司发布新产品",
      "云计算服务价格调整，影响企业技术选型",
      "湾区科技公司招聘和裁员情况出现波动"
    ],
    "domains": ["AI芯片", "云计算", "人才市场"]
  },
  "updatedAt": "2024-01-15T10:00:00"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `videoId` | string | YouTube 视频 ID（必需） |
| `title` | string | 视频标题 |
| `thumbnail` | string | 视频缩略图 URL（medium quality） |
| `publishedAt` | string | 发布时间（ISO 8601） |
| `url` | string | YouTube 视频完整 URL |
| `background` | string | 背景说明（一句陈述句，不超过80字） |
| `points` | string[] | 要点列表（2-3条，中性描述） |
| `domains` | string[] | 影响领域（可选） |

## 四、首页布局调整点

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
<EntertainmentCarousel />

{/* (9) 🧠 科技趋势 · 硅谷 */}
<TechTrends />  // ← 新增

{/* (10) 🗣 北美八卦 */}
<GossipCarousel />
```

### 位置确认
- ✅ 放在「今晚追什么」之后
- ✅ 「北美八卦」之前

## 五、响应式策略

### 桌面端（lg:）
- **布局**: 左右两栏（Grid 5列）
  - 左：Context Panel（2列，40%）
  - 右：Video Carousel（3列，60%）
- **间距**: `gap-6`

### 移动端（< lg）
- **布局**: 上下排列
  - 上：Context Panel（全宽）
  - 下：Video Carousel（全宽，横向滚动）
- **间距**: `mb-4`（Context Panel 底部间距）

### 实现代码

```tsx
<div className="lg:grid lg:grid-cols-5 lg:gap-6">
  {/* Left: Context Panel (40%) */}
  <div className="lg:col-span-2 mb-4 lg:mb-0">
    {/* Context content */}
  </div>

  {/* Right: Video Carousel (60%) */}
  <div className="lg:col-span-3">
    {/* Video carousel */}
  </div>
</div>
```

## 六、左侧 Context Panel 规则

### 内容结构
1. **一句背景说明**（陈述句）
   - 不使用第二人称（你）
   - 不出现"值得""建议""必须"等词
   - 总字数不超过 80 字

2. **2-3 条要点**（中性描述）
   - 使用项目符号（•）
   - 每条不超过 30 字
   - 不包含主观判断

3. **可选：影响范围**（领域枚举）
   - 使用标签样式
   - 最多 3-4 个领域

### 示例

```json
{
  "background": "硅谷科技公司近期动态涉及AI芯片、云计算和人才市场变化。",
  "points": [
    "AI芯片竞争持续，NVIDIA、AMD等公司发布新产品",
    "云计算服务价格调整，影响企业技术选型",
    "湾区科技公司招聘和裁员情况出现波动"
  ],
  "domains": ["AI芯片", "云计算", "人才市场"]
}
```

## 七、右侧 Video Carousel 规则

### 数据来源
- YouTube 频道：硅谷101
- 使用 Google Custom Search 搜索频道视频

### 数据规则
- 最近 3-5 条视频（根据 `limit` 参数）
- 按发布时间倒序
- 字段：`videoId`, `title`, `thumbnail`, `publishedAt`

### UI
- 横向滑动 carousel
- 每个卡片展示：
  - 视频封面（`h-32`）
  - 标题（最多 2 行，`line-clamp-2`）
  - 发布时间（相对时间，如"2 小时前"）

### 交互
- 点击 → 打开 YouTube 视频（新 tab）
- 移动端优先唤起 YouTube App（`vnd.youtube:` scheme）

## 八、强制约束执行

### ✅ 禁止营销式 subtitle
- 不使用"今天值得你花 X 分钟"
- 不使用"不该错过"
- 不使用"推荐""建议"等词

### ✅ 首页科技内容只保留这一处
- 移除其他科技相关模块（如 TechRadar）
- 统一到 TechTrends 模块

### ✅ 不使用 Hacker News
- 数据来源：YouTube 频道（硅谷101）
- 不依赖 Hacker News API

### ✅ 不生成冗长 AI 解读文本
- Context Panel 总字数不超过 80 字
- 要点列表简洁（每条不超过 30 字）
- 不包含长段落解释

## 九、技术实现细节

### 后端搜索逻辑

1. **Google Custom Search**
   - 搜索模式：
     - `"硅谷101" site:youtube.com`
     - `硅谷101 channel site:youtube.com`
     - `硅谷101 site:youtube.com`
   - 限制最近 30 天（`date_restrict="d30"`）
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
   - 并行请求视频和 Context
   - 错误处理：静默失败，使用默认值

2. **响应式布局**
   - 使用 Tailwind CSS Grid
   - 桌面端：`lg:grid-cols-5`（2:3 比例）
   - 移动端：单列堆叠

3. **视频 Carousel**
   - 横向滚动（`overflow-x-auto`）
   - 隐藏滚动条（CSS）
   - 卡片宽度：`w-56`

## 十、验收检查

### ✅ 功能完整性
- [x] 后端 API 正常工作
- [x] 前端组件正确渲染
- [x] 响应式布局正常
- [x] 点击跳转到 YouTube
- [x] 移动端优先唤起 App

### ✅ 内容质量
- [x] Context Panel 文字中性、简洁
- [x] 无营销语言
- [x] 视频列表按时间倒序
- [x] 视频封面清晰

### ✅ 用户体验
- [x] 加载状态显示
- [x] 空状态处理
- [x] 错误处理
- [x] 响应式布局流畅

### ✅ 约束遵守
- [x] 无营销式 subtitle
- [x] 首页科技内容只保留这一处
- [x] 不使用 Hacker News
- [x] 不生成冗长 AI 解读文本

## 十一、部署状态

✅ 后端 API 已创建
✅ 前端组件已创建
✅ 路由已注册
✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看新的「🧠 科技趋势 · 硅谷」模块。

