"""
Normalize layer: 补全日期、时间、时区、时长，并进行合法性校验
输入：字段可能缺失或不完整的事件数据
输出：校验通过的完整字段字典，可直接创建 Event 模型实例
"""

import re
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


class NormalizationError(Exception):
    """字段补全与校验失败"""
    pass


class EventNormalizer:
    """事件字段规范化器：补全、转换、校验"""

    # 默认值
    DEFAULT_DURATION_MINUTES = 60  # 默认 1 小时
    DEFAULT_ALLDAY_START_TIME = "09:00"  # 全天事件默认开始时间
    DEFAULT_ALLDAY_DURATION = 480  # 全天事件默认时长（8 小时）
    DEFAULT_REMINDER_MINUTES = 15
    DEFAULT_CATEGORY = "other"

    # 相对时间表达式（中文）
    RELATIVE_TIME_PATTERNS = {
        r'(明天|tomorrow|next day)': 1,
        r'(后天)': 2,
        r'(下周一|next monday)': lambda: _days_to_next_weekday(0),
        r'(下周二|next tuesday)': lambda: _days_to_next_weekday(1),
        r'(下周三|next wednesday)': lambda: _days_to_next_weekday(2),
        r'(下周四|next thursday)': lambda: _days_to_next_weekday(3),
        r'(下周五|next friday)': lambda: _days_to_next_weekday(4),
        r'(下周六|next saturday)': lambda: _days_to_next_weekday(5),
        r'(下周日|周日|next sunday)': lambda: _days_to_next_weekday(6),
        r'(本周一|this monday)': lambda: _days_to_weekday(0),
        r'(本周二|this tuesday)': lambda: _days_to_weekday(1),
        r'(本周三|this wednesday)': lambda: _days_to_weekday(2),
        r'(本周四|this thursday)': lambda: _days_to_weekday(3),
        r'(本周五|this friday)': lambda: _days_to_weekday(4),
        r'(本周六|this saturday)': lambda: _days_to_weekday(5),
        r'(本周日|this sunday)': lambda: _days_to_weekday(6),
    }

    def __init__(self, default_tz: str = 'UTC'):
        """
        初始化
        :param default_tz: 默认时区（如果输入未指定）
        """
        self.default_tz = default_tz

    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        补全并校验事件字段
        :param data: 原始字段字典（可能缺失某些字段）
        :return: 校验通过的完整字段字典
        :raises NormalizationError: 校验失败或字段无法补全
        """
        result = {}

        # 必填字段：标题
        title = data.get('title', '').strip()
        if not title:
            raise NormalizationError("title is required")
        result['title'] = title[:200]  # 截断至 200 个字符

        # 日期处理
        result['date'] = self._normalize_date(data.get('date'))

        raw_start = data.get('start_time')
        raw_duration = data.get('duration')
        raw_all_day = data.get('all_day') is True

        # Determine all-day: explicit flag, or missing time/duration
        all_day = raw_all_day or raw_start in (None, '') or raw_duration in (None, '')
        result['all_day'] = all_day

        if all_day:
            # Keep time fields empty for all-day; scheduler will map to full-day span.
            result['start_time'] = None
            result['duration'] = None
        else:
            # 时间处理
            result['start_time'] = self._normalize_start_time(raw_start)

            # 时长处理
            result['duration'] = self._normalize_duration(
                raw_duration,
                time_str=data.get('end_time')
            )

        # 可选字段
        result['location'] = self._normalize_string(data.get('location'), max_len=255)
        result['description'] = self._normalize_string(data.get('description'), max_len=2000)
        result['participants'] = self._normalize_participants(data.get('participants'))
        result['reminder'] = self._normalize_reminder(data.get('reminder'))
        result['category'] = self._normalize_category(data.get('category'))

        # 其他字段
        result['caldav_uid'] = data.get('caldav_uid')
        result['caldav_href'] = data.get('caldav_href')
        result['google_event_id'] = data.get('google_event_id')

        logger.info(f"Normalized event: {result['title']} on {result['date']}")
        return result

    def _normalize_date(self, date_input: Optional[Any]) -> str:
        """
        规范化日期，返回 YYYY-MM-DD 格式
        支持：字符串、datetime 对象、相对日期表达式
        """
        if date_input is None:
            # 默认为今天
            return datetime.now().date().isoformat()

        if isinstance(date_input, str):
            date_input = date_input.strip()

            # 尝试解析相对日期
            relative_days = self._parse_relative_date(date_input)
            if relative_days is not None:
                target_date = datetime.now().date() + timedelta(days=relative_days)
                return target_date.isoformat()

            # 尝试解析 ISO 格式
            try:
                dt = datetime.fromisoformat(date_input)
                return dt.date().isoformat()
            except:
                pass

            # 尝试解析常见格式：YYYY-MM-DD，MM-DD，MM/DD 等
            try:
                for fmt in ['%Y-%m-%d', '%m-%d', '%m/%d', '%Y/%m/%d', '%d-%m-%Y']:
                    try:
                        dt = datetime.strptime(date_input, fmt)
                        if dt.year == 1900:  # 年份未提供，使用当前年份
                            dt = dt.replace(year=datetime.now().year)
                        return dt.date().isoformat()
                    except:
                        continue
            except:
                pass

            raise NormalizationError(f"Cannot parse date: {date_input}")

        elif isinstance(date_input, datetime):
            return date_input.date().isoformat()

        elif hasattr(date_input, 'isoformat'):  # date 对象
            return date_input.isoformat()

        else:
            raise NormalizationError(f"Unsupported date type: {type(date_input)}")

    def _normalize_start_time(self, time_input: Optional[Any]) -> str:
        """规范化开始时间，返回 HH:MM:SS 格式"""
        if time_input is None:
            # 默认为 09:00
            return self.DEFAULT_ALLDAY_START_TIME + ":00"

        if isinstance(time_input, str):
            time_input = time_input.strip()
            # 支持 HH:MM, HH:MM:SS 等格式
            try:
                dt = datetime.strptime(time_input, '%H:%M:%S')
                return dt.time().isoformat()
            except:
                pass

            try:
                dt = datetime.strptime(time_input, '%H:%M')
                return (dt.time().isoformat('seconds'))
            except:
                pass

            raise NormalizationError(f"Cannot parse time: {time_input}")

        elif isinstance(time_input, time):
            return time_input.isoformat()

        else:
            raise NormalizationError(f"Unsupported time type: {type(time_input)}")

    def _normalize_duration(self, duration_input: Optional[Any], time_str: Optional[str] = None) -> int:
        """
        规范化时长（返回分钟数）
        支持：整数（分钟）、字符串（如 "1h", "90m"）、两个时间点的差值
        """
        if duration_input is not None:
            if isinstance(duration_input, int):
                if duration_input <= 0 or duration_input > 1440:  # > 24 小时
                    raise NormalizationError(f"Duration must be 1-1440 minutes, got {duration_input}")
                return duration_input

            elif isinstance(duration_input, str):
                return self._parse_duration_string(duration_input)

        # 如果提供了结束时间，计算时长
        if time_str:
            try:
                start_time = self._normalize_start_time(None)  # 默认开始时间
                end_time = self._normalize_start_time(time_str)
                start_dt = datetime.strptime(start_time, '%H:%M:%S')
                end_dt = datetime.strptime(end_time, '%H:%M:%S')
                minutes = int((end_dt - start_dt).total_seconds() / 60)
                if minutes > 0:
                    return minutes
            except:
                pass

        # 默认时长
        return self.DEFAULT_DURATION_MINUTES

    def _parse_duration_string(self, duration_str: str) -> int:
        """解析字符串格式的时长，如 '1h', '90m', '1 hour 30 minutes'"""
        duration_str = duration_str.lower().strip()

        # 匹配 "Xh" / "Xm" 格式
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:小时|hour|h)', duration_str)
        if match:
            hours = float(match.group(1))
            minutes = int(hours * 60)
        else:
            minutes = 0

        match = re.search(r'(\d+)\s*(?:分钟|minute|m)(?!in)', duration_str)
        if match:
            minutes += int(match.group(1))

        if minutes <= 0 or minutes > 1440:
            raise NormalizationError(f"Cannot parse duration or out of range: {duration_str}")

        return minutes

    def _normalize_string(self, string_input: Optional[Any], max_len: int = 255) -> Optional[str]:
        """规范化字符串字段，清理空格并截断"""
        if string_input is None:
            return None
        if isinstance(string_input, str):
            result = string_input.strip()
            return result[:max_len] if result else None
        return None

    def _normalize_participants(self, participants_input: Optional[Any]) -> Optional[str]:
        """规范化参与者列表（逗号分隔的邮箱）"""
        if participants_input is None:
            return None

        if isinstance(participants_input, str):
            # 验证邮箱格式
            emails = [e.strip() for e in participants_input.split(',') if e.strip()]
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            valid_emails = [e for e in emails if re.match(email_pattern, e)]
            return ','.join(valid_emails) if valid_emails else None

        elif isinstance(participants_input, list):
            return self._normalize_participants(','.join([str(p) for p in participants_input]))

        return None

    def _normalize_reminder(self, reminder_input: Optional[Any]) -> int:
        """规范化提醒时间（分钟数）"""
        if reminder_input is None:
            return self.DEFAULT_REMINDER_MINUTES

        try:
            reminder_min = int(reminder_input)
            if 0 <= reminder_min <= 40320:  # 0 - 28 天
                return reminder_min
        except:
            pass

        return self.DEFAULT_REMINDER_MINUTES

    def _normalize_category(self, category_input: Optional[Any]) -> str:
        """规范化事件分类"""
        valid_categories = ['work', 'personal', 'meeting', 'appointment', 'other']

        if category_input is None:
            return self.DEFAULT_CATEGORY

        if isinstance(category_input, str):
            category = category_input.lower().strip()
            return category if category in valid_categories else self.DEFAULT_CATEGORY

        return self.DEFAULT_CATEGORY

    def _parse_relative_date(self, text: str) -> Optional[int]:
        """
        解析相对日期表达式，返回相对于今天的天数
        :return: 相对天数，如果无法解析返回 None
        """
        text_lower = text.lower()

        for pattern, days_or_fn in self.RELATIVE_TIME_PATTERNS.items():
            if re.search(pattern, text_lower):
                if callable(days_or_fn):
                    return days_or_fn()
                else:
                    return days_or_fn

        return None


# 辅助函数
def _days_to_next_weekday(weekday: int) -> int:
    """计算距离下个指定工作日的天数（0 = 周一）"""
    today = datetime.now().date()
    current_weekday = today.weekday()
    days_ahead = weekday - current_weekday
    if days_ahead <= 0:
        days_ahead += 7
    return days_ahead


def _days_to_weekday(weekday: int) -> int:
    """计算距离本周指定工作日的天数（0 = 周一）"""
    today = datetime.now().date()
    current_weekday = today.weekday()
    days_ahead = weekday - current_weekday
    if days_ahead < 0:
        days_ahead += 7
    return days_ahead if days_ahead > 0 else 0
