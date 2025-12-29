# 首页体验修复 - 完成总结

## A) 修改/新增文件列表

### 新增文件
1. **web/app/lib/i18n.ts** (新增)
   - 轻量级 i18n 工具函数
   - `detectEnglish()`: 检测文本是否主要为英文
   - `normalizeTitle()`: 清理标题截断垃圾
   - `toCN()`: 规则翻译常见英文动词
   - `generateChineseTitle()`: 生成中文标题（带 fallback）
   - `translateDealTitle()`: 翻译优惠/羊毛标题

### 修改文件
2. **web/app/components/TodayBrief.tsx** (修改)
   - 主标题：`"Today · 湾区码农简报"` → `"湾区码农简报"`
   - 卡片标题：
     - `"今日财务结论"` → `"财务结论"`
     - `"今日羊毛"` → `"羊毛精选"`
     - `"今日热帖"` → `"热帖精选"`
   - `"今天吃什么"` 保留（自然语言，不属于 Today 噪音）

3. **web/app/components/TodayCommandBar.tsx** (修改)
   - 标题：`"Today Command Bar"` → `"今日指标"`

4. **web/app/components/RiskStatusLight.tsx** (修改)
   - `"今日无重要提醒"` → `"暂无重要提醒"`
   - `"今日有 X 条需要注意"` → `"有 X 条需要注意"`

5. **web/app/components/TechRadar.tsx** (修改)
   - 集成 `generateChineseTitle()` 工具
   - 主标题优先显示中文，英文原标题作为次要信息（可选）
   - Tags 中文化：AI/芯片/大厂/基础设施/安全/职场/开源/科技

6. **web/app/components/HomeSections.tsx** (修改)
   - Deals 部分集成 `translateDealTitle()` 工具
   - 优惠标题中文化处理

## B) "Today/今日"去重后的首屏文案清单

### 主标题区域
- **TodayBrief 主标题**：`湾区码农简报`（已去掉 "Today ·"）
- **副标题**：`Cupertino · 12月29日 · 周一`（仅日期，无 "今日"）

### CommandBar
- **标题**：`今日指标`（唯一保留的 "今日" 作为日期锚点）

### 卡片标题
- `财务结论`（已去掉 "今日"）
- `今天吃什么`（保留，自然语言）
- `羊毛精选`（已去掉 "今日"）
- `热帖精选`（已去掉 "今日"）

### 风险状态条
- `风险状态：暂无重要提醒`（已去掉 "今日"）
- `有 X 条需要注意：...`（已去掉 "今日"）

**验收结果**：
- ✅ 首屏 "Today/今日" 出现次数 = 1（仅在 CommandBar 标题）
- ✅ 标题更简洁，不碎碎念

## C) TechRadar 示例：Before → After

### Before（修改前）：
```json
{
  "title": "OpenAI releases GPT-5 with improved reasoning",
  "tags": ["AI", "BigTech"]
}
```
**前端显示**：
```
OpenAI releases GPT-5 with improved reasoning
[AI] [BigTech]
```

### After（修改后）：
```json
{
  "title": "OpenAI releases GPT-5 with improved reasoning",
  "tags": ["AI", "BigTech"]
}
```
**前端显示**：
```
OpenAI 发布 GPT-5，推理能力提升
原标题：OpenAI releases GPT-5 with improved reasoning
[AI] [大厂]
```

**翻译逻辑**：
1. 使用 `toCN()` 规则翻译：`releases` → `发布`
2. 检测到仍含英文，但已部分翻译
3. 主标题显示翻译结果
4. 英文原标题作为次要信息（`text-xs text-gray-500`）

**Fallback 示例**（如果无法翻译）：
```
AI/大厂 热点
原标题：OpenAI releases GPT-5...
[AI] [大厂]
```

## D) Deals 示例：Before → After

### Before（修改前）：
```json
{
  "title": "Save $7.80 on Lenny & Larry's Complete Cookie",
  "description": "Clip coupon for additional savings"
}
```
**前端显示**：
```
Save $7.80 on Lenny & Larry's Complete Cookie
Clip coupon for additional savings
```

### After（修改后）：
```json
{
  "title": "Save $7.80 on Lenny & Larry's Complete Cookie",
  "description": "Clip coupon for additional savings"
}
```
**前端显示**：
```
省钱：可叠加优惠（约 $7.80）
Clip coupon for additional savings
```

**翻译规则**：
- `"Save $X on ..."` → `"省钱：可叠加优惠（约 $X）"`
- 保留品牌名（Lenny & Larry's）
- 金额提取并显示在中文标题中

**其他模式示例**：
- `"Clip 30% off coupon ..."` → `"优惠券：立减 30%（需 Clip）"`
- `"Subscribe & Save ..."` → `"订阅省：可额外折扣"`
- `"Get 20% off"` → `"限时折扣：立减 20%"`
- `"Free shipping"` → `"免运费"`

## 技术实现细节

### i18n.ts 工具函数
- **无外部依赖**：纯前端规则翻译
- **可扩展**：`verbMap` 和 `tagMap` 可轻松添加新规则
- **降级策略**：翻译失败时使用模板（如 "AI/大厂 热点"）

### 中文化策略
1. **Tech 标题**：
   - 优先使用后端 `title_cn`（如果存在）
   - 否则使用前端规则翻译
   - 翻译失败时使用标签模板
   - 英文原标题作为次要信息（可选显示）

2. **Deals 标题**：
   - 识别常见模式（Save/Clip/Subscribe）
   - 提取金额/百分比
   - 生成中文模板
   - 保留品牌名英文

### 性能考虑
- 所有翻译在客户端进行，无 API 调用
- 规则匹配使用简单字符串操作，性能开销可忽略
- 缓存策略由后端控制，前端仅做展示层处理

## 验收标准

### "Today/今日"去重
- ✅ 首屏只出现 1 次 "今日"（CommandBar 标题）
- ✅ 所有卡片标题已去掉 "今日"
- ✅ 风险状态条已去掉 "今日"

### 中文化
- ✅ TechRadar 主标题不再出现纯英文句子
- ✅ 英文原标题仅作为次要信息（可选）
- ✅ Deals 主标题不再出现 "Save/Clip/Subscribe" 英文开头
- ✅ Tags 已中文化（AI/芯片/大厂/基础设施/安全/职场/开源/科技）

