from datetime import datetime, timedelta

from irony.config import config
from irony.models.location import Location, UserLocation


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
    # TODO check if this logic is right.
    n = config.DB_CACHE["config"]["delivery_schedule_time_gap"]["value"]
    current_time_plus_n = datetime.now() + timedelta(minutes=n)
    current_time_plus_n = (
        f"{current_time_plus_n.hour:02d}:{current_time_plus_n.minute:02d}"
    )
    if time_slot in config.DB_CACHE["config"]:
        time_slot_data = config.DB_CACHE["config"][time_slot]
        if current_time_plus_n < time_slot_data.get("start_time", "00:00"):
            return False
    return True


def get_maps_link(location: UserLocation):
    maps_link = config.DB_CACHE["google_maps_link"]
    if location.location and location.location.coordinates:
        return f"{maps_link}{location.location.coordinates[0]},{location.location.coordinates[1]}"
    return ""
