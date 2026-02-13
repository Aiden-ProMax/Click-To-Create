# 🔐 Google Calendar OAuth 测试完全指南

> 问题已解决！✅ `InsecureTransportError` 已被修复
> 
> 已在 `.env` 和代码中配置 `OAUTHLIB_INSECURE_TRANSPORT=true` 以支持本地开发环境

---

## 📝 正确的测试流程

### 第一步：注册新账户

1. 访问：http://localhost:8000/login.html
2. 点击 **Sign Up** 或 "Don't have an account?"
3. 填写表单：
   - Username: `testgoogleuser`
   - Email: `test@example.com`
   - Password: `TestPass123!`
4. 点击 **Register**

### 第二步：登录

1. 使用刚才注册的账户登录
2. 会进入 **Dashboard** 首页

### ⭐ 第三步：连接 Google Calendar（新步骤）

**在创建任何事件之前，必须先连接 Google Calendar！**

1. 在 Dashboard 右上角点击 **⚙️ 设置菜单**
2. 看到两个选项：
   - "Connect to Calendar"（蓝色按钮）
   - "Sign Out"（红色按钮）
3. 点击 **"Connect to Calendar"**

### 💫 第四步：Google OAuth 授权

1. 会被重定向到 **Google 登录页面**
2. 用你的 **真实 Google 账户** 登录
   - 如果有多个 Google 账户，选择要使用的那个
3. Google 会显示权限请求页面：
   ```
   "AutoPlanner 想要访问你的 Google Calendar"
   - 查看你的 Google Calendar 中的事件信息
   - 创建、更改和删除事件
   ```
4. 点击 **Allow** 或 **许可** 按钮
5. 授权成功后自动重定向回 **Dashboard**

**预期结果：**
- ✅ 页面回到 Dashboard
- ✅ 没有错误信息
- ✅ 右下角可能显示成功提示

### ✅ 第五步：验证 OAuth Token 已保存

打开浏览器开发者工具 Console，运行：

```javascript
// 检查系统是否成功保存了 OAuth Token
fetch('/api/auth/me/').then(r => r.json()).then(user => {
  console.log('Current user:', user);
  // 如果看到用户信息说明已登录
});
```

或者用 Django shell 检查数据库：

```bash
python manage.py shell

from django.contrib.auth.models import User
from google_sync.models import GoogleOAuthToken

user = User.objects.get(username='testgoogleuser')
token = GoogleOAuthToken.objects.filter(user=user).first()

if token:
    print('✅ Google OAuth Token 已成功保存！')
    print(f'  Access Token: {token.access_token[:50]}...')
    print(f'  User: {token.user.username}')
    print(f'  Scopes: {token.scopes}')
else:
    print('❌ 没有找到 Token，OAuth 可能失败了')

exit()
```

### 🎯 第六步：创建事件并同步到 Google Calendar

现在可以创建事件并同步到 Google Calendar：

1. 回到 Dashboard 首页
2. 在输入框输入：
   ```
   Tomorrow at 2pm team meeting
   ```
3. 点击➤按钮创建事件
4. 看到成功提示 ✅

5. **现在事件已在 AutoPlanner 中创建**
6. 要同步到 Google Calendar，在 Console 运行：

```javascript
// 同步最新创建的事件到 Google Calendar
(async () => {
  const csrf = (await fetch('/api/auth/csrf/').then(r => r.json())).csrfToken;
  
  // 获取最新事件
  const events = await fetch('/api/events/', {headers: {'X-CSRFToken': csrf}}).then(r => r.json());
  const latestEvent = events[events.length - 1];
  
  console.log('Syncing event:', latestEvent.title);
  
  // 同步到 Google Calendar
  const syncRes = await fetch('/api/google/events/sync/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf},
    body: JSON.stringify({
      event_id: latestEvent.id,
      calendar_id: 'primary'  // 主日历
    })
  });
  
  const syncData = await syncRes.json();
  
  if (syncData.ok) {
    console.log('✅ 事件已同步到 Google Calendar!');
    console.log('  Google Event ID:', syncData.google_event_id);
    console.log('  View in Google Calendar:', syncData.htmlLink);
  } else {
    console.error('❌ 同步失败:', syncData.error);
  }
})();
```

**预期输出：**
```
Syncing event: Tomorrow at 2pm team meeting
✅ 事件已同步到 Google Calendar!
  Google Event ID: abc123def456...
  View in Google Calendar: https://calendar.google.com/calendar/event?eid=...
```

### 🌐 第七步：在 Google Calendar 中验证

