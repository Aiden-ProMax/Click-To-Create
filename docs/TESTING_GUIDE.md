# 前端测试指南

## 快速开始

### 1️⃣ 启动应用

服务器已在后台运行 (`http://localhost:8000`)

**验证服务器状态：**
```bash
curl http://localhost:8000/
```

如果收到 HTML 响应，说明服务器正常。

---

## 📱 通过浏览器测试

### 步骤 1：访问首页并注册

1. 打开浏览器访问：**http://localhost:8000/**
2. 点击"注册"或导航到 **http://localhost:8000/login.html**
3. 填写注册表单：
   - 用户名：`testuser`
   - 邮箱：`test@example.com`
   - 密码：`TestPass123!`

### 步骤 2：登录

登录后进入 **Dashboard** 页面（首页）

**页面元素：**
- 顶部欢迎消息：`Good morning/afternoon/evening, testuser`
- 左上角输入框：用于输入自然语言或粘贴内容
- 右侧按钮：
  - 📎 上传文件（CSV/ICS）
  - ⚙️ 设置菜单
  - ✉️ 发送按钮

### 步骤 3：在 Dashboard 创建事件

#### 方式 A：手动通过表单创建（最简单）

1. 在 Dashboard 的输入框中输入示例：
   ```
   Tomorrow at 2pm team meeting for 1 hour in room A
   ```

2. 点击"发送"按钮（➤）

   > ⚠️ **当前状态**：前端会重定向到 `add_plan_backend.html`（确认页面）
   > 但该页面与 API 还未完全集成
   > 目前要求先直接跳到add_plan_backend.html界面，让用户手动输入

#### 方式 B：使用 API 直接创建事件（推荐测试）

打开浏览器开发者工具的 **Console** 标签，运行以下代码：

```javascript
// 获取 CSRF Token
async function createEventViaAPI() {
    // Step 1: Get CSRF token
    const csrfRes = await fetch('/api/auth/csrf/');
    const csrfData = await csrfRes.json();
    const csrfToken = csrfData.csrfToken;
    
    // Step 2: 规范化事件数据
    const normalizeRes = await fetch('/api/ai/normalize/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            events: [{
                title: 'Browser Test Meeting',
                date: 'tomorrow',
                start_time: '14:00',
                duration: '1.5h',
                location: 'Conference Room',
                category: 'meeting'
            }]
        })
    });
    
    const normalizeData = await normalizeRes.json();
    console.log('Normalize result:', normalizeData);
    
    if (!normalizeData.ok) {
        console.error('Normalization failed:', normalizeData.errors);
        return;
    }
    
    // Step 3: 创建事件
    const scheduleRes = await fetch('/api/ai/schedule/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            events: normalizeData.normalized_events
        })
    });
    
    const scheduleData = await scheduleRes.json();
    console.log('Schedule result:', scheduleData);
    
    if (scheduleData.ok) {
        console.log('✅ Events created successfully!');
        scheduleData.created_events.forEach(evt => {
            console.log(`  - ${evt.title} (ID: ${evt.id})`);
        });
    } else {
        console.error('Scheduling failed:', scheduleData.errors);
    }
}

// 执行
createEventViaAPI();
```

**预期输出：**
```
Normalize result: {ok: true, normalized_events: [...], errors: null}
Schedule result: {ok: true, created_events: [{id: X, title: "...", ...}], errors: null}
✅ Events created successfully!
  - Browser Test Meeting (ID: 8)
```

---

## 🔧 测试所有 API 端点（用 curl）

### 前置准备：获取认证

