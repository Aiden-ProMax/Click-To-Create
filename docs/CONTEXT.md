# Context (Stable)

## 产品目标
- 让用户用自然语言或粘贴内容快速生成可同步到 Google Calendar 的日历事件。
- 解析时间与事项，尽量减少手动输入。

## 非目标
- 不做复杂的团队协作/审批流。
- 不做完整的项目管理/任务看板。

## 技术栈
- Python / Django
- SQLite（开发阶段）
- HTML/CSS/JS 前端模板

## 约束
- 输入主要是复制粘贴长文本，需自动拆分与结构化。
- 必须处理时区与相对时间（如“下周五”）。
- 需要可回溯：保留原始输入与解析结果。
- 隐私敏感：只请求必要的 Google Calendar 权限范围（最小化 scopes）。

## 统一术语
- Event：单个日程事件（开始时间、时长等）。
- Task：可能转化为 Event 的待办。
- Reminder：仅提醒，不一定含完整事件信息。
- SourceText：用户原始输入文本。
- Chunk：对 SourceText 的拆分片段。