1. 打开 [Google Calendar](https://calendar.google.com)
2. 登录你刚才授权的 Google 账户
3. 查找新创建的事件
4. 应该能看到：`Tomorrow at 2pm team meeting`

---

## 🔧 如果遇到问题

### ❌ 问题 1: 仍然看到 `InsecureTransportError`

**检查清单：**

1. 确保 `.env` 中有：
   ```env
   OAUTHLIB_INSECURE_TRANSPORT=true
   ```

2. 重启 Django 服务器：
   ```bash
   # 停止当前服务器 (Ctrl+C)
   # 然后重新启动
   python manage.py runserver 0.0.0.0:8000
   ```

3. 验证配置已加载：
   ```bash
   python manage.py shell
   import os
   print(f"OAUTHLIB_INSECURE_TRANSPORT: {os.environ.get('OAUTHLIB_INSECURE_TRANSPORT')}")
   exit()
   ```

### ❌ 问题 2: Google 授权页面无法加载

**原因：** `webclient.json` 配置不正确

**解决方案：**
1. 确认 `webclient.json` 存在于项目根目录
2. 验证内容是有效的 JSON：
   ```bash
   python -c "import json; json.load(open('webclient.json'))" && echo "✅ Valid JSON"
   ```
3. 确保 `.env` 中的 `GOOGLE_OAUTH_CLIENT_JSON_PATH` 指向正确的文件：
   ```env
   GOOGLE_OAUTH_CLIENT_JSON_PATH=./webclient.json
   ```

### ❌ 问题 3: 授权后显示错误页面

**查看错误信息：**
- 错误页面会显示具体的异常消息
- 常见错误：
  - `invalid_client`：Client ID 或 Secret 错误
  - `invalid_scope`：权限范围不正确
  - `redirect_uri_mismatch`：回调 URL 不匹配

**检查配置：**
```env
# .env 中确认以下配置正确：
GOOGLE_OAUTH_CLIENT_JSON_PATH=./webclient.json
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/oauth/google/callback
GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/calendar.events
```

### ❌ 问题 4: OAuth 成功但 Token 未保存

**检查日志：**
```bash
# 在 Console 或服务器日志中查找：
# 应该能看到 "OAuth token stored for user xxx"

# 验证数据库：
python manage.py shell
from google_sync.models import GoogleOAuthToken
from django.contrib.auth.models import User

user = User.objects.get(username='testgoogleuser')
GoogleOAuthToken.objects.filter(user=user).exists()  # 应该返回 True
exit()
```

---

## 📊 完整的 OAuth 流程图

```
┌─────────────────────────────────────────────────────────────┐
│  1. Dashboard → Settings → Connect to Calendar              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Google OAuth Start (GET /oauth/google/start/)           │
│     ↓ 生成授权 URL 和 state 参数                              │
│     ↓ 保存 state 到 Session                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. 重定向用户到 Google 登录页面                              │
│     用户进行身份验证和授权                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Google 重定向回：                                        │
│     /oauth/google/callback?code=xxx&state=yyy              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. OAuth Callback 处理：                                    │
│     ✓ 验证 state 参数                                        │
│     ✓ 用 code 交换 Access Token & Refresh Token            │
│     ✓ 存储 Token 到 GoogleOAuthToken 表                      │
│     ✓ 重定向回 Dashboard                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Dashboard 显示连接成功状态                                │
│     ✓ Token 已保存到数据库                                    │
│     ✓ 用户现在可以创建事件并同步到 Google Calendar           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 快速检查清单

### 配置检查
- [ ] `.env` 文件存在
- [ ] `.env` 中有 `OAUTHLIB_INSECURE_TRANSPORT=true`
- [ ] `.webclient.json` 存在于项目根目录
- [ ] `webclient.json` 是有效的 JSON 格式
- [ ] 服务器已重启

### OAuth 流程检查
- [ ] 能访问 http://localhost:8000/login.html
- [ ] 能成功注册新账户
- [ ] 能成功登录
- [ ] Dashboard 显示欢迎消息
- [ ] 能看到设置菜单（⚙️）
- [ ] "Connect to Calendar" 按钮可点击
- [ ] Google 授权页面能正常加载
- [ ] 用真实 Google 账户授权后无错误

### 数据库检查
- [ ] `GoogleOAuthToken` 表中有新记录
- [ ] Token 原 (`access_token` 字段) 不为空
- [ ] Token 关联到正确的用户

### 事件同步检查
- [ ] 能在 Dashboard 创建事件
- [ ] 能调用 `/api/google/events/sync/` 不出错
- [ ] 返回的 `google_event_id` 不为空
- [ ] 事件出现在 Google Calendar 中

---

## 📚 相关文档

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - 完整的 API 测试指南
- [QUICK_START.md](QUICK_START.md) - 5分钟快速开始
- [PROGRESS.md](PROGRESS.md) - 项目进度

---

## 🚀 现在开始测试！

1. 打开：http://localhost:8000/login.html
2. 注册新账户
3. 登录
4. 点击 Connect to Calendar
5. 用 Google 账户授权
6. 创建事件并同步到 Google Calendar

**祝你测试顺利！** ✨
