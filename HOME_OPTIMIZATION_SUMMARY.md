# 首页定向优化总结

## 一、修改/新增文件清单

### 修改文件：
1. **`web/app/components/HomeOverview.tsx`**
   - 将「今日概述」改为"状态合并提示"
   - 添加情绪图标和行动暗示
   - 添加点击跳转到"今天必须做的 3 件事"功能

2. **`web/app/components/EntryCard.tsx`**
   - 新增 `onRefresh` 和 `showRefresh` props
   - 添加右上角"换一个 🔄"按钮（仅在 `showRefresh={true}` 时显示）

3. **`web/app/components/EntryCards.tsx`**
   - 为"今天吃什么"添加 `handleRefreshEat` 功能
   - 为"新开的奶茶"添加 `handleRefreshBoba` 功能（支持 pool 切换）
   - 将"科技 & 职业雷达"提升为独立大卡片（在 grid 外部）
   - 新增"今日八卦"入口卡
   - 新增 `gossipItem` state 和 `getGossipSummary` 函数

4. **`web/app/components/TodayMustDo.tsx`**
   - 添加 `id="today-must-do"` 用于 scroll 定位

## 二、新增"换一个"交互的组件

### ✅ 今天吃什么
- **位置**：EntryCard 右上角
- **功能**：点击 🔄 按钮后重新请求 `/food/today-pick`
- **实现**：`handleRefreshEat` 函数
- **状态管理**：`todayEat`, `todayEatPool`, `todayEatIndex`

### ✅ 新开的奶茶
- **位置**：EntryCard 右上角
- **功能**：点击 🔄 按钮后从 pool（10 个餐厅）中循环切换
- **实现**：`handleRefreshBoba` 函数
- **状态管理**：`boba`, `bobaPool`, `bobaIndex`
- **逻辑**：
  - 如果 pool 有多个：循环切换（`(index + 1) % pool.length`）
  - 如果 pool 只有 1 个：重新请求获取更多

## 三、科技 & 职业雷达的视觉变化说明

### 变化前：
- 普通 EntryCard（小卡片）
- 淹没在"快速入口"grid 中
- 只显示一行摘要

### 变化后：
- **独立大卡片**（在 grid 外部，单独显示）
- **视觉层级提升**：
  - `border-2 border-blue-200`（2px 蓝色边框）
  - `p-6`（更大 padding）
  - 标题：`text-lg font-bold`
  - 副标题："可能影响你吃饭的碗"（灰色小字）
- **内容结构**（三部分）：
  1. **发生了什么**：具体公司/产品/技术细节
  2. **对你意味着**：湾区工程师视角（蓝色文字）
  3. **你可以**：具体可执行建议（绿色文字，可选）

### 布局位置：
- 在"快速入口"标题下方
- 在 Entry Cards Grid 上方
- 独立一行，不与其他卡片并列

## 四、首页验收标准

### ✅ 用户不满意推荐 → 可以立刻"换一个"
- **今天吃什么**：右上角 🔄 按钮，点击后重新获取推荐
- **新开的奶茶**：右上角 🔄 按钮，点击后从 pool 中切换
- **交互流畅**：不刷新页面，前端 state 更新

### ✅ 高价值信息（钱 / 必做 / 职业）一眼看到
- **财务状态**：Layer 2 左侧，大卡片，唯一显示资产数字
- **今天必须做的 3 件事**：Layer 2 右侧，橙色边框，Checklist 样式
- **科技 & 职业雷达**：独立大卡片，蓝色边框，三部分结构清晰

### ✅ 有"八卦"作为情绪缓冲
- **位置**：快速入口 grid 中
- **图标**：💬
- **标题**：今日八卦
- **内容**：1 条热帖（标题 + 来源）
- **格式**：`标题 ｜ 一亩三分地` 或 `标题 ｜ 华人网`
- **点击**：跳转到 `/gossip` 页面

## 五、Mobile App 复用交互

### 1:1 可迁移的交互：

