from datetime import datetime


def power_state_name(state):
    if state == "standby":
        return "Standby"
    if state == "shutdown":
        return "Power Off"
    if state == "shutdown":
        return "Power Off"
    if state == "reboot":
        return "Restarting..."


def format_time(timestamp):
    if not timestamp:
        return "--:-- --"

    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1] + "+00:00"

    dt = datetime.fromisoformat(timestamp)
    am_pm = "AM" if dt.hour < 12 else "PM"
    hour = dt.hour % 12
    if hour == 0:
        hour = 12
    return f"{hour:02d}:{dt.minute:02d} {am_pm}"
