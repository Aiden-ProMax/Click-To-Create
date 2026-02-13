# 🚀 快速测试指南 - 5分钟上手

## 前置条件

✅ 服务器已启动：http://localhost:8000
✅ 数据库已初始化
✅ 代码已更新

---

## 📱 通过浏览器测试（最简单）

### 第一步：注册账户

1. 打开浏览器：**http://localhost:8000/login.html**
2. 点击"Sign Up"或"Don't have an account? Sign up"
3. 填写注册表单：
   - **Username**: `testuser`
   - **Email**: `test@example.com`
   - **Password**: `TestPass123!`
4. 点击 **Register** 按钮

![注册流程](注册成功后会自动进入登录页)

### 第二步：登录

1. 输入刚才注册的用户名和密码
2. 点击 **Login** 按钮
3. **成功！** 进入 Dashboard 首页

![Dashboard首页](顶部显示欢迎信息，例如："Good morning, testuser")

---

## 🎯 测试事件创建（核心功能）

### 方式 1️⃣：在 Dashboard 中直接创建（推荐）

**步骤：**

1. 在首页中央的输入框中输入：
   ```
   Tomorrow at 2pm team meeting for 1 hour in room A
   ```

2. 点击右侧的 **➤ 发送按钮**

3. **观察结果：**
   - 右下角显示成功提示：✅ Created 1 event(s)!
   - 或者显示错误信息