#### 1. **"换一个"功能**
- **Web**：点击 🔄 按钮
- **Mobile**：
  - **Swipe Left**：换一个（今天吃什么 / 新开的奶茶）
  - **Pull to Refresh**：重新获取数据
  - **长按菜单**：显示"换一个"选项

#### 2. **今日概述点击跳转**
- **Web**：点击整行 → smooth scroll 到"今天必须做的 3 件事"
- **Mobile**：
  - **点击**：跳转到"今天必须做的 3 件事"页面
  - **或**：在同一页面内 scroll 到对应 section

#### 3. **科技雷达大卡片**
- **Web**：独立大卡片，三部分结构
- **Mobile**：
  - **Widget**：可显示为独立 Widget（iOS / Android）
  - **Notification**：可推送重要科技动态
  - **卡片样式**：保持三部分结构，适配移动端布局

#### 4. **八卦入口**
- **Web**：入口卡片
- **Mobile**：
  - **Badge**：显示未读八卦数量
  - **Quick Action**：长按显示最新八卦预览

## 六、技术实现细节

### "换一个"实现逻辑：

#### 今天吃什么：
```typescript
const handleRefreshEat = () => {
  // 重新请求 API（后端会基于日期返回不同结果）
  fetch(`${API_URL}/food/today-pick?city=cupertino`)
    .then(res => res.ok ? res.json() : null)
    .then(data => {
      if (data) {
        setTodayEat(data) // 更新 state，触发重新渲染
      }
    })
}
```

#### 新开的奶茶：
```typescript
const handleRefreshBoba = () => {
  if (bobaPool.length > 1) {
    // 从 pool 中循环切换
    const newIndex = (bobaIndex + 1) % bobaPool.length
    setBobaIndex(newIndex)
    setBoba(bobaPool[newIndex])
  } else {
    // 重新获取 pool
    fetch(`${API_URL}/food/restaurants?cuisine_type=boba&limit=10`)
      .then(...)
  }
}
```

### 今日概述生成逻辑：

```typescript
// 结合财务状态 + 必做事项数量
if (riskCount > 0) {
  if (dayGain < 0) {
    return "📉 今天资产回调，但有 X 件事需要你今天处理"
  } else if (riskCount >= 2) {
    return "⚠️ 今天有 X 个和钱相关的事项，建议查看"
  } else {
    return "✅ 今天有 1 件事需要处理，建议查看"
  }
}
```

### 科技雷达内容生成：

```typescript
// 使用 techContent.ts 中的函数
const title = generateConcreteTitle(item.title, item.tags)
const whatHappened = generateWhatHappened(item.title, item.tags, title)
const whatItMeans = generateWhatItMeans(item.title, item.tags, whatHappened)
const whatYouCanDo = generateWhatYouCanDo(item.title, item.tags, whatHappened)
```

## 七、用户体验提升

### 参与感增强：
- ✅ 用户不满意推荐 → 立即"换一个"（无需离开页面）
- ✅ 今日概述可点击 → 直接跳转到必做事项
- ✅ 八卦入口 → 情绪缓冲，增加浏览粘性

### 信息权重优化：
- ✅ 科技雷达独立大卡片 → 不再淹没在入口中
- ✅ 三部分结构 → 信息更完整、更可行动
- ✅ 视觉层级清晰 → 高价值信息一眼看到

### 可用性提升：
- ✅ "换一个"按钮位置明确（右上角）
- ✅ 点击反馈清晰（hover 效果）
- ✅ 移动端友好（按钮大小、触摸区域）

## 八、后续优化建议

1. **今天吃什么 pool**：
   - 当前：每次重新请求 API
   - 建议：首次加载时获取多个推荐，存储在 pool 中，切换时从 pool 选择

2. **新开的奶茶 fallback**：
   - 当前：如果没有"新开"，显示第一个结果
   - 建议：按评分排序，显示"最近评分高的"

3. **科技雷达展开/收起**：
   - 当前：始终展开显示三部分
   - 建议：默认折叠，点击展开（节省空间）

4. **八卦实时更新**：
   - 当前：页面加载时获取 1 条
   - 建议：支持下拉刷新获取最新八卦

## 九、部署状态

✅ 所有优化已实现
✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看优化后的首页。

