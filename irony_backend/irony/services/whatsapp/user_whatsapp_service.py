import asyncio
from datetime import datetime, timedelta
from typing import Dict

from requests import options

from irony.config import config
from irony.exception.WhatsappException import WhatsappException
from irony.models.order_status_enum import OrderStatusEnum
from irony.models.whatsapp.contact_details import ContactDetails
from irony.models.order import Order
from irony.models.order_status import OrderStatus
from irony.models.service import Service
from irony.models.user import User
from irony.config.logger import logger
from irony.util import background_process, utils
from irony.util import whatsapp_utils
from irony.util.message import Message
from irony.db import db


# Start new order message reply
async def start_new_order(contact_details: ContactDetails):
    start_time = datetime.now()
    logger.info(f"Starting new order at: {start_time}")
    # Run a daily job to delete all pending orders which are not completed in 24 hours.
    last_message_update = None

    # 1: get step 1 message body.
    message_body = whatsapp_utils.get_reply_message(
        message_key="new_order_step_1",
        message_sub_type="reply",
    )

    logger.info(
        f"Get message body time taken, {(datetime.now() - start_time).total_seconds() * 1000:.2f} ms"
    )
    start_time = datetime.now()

    # 2: update last_message doc for
    last_message_update = {"type": config.MAKE_NEW_ORDER}

    # 3: send message to user
    # logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    logger.info(
        f"Message sent to time taken: {(datetime.now() - start_time).total_seconds() * 1000:.2f} ms"
    )
    start_time = datetime.now()

    # 4: create user if not exists
    await create_user_if_not_exists(contact_details)
    logger.info(
        f"Create user time taken: {(datetime.now() - start_time).total_seconds() * 1000:.2f} ms"
    )


async def create_user_if_not_exists(contact_details: ContactDetails):
    start_time = datetime.now()
    # 1: check if user exists
    user = await db.user.find_one({"wa_id": contact_details.wa_id})
    logger.info(
        f"Get user time taken: {(datetime.now() - start_time).total_seconds() * 1000:.2f} ms"
    )
    if not user:
        new_user = User(
            wa_id=contact_details.wa_id,
            name=contact_details.name,
            created_on=datetime.now(),
        )
        new_user_json = new_user.model_dump(exclude_unset=True)
        # 2: create user
        await db.user.insert_one(new_user_json)
        logger.info(f"Created new user : {new_user_json}")


# Set new order clothes count message reply
async def set_new_order_clothes_count(
    contact_details: ContactDetails, context, button_reply_obj
):
    message_body: Dict = {}
    last_message_update = None
    # 1: verify context id
    await whatsapp_utils.verify_context_id(contact_details, context)

    # 2 : get user
    user = await db.user.find_one({"wa_id": contact_details.wa_id})

    track_doc = await db.config.find_one_and_update(
        {"key": "simple_id_track"}, {"$inc": {"value": 1}}, return_document=True
    )
    track = str(track_doc["value"])

    if user:
        user = User(**user)

    # 3: update orders status
    order_status = OrderStatus(
        status=OrderStatusEnum.SERVICE_PENDING,
        created_on=datetime.now(),
    )
    # 4: update order with clothes count and order status
    order: Order = Order(
        user_id=user.id,
        simple_id=track,
        user_wa_id=contact_details.wa_id,
        count_range=button_reply_obj["id"],
        is_active=False,
        order_status=[order_status],
        created_on=datetime.now(),
    )

    # 5: create new order
    order_doc = await db.order.insert_one(order.model_dump(exclude_unset=True))

    # 6: get message body for services message
    message_body = whatsapp_utils.get_reply_message(
        message_key="services_message",
        message_sub_type="radio",
    )

    # 7: update last message doc
    last_message_update = {
        "type": config.CLOTHES_COUNT_KEY,
        "order_id": order_doc.inserted_id,
    }

    # 8: send message to user
    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)


