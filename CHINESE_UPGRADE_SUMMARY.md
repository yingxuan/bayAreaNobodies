# 用户核心体验升级 - 完成总结

## A) 实际修改的文件列表

### 前端文件
1. **web/app/components/TodayBrief.tsx** (修改)
   - 资产显示格式改为中文：`总资产：$X,XXX,XXX | 今日涨跌：+$Y,YYY（+Z.ZZ%）| 解读型结论`
   - 改进 `generateFinancialConclusion()` 函数，生成更具体的中文解读

2. **web/app/components/TechRadar.tsx** (修改)
   - 优先显示 `title_cn`（中文翻译），fallback 到 `title`
   - 所有标题显示位置已更新

### 后端文件
3. **api/app/services/tech_trending_service.py** (修改)
   - 新增 `translate_title_to_chinese()` 函数，使用 Gemini 翻译英文标题
   - 在 `fetch_hn_stories()` 中为每个 story 添加 `title_cn` 字段
   - Tags 改为中文：`芯片`、`大厂`、`职场`、`开源`、`安全`、`基础设施`、`科技`

4. **api/app/services/risk_service.py** (修改)
   - Gemini prompt 强制要求中文输出（在 system 和 user prompt 中明确说明）
   - 新增 `is_mostly_chinese()` 函数检测中文内容
   - 更新 `validate_risk_item()` 函数，如果字段是英文则直接丢弃并降级

## B) 首页资产展示的最终文案示例

### TodayBrief「今日财务结论」大卡显示格式：

```
总资产：$1,234,567
今日涨跌：+$12,345（+1.01%）
资产小幅上涨，主要受美股上涨影响
```

或（下跌情况）：
```
总资产：$1,234,567
今日涨跌：-$5,678（-0.46%）
资产微跌，市场整体平稳
```

**三行固定格式：**
1. 第一行：`总资产：$X,XXX,XXX`（必须显示具体金额）
2. 第二行：`今日涨跌：+$Y,YYY（+Z.ZZ%）`（必须显示金额和百分比）
3. 第三行：中文解读型结论（例如："资产小幅上涨，主要受美股上涨影响"）

## C) TechRadar 项的「英文 → 中文」前后对比示例

### Before（修改前）：
```json
{
  "id": "hn_12345678",
  "title": "OpenAI releases GPT-5 with improved reasoning",
  "tags": ["AI", "BigTech"]
}
```
**前端显示**：`OpenAI releases GPT-5 with improved reasoning` [AI] [BigTech]

### After（修改后）：
```json
{
  "id": "hn_12345678",
  "title": "OpenAI releases GPT-5 with improved reasoning",
  "title_cn": "OpenAI 发布 GPT-5，推理能力提升",
  "tags": ["AI", "大厂"]
}
```
**前端显示**：`OpenAI 发布 GPT-5，推理能力提升` [AI] [大厂]

**翻译逻辑：**
- 后端使用 Gemini 翻译英文标题（如果可用）
- 保留公司名和技术术语的英文（如 OpenAI、GPT、NVIDIA）
- 翻译失败时 fallback 到原始标题
- 前端优先显示 `title_cn`，如果不存在则显示 `title`

## D) Gemini 返回英文时的降级说明

### Risk Service 中的英文检测与降级：

1. **Gemini Prompt 强制中文**：
   - System prompt 明确要求："**所有内容必须使用中文，禁止使用英文句子。**"
   - User prompt 强调："所有字段（title/why/who/action）必须使用中文"

2. **验证阶段检测英文**：
   - `is_mostly_chinese()` 函数检测文本是否主要为中文（>50% 中文字符）
   - `validate_risk_item()` 函数检查所有字段（title/why/who/action）
   - 如果任何字段主要是英文 → 直接丢弃该 item

3. **降级流程**：
   ```
   Gemini 返回 items
   ↓
   验证每个 item（检查中文）
   ↓
   如果所有 items 都被丢弃（因为英文）
   ↓
   返回 None
   ↓
   fetch_risk_today() 检测到 None
   ↓
   自动降级到 Mock 种子库（全部为中文）
   ```

4. **Mock 种子库保证**：
   - 所有 mock seeds 都是中文
   - 基于 day of year 轮换（1-2 条）
   - 始终可用，永不失败

**结果**：即使用户看到的是 mock 数据，也保证 100% 中文，不会出现英文句子。

## 验收标准检查

### 首页首屏检查：
✅ **总资产显示**：`总资产：$X,XXX,XXX`（具体金额，不是百分比）  
✅ **今日涨跌显示**：`今日涨跌：+$Y,YYY（+Z.ZZ%）`（金额 + 百分比）  
✅ **无需滚动**：首屏即可看到资产信息  
✅ **无需展开**：TodayBrief 大卡直接显示

### 语言检查：
✅ **首页资产信息**：100% 中文  
✅ **科技内容标题**：优先显示中文翻译（`title_cn`）  
✅ **Tags**：已改为中文（AI、芯片、大厂、职场、开源、安全、基础设施、科技）  
✅ **Risk 提醒**：Gemini 输出强制中文，英文内容自动丢弃并降级到 mock

## 技术实现细节

### 翻译实现：
- **Tech 标题翻译**：使用 Gemini API（如果可用），fallback 到原始标题
- **Risk 内容**：Gemini prompt 强制中文，验证阶段检测并丢弃英文内容
- **Tags**：直接改为中文映射（无需翻译）

### 降级策略：
- Tech 翻译失败 → 显示原始英文标题（但会尝试翻译）
- Risk Gemini 返回英文 → 丢弃并降级到中文 mock seeds
- 所有降级都保证不出现空白或错误

### 性能考虑：
- Tech 标题翻译：每个标题单独调用 Gemini（有缓存机制）
- 翻译失败不影响功能，只是显示原始标题
- Risk 验证在内存中进行，性能影响可忽略

