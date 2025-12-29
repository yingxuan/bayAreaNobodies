# 「今日必做 3 件事」模块升级总结

## A) 新增/修改文件列表

### 新增文件
1. **web/app/components/TodayActions.tsx** (新增)
   - 替换 `RiskStatusLight` 的新组件
   - 显示 3 条今日必做事项
   - 包含严重等级、原因、建议、截止时间
   - 全中文显示

### 修改文件
2. **api/app/services/risk_service.py** (修改)
   - 新增 `MOCK_ACTIONS`: Mock 数据种子（3 条）
   - 新增 `get_actions_cache_key()`: 获取 actions 缓存 key
   - 新增 `is_mostly_chinese_actions()`: 验证中文内容
   - 新增 `validate_action_item()`: 验证 action item 结构
   - 新增 `generate_actions_with_gemini()`: 使用 Gemini 生成今日必做
   - 新增 `fetch_today_actions()`: 获取今日必做（带缓存和降级）
   - 新增 `get_mock_actions_response()`: 返回 mock 数据

3. **api/app/routers/risk.py** (修改)
   - 新增 `GET /risk/today-actions` 端点
   - 导入 `fetch_today_actions`

4. **web/app/components/TodayBrief.tsx** (修改)
   - 替换 `RiskStatusLight` 为 `TodayActions`
   - 移除 `riskItems` 相关逻辑（不再需要）

## B) curl 示例

### 成功响应（Gemini）
```bash
curl -X GET "http://localhost:8000/risk/today-actions?city=cupertino" \
  -H "Accept: application/json"
```

**响应示例：**
```json
{
  "city": "cupertino",
  "date": "2025-12-29",
  "updatedAt": "2025-12-29T21:00:00.000000+00:00",
  "dataSource": "gemini",
  "stale": false,
  "ttlSeconds": 43200,
  "items": [
    {
      "title": "检查 401(k) rollover 截止时间",
      "why": "避免错过 60 天窗口导致税务后果",
      "action": "今天把旧账户的 rollover 流程和所需表格确认完",
      "deadline": "60 天内",
      "severity": "high",
      "links": []
    },
    {
      "title": "确认 HSA/FSA 账户余额和使用期限",
      "why": "FSA 通常年底清零，HSA 可累积但需合理规划",
      "action": "登录账户查看余额，规划剩余医疗支出",
      "deadline": "年底前",
      "severity": "medium",
      "links": []
    },
    {
      "title": "准备报税所需文件清单",
      "why": "提前准备可避免报税季手忙脚乱，确保不遗漏抵扣项",
      "action": "整理 W-2、1099、房贷利息、慈善捐赠等文件",
      "deadline": "1 月底前",
      "severity": "medium",
      "links": []
    }
  ],
  "disclaimer": "信息仅供参考，不构成税务/法律/投资建议。"
}
```

### Mock 降级响应
```json
{
  "city": "cupertino",
  "date": "2025-12-29",
  "updatedAt": "2025-12-29T21:00:00.000000+00:00",
  "dataSource": "mock",
  "stale": true,
  "ttlSeconds": 43200,
  "items": [
    {
      "title": "检查 401(k) rollover 截止时间",
      "why": "避免错过 60 天窗口导致税务后果",
      "action": "今天把旧账户的 rollover 流程和所需表格确认完",
      "deadline": "60 天内",
      "severity": "high",
      "links": []
    },
    {
      "title": "确认 HSA/FSA 账户余额和使用期限",
      "why": "FSA 通常年底清零，HSA 可累积但需合理规划",
      "action": "登录账户查看余额，规划剩余医疗支出",
      "deadline": "年底前",
      "severity": "medium",
      "links": []
    },
    {
      "title": "准备报税所需文件清单",
      "why": "提前准备可避免报税季手忙脚乱，确保不遗漏抵扣项",
      "action": "整理 W-2、1099、房贷利息、慈善捐赠等文件",
      "deadline": "1 月底前",
      "severity": "medium",
      "links": []
    }
  ],
  "disclaimer": "信息仅供参考，不构成税务/法律/投资建议。"
}
```

## C) 首页模块最终文案示例

