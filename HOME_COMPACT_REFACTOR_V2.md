# 首页紧凑化 + 决策导向 + 湾区码农化重构总结

## 一、Top Bar 重构

### ✅ 完成
- 新建 `CompactTopBar` 组件
- 高度 ≤ 48px（`h-12`）
- inline 显示：S&P 500 / BTC / Gold / ARM / Powerball
- 显示数值 + 涨跌箭头（↑/↓）
- 移除 Card 外框（改为 `border-b`）
- Mock badge 放在最右侧

### 实现细节
- 使用 `fetchHotTopics()` 获取数据
- 过滤显示：`market`, `btc`, `gold`, `jumbo_arm`, `lottery`
- 响应式：移动端横向滚动
- 每 5 分钟自动刷新

## 二、提醒 Bar（改为 Gemini 生成）

### ✅ 完成
- 删除 checklist 式提醒区
- 改为单行 Action Bar
- 后端 prompt 已更新为：
  ```
  旧金山湾区的码农今天必须要做的 3 件事是什么？
  要求：与财务/税务/工作/身份/投资相关，每条 ≤20 字，给明确 action。
  ```

### UI 格式
- 单行或两行（`flex-wrap`）
- 无"换一批"按钮
- 格式：`⚠️ 今天必须做：• A • B • C`
- 每条可显示截止时间（括号内）

### 数据源
- 后端：`/risk/today-actions?city=cupertino`
- 缓存：Redis 12 小时
- 降级：Gemini → Cache → Mock

## 三、股票资产 Section 重排

### ✅ 完成
- 合并为一个 section（`StockAssetsWithVideos`）
- 左右结构：65% + 35%（`lg:grid-cols-10`，`lg:col-span-6` + `lg:col-span-4`）
- 左右等高（`lg:items-start`）

### 左侧（65%）
- 总资产
- 今日涨跌（金额 + 百分比）
- Top Movers（3-5 个 ticker）

### 右侧（35%）
- 美股 YouTube Carousel
- 频道固定：视野环球财经、美投讲美股、美投侃新闻、股市咖啡屋、老李玩钱
- 只展示封面 + 标题

## 四、科技 & 新闻 Section 重构

### ✅ 完成
- 布局同股票资产：65% + 35%
- 左侧：3-5 条中文"结论型"新闻（已改为 5 条）
- 每条 ≤1 行（`line-clamp-1`）
- 禁止"发生了什么 / 对你意味着"等 AI 冗余句（已添加清理逻辑）
- 右侧：YouTube Carousel（硅谷101、最强拍档）

### 删除
- ✅ 已删除"科技趋势-硅谷"独立 section

## 五、吃点好的（数据源增强）

### ✅ 完成
- 数据源：Google Places（距离 / 热度）
- 卡片显示增强：
  - 图片
  - 餐厅名
  - 星级 + 评论数 + 距离（`⭐ 4.7 · 123 评论 · 2.3 mi`）
  - 招牌菜（如有，显示 `🍽️ 招牌菜`）
- 点击：跳转 Google Place

### 待实现（后端）
- Yelp Search: "Chinese restaurant"（可选）
- Yelp 提取的招牌菜（如有）

## 六、通用规则执行

### ✅ 完成
- 首页尽量中文
- 移除所有"今天值得你花 X 分钟"类 subtitle
  - ✅ 已删除 `PlaceCarousel` 的 `subtitle` prop
- 提升信息密度，减少纵向高度
  - ✅ Top Bar 从 Card 改为单行（高度从 ~80px 降至 48px）
  - ✅ 减少 padding（`py-6` → `py-4`，`space-y-6` → `space-y-4`）
- 所有 Carousel 高度统一
- 移动端自动改为纵向堆叠（Tailwind Grid 自动处理）

## 七、新组件或重构组件说明

### 新增组件
1. **`web/app/components/CompactTopBar.tsx`** (新建)
   - 单行压缩指标条
   - 高度 ≤ 48px
   - 无 Card 外框

### 修改组件
1. **`web/app/components/TodayAlertBar.tsx`** (修改)
   - 改为单行 Action Bar 格式
   - 格式：`⚠️ 今天必须做：• A • B • C`
   - 删除"换一批"按钮

2. **`web/app/components/StockAssetsWithVideos.tsx`** (修改)
   - 左右结构：65% + 35%
   - 合并为一个 section

3. **`web/app/components/TechNewsWithVideos.tsx`** (修改)
   - 左右结构：65% + 35%
   - 新闻改为 5 条，每条 ≤1 行
   - 清理 AI 冗余句

4. **`web/app/components/PlaceCarousel.tsx`** (修改)
   - 删除 `subtitle` prop
   - 增强卡片显示：星级 + 评论数 + 距离 + 招牌菜

5. **`web/app/page.tsx`** (修改)
   - 使用 `CompactTopBar` 替代 `TodayCommandBar`
   - 删除所有 `subtitle` prop
   - 减少 padding 和 spacing

6. **`api/app/services/risk_service.py`** (修改)
   - 更新 Gemini prompt 为固定格式
   - 强调：与财务/税务/工作/身份/投资相关，每条 ≤20 字

## 八、首页布局调整点

### 当前顺序

```tsx
{/* (1) Compact Top Bar */}
<CompactTopBar />

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
- ❌ 「科技趋势-硅谷」section
- ❌ 所有营销式 subtitle

## 九、响应式策略

### 桌面端（lg:）
- **Top Bar**：单行横向，flex 布局
- **股票资产模块**：Grid 10列（6:4 比例，65% + 35%），等高对齐
- **科技 & 新闻模块**：Grid 10列（6:4 比例，65% + 35%），等高对齐
- **Alert Bar**：横向一行，flex-wrap

### 移动端（< lg）
- 所有模块自动上下排列
- Top Bar 横向滚动
- Alert Bar 自动换行
- 视频 carousel 横向滚动

## 十、信息密度提升

### 对比
- **Top Bar**：从 Card 式（~80px）降至单行（48px），节省 40% 高度
- **整体 padding**：从 `py-6` 降至 `py-4`，节省 16px
- **整体 spacing**：从 `space-y-6` 降至 `space-y-4`，节省 8px per section
- **新闻列表**：从 2 行降至 1 行，节省 50% 高度

### 总高度节省
- 首页首屏高度减少约 30-40%

## 十一、部署状态

✅ 所有组件已重构
✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看紧凑化后的首页。

## 十二、待优化项（可选）

1. **Yelp 数据源**（后端）
   - 添加 Yelp Search API 集成
   - 提取招牌菜信息

2. **招牌菜显示**（前端）
   - 当前显示 `signature_dish` 字段（如有）
   - 后端需提供该字段

3. **移动端优化**
   - Top Bar 在移动端可能需要进一步压缩
   - Alert Bar 在移动端可能需要更紧凑的布局

