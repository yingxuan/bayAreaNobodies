# 首页信息密度 + 视觉权重精修总结

## 一、修改/新增组件列表

### 修改文件：
1. **`web/app/components/FinancialStatusCard.tsx`**
   - 新增 `getTopMovers()` 函数
   - 新增「Top Movers」区域（显示波动最大的3个持仓）
   - 保持卡片高度不显著增加（紧凑布局）

2. **`web/app/components/EntryCards.tsx`**
   - 科技雷达卡片改为高密度单条卡
   - 今天吃什么/奶茶/羊毛卡片标题改为口语化
   - 新增 `extractEntity` helper 函数
   - 更新卡片 props（`highlightReason`, `imageHeight`）

3. **`web/app/components/EntryCard.tsx`**
   - 新增 `highlightReason` prop（显示推荐理由）
   - 新增 `imageHeight` prop（支持 `normal` / `large`）
   - 图片位置调整到顶部（更醒目）
   - 刷新按钮样式增强（更明显的 icon button）
   - 图片高度可配置（`h-24` / `h-32`）

## 二、财务状态卡 Top Movers 字段说明

### 数据来源：
- API: `GET /portfolio/db-summary`
- 字段：`holdings` 数组，每个 holding 包含：
  - `ticker`: 股票代码（如 "NVDA", "MSFT"）
  - `day_gain`: 今日涨跌金额（$）
  - `day_gain_percent`: 今日涨跌百分比（%）

### 排序逻辑：
```typescript
// 按 abs(day_gain) 降序排序
const sorted = holdings.sort((a, b) => {
  const absA = Math.abs(a.day_gain || 0)
  const absB = Math.abs(b.day_gain || 0)
  return absB - absA
})
// 只取前 3 个
return sorted.slice(0, 3)
```

### 显示格式：
- **第一列**：Ticker（如 "NVDA"）
- **第二列**：涨跌百分比（红/绿）+ 涨跌金额（$）
- **示例**：
  ```
  NVDA  -2.1%  (-$4,320)
  MSFT  +1.3%  (+$2,180)
  QQQ   -0.9%  (-$1,050)
  ```

### 交互：
- 点击任意一行 → 跳转到 `/wealth`（我的资产详情页）
- 点击"查看详情" → 同样跳转到 `/wealth`

### 视觉设计：
- 标题：`📊 今日波动最大的持仓`（小字，灰色）
- 每行：hover 背景色变化
- 颜色：绿色（涨）/ 红色（跌）
- 布局：紧凑，不显著增加卡片高度

## 三、科技雷达新布局的文字结构

### 旧布局（已废弃）：
- 大卡片，多行空白
- 标题 + 副标题 + 三部分内容
- 高度：约半屏

### 新布局（高密度单条卡）：
```
第一行（加粗）：
🧠 科技 / 职业雷达 · 今天值得你花 30 秒看的事  [查看详情 →]

第二行：
【Google】搜索结果直接显示 AI 生成的答案，不再只是链接列表

第三行（重点，蓝色）：
👉 SEO 价值下降，Prompt 能力更重要

第四行（可选，弱化，灰色小字）：
你可以考虑：在 Side Project 中尝试 AI 搜索集成，学习 Prompt 工程
```

### 视觉要求：
- **整体高度**：≤ "今天吃什么"卡（约 `p-4`，紧凑）
- **不留大块空白**：`space-y-1.5`（行间距小）
- **字号**：比普通入口略大（`text-sm`）
- **边框**：`border border-blue-200`（1px，不突出）
- **点击区域**：整卡可点击

### 内容生成逻辑：
1. **提取公司/主题**：从 title 中提取（如 "Google"）
2. **发生了什么**：`generateWhatHappened()` 生成
3. **对你意味着**：`generateWhatItMeans()` 生成（蓝色高亮）
4. **你可以考虑**：`generateWhatYouCanDo()` 生成（可选，灰色）

## 四、高点击预期卡片（主入口）

### 1. 🍜 不想做饭？吃这个
- **标题**：口语化（"不想做饭？吃这个"）
- **图片**：`imageHeight="large"`（`h-32`，更醒目）
- **推荐理由**：`highlightReason` 显示 "招牌流沙包 · ⭐ 4.6 · Cupertino"
- **刷新按钮**：明显的 icon button（带阴影、边框）
- **点击行为**：直接跳转 Google Maps

### 2. 🧋 今天可以试试的新奶茶
- **标题**：口语化（"今天可以试试的新奶茶"）
- **图片**：`imageHeight="large"`（`h-32`）
- **推荐理由**：`highlightReason` 显示 "⭐ 4.6 · Cupertino"
- **刷新按钮**：明显的 icon button
- **点击行为**：跳转到 `/food?cuisine_type=boba`