```bash
# 1. 获取 CSRF Token
CSRF=$(curl -s http://localhost:8000/api/auth/csrf/ | jq -r '.csrfToken')
echo "CSRF Token: $CSRF"

# 2. 注册新用户（如果还没有）
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -H "Cookie: csrftoken=$CSRF" \
  -d '{
    "username": "curltester",
    "email": "curl@test.local",
    "password": "TestPass123!",
    "first_name": "Curl",
    "last_name": "Tester"
  }'

# 3. 登录
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -H "Cookie: csrftoken=$CSRF" \
  -d '{
    "username": "curltester",
    "password": "TestPass123!"
  }' \
  -c cookies.txt

# 4. 刷新 CSRF Token（用于后续请求）
CSRF=$(curl -s http://localhost:8000/api/auth/csrf/ -b cookies.txt | jq -r '.csrfToken')
echo "Updated CSRF Token: $CSRF"
```

### API 测试命令

#### ✅ Test 1: Normalize 端点

```bash
CSRF=$(curl -s http://localhost:8000/api/auth/csrf/ | jq -r '.csrfToken')

curl -X POST http://localhost:8000/api/ai/normalize/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d '{
    "events": [
      {
        "title": "Team Standup",
        "date": "tomorrow",
        "start_time": "10:00",
        "duration": "30m",
        "location": "Zoom",
        "category": "meeting"
      },
      {
        "title": "Lunch Break",
        "date": "2026-02-07",
        "start_time": "12:00",
        "duration": 60
      }
    ]
  }' | jq '.'
```

**预期输出：**
```json
{
  "ok": true,
  "normalized_events": [
    {
      "title": "Team Standup",
      "date": "2026-02-06",
      "start_time": "10:00:00",
      "duration": 30,
      ...
    },
    {
      "title": "Lunch Break",
      "date": "2026-02-07",
      "start_time": "12:00:00",
      "duration": 60,
      ...
    }
  ],
  "errors": null
}
```

#### ✅ Test 2: Schedule 端点

```bash
# 使用上面 normalize 的输出
curl -X POST http://localhost:8000/api/ai/schedule/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d '{
    "events": [
      {
        "title": "API Created Event",
        "date": "2026-02-06",
        "start_time": "15:00:00",
        "duration": 90,
        "location": "Meeting Room",
        "description": "Test event via API",
        "participants": "alice@example.com,bob@example.com",
        "reminder": 30,
        "category": "meeting",
        "caldav_uid": null,
        "caldav_href": null,
        "google_event_id": null
      }
    ]
  }' | jq '.'
```

**预期输出：**
```json
{
  "ok": true,
  "created_events": [
    {
      "id": 12,
      "title": "API Created Event",
      "date": "2026-02-06",
      "start_time": "15:00:00",
      "duration": 90,
      "location": "Meeting Room",
      "created_at": "2026-02-05T04:20:00Z",
      ...
    }
  ],
  "errors": null
}
```

#### ✅ Test 3: 列出用户所有事件

```bash
curl -X GET http://localhost:8000/api/events/ \
  -H "X-CSRFToken: $CSRF" | jq '.'
```

#### ✅ Test 4: 检索单个事件

```bash
EVENT_ID=12  # 使用上面创建的事件 ID

curl -X GET http://localhost:8000/api/events/$EVENT_ID/ \
  -H "X-CSRFToken: $CSRF" | jq '.'
```

#### ✅ Test 5: 更新事件

```bash
EVENT_ID=12

curl -X PATCH http://localhost:8000/api/events/$EVENT_ID/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d '{
    "title": "Updated Meeting Title",
    "description": "Updated via API patch"
  }' | jq '.'
```

#### ✅ Test 6: 删除事件

```bash
EVENT_ID=12

curl -X DELETE http://localhost:8000/api/events/$EVENT_ID/ \
  -H "X-CSRFToken: $CSRF"

echo "Event deleted!"
```

---

## 🔌 Google Calendar 同步测试

### Step 1: 连接 Google Calendar

1. 登录 Dashboard
2. 点击右上角设置菜单 (⚙️)
3. 点击"Connect to Google Calendar"按钮
4. 将被重定向到 `http://localhost:8000/oauth/google/start/`
5. Google OAuth 授权页面（需真实 Google 账户）
6. 授予权限后回调到 `http://localhost:8000/oauth/google/callback`
7. 重定向回 Dashboard

