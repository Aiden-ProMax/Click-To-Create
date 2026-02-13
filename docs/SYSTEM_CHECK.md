# ✅ 系统检查清单

> 运行这个清单来验证所有组件都正常工作

---

## 🔍 快速检查

### 基本检查

- [ ] Django 服务器正在运行（http://localhost:8000）
- [ ] 能访问 http://localhost:8000/dashboard.html（显示 Dashboard）
- [ ] 已登入用户账户
- [ ] 设置菜单显示"Connect to Calendar"或已连接状态

### OAuth 检查

- [ ] 点击 "Connect to Calendar" 时能进入 Google OAuth 页面
- [ ] 授权后无错误
- [ ] 数据库中有 OAuth Token：
  ```bash
  python manage.py shell
  from google_sync.models import GoogleOAuthToken
  from django.contrib.auth.models import User
  
  user = User.objects.get(username='test')
  token = GoogleOAuthToken.objects.filter(user=user).first()
  print('✅ Token saved!' if token else '❌ No token')
  ```

### 前端检查

- [ ] Dashboard 的输入框在顶部可见
- [ ] 发送按钮（➤）在输入框旁边
- [ ] 快速示例芯片显示在下方
- [ ] 设置菜单能正确打开/关闭

---

## 🧪 完整功能测试

### 1️⃣ 事件创建流程

运行以下测试：

```bash
# 打开 Dashboard
http://localhost:8000/dashboard.html

# 在输入框输入
"Tomorrow at 3pm lunch meeting"

# 点击发送按钮
# 应该自动跳转到编辑表单
```

**预期结果：**
- ✅ 自动跳转到 `add_plan_backend.html`
- ✅ Title 字段显示 "Tomorrow at 3pm lunch meeting"
- ✅ 能看到所有表单字段

### 2️⃣ 表单验证

在编辑表单中测试验证：

```javascript
// 在浏览器 Console 中运行这段代码来测试日期验证
document.getElementById('eventDate').value = '2026-02-04';
document.getElementById('startTime').value = '14:00';
// 检查字段是否示绿色（有效）

// 现在尝试无效的日期
document.getElementById('eventDate').value = 'invalid';
// 应该看到红色错误和错误消息
```

### 3️⃣ 事件保存

在编辑表单中填写完整信息：

```
Title: "Lunch meeting"
Date: "2026-02-04"
Start time: "12:30"
Duration: "60"
Location: "Cafe"
Description: "Team lunch"
Participants: ""
Reminder: "15"
Category: "personal"
```

点击 **Create** 按钮

**预期结果：**
- ✅ 看到加载动画
- ✅ 显示 "Schedule created successfully!" 消息
- ✅ 3 秒后自动回到 Dashboard
- ✅ 网络标签显示两个成功的 POST 请求：
  - `POST /api/events/` (201 Created)
  - `POST /api/google/events/sync/` (200 OK)

### 4️⃣ 数据库验证

验证事件已保存：

```bash
python manage.py shell

from events.models import Event
from django.contrib.auth.models import User

user = User.objects.get(username='test')
latest_event = Event.objects.filter(user=user).order_by('-created_at').first()

if latest_event:
    print(f"✅ 事件已保存！")
    print(f"   Title: {latest_event.title}")
    print(f"   Date: {latest_event.date}")
    print(f"   Start time: {latest_event.start_time}")
    print(f"   Duration: {latest_event.duration}")
    print(f"   Google Event ID: {latest_event.google_event_id}")
else:
    print("❌ 没有找到最近创建的事件")

exit()
```

### 5️⃣ Google Calendar 验证

验证事件已同步到 Google Calendar：

```bash
# 打开 Google Calendar
https://calendar.google.com

# 用授权的 Google 账户登录
# 应该看到新创建的事件 "Lunch meeting"
```

---

## 🐛 常见问题检查

### 问题：点击发送按钮没有反应

**检查步骤：**
1. 打开浏览器开发者工具（F12）
2. 点击 Console 标签
3. 检查是否有错误消息
4. 在控制台输入：
   ```javascript
   document.getElementById('magicInput').value  // 应该返回你的输入
   ```

### 问题：输入不会自动填充到表单中

