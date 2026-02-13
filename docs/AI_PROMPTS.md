# AI 调用提示词（Prompt）规范

目的：为 Dashboard 传入的自由文本生成一套确定、不模糊、可直接填入 `add_plan_backend.html` 表单的字段。每次调用 AI 服务时，后端应使用下面的模板并替换占位变量（例如当前日期与默认时区）。

重要说明（必须在每次调用时传入给模型的上下文）
- `CURRENT_DATE`: 当前日期，格式 `YYYY-MM-DD`（例如：`2026-02-09`）。用于把相对日期（"明天"、"下周五"）解析为具体日期。
- `DEFAULT_TZ`: 当用户未明确指定时使用的默认时区（示例项目中默认为 `America/Los_Angeles`）。模型应把此值放到返回 JSON 的 `timezone` 字段。

总体规则（模型必须严格遵守）
- 输出只能是单个 JSON 对象（不允许多余文字或代码块）。
- JSON 必须包含下列字段（类型与格式必须严格符合）：
  - `title` (string) — 事件标题（非空，最长 200 字符）。
  - `date` (string) — 事件日期，固定格式 `YYYY-MM-DD`（若输入为相对日期，模型必须基于 `CURRENT_DATE` 解析并返回具体日期）。
  - `start_time` (string|null) — 开始时间，格式 `HH:MM`（24 小时制），如果用户未指定明确开始时间或意图为全天事件则返回 `null`。
  - `duration` (integer|null) — 时长，单位分钟（整数）。若用户未指定且确认为全天或无明确时段则返回 `null`。注意：不要返回字符串如 `1h`。
  - `all_day` (boolean) — 是否为全天事件。规则：若 `start_time` 或 `duration` 为 `null`，`all_day` 应为 `true`；否则为 `false`。
  - `location` (string|null) — 地点或地址，若无则 `null`。
  - `description` (string|null) — 事件详情，若无则 `null`。
  - `participants` (string|null) — 参与者，逗号分隔的邮箱列表（例如：`alice@example.com,bob@example.com`）。若无法识别或无则 `null`。
  - `reminder` (integer) — 提前提醒分钟数（整数），若未指定返回默认 `15`。
  - `category` (string) — 事件分类，限定为 `work|personal|meeting|appointment|other` 中的一项；若无法判定返回 `other`。
  - `timezone` (string) — 时区标识符（例如 `America/Los_Angeles`）。若用户未指定，必须使用输入 `DEFAULT_TZ`。
  - `needs_confirmation` (boolean) — 如果解析中存在无法在上下文中安全决定的歧义（例如：无法确定要哪个星期五），设置为 `true`，并在 `notes` 中说明需要用户确认的点；否则 `false`。
  - `notes` (string|null) — 对解析结果的简短说明或提醒（例如："用户未指定时区，使用默认时区 America/Los_Angeles"）。若没有备注则 `null`。

额外要求：
- 如果输入包含明确的结束时间（例如 `ends at 16:00` 或 `from 14:00 to 16:00`），返回 `duration` 为分钟差值且 `start_time` 为起始时间。
- 对于只给出日期而无时间的输入，应把 `start_time` 设为 `null`，`duration` 设为 `null`，并把 `all_day` 设为 `true`。
- 对于“相对时间”表达（如“明天 3pm”），模型必须基于 `CURRENT_DATE` 解析出具体的 `date`。
- 若文本中出现非邮箱形式的参与者（如“Tom、Alice”），模型应尽力识别邮箱格式；无法识别时把 `participants` 设为 `null`，并在 `notes` 中列出原始未解析的参与者名。
- 时区默认：如果文本未明确时区，则 `timezone` 使用 `DEFAULT_TZ`（项目中约定为 LA），并在 `notes` 中说明“使用默认时区”。

调用模板（系统/用户提示示例）
-- 系统级（system）提示（固定） --

You are a strict parser assistant. Output only valid JSON matching the schema described below. Do not output any explanation, markdown, or text outside the JSON. Use the supplied variables `CURRENT_DATE` and `DEFAULT_TZ` to resolve relative dates and default timezone. When ambiguous, follow the deterministic rules in the user prompt.

-- 用户级（user）提示模板（在每次调用时替换占位符） --