# Set new order service message reply
async def set_new_order_service(
    contact_details: ContactDetails, context, list_reply_obj
):
    message_body = {}
    last_message_update = None
    # verify context id
    last_message = await whatsapp_utils.verify_context_id(contact_details, context)

    # get selected service
    selected_service: Service = config.DB_CACHE["services"][list_reply_obj["id"]]
    # check if last location exists, if yes drirectly send time slot message
    last_location_doc = await db.location.find_one(
        {"user": contact_details.wa_id, "nickname": {"$exists": True}},
        sort=[("last_used", -1)],
    )

    # Last location with nickname exists. Directly send time slot message.
    order_doc = None
    if last_location_doc:
        # udpate order for existsing location
        order_doc = await handle_existing_location_order_update(
            last_message, selected_service, last_location_doc
        )

        # get timeslot messsage
        message_body = await get_time_slot_message()

        # update last message doc
        last_message_update = {
            "type": config.SERVICE_ID_KEY,
            "order_id": order_doc.id,
            "existing_location": True,
        }

    # Last location with nickname does not exists. Ask user to send location.
    else:
        # update order for no location
        order_doc = await handle_no_location_order_update(
            contact_details, last_message, selected_service
        )

        # get ask location message
        message_body = whatsapp_utils.get_reply_message(message_key="ASK_LOCATION")

        # update last message doc
        last_message_update = {
            "type": config.SERVICE_ID_KEY,
            "order_id": order_doc.id,
        }

    # send message to user
    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)


async def handle_no_location_order_update(
    contact_details, last_message, selected_service: Service
):
    order_status = OrderStatus(
        status=OrderStatusEnum.LOCATION_PENDING,
        created_on=datetime.now(),
    )
    # since there are no nicknames for any locaiton, makes no sense to store existing locations.
    await db.location.delete_many({"user": contact_details.wa_id})
    order_doc = await db.order.find_one_and_update(
        {"_id": last_message["order_id"]},
        {
            "$set": {
                "services": [
                    selected_service.model_dump(exclude_defaults=True, by_alias=True)
                ],
                "updated_on": datetime.now(),
            },
            "$push": {
                "order_status": {
                    "$each": [order_status.model_dump(exclude_unset=True)],
                    "$position": 0,
                }
            },
        },
        return_document=True,
    )
    order_doc = Order(**order_doc)
    return order_doc


async def handle_existing_location_order_update(
    last_message, selected_service: Service, last_location_doc
):
    order_status = OrderStatus(
        status=OrderStatusEnum.TIME_SLOT_PENDING,
        created_on=datetime.now(),
    )
    order_doc = await db.order.find_one_and_update(
        {"_id": last_message["order_id"]},
        {
            "$set": {
                "services": [
                    selected_service.model_dump(exclude_defaults=True, by_alias=True)
                ],
                "location": last_location_doc,
                "existing_location": True,
                "updated_on": datetime.now(),
            },
            "$push": {
                "order_status": {
                    "$each": [order_status.model_dump(exclude={"_id", "order_id"})],
                    "$position": 0,
                }
            },
        },
        return_document=True,
    )
    order_doc = Order(**order_doc)
    return order_doc


async def set_new_order_location(message_details, contact_details: ContactDetails):
    last_message = await whatsapp_utils.verify_context_id(
        contact_details, message_details.get("context", {}).get("id", None)
    )
    coords = message_details["location"]

    order = await db.order.find_one({"_id": last_message["order_id"]})
    if order is not None:
        order = Order(**order)

    if order.existing_location:
        await handle_order_location_update(contact_details, coords, order)
    else:
        location = await whatsapp_utils.add_user_location(contact_details, coords)
        order.location = location
        message_body = await get_time_slot_message()
        order.order_status.insert(
            0,
            OrderStatus(
                status=OrderStatusEnum.TIME_SLOT_PENDING, created_on=datetime.now()
            ),
        )

    order.updated_on = datetime.now()
    # update order
    updated_order = await db.order.replace_one(
        {"_id": order.id},
        order.model_dump(exclude_defaults=True, exclude={"id"}, by_alias=True),
    )
    if updated_order.modified_count == 0:
        raise WhatsappException(
            message="Unable to update location for your order.",
            reply_message="Unable to update location for your order. Please try again.",
        )

    # update last message doc
    last_message_update = {
        "type": config.LOCATION,
        "order_id": last_message["order_id"],
    }

    # send message to user
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    logger.info("Location message handled")