### 3. 💰 今天不薅就亏了的羊毛
- **标题**：口语化（"今天不薅就亏了的羊毛"）
- **图片**：`imageHeight="large"`（`h-32`）
- **推荐理由**：`highlightReason` 显示 "可省 $8 · BOGO" 或 "可省 $5 · 需 Clip"
- **Badge**：限时（蓝色背景）
- **点击行为**：跳转到 `/deals`

### 视觉增强细节：
- **图片位置**：顶部（`mb-3`），更抓眼
- **刷新按钮**：`bg-white shadow-sm border border-gray-200`（带阴影、边框）
- **标题**：`font-bold`（加粗）
- **推荐理由**：`text-xs text-gray-600`（小字，但可见）

## 五、验收标准检查

### ✅ 5 秒内能知道：

#### 1. 今天亏钱是因为哪几只
- **位置**：财务状态卡底部
- **显示**：Top 3 Movers（按波动金额排序）
- **格式**：`NVDA  -2.1%  (-$4,320)`
- **颜色**：红/绿一目了然

#### 2. 有没有一条科技信息值得我关注
- **位置**：Entry Cards Grid 上方（独立一行）
- **格式**：高密度单条卡，4 行结构
- **重点**：第三行蓝色高亮（"对你意味着"）
- **高度**：紧凑，不占空间

#### 3. 今天下班可以吃什么 / 喝什么 / 薅什么
- **位置**：Entry Cards Grid 中
- **标题**：口语化（"不想做饭？" / "今天可以试试" / "今天不薅就亏了"）
- **图片**：大图（`h-32`），顶部显示
- **推荐理由**：直接显示（招牌菜、评分、可省金额）

### ✅ 首页比现在：

#### 更"紧凑"
- 科技雷达：从半屏 → 单条卡（高度减少 60%+）
- Top Movers：紧凑布局，不增加卡片高度
- 图片统一：`h-32`（统一高度，视觉整齐）

#### 更"像给码农看的"
- **Top Movers**：直接显示 Ticker + 金额（码农最关心的）
- **科技雷达**：高密度信息，像 internal memo
- **口语化标题**：更生活化，不正式

#### 更适合未来改成 Mobile（这些卡可以直接变成 swipe）
- **卡片结构**：统一，适合 swipe
- **图片顶部**：移动端更友好
- **刷新按钮**：触摸友好（`p-2`，足够大）
- **高密度信息**：移动端不浪费空间

## 六、技术实现细节

### Top Movers 实现：
```typescript
const getTopMovers = () => {
  const holdings = portfolioData.holdings.filter(h => 
    h.day_gain !== null && h.ticker
  )
  const sorted = [...holdings].sort((a, b) => {
    const absA = Math.abs(a.day_gain || 0)
    const absB = Math.abs(b.day_gain || 0)
    return absB - absA
  })
  return sorted.slice(0, 3)
}
```

### 科技雷达高密度卡：
```typescript
// 提取公司/主题
const { company } = extractEntity(item.title)
const companyOrTheme = company || title.split(' ')[0] || '科技'

// 4 行结构
第一行：🧠 科技 / 职业雷达 · 今天值得你花 30 秒看的事
第二行：【{companyOrTheme}】{whatHappened}
第三行：👉 {whatItMeans}（蓝色高亮）
第四行：你可以考虑：{whatYouCanDo}（可选，灰色）
```

### 卡片增强：
```typescript
// EntryCard 新增 props
highlightReason?: string  // 推荐理由
imageHeight?: 'normal' | 'large'  // 图片高度

// 图片位置调整
{imageUrl && (
  <div className={`mb-3 rounded-lg overflow-hidden ${imageHeightClass}`}>
    <img ... />
  </div>
)}

// 刷新按钮增强
<button className="absolute top-2 right-2 p-2 rounded-full bg-white shadow-sm hover:bg-gray-50 hover:shadow-md transition-all border border-gray-200">
  <span className="text-base">🔄</span>
</button>
```

## 七、用户体验提升

### 信息密度提升：
- ✅ Top Movers：一眼看到"哪几只拖后腿/带我飞"
- ✅ 科技雷达：从半屏 → 单条卡，信息更集中
- ✅ 推荐理由：直接显示，不用猜测

### 视觉权重优化：
- ✅ 图片更大（`h-32`）：更抓眼
- ✅ 标题口语化：更生活化，更想点
- ✅ 刷新按钮明显：更容易发现

### 码农友好：
- ✅ Ticker 直接显示：不用翻译
- ✅ 金额 + 百分比：双重信息
- ✅ 高密度信息：像看代码注释

## 八、部署状态

✅ 所有优化已实现
✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看优化后的首页。

