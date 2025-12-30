# 🎬 今晚追什么 Carousel 实现总结

## 一、组件位置

**文件**：`web/app/components/EntertainmentCarousel.tsx`

**首页位置**：
- 放在「遍地羊毛」(7) 之后
- 「北美八卦」(9) 之前
- 即：第 8 个模块

## 二、模块结构

### 标题与副标题
- **标题**：🎬 今晚追什么
- **副标题**：yfsp.tv 最新更新 · 下班后轻松看

### Carousel 特性
- ✅ 横向滑动（使用 `CarouselSection` 通用组件）
- ✅ 支持"换一批"按钮（随机 shuffle）
- ✅ 与其他 carousel（吃点好的/肥宅快乐水）使用相同风格

## 三、Card 结构

每个 Card 包含：

1. **海报图片（poster）**
   - 优先使用 `item.poster`
   - Fallback：统一占位图（SVG data URI，深色背景 + 🎬 emoji）
   - 尺寸：`w-40 h-56`（与其他 carousel 一致）

2. **中文标题（优先）**
   - 显示：`item.title_cn || item.title`
   - 字体：`text-xs font-semibold`
   - 行数：`line-clamp-2`（最多 2 行）

3. **一行关键信息**
   - 电视剧：`更新至第 X 集`（来自 `episode_info`）
   - 电影：`最近上线` 或 `热度高`（来自 `episode_info`）
   - 字体：`text-xs text-gray-600`

4. **整卡可点击**
   - 点击行为：直接跳转到 yfsp.tv 对应详情页（外链）
   - 使用 `window.open(url, '_blank')`

## 四、数据源

### API 接口（待后端实现）
```
GET /entertainment/yfsp/latest?limit=12
```

**返回字段**：
```typescript
{
  items: [
    {
      id: number | string
      title: string          // 英文标题
      title_cn?: string      // 中文标题（优先显示）
      poster?: string        // 海报 URL（必须）
      type?: 'movie' | 'tv'  // 类型
      episode_info?: string  // 关键信息（"更新至第 X 集" / "最近上线"）
      link?: string          // yfsp.tv 详情页链接
      updated_at?: number    // 更新时间（用于排序）
      created_at?: number    // 创建时间（用于排序）
    }
  ]
}
```

### Mock 数据（当前使用）
- 6 条 mock 数据，包含：
  - 电视剧：最后生还者、继承之战、熊家餐厅
  - 电影：瞬息全宇宙、沙丘、奥本海默
- 所有 mock 数据都有 `poster`、`title_cn`、`episode_info`、`link`

### 数据获取逻辑
1. 优先尝试 API：`GET /entertainment/yfsp/latest?limit=12`
2. API 失败或返回空：fallback 到 mock 数据
3. 过滤：只显示有 `poster` 的 items
4. 排序：优先最近更新（`updated_at` 或 `created_at` 降序）

## 五、排序逻辑

1. **优先最近更新**
   - 使用 `updated_at` 或 `created_at` 降序排序
   - 确保最新内容在前

2. **无数据时随机**
   - 如果 API 返回空，使用 mock 数据
   - "换一批"时随机 shuffle

3. **必须有图片**
   - 过滤掉没有 `poster` 的 items
   - 确保所有卡片都有图片（或 fallback）

## 六、点击行为

### 跳转逻辑
```typescript
const url = item.link || item.url
if (url) {
  const fullUrl = url.startsWith('http') ? url : `https://yfsp.tv${url}`
  window.open(fullUrl, '_blank')
}
```

- 优先使用 `item.link`
- Fallback 到 `item.url`
- 确保是完整 URL（如果不是，添加 `https://yfsp.tv` 前缀）
- 新标签页打开（`_blank`）

## 七、样式一致性

### 与其他 Carousel 保持一致
- **卡片宽度**：`w-40`（与 PlaceCarousel 的 `w-48` 略有不同，但风格一致）
- **卡片高度**：海报 `h-56`，内容区 `p-2`
- **边框**：`border border-gray-200`
- **Hover**：`hover:shadow-md transition-all`
- **圆角**：`rounded-lg`

### 海报图片
- **尺寸**：`w-full h-56`（固定高度）
- **对象适配**：`object-cover`（保持比例，裁剪多余部分）
- **Fallback**：深色背景 SVG（`#1f2936`）+ 白色文字

## 八、Mobile App 扩展

### 保持 Carousel 通用性
- ✅ 使用 `CarouselSection` 通用组件
- ✅ 横向滚动结构，适合 mobile swipe
- ✅ 卡片尺寸可响应式调整

### Mobile 适配建议
1. **Swipe 手势**
   - 使用 `react-swipeable` 或原生 touch 事件
   - 支持左右滑动切换卡片

2. **卡片尺寸**
   - Desktop：`w-40`（160px）
   - Mobile：`w-32`（128px）或 `w-28`（112px）

3. **海报优化**
   - 使用 `next/image` 的 `priority` 和 `loading="lazy"`
   - 响应式图片尺寸（`srcSet`）

4. **点击区域**
   - 确保触摸区域足够大（≥ 44x44px）
   - 添加触摸反馈（ripple effect）

## 九、未来扩展

### 后端 API 实现建议
1. **数据抓取**
   - 定期抓取 yfsp.tv 最新列表
   - 缓存 TTL：12 小时
   - 使用 Redis 缓存

2. **翻译服务**
   - 使用 Gemini API 翻译英文标题
   - 缓存翻译结果（Redis key: `entertainment:title_cn:{title_hash}`）

3. **图片处理**
   - 验证 poster URL 有效性
   - 提供 CDN 代理（可选）

4. **排序优化**
   - 根据用户观看历史推荐
   - 根据热度（观看数/评分）排序

### 功能增强
1. **收藏功能**
   - 允许用户收藏想看的影视
   - 显示"已收藏"标记

2. **观看历史**
   - 记录用户点击的影视
   - 显示"已看过"标记

3. **个性化推荐**
   - 基于用户偏好推荐
   - 显示"为你推荐"标签

## 十、验收检查

### ✅ 位置正确
- 放在「遍地羊毛」之后
- 「北美八卦」之前

### ✅ 标题与副标题
- 标题：🎬 今晚追什么
- 副标题：yfsp.tv 最新更新 · 下班后轻松看

### ✅ Carousel 功能
- 横向滑动
- 支持"换一批"
- 样式与其他 carousel 一致

### ✅ Card 内容
- 海报图片（有 fallback）
- 中文标题（优先）
- 关键信息（更新至第 X 集 / 最近上线）
- 整卡可点击

### ✅ 点击行为
- 直接跳转到 yfsp.tv（外链）
- 新标签页打开

### ✅ 数据源
- 优先 API，fallback 到 mock
- 只显示有图片的 items
- 排序：最近更新优先

## 十一、部署状态

✅ 组件已创建并完善
✅ 已集成到首页（page.tsx）
✅ 构建成功
✅ 已部署到生产环境

访问 `http://localhost:3000` 查看新增的「🎬 今晚追什么」carousel。

