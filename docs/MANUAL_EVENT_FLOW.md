# 📝 手动创建事件完整指南

> 现在**无需 AI 解析**，直接手动填写事件信息！

---

## 🔄 新的事件创建流程

### 第一步：在 Dashboard 中输入

1. 打开 Dashboard：http://localhost:8000/dashboard.html
2. 在最上面的输入框输入任何内容
   - 例如：`Tomorrow at 2pm team meeting`
   - 或者：`My birthday party`
   - 或简单的：`Team sync`
3. 点击 **➤ 发送按钮**

### 第二步：自动跳转到事件编辑页面

1. 系统会**自动跳转**到事件编辑表单
2. 你的输入会自动填充在 **Title（标题）** 字段中
3. 现在你可以编辑所有字段

### 第三步：手动填写完整信息

填写表单的每个字段：

#### ✏️ 必填字段

- **Title** - 已由你的输入预填充
- **Date** - 输入格式：`YYYY-MM-DD`（例：`2026-02-05`）
- **Start time** - 输入格式：`HH:MM`（例：`14:00`）
- **Duration (minutes)** - 输入数字，例：`60`

#### 📌 可选字段

- **Location** - 会议地点或地址
- **Description/Notes** - 详细说明
- **Participants** - 参与人的邮箱（用逗号分隔）
- **Reminder** - 提前多久提醒（分钟）
- **Category** - 事件类型（Work/Personal/Meeting/Appointment/Other）

### ✅ 第四步：提交并创建

1. 检查所有信息无误
2. 点击 **Create** 按钮
3. 看到加载动画 ⏳

### 🎉 第五步：自动同步到 Google Calendar

1. 事件已保存到 AutoPlanner 数据库
2. 系统**自动同步**到你的 Google Calendar
3. 看到成功消息
4. **自动重定向**回 Dashboard

---

## 📊 完整的数据流图

```
┌─────────────────────────────────┐
│ 1. Dashboard 输入框             │
│ 输入：Tomorrow at 2pm meeting   │
└────────────┬────────────────────┘
             │ 点击➤
             ▼
┌─────────────────────────────────┐
│ 2. 直接跳转到编辑表单            │
│ Title 自动预填用户输入          │
└────────────┬────────────────────┘
             │ 用户手动编辑详情
             ▼
┌─────────────────────────────────┐
│ 3. 填写完整信息                 │
│ Date: 2026-02-05               │
│ Start time: 14:00              │
│ Duration: 60 minutes           │
│ Location: (可选)                │
└────────────┬────────────────────┘
             │ 点击 Create
             ▼
┌─────────────────────────────────┐
│ 4. POST /api/events/             │
│ 保存到数据库                    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 5. 自动同步到 Google Calendar   │
│ POST /api/google/events/sync/    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 6. 成功！重定向回 Dashboard      │
│ 现在可以创建下一个事件          │
└─────────────────────────────────┘
```

---

## 🧪 完整测试步骤

### 前置条件
- ✅ OAuth 已授权（Token 已保存）
- ✅ 服务器正在运行
- ✅ 已登入用户账户

### 测试场景 1：基本事件创建

```
输入信息：
- Dashboard 输入：Daily standup
- Date: 2026-02-04
- Start time: 10:00
- Duration: 30
```

**预期结果：**
- ✅ 自动跳转到编辑表单
- ✅ Title 显示 "Daily standup"
- ✅ 填写完所有字段后点击创建
- ✅ 看到成功提示
- ✅ 重定向回 Dashboard
- ✅ 在 Google Calendar 中能看到新事件

### 测试场景 2：包含所有字段的事件

```
输入信息：
- Dashboard 输入：Project kickoff meeting
- Title: Project kickoff meeting
- Date: 2026-02-10
- Start time: 14:00
- Duration: 90
- Location: Conference Room A
- Description: Initialize the new project
- Participants: team@example.com, manager@example.com
- Reminder: 15
- Category: Meeting
```

**预期结果：**
- ✅ 所有字段都被正确保存
- ✅ Google Calendar 中的事件包含所有信息
- ✅ 提醒设置生效

### 测试场景 3：日期和时间格式验证

尝试这些**无效的输入**（应该看到错误提示）：

