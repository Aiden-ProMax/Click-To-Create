# Architecture

## 模块划分
- ingest：接收用户输入（文本/文件/粘贴）与基础清洗。
- parse：将自然语言解析为结构化事件字段。
- normalize：补全日期/时间/时区/时长，并做合法性校验。
- schedule：生成可写入的事件实体，处理冲突/默认值。
- export：写出到本地事件存储与 Google Calendar API。
- integrations：第三方日历与账号系统对接。

## 数据流（文字）
用户输入 → ingest 清洗 → parse 抽取字段 → normalize 补全与校验 → schedule 生成事件 → export 写入 Google Calendar → 客户端同步。

## 关键边界（纯函数 vs I/O）
- 纯函数（建议保持纯）：
  - parse（给定文本输出结构化字段）
  - normalize（字段补全/校验）
  - schedule（从字段生成事件对象）
- I/O：
  - ingest（文件读取、上传）
  - export（写数据库/调用 Google Calendar API）
  - integrations（OAuth/第三方 API/账号系统）
