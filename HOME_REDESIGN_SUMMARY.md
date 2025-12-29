# 首页"终极砍 + 重排"重构总结

## 一、新首页组件渲染树

```
Home (page.tsx)
├── TabNavigation
└── Container
    ├── Layer 1: State (10秒扫完)
    │   └── HomeOverview
    │       ├── TodayCommandBar (市场指标)
    │       └── OverviewLine (今日概览行)
    │
    ├── Layer 2: Decision (30秒决定)
    │   ├── FinancialStatusCard (财务状态卡 - 唯一显示资产数字的地方)
    │   └── TodayMustDo (今天必须做的3件事)
    │
    └── Layer 3: Entry (入口，不展示列表)
        └── EntryCards (6个入口卡)
            ├── 今天吃什么 (EntryCard)
            ├── 新开的奶茶 (EntryCard)
            ├── 今日羊毛 (EntryCard)
            ├── 最近可以追的 (EntryCard)
            ├── 科技 & 职业雷达 (EntryCard)
            └── 我的资产 (EntryCard)
```

## 二、修改/新增文件清单

### 新增文件：
1. `web/app/components/HomeOverview.tsx` - 层1：状态概览
2. `web/app/components/FinancialStatusCard.tsx` - 层2：财务状态卡（唯一显示资产数字）
3. `web/app/components/TodayMustDo.tsx` - 层2：今天必须做的3件事
4. `web/app/components/EntryCard.tsx` - 层3：通用入口卡组件
5. `web/app/components/EntryCards.tsx` - 层3：6个入口卡集合

### 修改文件：
1. `web/app/page.tsx` - 主页面，完全重构为三层结构
   - 移除了所有列表组件（HomePortfolioSection, HomeRestaurantSection, HomeDealsSection, HomeGossipSection, TechRadar）
   - 移除了 TodayBrief 组件

### 保留但未使用的文件（可后续清理）：
- `web/app/components/TodayBrief.tsx` - 已不再使用
- `web/app/components/HomeSections.tsx` - 列表组件已移除，但可能被其他页面使用

## 三、首屏自测验收

### ✅ 10秒内看到：总资产 + 今日涨跌（金额+百分比）
- **位置**：`FinancialStatusCard` 组件
- **显示内容**：
  - 总资产：$X,XXX,XXX（大字体）
  - 今日涨跌：+$Y,YYY（+Z.ZZ%）或 -$Y,YYY（-Z.ZZ%）
  - 一句结论（不重复数字）

### ✅ 30秒内看到：今天必须做的3件事
- **位置**：`TodayMustDo` 组件
- **数据来源**：`/risk/today-actions?city=cupertino`
- **显示格式**：Checklist 样式，每条最多1行
- **内容要求**：禁止抽象词，必须具体可执行

### ✅ 首页不再有任何完整列表
- **已移除**：
  - ❌ 餐厅图墙（HomeRestaurantSection）
  - ❌ 奶茶图墙（HomeRestaurantSection）
  - ❌ 羊毛6卡（HomeDealsSection）
  - ❌ 八卦列表（HomeGossipSection）
  - ❌ 科技新闻列表（TechRadar）
  - ❌ 资产持仓列表（HomePortfolioSection - 首页只显示入口）

### ✅ 英文内容明显减少，中文为主
- **TodayCommandBar**：市场指标（中文标签）
- **FinancialStatusCard**：全中文
- **TodayMustDo**：全中文（Gemini生成）
- **EntryCards**：
  - 今天吃什么：中文餐厅名 + 中文菜品名
  - 新开的奶茶：中文店名
  - 今日羊毛：中文格式化（品牌/商品 · 能省 $X · 门槛）
  - 科技 & 职业雷达：中文标题 + 中文摘要
  - 我的资产：中文描述

## 四、Mobile App 复用结构

### 可直接复用的组件：

1. **HomeOverview** → **Dashboard Widget**
   - TodayCommandBar：市场指标卡片组
   - OverviewLine：一行概览文本
   - 适合：iOS Widget / Android Widget

2. **FinancialStatusCard** → **Notification / Widget**
   - 总资产 + 今日涨跌
   - 适合：iOS Notification / Android Notification / Widget

3. **TodayMustDo** → **Notification / Widget**
   - 3个待办事项
   - 适合：iOS Notification / Android Notification / Widget

4. **EntryCard** → **Dashboard / Quick Actions**
   - 6个入口卡
   - 适合：iOS Dashboard / Android Quick Actions

### 数据结构复用：

```typescript
// 所有组件都使用统一的 API 响应格式
// 可以直接在 Mobile App 中复用相同的 API 调用逻辑

// 1. 市场指标
GET /market/snapshot
→ TodayCommandBar 数据

// 2. 资产状态
GET /portfolio/db-summary
→ FinancialStatusCard 数据

// 3. 今日必做
GET /risk/today-actions?city=cupertino
→ TodayMustDo 数据

// 4. 入口数据
GET /food/today-pick?city=cupertino
GET /food/restaurants?cuisine_type=boba&limit=1
GET /deals/food?city=cupertino&limit=1
GET /tech/trending?source=hn&limit=1
→ EntryCards 数据
```

## 五、关键约束遵守情况

### ✅ 不改后端 FastAPI 现有接口
- 所有组件都使用现有 API 端点
- 未破坏任何现有接口

### ✅ 不引入新第三方依赖
- 所有组件都使用现有依赖（React, Next.js, TailwindCSS）

### ✅ 首页只负责「状态 + 决策 + 入口」
- Layer 1: 状态（市场指标 + 概览）
- Layer 2: 决策（财务状态 + 今日必做）
- Layer 3: 入口（6个入口卡）

### ✅ 首页信息必须 30 秒内扫完
- 所有列表已移除
- 只显示关键数字和结论
- 入口卡只显示一行摘要

### ✅ 所有"列表 / 图墙"必须下沉到二级页
- 餐厅列表 → `/food`
- 羊毛列表 → `/deals`
- 八卦列表 → `/gossip`
- 科技新闻 → `/tech`
- 资产持仓 → `/wealth`

### ✅ 为未来 Mobile App 做结构准备
- 组件化设计，易于复用
- 统一的数据获取逻辑
- Widget/Notification 友好的数据结构

## 六、用户体验优化

### 信息层次：
1. **紧凑数字**（TodayCommandBar）
2. **一句结论**（OverviewLine + FinancialStatusCard 结论）
3. **可执行事项**（TodayMustDo）
4. **决策入口**（EntryCards）

### 视觉节奏：
- 所有卡片统一 CTA 文案："查看 →"
- 中文优先，英文只作为补充信息（小字）
- 统一的卡片样式和间距

### 去冗余：
- 资产数字只在 `FinancialStatusCard` 显示一次
- 不再有重复的"Today / 今日"标题
- 科技新闻不再显示长段落（入口卡只显示一行摘要）
- 羊毛卡片必须包含：品牌/商品 + 节省金额 + 门槛

## 七、后续优化建议

1. **娱乐内容**（最近可以追的）：
   - 当前为 Mock 数据
   - 建议：集成 `/feeds/gossip` 或新增娱乐内容 API

2. **奶茶新店检测**：
   - 当前只显示第一个结果
   - 建议：增加"新店"判断逻辑（基于开业时间或评分时间）

3. **科技雷达摘要**：
   - 当前使用 `generateWhatItMeans` 可能过长
   - 建议：优化为更简洁的摘要（60字符以内）

4. **资产数字格式化**：
   - 当前使用 `toLocaleString`
   - 建议：考虑添加 K/M/B 缩写（如 $1.2M）

## 八、部署状态

✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看新首页。

