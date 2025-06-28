import re
from datetime import datetime, timedelta, date, time
from typing import Dict, Optional, Any
from dateutil.parser import parse as dateutil_parse


class DateTimeParser:
    def __init__(self):
        self.time_patterns = {
            'morning': time(9, 0),
            'afternoon': time(14, 0),
            'evening': time(18, 0),
            'noon': time(12, 0),
            'midnight': time(0, 0)
        }

    def _get_weekday_offset(self, target_weekday: int) -> int:
        today = datetime.now().weekday()
        days_ahead = target_weekday - today
        if days_ahead <= 0:
            days_ahead += 7
        return days_ahead

    def _get_day_patterns(self) -> Dict[str, int]:
        return {
            'today': 0,
            'tomorrow': 1,
            'day after tomorrow': 2,
            'monday': self._get_weekday_offset(0),
            'tuesday': self._get_weekday_offset(1),
            'wednesday': self._get_weekday_offset(2),
            'thursday': self._get_weekday_offset(3),
            'friday': self._get_weekday_offset(4),
            'saturday': self._get_weekday_offset(5),
            'sunday': self._get_weekday_offset(6),
        }

    def parse_natural_language(self, text: str) -> Dict[str, Any]:
        text = text.lower().strip()
        result = {}

        parsed_date = self._parse_date(text)
        if parsed_date:
            result['date'] = parsed_date

        parsed_time = self._parse_time(text)
        if parsed_time:
            result['time'] = parsed_time

        duration = self._parse_duration(text)
        if duration:
            result['duration'] = duration

        title = self._extract_meeting_title(text)
        if title:
            result['title'] = title

        return result

    def _parse_date(self, text: str) -> Optional[date]:
        today = datetime.now().date()
        day_patterns = self._get_day_patterns()

        for pattern, offset in day_patterns.items():
            if pattern in text:
                return today + timedelta(days=offset)

        if 'next week' in text:
            return today + timedelta(days=7)

        if 'this week' in text:
            return today + timedelta(days=1)

        # Try standard date formats
        try:
            parsed = dateutil_parse(text, fuzzy=True, default=datetime.now())
            return parsed.date()
        except Exception:
            return None

    def _parse_time(self, text: str) -> Optional[time]:
        for pattern, t in self.time_patterns.items():
            if pattern in text:
                return t

        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2})[:.](\d{2})'
        ]

        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        hour, minute, ampm = int(groups[0]), int(groups[1]), groups[2]
                        if ampm and ampm.lower() == 'pm' and hour != 12:
                            hour += 12
                        elif ampm and ampm.lower() == 'am' and hour == 12:
                            hour = 0
                        return time(hour, minute)
                    elif len(groups) == 2:
                        hour = int(groups[0])
                        if groups[1] in ['am', 'pm']:
                            ampm = groups[1].lower()
                            if ampm == 'pm' and hour != 12:
                                hour += 12
                            elif ampm == 'am' and hour == 12:
                                hour = 0
                            return time(hour, 0)
                        else:
                            minute = int(groups[1])
                            return time(hour, minute)
                except Exception:
                    continue

        return None

    def _parse_duration(self, text: str) -> Optional[int]:
        duration_patterns = [
            r'(\d+)\s*hours?',
            r'(\d+)\s*hrs?',
            r'(\d+)\s*minutes?',
            r'(\d+)\s*mins?',
            r'(\d+)\s*h',
            r'(\d+)\s*m',
        ]

        total_minutes = 0
        for pattern in duration_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                value = int(match)
                if 'hour' in pattern or 'hr' in pattern or pattern.endswith('h'):
                    total_minutes += value * 60
                else:
                    total_minutes += value

        if 'quick' in text or 'brief' in text:
            return 30
        elif 'long' in text or 'extended' in text:
            return 120
        elif total_minutes > 0:
            return total_minutes

        return None

    def _extract_meeting_title(self, text: str) -> Optional[str]:
        meeting_keywords = {
            'call': 'Phone Call',
            'meeting': 'Meeting',
            'interview': 'Interview',
            'discussion': 'Discussion',
            'review': 'Review Meeting',
            'standup': 'Standup Meeting',
            'sync': 'Sync Meeting',
            'demo': 'Demo',
            'presentation': 'Presentation',
            'training': 'Training Session',
            'workshop': 'Workshop',
            'consultation': 'Consultation',
        }

        for keyword, title in meeting_keywords.items():
            if keyword in text:
                return title

        quoted_match = re.search(r'["\']([^"\']+)["\']', text)
        if quoted_match:
            return quoted_match.group(1)

        for_match = re.search(r'for\s+(.+?)(?:\s+(?:on|at|tomorrow|today|next|this)|\s*$)', text)
        if for_match:
            return for_match.group(1).strip()

        return None


# Global parser instance
date_parser = DateTimeParser()

# Public utility function
def parse_natural_date_time(text: str) -> Dict[str, Any]:
    return date_parser.parse_natural_language(text)


# Optional test
if __name__ == "__main__":
    tests = [
        "Schedule a meeting for tomorrow at 2 PM",
        "Book a call for next Friday afternoon",
        "I need a 30-minute meeting this Thursday at 10:30 AM",
        "Can we meet for a quick discussion tomorrow morning?",
        "Schedule an interview for 2023-12-15 at 3:00 PM"
    ]
    for t in tests:
        print(f"Input: {t}")
        print("Parsed:", parse_natural_date_time(t))
        print("-" * 40)