Parse the following user input into the exact JSON schema. CURRENT_DATE={CURRENT_DATE}; DEFAULT_TZ={DEFAULT_TZ}.

User input:
"""
{USER_TEXT}
"""

Rules (repeat and enforce):
- Return only JSON. No commentary.
- `date` must be YYYY-MM-DD resolved from relative expressions using CURRENT_DATE.
- `start_time` must be HH:MM (24-hour) or null.
- `duration` must be integer minutes or null.
- If either `start_time` or `duration` is null -> `all_day` true.
- `timezone` = extracted timezone or DEFAULT_TZ if missing.
- `reminder` default to 15 if missing.
- `category` must be one of work/personal/meeting/appointment/other.
- Set `needs_confirmation` true only when resolution is unsafe; explain concisely in `notes`.

JSON schema (example keys and types):
{
  "title": "string",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM or null",
  "duration": integer or null,
  "all_day": boolean,
  "location": string or null,
  "description": string or null,
  "participants": string or null,
  "reminder": integer,
  "category": "work|personal|meeting|appointment|other",
  "timezone": "Olson tz name, e.g. America/Los_Angeles",
  "needs_confirmation": boolean,
  "notes": string or null
}

示例（示范输入与期望输出）
- 输入示例 1：
  USER_TEXT = "明天下午2点与 Alice 和 Bob 开会，地点在 会议室 A，持续 1 小时。"
  假设 CURRENT_DATE=2026-02-09, DEFAULT_TZ=America/Los_Angeles

  输出：
  {
    "title": "与 Alice 和 Bob 开会",
    "date": "2026-02-10",
    "start_time": "14:00",
    "duration": 60,
    "all_day": false,
    "location": "会议室 A",
    "description": null,
    "participants": "alice@example.com,bob@example.com",
    "reminder": 15,
    "category": "meeting",
    "timezone": "America/Los_Angeles",
    "needs_confirmation": false,
    "notes": null
  }

- 输入示例 2（不含时间）：
  USER_TEXT = "下周五 公司野餐"
  假设 CURRENT_DATE=2026-02-09, DEFAULT_TZ=America/Los_Angeles

  输出：
  {
    "title": "公司野餐",
    "date": "2026-02-13",
    "start_time": null,
    "duration": null,
    "all_day": true,
    "location": null,
    "description": null,
    "participants": null,
    "reminder": 15,
    "category": "other",
    "timezone": "America/Los_Angeles",
    "needs_confirmation": false,
    "notes": "No time provided — treated as all-day event"
  }

歧义处理与降级规则（必须内置并遵守）：
- 模糊“星期/日期”例如仅写“周五”时：解析为下一个将到来的该星期日历日（deterministic）。在 `notes` 中注明 "Resolved to next occurrence from CURRENT_DATE"。
- 如果输入包含多个可能解释（例如“下午”但没有明确小时数），选择最常见的工作时间：15:00（3pm）；并在 `notes` 中写出 "Assumed 15:00 due to ambiguous afternoon"，同时将 `needs_confirmation` 设为 `true`。
- 若用户文本中包含显式时区（例如 "PST"、"UTC+1"、"America/New_York"），以之为准并写入 `timezone`。
- 当解析参与者名字但无法匹配邮箱格式时：把 `participants` 设为 `null`，并在 `notes` 中列出原始名字供前端显示供用户手动补全。

调用示例（伪代码）
1. 后端准备替换变量并传入模型：

system_prompt = <系统级提示上面那段>
user_prompt = TEMPLATE_USER_PROMPT.replace('{CURRENT_DATE}', today).replace('{DEFAULT_TZ}', default_tz).replace('{USER_TEXT}', user_text)

2. 调用 Google AI / OpenAI 并解析返回的 JSON。若解析失败（非 JSON 或字段缺失），后端应记录错误并回退为显示原始文本让用户手动填写。

注意事项
- 模型输出务必是单一 JSON 对象（便于前端直接 URL-encode 到 `add_plan_backend.html?data=`）。
- 强制在 `notes` 中写入任何默认/假设（例如使用默认时区或假设时间），以便 front-end 能明确提示用户确认。
- 不要在模型端做数据库或网络请求，模型只负责解析并返回字段。

结束。请把这个文档作为每次调用时的提示词规范。后续我可以根据需要把这个 prompt 模板注入到 `ai/services.py` 或后端调用模块中。