**检查步骤：**
1. 打开开发者工具 Network 标签
2. 点击发送按钮
3. 查看跳转后的 URL 是否包含参数：
   ```
   add_plan_backend.html?input=xxx&mode=manual
   ```
4. 检查 Console 中是否有 JavaScript 错误

### 问题：提交表单后显示 "Failed to create event"

**检查步骤：**
```bash
# 1. 验证 CSRF Token 存在
# F12 → Application → Cookies → 查找 csrftoken

# 2. 检查 API 响应
# F12 → Network → 查找 POST /api/events/ 请求
# 查看 Response 标签中的错误信息

# 3. 检查服务器日志中的错误
# 查看运行 Django 服务器的终端
```

### 问题：事件已创建但没有同步到 Google Calendar

**检查步骤：**
```bash
# 1. 验证 Google OAuth Token 有效
python manage.py shell
from google_sync.models import GoogleOAuthToken
from django.contrib.auth.models import User

user = User.objects.get(username='test')
token = GoogleOAuthToken.objects.filter(user=user).first()

if token:
    print(f"✅ Token 存在")
    print(f"   Token 长度: {len(token.access_token)}")
else:
    print("❌ 没有 Token")

exit()

# 2. 检查 Network 标签中的 POST /api/google/events/sync/ 响应
# F12 → Network → 查看 sync/ 请求的 Response
```

---

## 📊 系统状态检查

运行以下命令获取完整的系统状态报告：

```bash
#!/bin/bash

echo "=== AutoPlanner 系统检查 ==="
echo ""

echo "1️⃣ Django 数据库迁移"
python manage.py migrate --check && echo "✅ 所有迁移已应用" || echo "❌ 迁移问题"
echo ""

echo "2️⃣ 用户账户"
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
count = User.objects.count()
print(f"✅ 用户总数: {count}")
for u in User.objects.all()[:5]:
    print(f"   - {u.username} ({u.email})")
if count > 5:
    print(f"   ... 以及其他 {count-5} 个用户")
exit()
EOF
echo ""

echo "3️⃣ Google OAuth Token"
python manage.py shell << 'EOF'
from google_sync.models import GoogleOAuthToken
count = GoogleOAuthToken.objects.count()
print(f"✅ OAuth Token 总数: {count}")
for token in GoogleOAuthToken.objects.all()[:3]:
    print(f"   - {token.user.username}: {token.access_token[:30]}...")
exit()
EOF
echo ""

echo "4️⃣ 创建的事件"
python manage.py shell << 'EOF'
from events.models import Event
count = Event.objects.count()
print(f"✅ 事件总数: {count}")
for event in Event.objects.order_by('-created_at')[:3]:
    synced = "✅" if event.google_event_id else "❌"
    print(f"   {synced} {event.title} - {event.date} ({event.user.username})")
exit()
EOF
echo ""

echo "=== 检查完成 ==="
```

保存为 `check_system.sh`，然后运行：

```bash
bash check_system.sh
```

---

## 🚀 性能检查

### API 响应时间

使用 Chrome DevTools 测试 API 性能：

```javascript
// 在浏览器 Console 运行
(async () => {
  console.time('GET /api/events/');
  const r = await fetch('/api/events/');
  const data = await r.json();
  console.timeEnd('GET /api/events/');
  console.log(`事件数: ${data.length}`);
})();

// 应该在 100ms 内完成
```

### 页面加载时间

```javascript
// 在浏览器 Console 运行
window.addEventListener('load', () => {
  const perfData = performance.timing;
  const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
  console.log(`✅ 页面加载时间: ${pageLoadTime}ms`);
});
```

---

## 📝 问题报告模板

如果遇到问题，请收集以下信息：

```
**问题描述：**
[描述你遇到的问题]

**重现步骤：**
1. 
2. 
3. 

**预期结果：**
[应该发生什么]

**实际结果：**
[实际发生了什么]

**浏览器：**
[Chrome/Firefox/Safari 版本]

**控制台错误：**
[F12 的 Console 标签中的任何错误]

**网络请求：**
[F12 的 Network 标签中失败的请求]

**数据库状态：**
[运行 system check 脚本的输出]
```

---

**现在开始检查吧！** ✨