async def handle_order_location_update(contact_details, coords, order):
    order.existing_location = False
    if order.trigger_order_request_at < datetime.now():
        # send user that time is up for sending location.
        message_body = whatsapp_utils.get_free_text_message(
            "Time is up for sending location for this order."
        )
    else:
        location = await whatsapp_utils.add_user_location(contact_details, coords)
        order.location = location
        message_body = whatsapp_utils.get_reply_message(
            message_key="new_order_pending",
            message_sub_type="reply",
        )

        utils.replace_message_keys_with_values(
            message_body,
            {
                # TODO change this to actual chosen date
                "{date}": order.created_on.strftime("%d-%m-%Y"),
                "{time}": config.DB_CACHE["call_to_action"]
                .get(order.time_slot, {})
                .get("title", "N/A"),
            },
        )


# Set new order time slot message reply
async def set_new_order_time_slot(
    contact_details: ContactDetails, context, button_reply_obj
):
    message_body = {}
    last_message_update = None
    order = None

    # verify context id
    last_message = await whatsapp_utils.verify_context_id(contact_details, context)

    order_status = OrderStatus(
        status=OrderStatusEnum.FINDING_IRONMAN, created_on=datetime.now()
    )

    buton_reply_length = len(button_reply_obj["id"])
    pickup_datetime = datetime.now()
    button_reply_id = button_reply_obj["id"]

    if button_reply_obj["id"][buton_reply_length - 1] == "T":
        pickup_datetime = pickup_datetime + timedelta(days=1)
        button_reply_id = button_reply_obj["id"][: buton_reply_length - 1]
    # check if last location exists, update timeslot and send message to user saying that last location will be used.
    if "existing_location" in last_message:
        order = await update_order_timeslot_details(
            button_reply_id,
            last_message,
            order_status,
            pickup_datetime,
            extra_set={
                "trigger_order_request_at": datetime.now() + timedelta(minutes=3),
                "trigger_order_request_pending": True,
            },
        )
        order = Order(**order)

        # send message to user that last location will be used with location reply. and if he wants to change location he can do so.
        message_body = whatsapp_utils.get_reply_message(
            message_key="existing_location",
        )

        utils.replace_message_keys_with_values(
            message_body, {"{nickname}": order.location.nickname}
        )

    # Else update timeslot and send message new_order_pending message to user.
    else:
        order = await update_order_timeslot_details(
            button_reply_id, last_message, order_status, pickup_datetime
        )
        order = Order(**order)

        message_body = whatsapp_utils.get_reply_message(
            message_key="new_order_pending",
            message_sub_type="reply",
        )

        utils.replace_message_keys_with_values(
            message_body,
            {
                # TODO change this to actual chosen date
                "{date}": order.pickup_date_time.start.strftime("%d-%m-%Y"),
                "{time}": config.DB_CACHE["call_to_action"]
                .get(order.time_slot, {})
                .get("title", "N/A"),
            },
        )

    # update last message doc
    last_message_update = {
        "type": config.TIME_SLOT_ID_KEY,
        "order_id": last_message["order_id"],
        "order_taken": True,
    }

    logger.info(f"Sending message to user : {message_body}")
    # send message to user
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    # create ironman order request if not exitsing location
    if not order.existing_location:
        asyncio.create_task(
            background_process.create_ironman_order_requests(
                order, contact_details.wa_id
            )
        )


