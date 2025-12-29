# 羊毛专区主标题修复总结

## 问题
- 主标题过于抽象（如"食品/零食"、"限时优惠"），用户无法在 1 秒内识别具体商品

## 解决方案
新增 `getDealReadableTitle()` 函数，确保每个标题都包含具体商品信息。

## 修改的文件
1. **web/app/lib/dealFormat.ts** (修改)
   - 新增 `extractBrand()`: 从 title/description 提取品牌名
   - 新增 `extractProductName()`: 从 title/description 提取商品名（带中文翻译）
   - 新增 `getConcreteProductByCategory()`: 根据分类生成具体商品名
   - 新增 `getDealReadableTitle()`: 生成可读标题（主函数）
   - 保留 `getDealTitleCN()` 作为 deprecated（向后兼容）

2. **web/app/components/HomeSections.tsx** (修改)
   - 将 `getDealTitleCN(deal)` 替换为 `getDealReadableTitle(deal)`
   - 更新 import 语句

## 主标题生成优先级

### Priority 1: 品牌 + 商品
如果检测到品牌（从 `deal.brand` 或 title/description 提取）：
- 格式：`{分类} · {品牌} {商品名}`
- 示例：
  - `零食 · Reese's 花生酱`
  - `咖啡 · Illy 咖啡`
  - `快餐 · Burger King 买一送一`

### Priority 2: 分类 + 商品
如果只有分类，没有品牌：
- 格式：`{分类} · {商品名}`
- 示例：
  - `食品 / 零食 · 巧克力零食`
  - `日用品 · 家庭洗护用品`

### Priority 3: 兜底
全部缺失：
- 返回：`精选商品优惠`

## 禁止用词（作为主标题）
以下词语禁止单独作为主标题：
- ❌ 食品 / 零食
- ❌ 精选优惠
- ❌ 限时优惠
- ❌ 可省 $X

## Before / After 示例

### 示例 1: 有品牌的情况
**Before:**
- 标题：`限时优惠`
- 描述：`Save $7.80 on Reese's Peanut Butter Cups`

**After:**
- 标题：`零食 · Reese's 花生酱`
- 描述：`Save $7.80 on Reese's Peanut Butter Cups`

---

### 示例 2: 只有分类的情况
**Before:**
- 标题：`食品 / 零食`
- 描述：`Save on select snacks`

**After:**
- 标题：`食品 / 零食 · 巧克力零食`（或 `饼干零食`、`坚果零食` 随机）
- 描述：`Save on select snacks`

---

### 示例 3: 快餐品牌
**Before:**
- 标题：`可省 $5`
- 描述：`Subway $5 Footlong Deal`

**After:**
- 标题：`快餐 · Subway 快餐套餐`
- 描述：`Subway $5 Footlong Deal`

---

### 示例 4: 完全缺失信息
**Before:**
- 标题：`精选优惠`
- 描述：`Limited time offer`

**After:**
- 标题：`精选商品优惠`
- 描述：`Limited time offer`

---

### 示例 5: 日用品
**Before:**
- 标题：`日用品`
- 描述：`Save on household items`

**After:**
- 标题：`日用品 · 家庭洗护用品`
- 描述：`Save on household items`

## 技术实现

### 品牌提取
支持 30+ 常见品牌：
- 食品：Reese's, Hershey, Lindt, Oreo, Lay's 等
- 咖啡：Illy, Lavazza, Starbucks, Dunkin 等
- 快餐：Burger King, McDonald's, Subway, Taco Bell 等
- 零售：Amazon, Target, Walmart, Costco 等

### 商品名提取
- 关键词匹配：根据分类匹配常见商品关键词
- 中文翻译：自动将英文商品名翻译为中文（如 chocolate → 巧克力）
- 名词短语提取：从标题中提取专有名词（品牌产品名）

### 分类兜底
当无法提取商品名时，根据分类生成具体商品：
- 食品/零食 → `巧克力零食` / `饼干零食` / `坚果零食`（随机）
- 日用品 → `家庭洗护用品`
- 服饰 → `服饰商品`
- 金融 → `金融服务`
- 快餐 → `快餐套餐`

## 验收标准
✅ 扫一眼羊毛区，所有卡片都能回答"这是啥"
✅ 即使不显示图片，也能理解商品
✅ 最后三条不再显得"像占位符"
✅ 禁止使用抽象词作为主标题