### Step 2: 验证 Token 存储

打开 Django shell 检查：

```bash
python manage.py shell

from django.contrib.auth.models import User
from google_sync.models import GoogleOAuthToken

user = User.objects.get(username='testuser')
token = GoogleOAuthToken.objects.filter(user=user).first()

if token:
    print(f"✅ Token stored!")
    print(f"  Access Token: {token.access_token[:50]}...")
    print(f"  Refresh Token: {token.refresh_token}")
    print(f"  Scopes: {token.scopes}")
else:
    print("❌ No token found")

exit()
```

### Step 3: 同步事件到 Google Calendar

```bash
# 获取事件 ID
EVENT_ID=12

# 调用同步端点
curl -X POST http://localhost:8000/api/google/events/sync/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d "{
    \"event_id\": $EVENT_ID,
    \"calendar_id\": \"primary\"
  }" | jq '.'
```

**预期输出：**
```json
{
  "ok": true,
  "google_event_id": "abc123def456...",
  "htmlLink": "https://calendar.google.com/calendar/event?eid=...",
  "action": "insert"
}
```

### Step 4: 在 Google Calendar 中验证

登录 [Google Calendar](https://calendar.google.com)，查看事件是否出现在日历中。

---

## 🎯 完整集成测试场景

### 场景 1：从自然语言文本一步到 Google Calendar

```bash
#!/bin/bash

# 1. 登录
CSRF=$(curl -s http://localhost:8000/api/auth/csrf/ | jq -r '.csrfToken')

# 2. 规范化
NORMALIZE=$(curl -s -X POST http://localhost:8000/api/ai/normalize/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d '{
    "events": [{
      "title": "Important Meeting",
      "date": "next Friday",
      "start_time": "14:00",
      "duration": "2h",
      "location": "Office"
    }]
  }')

echo "Normalized: $NORMALIZE"

# 3. 创建事件
SCHEDULE=$(curl -s -X POST http://localhost:8000/api/ai/schedule/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d "{\"events\": $(echo $NORMALIZE | jq '.normalized_events')}")

EVENT_ID=$(echo $SCHEDULE | jq -r '.created_events[0].id')
echo "Event created with ID: $EVENT_ID"

# 4. 同步到 Google Calendar
SYNC=$(curl -s -X POST http://localhost:8000/api/google/events/sync/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d "{
    \"event_id\": $EVENT_ID,
    \"calendar_id\": \"primary\"
  }")

GOOGLE_ID=$(echo $SYNC | jq -r '.google_event_id')
echo "Synced to Google Calendar: $GOOGLE_ID"

echo "✅ Full pipeline completed!"
```

---

## 📊 测试检查清单

- [ ] **用户认证**
  - [ ] 注册新用户
  - [ ] 登录成功
  - [ ] Dashboard 显示用户名
  - [ ] 登出

- [ ] **事件 CRUD**
  - [ ] 创建事件 (POST /api/events/)
  - [ ] 列表事件 (GET /api/events/)
  - [ ] 检索单个 (GET /api/events/{id}/)
  - [ ] 更新事件 (PATCH /api/events/{id}/)
  - [ ] 删除事件 (DELETE /api/events/{id}/)

- [ ] **Normalize 流程**
  - [ ] 处理完整字段
  - [ ] 处理缺失字段（用默认值）
  - [ ] 相对日期解析（tomorrow, next friday）
  - [ ] 时长字符串解析 (1h, 90m)
  - [ ] 邮箱验证与清理
  - [ ] 错误处理（缺失标题）

- [ ] **Schedule 流程**
  - [ ] 创建单个事件
  - [ ] 批量创建事件
  - [ ] 更新现有事件

- [ ] **Google integration**
  - [ ] OAuth 授权流程
  - [ ] Token 存储验证
  - [ ] 事件同步到 Google Calendar
  - [ ] 验证 `google_event_id` 已保存

---

## 🐛 常见问题

### 问题 1：401 Unauthorized
**原因**：未认证或 CSRF Token 无效
**解决**：
1. 确保已登录
2. 获取新的 CSRF Token：`curl http://localhost:8000/api/auth/csrf/`
3. 在每个请求的 `-H "X-CSRFToken: $CSRF"` 中使用

### 问题 2：403 Forbidden
**原因**：权限不足或 CSRF 验证失败
**解决**：
1. 确保 `-H "X-CSRFToken: $CSRF"` 已包含
2. 确保 Content-Type 是 `application/json`

### 问题 3：Parse 端点返回 400
**原因**：`OPENAI_API_KEY` 未配置
**解决**：
1. 编辑 `.env` 文件
2. 添加：`OPENAI_API_KEY=sk-your-key-here`
3. 重启 Django 服务器

### 问题 4：Google 同步返回 403
**原因**：Google OAuth Token 无效或过期
**解决**：
1. 重新授权：访问 `/oauth/google/start/`
2. 检查 Django shell：`GoogleOAuthToken.objects.filter(user=user).first()`

---

## 📝 下一步前端改进

当前前端存在的问题 & 改进计划：

1. **前端 JS 不完整**
   - 现在：`processInput()` 只是简单重定向
   - 改进：实际调用 `/api/ai/normalize/` 和 `/api/ai/schedule/`

2. **缺失实时反馈**
   - 现在：用户输入后没有加载状态
   - 改进：显示进度条、成功/错误提示

3. **Google 连接 UI**
   - 现在：没有显示连接状态
   - 改进：按钮须显示"已连接"或"连接"状态

4. **事件列表视图**
   - 现在：Dashboard 未显示用户事件列表
   - 改进：在侧边栏显示今天/本周的事件

---

## 🚀 快速测试脚本

保存为 `quick_test.sh`：

```bash
#!/bin/bash

set -e

BASE_URL="http://localhost:8000"
CSRF=$(curl -s $BASE_URL/api/auth/csrf/ | jq -r '.csrfToken')

echo "📋 Running AutoPlanner Quick Test Suite"
echo "========================================"

# Test 1: Normalize
echo -e "\n[1/3] Testing Normalize endpoint..."
NORMALIZE=$(curl -s -X POST $BASE_URL/api/ai/normalize/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d '{"events": [{"title": "Test", "date": "tomorrow"}]}')

if echo "$NORMALIZE" | jq -e '.ok' > /dev/null; then
    echo "✅ Normalize: PASS"
else
    echo "❌ Normalize: FAIL"
    echo "$NORMALIZE" | jq '.'
fi

# Test 2: Schedule
echo -e "\n[2/3] Testing Schedule endpoint..."
SCHEDULE=$(curl -s -X POST $BASE_URL/api/ai/schedule/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d "{\"events\": $(echo "$NORMALIZE" | jq '.normalized_events')}")

if echo "$SCHEDULE" | jq -e '.ok' > /dev/null; then
    echo "✅ Schedule: PASS"
    EVENT_ID=$(echo "$SCHEDULE" | jq -r '.created_events[0].id')
    echo "   Event ID: $EVENT_ID"
else
    echo "❌ Schedule: FAIL"
    echo "$SCHEDULE" | jq '.'
fi

# Test 3: List Events
echo -e "\n[3/3] Testing Events List..."
LIST=$(curl -s -X GET $BASE_URL/api/events/ \
  -H "X-CSRFToken: $CSRF")

COUNT=$(echo "$LIST" | jq 'length')
echo "✅ Events List: PASS"
echo "   Total events: $COUNT"

echo -e "\n========================================"
echo "🎉 Test suite completed!"
```

运行：
```bash
chmod +x quick_test.sh
./quick_test.sh
```

---

## 📚 有用的链接

- 本地应用：http://localhost:8000
- Django Admin：http://localhost:8000/admin （用户名/密码需创建 superuser）
- API 文档：见 [docs/PROGRESS.md](docs/PROGRESS.md)
- 架构：见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