![创建事件](https://placeholder-for-screenshot)

---

### 方式 2️⃣：使用浏览器控制台（更详细）

1. 在 Dashboard 按 **F12** 打开开发者工具
2. 点击 **Console** 标签
3. 复制以下代码粘贴并运行：

```javascript
// 完整的事件创建流程
(async function() {
    console.log('🚀 开始创建事件...');
    
    // 获取 CSRF Token
    const csrfRes = await fetch('/api/auth/csrf/');
    const csrfData = await csrfRes.json();
    const csrfToken = csrfData.csrfToken;
    console.log('✅ CSRF Token 已获取');
    
    // Step 1: 规范化
    const normalizeRes = await fetch('/api/ai/normalize/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            events: [{
                title: 'Console Test Meeting',
                date: 'tomorrow',
                start_time: '14:00',
                duration: '1h',
                location: 'Meeting Room',
                category: 'meeting'
            }]
        })
    });
    
    const normalizeData = await normalizeRes.json();
    console.log('✅ Normalize 完成:', normalizeData.normalized_events[0]);
    
    // Step 2: 创建事件
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
    const event = scheduleData.created_events[0];
    
    console.log('✅ Event 已创建!');
    console.log('  Event ID:', event.id);
    console.log('  Title:', event.title);
    console.log('  Date:', event.date);
    console.log('  Start:', event.start_time);
    console.log('  Duration:', event.duration, 'min');
    
    // Step 3: 列出所有事件
    const listRes = await fetch('/api/events/', {
        headers: { 'X-CSRFToken': csrfToken }
    });
    const events = await listRes.json();
    console.log(`✅ 用户总共有 ${events.length} 个事件`);
})();
```

**预期输出：**
```
🚀 开始创建事件...
✅ CSRF Token 已获取
✅ Normalize 完成: {title: "Console Test Meeting", date: "2026-02-06", start_time: "14:00:00", ...}
✅ Event 已创建!
  Event ID: 12
  Title: Console Test Meeting
  Date: 2026-02-06
  Start: 14:00:00
  Duration: 60 min
✅ 用户总共有 5 个事件
```

---

### 方式 3️⃣：使用快速示例（最快）

1. 在 Dashboard 首页，向下滑到"Quick examples"
2. 点击任意示例卡片，例如：
   - ✅ "Team stand-up tomorrow at 10am"
   - ✅ "Work out every Friday at 5pm for 1 hour"
3. 输入框会自动填充文本
4. 点击➤按钮发送
5. 事件创建成功！

---

## 🧪 测试用例清单

### ✅ 用户认证
- [ ] 注册新用户
- [ ] 使用注册的账号登录
- [ ] Dashboard 显示用户名
- [ ] 在设置菜单中点击 Sign Out

### ✅ 事件创建（各种输入）
- [ ] 完整的事件描述：`"Tomorrow at 3pm meeting for 1 hour"`
- [ ] 只有标题：`"Team Standup"`
- [ ] 相对日期：`"Next Friday at 2pm"`
- [ ] 时长字符串：`"30 min appointment"`
- [ ] 邮箱：`"Call alice@example.com tomorrow"`

### ✅ 验证规范化逻辑
- [ ] 缺失的字段使用默认值
- [ ] 相对日期被正确解析
- [ ] 时长格式正确转换

### ✅ 事件管理
- [ ] 列表显示所有创建的事件
- [ ] 可以更新事件（修改标题、时间等）
- [ ] 可以删除事件

---

## 🔗 快速链接

| 功能 | URL | 说明 |
|------|-----|------|
| 首页/注册 | http://localhost:8000/login.html | 登录和注册 |
| Dashboard | http://localhost:8000/dashboard.html | 主界面 |
| 日历连接 | http://localhost:8000/oauth/google/start | Google OAuth 流程 |
| API 文档 | 见下方 | 所有 REST API 端点 |

---

## 🌐 Available API 端点

### 事件管理
```
POST   /api/events/              # 创建事件
GET    /api/events/              # 列表事件
GET    /api/events/{id}/         # 获取单个事件
PATCH  /api/events/{id}/         # 更新事件
DELETE /api/events/{id}/         # 删除事件
```

### 数据处理管道
```
POST   /api/ai/normalize/        # 规范化字段
POST   /api/ai/schedule/         # 创建事件实体
POST   /api/ai/parse/            # 解析自然语言（需要 OpenAI）
POST   /api/ai/process/          # 一步到位：parse → normalize → schedule
```

### 用户认证
```
POST   /api/auth/register/       # 注册新用户
POST   /api/auth/login/          # 登录
POST   /api/auth/logout/         # 登出
GET    /api/auth/csrf/           # 获取 CSRF Token
GET    /api/auth/me/             # 获取当前用户信息
```

### Google Calendar 同步
```
GET    /oauth/google/start/      # 开始 OAuth 授权
GET    /oauth/google/callback    # OAuth 回调（自动处理）
POST   /api/google/events/sync/  # 同步事件到 Google Calendar
```

---

## 💡 常见问题排查

### ❌ "CSRF token is missing"
**解决方案：**
```javascript
// 手动确保 CSRF Token 被正确设置
const csrf = await fetch('/api/auth/csrf/').then(r => r.json()).then(d => d.csrfToken);
console.log('Current CSRF:', csrf);
```

### ❌ 登录后跳转到登录页面
**原因：** auth.js 脚本未加载
**解决方案：** 刷新页面或检查浏览器控制台的错误

### ❌ "Event created" 但无法看到事件
**原因：** Event 列表功能尚未完整实现
**解决方案：** 在控制台运行以下代码查看：
```javascript
const events = await fetch('/api/events/', {
    headers: {'X-CSRFToken': await fetch('/api/auth/csrf/').then(r => r.json()).then(d => d.csrfToken)}
}).then(r => r.json());
console.table(events);
```

---

## 📊 高级测试：完整流程

### 场景：从输入文本到 Google Calendar

```bash
# 在终端运行这个完整的流程
cat > test_full_flow.sh << 'EOF'
#!/bin/bash

BASE="http://localhost:8000"

echo "=== Full Pipeline Test ==="

# 1. 获取 CSRF
echo "[1/5] Getting CSRF token..."
CSRF=$(curl -s $BASE/api/auth/csrf/ | jq -r '.csrfToken')

# 2. 规范化
echo "[2/5] Normalizing..."
NORM=$(curl -s -X POST $BASE/api/ai/normalize/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d '{
    "events": [{
      "title": "Full Test Event",
      "date": "next Friday",
      "start_time": "10:00",
      "duration": "45m"
    }]
  }')

echo "Normalized: $(echo $NORM | jq '.normalized_events[0].title')"

# 3. 创建
echo "[3/5] Scheduling..."
SCHED=$(curl -s -X POST $BASE/api/ai/schedule/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d "{\"events\": $(echo $NORM | jq '.normalized_events')}")

EVENT_ID=$(echo $SCHED | jq -r '.created_events[0].id')
echo "Created Event ID: $EVENT_ID"

# 4. 列表
echo "[4/5] Listing all events..."
curl -s -X GET $BASE/api/events/ \
  -H "X-CSRFToken: $CSRF" | jq ".[].title" | head -5

# 5. 完成
echo "[5/5] ✅ Full pipeline completed!"
echo "Event URL: $BASE/api/events/$EVENT_ID/"

EOF

chmod +x test_full_flow.sh
./test_full_flow.sh
```

---

## 📸 预期的 UI 流程

### Step 1: 登录页面
```
┌─────────────────────────────────┐
│  Smart Calendar Hub             │
│                                 │
│  📧 Email: test@example.com     │
│  🔐 Password: *****             │
│                                 │
│  [ Sign Up ]  [ Login Button ]  │
└─────────────────────────────────┘
```

### Step 2: Dashboard
```
┌──────────────────────────────────────────┐
│ ☰ Smart Calendar Hub        ⚙️ Settings │
│                                          │
│ Good morning, testuser                   │
│ Create your schedule                     │
│                                          │
│ ┌──────────────────────────────────────┐ │
│ │ Type anything you want to do...  ➤ 📎 │
│ └──────────────────────────────────────┘ │
│                                          │
│ Quick examples:                          │
│ [Team standup tomorrow] [Work out...]   │
│ [Vacation March 10-15] [Lunch break]    │
└──────────────────────────────────────────┘
```

### Step 3: 事件创建成功
```
┌─────────────────────────────────────────┐
│ 📍  右下角弹出提示：                      │
│ ✅ Created 1 event(s)!                  │
│                                         │
│ 新建事件：                              │
│ - Tomorrow at 2pm team meeting (ID: 5) │
└─────────────────────────────────────────┘
```

---

## 🎓 下一步

完成基础测试后，尝试：

1. **Google Calendar 集成**
   - 点击设置菜单的"Connect to Calendar"
   - 授予 Google Calendar 权限
   - 创建事件后同步到 Google Calendar

2. **AI 解析功能**（需配置 OpenAI API Key）
   - 获取 [OpenAI API Key](https://platform.openai.com/api-keys)
   - 在 `.env` 中设置 `OPENAI_API_KEY`
   - 尝试自然语言输入，让 AI 自动提取事件信息

3. **批量导入**
   - 上传 CSV 或 ICS 文件
   - 自动创建多个事件

---

## 📝 记录你的测试结果

保存到 `test_results.md`：

```markdown
# 测试结果 - 2026-02-05

## ✅ 已通过的测试
- [ ] 用户注册
- [ ] 用户登录
- [ ] 事件创建（通过 API）
- [ ] 事件列表
- [ ] 事件更新
- [ ] 事件删除

## ❌ 发现的问题
- 问题 1：...
- 问题 2：...

## 📌 待办项
- [ ] 完成事件列表 UI
- [ ] 添加 Google Calendar 同步按钮
- [ ] 实现重复事件
```

---

## 🆘 需要帮助？

查看详细文档：
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - 完整测试指南
- [PROGRESS.md](PROGRESS.md) - 项目进度
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构说明
