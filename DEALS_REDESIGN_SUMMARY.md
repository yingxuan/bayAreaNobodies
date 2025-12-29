# 羊毛专区卡片重构总结

## A) 修改文件列表

### 修改文件
1. **web/app/lib/i18n.ts** (修改)
   - 新增 `getDealCategory()`: 根据 title/description/tags 判断中文 Deal 类型
   - 新增 `generateDealTitle()`: 生成中文结论型标题，并提取省钱金额
   - 新增 `getDealMetadata()`: 提取补充信息（限时/长期、是否适合囤货、使用门槛）

2. **web/app/components/HomeSections.tsx** (修改)
   - 重写 `HomeDealsSection` 组件的卡片渲染逻辑
   - 新增分类标签显示
   - 新增显眼的省钱金额显示
   - 新增补充信息显示（限时、适合囤货、使用门槛）

## B) Before / After 示例

### Before（修改前）：
```
[卡片]
省钱：可叠加优惠（约 $7.80）
Save $7.80 on select item(s). Clip coupon for additional savings.
[category]
```

**问题：**
- 英文描述直接显示
- 省钱金额不够显眼
- 不知道是什么类型（食品/日用品等）
- 不知道是否限时、是否需要订阅

### After（修改后）：
```
[食品 / 零食] [限时]
可省约 $7.80（可叠加优惠）
可省 $7.80
─────────────────────────
适合囤货 | 需 Clip 优惠券
```

**改进：**
- ✅ 中文分类标签（食品 / 零食）
- ✅ 中文结论型标题（无英文）
- ✅ 省钱金额显眼显示（大号绿色字体）
- ✅ 补充信息清晰（限时、适合囤货、使用门槛）

## C) 核心功能实现

### 1. 中文 Deal 类型判断
基于 `title`、`description`、`tags` 关键词匹配：

- **食品 / 零食**: food, snack, cookie, candy, chocolate, coffee, tea, beverage, protein, bar, granola, nuts, chips, crackers, pasta, rice, sauce, condiment
- **日用品**: toilet, paper, tissue, soap, shampoo, toothpaste, detergent, cleaning, wipe, towel, bath, personal care
- **订阅服务**: subscribe, subscription, membership, prime, premium, trial, recurring
- **衣物 / 鞋帽**: clothing, clothes, shirt, pants, shoes, sneakers, jacket, coat, dress, apparel, fashion, wear
- **家庭用品**: home, furniture, kitchen, bedding, pillow, mattress, decor, appliance, tool, garden, outdoor
- **兜底**: 精选优惠

### 2. 中文结论型标题生成
规则示例：

- **"Save $X"** → `"可省约 $X（可叠加优惠）"`
- **"X% off"** → `"X% 折扣"`
- **"Subscribe & Save"** → `"订阅可叠加优惠"`
- **"Clip coupon"** → `"立减 X%（需 Clip 优惠券）"`
- **"Free shipping"** → `"免运费"`
- **无法解析** → `"限时优惠"` 或 `"限时优惠（可省约 $X）"`

### 3. 省钱金额显眼显示
- 位置：主标题下方
- 样式：`text-lg font-bold text-green-600`
- 格式：`可省 $X.xx` 或 `可省 约 X%`
- 若无法精确解析，显示 `约 $X` 或 `约 X%`

### 4. 补充信息生成
基于 `title` 和 `description` 关键词匹配：

- **限时判断**: limited, 限时, today only, flash sale, 24 hours, ends soon
- **适合囤货判断**: paper, tissue, detergent, cleaning, toilet, shampoo, toothpaste, snack, cookie, pasta, rice, coffee, tea（且不包含 perishable, fresh, produce, vegetable, fruit, meat, dairy）
- **使用门槛判断**:
  - `subscribe/subscription/membership` → `"需订阅"`
  - `clip/coupon/code/promo` → `"需 Clip 优惠券"`
  - 其他 → `"无门槛"`

## D) 卡片信息结构（2秒决策）

每条卡片现在包含：

1. **这是什么？** → 分类标签（食品/零食、日用品等）
2. **能省多少钱？** → 显眼的绿色金额（`可省 $X.xx`）
3. **值不值得现在点？** → 补充信息（限时、适合囤货、使用门槛）

**视觉层次：**
- 顶部：分类标签 + 限时标记（如有）
- 中部：中文标题 + **显眼的省钱金额**
- 底部：补充信息（小字、灰色分隔线）

## E) 验收标准

✅ **用户无需读英文即可理解**
- 所有主信息都是中文
- 英文只用于品牌名（如果有）

✅ **省钱金额显眼**
- 大号绿色字体
- 位置突出（标题下方）

✅ **2秒内能回答三个问题**
- 分类标签清晰
- 省钱金额显眼
- 补充信息完整

✅ **符合湾区码农快速决策习惯**
- 信息密度高
- 关键信息（金额）突出
- 补充信息（门槛）明确

## F) 技术实现细节

### 前端规则生成（无后端依赖）
- `getDealCategory()`: 基于关键词匹配判断类型
- `generateDealTitle()`: 基于模式匹配生成中文标题并提取金额
- `getDealMetadata()`: 基于关键词匹配提取补充信息
- 所有规则都是 deterministic（相同输入产生相同输出）
- 无外部 API 调用，纯前端逻辑

### 样式设计
- 分类标签：`bg-blue-50 text-blue-700`
- 限时标记：`bg-orange-50 text-orange-700`
- 省钱金额：`text-lg font-bold text-green-600`
- 补充信息：`text-xs text-gray-500` + 分隔线

### 数据流
1. 从 API 获取 deals（包含 title, description, tags）
2. 对每条 deal 生成：
   - 分类（`getDealCategory`）
   - 中文标题和金额（`generateDealTitle`）
   - 补充信息（`getDealMetadata`）
3. 渲染卡片，突出显示省钱金额

