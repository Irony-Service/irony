from datetime import datetime, timedelta

from irony.config import config


def replace_message_keys_with_values(message_body, replacements):
    message_body["interactive"]["body"]["text"] = replace_keys_with_values(
        message_body["interactive"]["body"]["text"], replacements
    )
    return message_body


def replace_keys_with_values(input_string, replacements):
    for key, value in replacements.items():
        input_string = input_string.replace(key, value)
    return input_string


def is_time_slot_expired(time_slot):
    n = config.DB_CACHE["config"]["time_slot_gap"]["value"]
    current_time_plus_n = datetime.now() + timedelta(hours=n)
    current_time_plus_n = (
        f"{current_time_plus_n.hour:02d}:{current_time_plus_n.minute:02d}"
    )
    if time_slot in config.DB_CACHE["config"]:
        time_slot_data = config.DB_CACHE["config"][time_slot]
        if current_time_plus_n < time_slot_data.get("time", "00:00"):
            return False
    return True
