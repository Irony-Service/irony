import redis

# Initialize your Redis client
r = redis.Redis(host="redis", port=6379, db=0)


def add_message_id(message):
    unique_id = None
    if "id" not in message:
        raise Exception("Message id not found in message object.")
    unique_id = message["id"]
    return add_id(unique_id)


def add_id(unique_id):
    # Try to set the key with NX flag (only set if not exists)
    # and set the expiration to 10 seconds.
    # Will return True if the key was set successfully, if already exists will return False
    return r.set(name=unique_id, value=1, ex=10, nx=True)
