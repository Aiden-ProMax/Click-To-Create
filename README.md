# AutoPlanner

## 项目一句话目标
把用户的自然语言/粘贴文本快速解析成结构化日程，并通过 Google Calendar API 同步到用户日历。

## 最小可用流程（输入 → 解析 → 生成事件 → 同步日历）
1) 用户在 Dashboard 输入自然语言或上传文本/文件。
2) 解析模块抽取事件字段（标题、日期、时间、时长、地点、备注等）。
3) 规范化模块补全与校验时间/时区/时长。
4) 事件写入本地事件存储，并通过 Google Calendar API 写入用户日历。

## 如何运行
1) 安装依赖
```bash
pip install -r requirements.txt
```
2) 准备 Google OAuth（Web 应用客户端，推荐）
- 在 Google Cloud Console 启用 Google Calendar API
- 创建 OAuth 客户端（类型：Web 应用）
- 将 client JSON 放在项目根目录（例如 `webclient.json`），或设置路径环境变量
- 配置授权回调（示例）
  - `http://localhost:8000/oauth/google/callback`
3) 配置环境变量（示例）
```
GOOGLE_OAUTH_CLIENT_JSON_PATH=./webclient.json
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/oauth/google/callback
GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/calendar.events
```
4) 迁移数据库
```bash
python manage.py migrate
```
5) 启动开发服务器
```bash
python manage.py runserver
```
6) 打开页面
- 入口模板位于 `templates/`

## 如何测试
目前无自动化测试。建议手动验证：
- 登录/注册流程
- 输入文本 → 解析 → 事件创建 → Google Calendar 同步

## 文档
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/CONTEXT.md`