### 模块展示结构
```
┌─────────────────────────────────────────────┐
│ 🧠 今日必做 3 件事    更新于 5 分钟前 [Mock] │
├─────────────────────────────────────────────┤
│ 🔴 检查 401(k) rollover 截止时间            │
│     避免错过 60 天窗口导致税务后果          │
│     ✅ 建议：今天把旧账户的 rollover 流程和 │
│         所需表格确认完                     │
│     ⏰ 截止：60 天内                        │
├─────────────────────────────────────────────┤
│ 🟡 确认 HSA/FSA 账户余额和使用期限          │
│     FSA 通常年底清零，HSA 可累积但需合理规划│
│     ✅ 建议：登录账户查看余额，规划剩余医疗 │
│         支出                                │
│     ⏰ 截止：年底前                         │
├─────────────────────────────────────────────┤
│ 🟡 准备报税所需文件清单                     │
│     提前准备可避免报税季手忙脚乱，确保不遗漏│
│     抵扣项                                  │
│     ✅ 建议：整理 W-2、1099、房贷利息、慈善 │
│         捐赠等文件                           │
│     ⏰ 截止：1 月底前                       │
├─────────────────────────────────────────────┤
│                             查看详情 →      │
└─────────────────────────────────────────────┘
```

### 每条内容结构
- **严重等级图标**：🔴 (high) / 🟡 (medium) / 🟢 (low)
- **标题**：粗体，一行显示
- **原因 (why)**：灰色小字，一行显示
- **建议 (action)**：绿色 "✅ 建议：" 前缀 + 具体行动
- **截止时间 (deadline)**：灰色 "⏰ 截止：" 前缀（如果有）

## D) 降级与缓存策略摘要

### 降级顺序
1. **Redis 缓存命中** → `dataSource: "cache"`, `stale: false`
2. **Gemini 成功** → 写入缓存 → `dataSource: "gemini"`, `stale: false`
3. **Gemini 失败但有 last-known-good** → `dataSource: "cache"`, `stale: true`
4. **全部失败** → Mock 数据 → `dataSource: "mock"`, `stale: true`

### 缓存策略
- **Redis Key**: `risk:actions:{city}:{YYYY-MM-DD}`
- **TTL**: 12 小时（43200 秒）
- **分布式锁**: `risk:actions:lock:{city}:{YYYY-MM-DD}` (30 秒)
- **同一天同城所有用户看到一致结果**

### 永不 500
- 所有异常都捕获并返回 mock 数据
- 即使 Gemini 失败、Redis 失败、JSON 解析失败，也返回 mock
- 前端组件有加载状态和空状态处理

## E) Gemini Prompt（完整版）

```
【系统要求】
你是面向旧金山湾区的资深工程师生活助理，只输出严格 JSON，不要输出多余文字。
【用户需求】
请给"旧金山湾区的码农"生成今天必须要做的 3 件事，要求：
- 全中文
- 每条都包含：title, why, action, deadline(可为空字符串), severity(high/medium/low)
- 偏实用：税务/财务/身份/工作/生活办事相关（例如 tax harvesting、报税准备、401k rollover、HSA/FSA、RSU vest、信用卡福利、租房/保险续期等）
- 避免违法或鼓励逃税；若涉及税务只给合规建议
- 不要泛泛而谈，不要"注意身体""多喝水"
- action 必须具体可执行（1 句）
输出 JSON schema：
{"items":[{"title":"","why":"","action":"","deadline":"","severity":""}]}
```

## F) 技术实现细节

### 后端验证
- **中文验证**: `is_mostly_chinese_actions()` 检查中文字符占比 ≥ 50%
- **字段验证**: `validate_action_item()` 检查必填字段和长度
- **严重等级**: 必须是 `high` / `medium` / `low`
- **JSON 解析**: 支持从 markdown code blocks 中提取 JSON

### 前端显示
- **Client Component**: 使用 `useState` 和 `useEffect` 获取数据
- **相对时间**: `formatRelativeTime()` 显示 "X 分钟前"
- **状态标识**: Mock/Stale badge 显示数据来源
- **空状态**: 如果数据为空，显示 mock 数据避免空白

### 数据流
1. 前端请求 `/risk/today-actions?city=cupertino`
2. 后端检查 Redis 缓存
3. 如果无缓存：
   - 调用 Gemini 生成 3 条事项
   - 验证 JSON 和中文内容
   - 如果不足 3 条，用 mock 补齐
   - 缓存结果 12 小时
4. 返回 JSON 响应
5. 前端渲染卡片列表