async def update_order_timeslot_details(
    button_reply_id: str,
    last_message: Dict,
    order_status: OrderStatus,
    pickup_datetime: datetime,
    extra_set={},
):
    # call_action_config = await db.config.find({"group": "TIME_SLOT_ID"}).to_list(None)
    call_action_config = [
        value
        for key, value in config.DB_CACHE["config"].items()
        if "TIME_SLOT_ID" in key
    ]

    slot_start = get_slots(call_action_config, "start_time")
    slot_end = get_slots(call_action_config, "end_time")
    h, m = get_time_from_stamp(slot_start[button_reply_id])
    he, me = get_time_from_stamp(slot_end[button_reply_id])
    start_time = pickup_datetime.replace(hour=h, minute=m, second=0, microsecond=0)
    end_time = pickup_datetime.replace(hour=he, minute=me, second=0, microsecond=0)
    date_time = pickup_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    order = await db.order.find_one_and_update(
        {"_id": last_message["order_id"]},
        {
            "$set": {
                "time_slot": button_reply_id,
                "updated_on": datetime.now(),
                "pickup_date_time": {
                    "date": date_time,
                    "start": start_time,
                    "end": end_time,
                },
                **extra_set,
            },
            "$push": {
                "order_status": {
                    "$each": [order_status.model_dump(exclude_unset=True)],
                    "$position": 0,
                }
            },
        },
        return_document=True,
    )

    return order


def generate_time_slot_title(config_slot, tomorrow=False):
    if tomorrow:
        return f"Tomorrow {get_neat_time_description(config_slot['start_time'])} - {get_neat_time_description(config_slot['end_time'])}"
    return f"Today {get_neat_time_description(config_slot['start_time'])} - {get_neat_time_description(config_slot['end_time'])}"


def get_neat_time_description(time_str):
    hour = int(time_str[:2])
    minute = int(time_str[3:])
    am_pm = "AM" if hour < 12 else "PM"
    if hour == 0:
        hour = 12
    elif hour > 12:
        hour -= 12
    return f"{hour}{':' + str(minute) if minute > 0 else ''}{am_pm}"


async def get_time_slot_message():
    message_body = whatsapp_utils.get_reply_message(
        message_key="time_slots_message",
        message_sub_type="radio",
    )

    delivery_schedule_time_gap = config.DB_CACHE["config"][
        "delivery_schedule_time_gap"
    ]["value"]

    current_time_plus_delay = datetime.now() + timedelta(
        minutes=delivery_schedule_time_gap + 560
    )
    current_time_plus_delay_str = current_time_plus_delay.strftime("%H:%M")

    config_ordered_time_slots = config.DB_CACHE["ordered_time_slots"]

    config_time_slots_today = [
        slot for slot in config_ordered_time_slots if slot.get("is_active", False)
    ]
    config_time_slots_today_dict = {
        slot["key"]: slot for slot in config_time_slots_today
    }

    config_time_slots_tommrrow = [
        slot
        for slot in config_ordered_time_slots
        if slot.get("is_tomorrow_active", False)
    ]
    config_time_slots_tommrrow_dict = {
        slot["key"]: slot for slot in config_time_slots_tommrrow
    }

    time_slots_in_message = message_body["interactive"]["action"]["sections"][0]["rows"]

    today_time_slots_in_message = [
        slot
        for slot in time_slots_in_message
        if slot["id"] in config_time_slots_today_dict
    ]
    tomorrow_time_slots_in_message = [
        slot
        for slot in time_slots_in_message
        if slot["id"] in config_time_slots_tommrrow_dict
    ]

    final_slots = []
    for slot in today_time_slots_in_message:
        if (
            config_time_slots_today_dict[slot["id"]]["start_time"]
            > current_time_plus_delay_str
        ):
            slot["title"] = generate_time_slot_title(
                config_time_slots_today_dict[slot["id"]]
            )
            final_slots.append(slot)

    if (
        len(config_time_slots_tommrrow)
        and current_time_plus_delay_str > config_time_slots_tommrrow[0]["start_time"]
    ):
        for slot in tomorrow_time_slots_in_message:
            slot["title"] = generate_time_slot_title(
                config_time_slots_tommrrow_dict[slot["id"]], True
            )
            slot["id"] = slot["id"] + "T"
            final_slots.append(slot)

    message_body["interactive"]["action"]["sections"][0]["rows"] = final_slots
    return message_body


def get_time_from_stamp(timstr):
    h = int(timstr[:2])
    m = int(timstr[3:])
    return h, m


def get_slots(slotObj, option):
    slot = {}
    for i in slotObj:
        slot[i["key"]] = i[option]
    return slot