```javascript
// 无效的日期格式
Date: "2026/02/04"  // ❌ 应该是 2026-02-04
Date: "Feb 4, 2026" // ❌ 应该是 2026-02-04

// 无效的时间格式
Start time: "2:00pm"   // ❌ 应该是 14:00
Start time: "14:00:00" // ❌ 应该是 14:00
```

**预期结果：**
- ✅ 表单显示红色错误边框
- ✅ 弹出错误提示
- ✅ 无法提交表单

---

## 🛠️ 故障排除

### ❌ 问题 1: 点击发送后页面无反应

**原因：** 输入框为空

**解决方案：**
1. 检查输入框是否有内容
2. 确保点击的是 ➤ 按钮（圆形按钮）

### ❌ 问题 2: 跳转到编辑表单后没有看到预填的 title

**原因：** 可能是 URL 参数传递有误

**排查步骤：**
1. 打开浏览器开发者工具（F12）
2. 查看 URL 栏，应该看到：`add_plan_backend.html?input=xxx&mode=manual`
3. 如果没有 `input` 参数，说明前端代码有问题

### ❌ 问题 3: 表单验证一直出错

**原因：** 日期或时间格式不正确

**检查清单：**
- Date 必须是：`YYYY-MM-DD` 格式（例：`2026-02-04`）
- Start time 必须是：`HH:MM` 格式（例：`14:00`）
- Duration 必须是数字（例：`60`，不能是 `1小时`）

### ❌ 问题 4: 提交后显示错误 "Failed to create event"

**可能的原因和解决方案：**

1. **CSRF Token 错误**
   ```bash
   # 检查浏览器的 Cookie 是否有 csrftoken
   # F12 → Application → Cookies → csrftoken 应该存在
   ```

2. **API 响应 404 或 500**
   ```bash
   # 检查服务器日志
   # 确保 Django 服务器仍在运行
   python manage.py runserver 0.0.0.0:8000
   ```

3. **用户未认证**
   ```bash
   # 确保已登入
   # 刷新页面，重新登录
   ```

### ❌ 问题 5: 事件已创建，但没有同步到 Google Calendar

**排查步骤：**
1. 登录 Django shell 检查事件是否存在：
   ```bash
   python manage.py shell
   from events.models import Event
   Event.objects.filter(user__username='test').last()
   ```

2. 检查 Google OAuth Token 是否有效：
   ```bash
   from google_sync.models import GoogleOAuthToken
   token = GoogleOAuthToken.objects.filter(user__username='test').first()
   print(token.access_token[:50])  # Should not be empty
   ```

3. 检查浏览器开发者工具的 Console，查看同步请求的响应

---

## ⚡ 快速参考

### 表单字段要求

| 字段 | 类型 | 格式 | 示例 | 必需 |
|------|------|------|------|------|
| Title | 文本 | 任意 | "Team meeting" | ✅ |
| Date | 文本 | YYYY-MM-DD | "2026-02-04" | ✅ |
| Start time | 文本 | HH:MM | "14:00" | ✅ |
| Duration | 数字 | 分钟 | 60 | ✅ |
| Location | 文本 | 任意 | "Room A" | ❌ |
| Description | 文本 | 任意 | "Discuss Q1 goals" | ❌ |
| Participants | 文本 | 邮箱逗号分隔 | "a@b.com,c@d.com" | ❌ |
| Reminder | 数字 | 分钟 | 15 | ❌ |
| Category | 下拉 | work/personal/meeting | "work" | ❌ |

### 支持的日期格式

✅ **支持的格式：**
- `2026-02-04` (ISO 8601)
- `2026-2-4` (自动转换)
- `02/04/2026` (美国格式)

❌ **不支持的格式：**
- `Feb 4, 2026`
- `4-Feb-2026`
- `2026/02/04`

---

## 📞 需要帮助？

如果遇到问题，检查：
1. 浏览器开发者工具（F12）的 Console 标签
2. 浏览器开发者工具的 Network 标签（查看 API 调用）
3. Django 服务器的终端输出

---

## 🎯 下一步

当这个流程完全验证后，你可以：

1. **启用 AI 解析**（需要 OpenAI API Key）
   - 这样用户就不需要手动填写所有字段
   - AI 会自动解析 "Tomorrow at 2pm team meeting" 并填充所有字段

2. **添加更多功能**
   - 事件重复/频繁
   - 批量导入（CSV/ICS 文件）
   - 冲突检测和自动重新安排

**现在开始测试手动事件创建吧！** 🚀
