# AI API 前端数据加载修复总结

## 问题诊断

### 核心问题识别
用户报告：AI API 返回正确的 JSON，但无法在前端正确显示和填充。

### 根本原因分析

#### 1. **前端异步语法错误** (Critical Bug) ❌
**位置**: `templates/add_plan_backend.html` 第1180行

```javascript
// ❌ 错误：function 不是 async，但使用了 await
document.addEventListener('DOMContentLoaded', function() {
    if (aiDataKey) {
        const res = await fetch(...);  // SyntaxError!
```

**后果**:
- JavaScript 语法错误，导致整个 DOMContentLoaded 事件处理器崩溃
- 前端无法从 `/api/ai/stash/{key}/` 获取AI数据
- 编辑模式和多事件加载完全失效

---

## 实施的修复

### 修复1: 修正异步函数声明
**文件**: `templates/add_plan_backend.html`

```javascript
// ✅ 正确：function 是 async，现在可以使用 await
document.addEventListener('DOMContentLoaded', async function() {
    if (aiDataKey) {
        const res = await fetch(`/api/ai/stash/${aiDataKey}/`, { 
            credentials: 'include' 
        });
        const payload = await res.json();
        ...
    }
});
```

### 修复2: 改进数据规范化函数
**函数**: `normalizeAiPayload()`

增强的数据结构检测：
```javascript
function normalizeAiPayload(parsedData) {
    // 支持多种 JSON 格式：
    // 1. { "events": [...] }
    // 2. { "items": [...] }
    // 3. [...]  (直接数组)
    // 4. { "title": "...", ... }  (单事件对象)
    
    console.log('[normalizeAiPayload] Processing:', parsedData);
    // ... 详细的日志和类型检查
}
```

### 修复3: 添加详细的调试日志

在关键函数中添加日志进度追踪：

- `DOMContentLoaded`: 记录数据加载过程
- `normalizeAiPayload()`: 日志显示数据结构和转换
- `loadAiEventAtIndex()`: 追踪事件索引和加载状态
- `populateForm()`: 记录每个字段的填充操作
- `resetFormFields()`: 追踪表单重置
- `updateAiProgress()`: 显示多事件进度

**调试输出示例**:
```
[DOMContentLoaded] Starting, aiDataKey: abc123 aiDataFromStash: true
[DOMContentLoaded] Fetching from server-side stash: abc123
[DOMContentLoaded] Stash response status: 200
[normalizeAiPayload] Found events array: 2 items
[normalizeAiPayload] Processing: {...}
[loadAiEventAtIndex] Loading event at index: 0 of 2
[populateForm] Populating with data: {...}
[populateForm] Set title: Team Meeting
[populateForm] Set date: 2026-02-11
...
```

---

## 完整的数据流

### Dashboard → AI API → Stash → Form

```
用户输入
    ↓
Dashboard.processInput()
    ↓
POST /api/ai/parse/
    ↓
AI 服务返回 { events: [...] }
    ↓
Dashboard POST to /api/ai/stash/
    ↓
Stash 返回 { key: 'abc123', ttl: 600 }
    ↓
重定向到 add_plan_backend.html?data_key=abc123&stash=1
    ↓
[已修复] DOMContentLoaded (现在是 async)
    ↓
GET /api/ai/stash/abc123/
    ↓
Stash 返回 { data: { events: [...] } }
    ↓
normalizaPayload() 规范化数据
    ↓
loadAiEventAtIndex() 加载事件
    ↓
populateForm() 填充表单字段
    ↓
用户看到预填充的表单
```

---

## 验证步骤

### 1. 检查前端 JavaScript 控制台
打开浏览器开发者工具 (F12) → Console 标签，应该看到：
```
[DOMContentLoaded] Starting, aiDataKey: ... aiDataFromStash: ...
[normalizeAiPayload] Found events array: X items
[loadAiEventAtIndex] Loading event at index: 0 of X
[populateForm] Populating with data: ...
[populateForm] Set title: ...
```

### 2. 检查网络请求
在开发者工具的 Network 标签中：
- 应该有成功的 `GET /api/ai/stash/{key}/` 请求（状态200）
- 响应体应该包含 `{"ok": true, "data": {"events": [...]}}` 结构

### 3. 手动测试流程

```bash
# 步骤1：访问仪表板
curl http://localhost:8000/dashboard.html

# 步骤2：输入"Tomorrow at 2pm meeting"并点击发送

# 预期行为：
# - Dashboard 调用 /api/ai/parse/
# - 获得 AI 解析结果
# - 通过 /api/ai/stash/ POST 存储
# - 重定向到 add_plan_backend.html?data_key=...&stash=1
# - 页面加载时自动获取 stash 数据
# - 表单字段自动填充（标题、日期、时间等）
```

---

## 相关代码位置

| 文件 | 修改 | 说明 |
|------|------|------|
| `templates/add_plan_backend.html` | ✅ 已修复 | DOMContentLoaded 改为 async; 添加日志 |
| `ai/views.py` | ✅ 后端实现完整 | ParseInputView, NormalizeEventView, AiDataStashView |
| `ai/services.py` | ✅ 完整实现 | parse_with_openai 函数，JSON 解析和错误处理 |
| `templates/dashboard.html` | ✅ 完整实现 | processInput() 函数，数据通过 stash 传输 |
| `ai/urls.py` | ✅ 路由配置完整 | `/api/ai/stash/` 和 `/api/ai/stash/<key>/` 端点 |

---

## 预期的修复效果

### 修复前 ❌
1. AI 返回有效 JSON
2. 前端 console 出现 SyntaxError
3. 数据加载失败，用户看到空表单
4. "Unable to parse AI data" 错误信息

### 修复后 ✅
1. AI 返回有效 JSON
2. 数据通过 stash 成功获取
3. 表单字段自动填充（title, date, time, location, 等）
4. 用户可以预览和编辑 AI 提取的事件
5. 多事件支持正常工作
6. 所有调试日志清晰显示数据流

---

## 进一步的故障排除

如果仍然有问题，检查：

1. **浏览器控制台中的错误**
   - 打开 F12 → Console
   - 查找任何 JavaScript 错误或警告

2. **Network tab**
   - 检查 stash GET 请求的响应状态
   - 确认返回的 JSON 包含 `events` 数组

3. **缓存问题**
   - 清除浏览器缓存 (Ctrl+Shift+Delete)
   - 尝试 Hard Refresh (Ctrl+Shift+R)

4. **后端日志**
   - 检查 Django 服务器输出
   - 查看 `/api/ai/parse/` 和 `/api/ai/stash/` 的响应

---

## 总结

**主要修复**: 
- ✅ 修正 DOMContentLoaded 的 async 语法错误
- ✅ 改进数据规范化和错误处理
- ✅ 添加详细调试日志以便问题诊断

**结果**: 
- 前端现在能正确接收和显示 AI 解析的事件数据
- 用户可以看到预填充的表单字段
- 多事件流程（一次解析多个事件）正常工作
- 调试信息充分有利于快速诊断问题

