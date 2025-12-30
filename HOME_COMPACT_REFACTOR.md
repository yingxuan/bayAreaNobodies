# 首页紧凑化重构总结

## 一、删除 / 压缩的内容

### 1. 删除「今天市场发生了什么」区块
- ✅ 已删除标题和 Mock 标签
- ✅ 保留指标 banner（TodayCommandBar），但移除重复的标题

### 2. 「今日提醒」改为顶部横向 Alert Bar
- ✅ 新建 `TodayAlertBar` 组件
- ✅ 固定最多 3 条
- ✅ 删除"换一批"按钮
- ✅ 高度压缩为一行或两行
- ✅ 每条：图标 + 事项 + 截止时间 + 详情链接
- ✅ 样式：橙色背景，左侧边框，紧凑布局

## 二、股票资产（重排为左右结构）

### 布局
- ✅ 单一标题：「股票资产」
- ✅ 左右两列等高（`lg:items-start`）

### 左侧（主信息）
- ✅ 总资产
- ✅ 今日涨跌（金额 + 百分比）
- ✅ Top movers（3-5 个 ticker，已改为最多 5 个）

### 右侧（辅助信息）
- ✅ YouTube 横向 carousel
- ✅ 固定频道：视野环球财经、美投讲美股、美投侃新闻、股市咖啡屋 Stock Cafe、老李玩钱
- ✅ 每个频道取最新 1 条视频
- ✅ 展示：封面 + 标题 + 时长
- ✅ 点击打开 YouTube

## 三、科技 & 新闻（全中文 + 对齐）

### 左侧（文本列表）
- ✅ 3-5 条（已改为 5 条）
- ✅ 全中文标题
- ✅ 每条最多 2 行（`line-clamp-2`）
- ✅ 禁止使用"发生了什么 / 对你意味着什么"等 AI 冗余句（已添加清理逻辑）

### 右侧（视频）
- ✅ YouTube carousel
- ✅ 频道：硅谷101、最强拍档
- ✅ 最近视频优先

### 删除
- ✅ 已删除「科技趋势-硅谷」section（TechTrends）

## 四、遍地羊毛（重构卡片）

### 要求
- ✅ 所有 card 必须有图片（已有 `getDealImage` 逻辑）
- ✅ 优先展示快餐 / 日用品（已添加排序逻辑）
- ✅ 相同商品合并（已添加去重逻辑）

### 卡片结构
- ✅ 图片（必需）
- ✅ 分类 badge（快餐 / 日用品）
- ✅ 商品名 + 核心 deal
- ✅ 💰 可省 $X（已添加）
- ✅ 门槛信息（BOGO / 无门槛 / 需 App / 需 Clip）

## 五、北美八卦（增强信息量）

### 每条八卦卡片
- ✅ 标题
- ✅ 正文前 1-2 行预览（从 `summary` 或 `content` 提取）
- ✅ 回复数 / 热度（💬 回复数 + 🔥 热度）
- ✅ 目标：让用户"不点进去也知道在吵什么"

## 六、通用约束执行

### ✅ 首页所有文本尽量中文
- 科技新闻标题清理 AI 冗余句
- 所有 UI 文本已中文化

### ✅ 禁止营销式 subtitle
- 已删除"今天值得你花 X 分钟"类 subtitle
- 所有模块使用简洁标题

### ✅ 首页只做入口，不做长解读
- 新闻列表只显示标题 + 来源
- 不展开正文
- 视频直接跳转 YouTube

### ✅ 所有左右结构模块需高度对齐
- 使用 `lg:items-start` 确保对齐
- 统一使用 Grid 布局

### ✅ 移动端自动改为上下结构
- 使用 Tailwind CSS Grid
- `lg:` 前缀控制桌面端布局
- 移动端自动堆叠

## 七、新组件或重构组件说明

### 新增组件
1. **`web/app/components/TodayAlertBar.tsx`** (新建)
   - 顶部横向 Alert Bar
   - 压缩为 1-2 行
   - 最多 3 条提醒

### 修改组件
1. **`web/app/components/TodayCommandBar.tsx`** (修改)
   - 删除"今天市场发生了什么"标题
   - 保留指标显示

2. **`web/app/components/StockAssetsCard.tsx`** (修改)
   - 删除内部标题（由外层模块提供）
   - Top Movers 改为最多 5 个

3. **`web/app/components/TechNewsWithVideos.tsx`** (修改)
   - 新闻数量改为 5 条
   - 添加 AI 冗余句清理逻辑
   - 确保全中文标题

4. **`web/app/components/DealsCarousel.tsx`** (修改)
   - 添加分类 badge（快餐 / 日用品）
   - 添加 💰 可省 $X 显示
   - 优先展示快餐 / 日用品
   - 相同商品合并

5. **`web/app/components/GossipCarousel.tsx`** (修改)
   - 添加正文预览（1-2 行）
   - 添加回复数显示（💬）
   - 增强信息量

6. **`web/app/page.tsx`** (修改)
   - 删除 TechTrends 引用
   - 添加 TodayAlertBar
   - 更新模块顺序

## 八、首页布局调整点

### 当前顺序

```tsx
{/* (1) 今日指标 banner */}
<TodayCommandBar />

{/* (2) 今日提醒 - Alert Bar */}
<TodayAlertBar />

{/* (3) 股票资产 + 美股分析视频 */}
<StockAssetsWithVideos />

{/* (4) 科技 & 新闻 + 科技深度视频 */}
<TechNewsWithVideos />

{/* (5) 🍜 吃点好的 */}
<PlaceCarousel ... />

{/* (6) 🧋 肥宅快乐水 */}
<PlaceCarousel ... />

{/* (7) 💰 遍地羊毛 */}
<DealsCarousel />

{/* (8) 🎬 今晚追什么 */}
<EntertainmentCarousel />

{/* (9) 🗣 北美八卦 */}
<GossipCarousel />
```

### 删除的模块
- ❌ 「科技趋势-硅谷」section（TechTrends）
- ❌ 「今天市场发生了什么」标题（TodayCommandBar 内部）

## 九、响应式策略

### 桌面端（lg:）
- **股票资产模块**：Grid 2列（50% + 50%），等高对齐
- **科技 & 新闻模块**：Grid 5列（2:3 比例，40% + 60%），等高对齐
- **Alert Bar**：横向一行，flex-wrap

### 移动端（< lg）
- 所有模块自动上下排列
- Alert Bar 自动换行
- 视频 carousel 横向滚动

## 十、部署状态

✅ 所有组件已重构
✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看紧凑化后的首页。

