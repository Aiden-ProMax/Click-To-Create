# 操作日志

## 2026-02-04
- 切换技术路线：弃用 Radicale/CalDAV，改用 Google Calendar API（OAuth Web 应用）。
- 新增 `google_sync` 应用：OAuth 授权、token 存储、事件同步接口。
- Event 增加 `google_event_id` 字段，避免重复创建。
- 更新配置示例与 README，使用 `webclient.json` 与回调 `http://localhost:8000/oauth/google/callback`。
- 新增 Google API 依赖。
- 更新连接日历页面 UI：改为 Google OAuth 连接流程。

## 2026-02-10
- Index 页面文案更新为英文新卖点，并新增 beta 联系信息栏。
- 修复注册失败：补齐 `users_userprofile.google_connect_prompted` 字段（手动 SQLite 迁移）。
- Google OAuth 回调增强：签名 state、允许无 session 回调并恢复用户登录，减少 403。
- OAuth 兼容性：在 DEBUG 下容忍 state mismatch；并在回调中尽量恢复用户。
- 全天事件规则：无明确时间/时长即 all-day；规范化层保留空时间，调度层按 00:00 + 1440 创建。
- Google 日历同步：all-day 使用 `date` 字段；description/location/title 进行长度裁剪以避免 API 拒绝。
- Google 同步 attendees 过滤：仅保留合法邮箱，否则忽略。
- 默认时区改为 `America/Los_Angeles`。
- AI 解析稳定性：输入清洗（去 emoji/变体符号），Prompt 简化并强制 24h；冲突日期规则、长文本摘要规则（<=2000 字符）。
- 解析输出调试：终端打印 AI raw response；Google sync 失败错误打印。
- 长文本 description 处理：服务端强制截断至 2000 字符。
- 前端 AI 传输改造：弃用 URL base64，新增 server-side stash `/api/ai/stash/`；前端通过 stash key 拉取。
- Add Event 页面：Invitees 提示为 email only，校验非法输入标红并阻止提交；AI 非法邀请自动清空。
- 时间纠偏：从描述/备注中解析中文时间（如“晚上8:00”）并覆盖错误的 start_time。
