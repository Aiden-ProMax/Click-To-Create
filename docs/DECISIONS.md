# Decisions (ADR)

## ADR-001：直接接入 Google Calendar API（OAuth）
- 决定：优先实现 Google Calendar API 的 OAuth 同步链路。
- 原因：产品目标是与用户真实日历保持一致，OAuth 同步是最直接可验证路径。
- 替代方案：先做本地 ICS/CalDAV 输出，再扩展到 Google Calendar。
- 后果：增加 OAuth 与第三方 API 依赖，但同步能力与用户体验更好。

## ADR-002：解析与规范化分层
- 决定：parse 与 normalize 分离，parse 只抽取字段，normalize 负责补全与校验。
- 原因：减少复杂耦合，便于测试与迭代。
- 替代方案：解析阶段一次性输出完整事件对象。
- 后果：多一步处理，但可维护性更强。

## ADR-003：事件生成与写入解耦
- 决定：schedule 只生成事件实体，export 负责写入与同步。
- 原因：便于后续增加不同输出渠道（Google/其他日历）。
- 替代方案：schedule 直接写数据库与日历。
- 后果：流程更清晰，但需要明确事件实体接口。
