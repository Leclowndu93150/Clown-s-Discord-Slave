# features/reminder.py
import json
import re
import os
import time
from datetime import datetime, timedelta


class ReminderSystem:
    def __init__(self):
        self.reminders_file = "data/reminders.json"
        self.reminders = self.load_reminders()

    def load_reminders(self):

        os.makedirs(os.path.dirname(self.reminders_file), exist_ok=True)

        try:
            with open(self.reminders_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_reminders(self):
        with open(self.reminders_file, 'w') as f:
            json.dump(self.reminders, f, indent=4)

    def parse_time(self, time_str):
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        total_seconds = 0
        matches = re.finditer(r'(\d+)([smhd])', time_str.lower())
        for match in matches:
            value = int(match.group(1))
            unit = match.group(2)
            total_seconds += value * time_units[unit]
        return total_seconds

    def add_reminder(self, user_id, channel_id, time_str, message):
        seconds = self.parse_time(time_str)
        if seconds == 0:
            return False, "Invalid time format. Use combinations of s/m/h/d\nExample: 1d 2h 3m 4s"
        target_time = int(time.time() + seconds)
        reminder = {
            "user_id": user_id,
            "channel_id": channel_id,
            "message": message,
            "target_time": target_time,
            "created_at": int(time.time())
        }
        self.reminders.append(reminder)
        self.save_reminders()
        remind_time = datetime.fromtimestamp(target_time)
        return True, remind_time.strftime('%Y-%m-%d %H:%M:%S')

    def check_reminders(self):
        current_time = int(time.time())
        due_reminders = []
        reminders_to_keep = []
        for reminder in self.reminders:
            if current_time >= reminder["target_time"]:
                reminder['time_delta'] = timedelta(seconds=current_time - reminder['created_at'])
                due_reminders.append(reminder)
            else:
                reminders_to_keep.append(reminder)
        if due_reminders:
            self.reminders = reminders_to_keep
            self.save_reminders()
        return due_reminders
