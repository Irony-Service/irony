import asyncio
from datetime import datetime, timedelta, time, date
import json
import random
from typing import Any, List, Optional
from bson import ObjectId
from fastapi import Response
from fastapi.encoders import jsonable_encoder

from irony.config import config
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.models.location import Location, UserLocation
from irony.models.order import Order
from irony.models.order_status import OrderStatus, OrderStatusEnum
from irony.models.service import Service
from irony.models.user import User
from irony.config.logger import logger
from irony.util import background_process, utils
from irony.util import whatsapp_utils
from irony.util.message import Message
from irony.db import db


# Start new order message reply
async def start_new_order(contact_details: ContactDetails):
    # Instead of below run a daily job to delete all pending orders which are not completed in 24 hours.
    # Delete order if existing pending order exists
    # last_message = await db.last_message.find_one({"user": contact_details.wa_id})
    # if last_message and "order_taken" not in last_message:
    #     await db.order.delete_one({"order_id": last_message["order_id"]})

    last_message_update = None

    # 1: get step 1 message body.
    message_body = whatsapp_utils.get_reply_message(
        message_key="new_order_step_1",
        message_sub_type="reply",
    )

    # 2: update last_message doc for
    last_message_update = {"type": config.MAKE_NEW_ORDER}

    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    # BUG Continue here
    await create_user_if_not_exists(contact_details)


async def create_user_if_not_exists(contact_details):
    user = await db.user.find_one({"_id": contact_details.wa_id})
    if not user:
        new_user = User(
            wa_id=contact_details.wa_id,
            name=contact_details.name,
            created_on=datetime.now(),
        )
        new_user_json_dump = new_user.model_dump_json()
        logger.info(f"Creating new user : {new_user_json_dump}")
        await db.user.insert_one({new_user.model_dump(exclude_defaults=True)})
        logger.info(f"Created new user : {new_user_json_dump}")


# Set new order clothes count message reply
async def set_new_order_clothes_count(
    contact_details: ContactDetails, context, button_reply_obj
):
    message_body = {}
    last_message_update = None

    await whatsapp_utils.verify_context_id(contact_details, context)

    user_doc = await db.user.find_one({"wa_id": contact_details.wa_id})
    user: User
    if user_doc is not None:
        user = User(**user_doc)
    order_status = OrderStatus(
        status=OrderStatusEnum.SERVICE_PENDING,
        created_on=datetime.now(),
    )

    order: Order = Order(
        user_id=user._id,
        user_wa_id=contact_details.wa_id,
        count_range=button_reply_obj["id"],
        is_active=False,
        order_status=[order_status],
        created_on=datetime.now(),
    )

    order_doc = await db.order.insert_one(order.model_dump(exclude_defaults=True))
    # logger.info(order_doc, order_status_doc)

    message_body = whatsapp_utils.get_reply_message(
        message_key="services_message",
        message_sub_type="radio",
    )

    last_message_update = {
        "type": config.CLOTHES_COUNT_KEY,
        "order_id": order_doc.inserted_id,
    }

    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)


# Set new order service message reply
async def set_new_order_service(
    contact_details: ContactDetails, context, list_reply_obj
):
    message_body = {}
    last_message_update = None

    last_message = await whatsapp_utils.verify_context_id(contact_details, context)

    # user: User = await db.user.find_one({"wa_id": contact_details.wa_id})

    selected_service: Service = config.DB_CACHE["services"][list_reply_obj["id"]]

    # check if last location exists, if yes drirectly send time slot message
    last_location_doc = await db.location.find_one(
        {"user": contact_details.wa_id, "nickname": {"$exists": True}},
        sort=[("last_used", -1)],
    )

    # Last location with nickname exists. Directly send time slot message.
    order_doc = None
    if last_location_doc:
        order_status = OrderStatus(
            status=OrderStatusEnum.TIME_SLOT_PENDING,
            created_on=datetime.now(),
        )
        order_doc = await db.order.find_one_and_update(
            {"_id": last_message["order_id"]},
            {
                "$set": {
                    "services": [
                        selected_service.model_dump(
                            exclude_defaults=True, by_alias=True
                        )
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

        message_body = await get_time_slot_message()

        last_message_update = {
            "type": config.SERVICE_ID_KEY,
            "order_id": order_doc.id,
            "existing_location": True,
        }

        logger.info(f"Sending message to user : {message_body}")
        await Message(message_body).send_message(
            contact_details.wa_id, last_message_update
        )

    # Last location with nickname does not exists. Ask user to send location.
    else:
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
                        selected_service.model_dump(
                            exclude_defaults=True, by_alias=True
                        )
                    ],
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

        message_body = whatsapp_utils.get_reply_message(message_key="ASK_LOCATION")

        last_message_update = {
            "type": config.SERVICE_ID_KEY,
            "order_id": order_doc.id,
        }

        logger.info(f"Sending message to user : {message_body}")
        await Message(message_body).send_message(
            contact_details.wa_id, last_message_update
        )


async def set_new_order_location(message_details, contact_details: ContactDetails):
    last_message = await whatsapp_utils.verify_context_id(
        contact_details, message_details.get("context", {}).get("id", None)
    )
    coords = message_details["location"]

    order = await db.order.find_one({"_id": last_message["order_id"]})
    if order is not None:
        order = Order(**order)

    if order.existing_location:
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
    updated_order = await db.order.replace_one(
        {"_id": order.id},
        order.model_dump(exclude_defaults=True, exclude={"id"}, by_alias=True),
    )
    if updated_order.modified_count == 0:
        raise WhatsappException(
            message="Unable to update location for your order.",
            reply_message="Unable to update location for your order. Please try again.",
        )

    last_message_update = {
        "type": config.LOCATION,
        "order_id": last_message["order_id"],
    }

    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    logger.info("Location message handled")


# Set new order time slot message reply
async def set_new_order_time_slot(
    contact_details: ContactDetails, context, button_reply_obj
):
    message_body = {}
    last_message_update = None

    last_message = await whatsapp_utils.verify_context_id(contact_details, context)

    # # user: User = await db.user.find_one({"wa_id": contact_details.wa_id})
    # order_doc: Order = await db.order.find_one({"_id": last_message["order_id"]})
    # order = Order(**order_doc)

    # await background_process.find_ironman(order, contact_details)
    # return

    order_status = OrderStatus(
        status=OrderStatusEnum.FINDING_IRONMAN, created_on=datetime.now()
    )

    if "existing_location" in last_message:
        order = await db.order.find_one_and_update(
            {"_id": last_message["order_id"]},
            {
                "$set": {
                    "time_slot": button_reply_obj["id"],
                    "updated_on": datetime.now(),
                    "trigger_order_request_at": datetime.now() + timedelta(minutes=3),
                    "trigger_order_request_pending": True,
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

        order = Order(**order)

        # send message to user that last location will be used with location reply. and if he wants to change location he can do so.
        message_body = whatsapp_utils.get_reply_message(
            message_key="existing_location",
        )

        utils.replace_message_keys_with_values(
            message_body, {"{nickname}": order.location.nickname}
        )

    else:
        call_action_config = await db.config.find({"group": "TIME_SLOT_ID"}).to_list(
            None
        )
        slot_start = getSlots(call_action_config, "start_time")
        slot_end = getSlots(call_action_config, "end_time")

        l = len(button_reply_obj["id"])
        if button_reply_obj["id"][l - 1] != "T":

            now = datetime.now()
            h, m = getTimeFromStamp(slot_start[button_reply_obj["id"]])
            he, me = getTimeFromStamp(slot_end[button_reply_obj["id"]])
            start_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            end_time = now.replace(hour=he, minute=me, second=0, microsecond=0)
            order_doc: Order = await db.order.find_one_and_update(
                {"_id": last_message["order_id"]},
                {
                    "$set": {
                        "time_slot": button_reply_obj["id"],
                        "updated_on": datetime.now(),
                        "pick_up_time": {"start": start_time, "end": end_time},
                    },
                    "$push": {
                        "order_status": {
                            "$each": [
                                order_status.model_dump(exclude={"_id", "order_id"})
                            ],
                            "$position": 0,
                        }
                    },
                },
                return_document=True,
            )

        else:
            now = datetime.now() + timedelta(1)
            h, m = getTimeFromStamp(slot_start[button_reply_obj["id"][: l - 1]])
            start_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=3)
            order = await db.order.find_one_and_update(
                {"_id": last_message["order_id"]},
                {
                    "$set": {
                        "time_slot": button_reply_obj["id"][: l - 1],
                        "updated_on": datetime.now(),
                        "pick_up_time": {"start": start_time, "end": end_time},
                    },
                    "$push": {
                        "order_status": {
                            "$each": [
                                order_status.model_dump(exclude={"_id", "order_id"})
                            ],
                            "$position": 0,
                        }
                    },
                },
                return_document=True,
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
                "{date}": order.pick_up_time.start.strftime("%d-%m-%Y"),
                "{time}": config.DB_CACHE["call_to_action"]
                .get(order.time_slot, {})
                .get("title", "N/A"),
            },
        )

    last_message_update = {
        "type": config.TIME_SLOT_ID_KEY,
        "order_id": last_message["order_id"],
        "order_taken": True,
    }

    logger.info(f"Sending message to user : {message_body}")
    await Message(message_body).send_message(contact_details.wa_id, last_message_update)

    if not order.existing_location:
        asyncio.create_task(
            background_process.create_ironman_order_requests(
                order, contact_details.wa_id
            )
        )


async def get_time_slot_message():
    message_body = whatsapp_utils.get_reply_message(
        message_key="time_slots_message",
        message_sub_type="radio",
    )
    # Teja start
    current_time = datetime.now().time()

    hours = current_time.hour
    minutes = current_time.minute

    total_min = hours * 60 + minutes

    call_action_config = await db.config.find({"group": "TIME_SLOT_ID"}).to_list(None)

    delivery_schedule_time_gap = config.DB_CACHE["config"][
        "delivery_schedule_time_gap"
    ]["value"]

    total_min += delivery_schedule_time_gap

    slot_start = {}
    slot_end = {}
    for i in call_action_config:
        h = int(i["start_time"][0:2])
        m = int(i["start_time"][3:5])
        tot = h * 60 + m
        slot_start[i["key"]] = tot
        he = int(i["end_time"][0:2])
        me = int(i["end_time"][3:5])
        te = he * 60 + me
        slot_end[i["key"]] = te

    body = message_body["interactive"]["action"]["sections"][0]["rows"]
    if (
        total_min
        > slot_start[
            message_body["interactive"]["action"]["sections"][0]["rows"][0]["id"]
        ]
    ):

        filtered_today_slots = [
            slot for slot in body if slot_start[slot["id"]] > total_min
        ]
        filtered_tom_slots = body
        filtered_tom_slots = [slot.copy() for slot in body]
        for slot1 in filtered_tom_slots:
            slot1["title"] = "Tomorrow " + " ".join(slot1["title"].split(" ")[1:])
            slot1["id"] = slot1["id"] + "T"
        body = filtered_today_slots + filtered_tom_slots

    message_body["interactive"]["action"]["sections"][0]["rows"] = body
    # Teja end

    return message_body


def getTimeFromStamp(timstr):
    h = int(timstr[:2])
    m = int(timstr[3:])
    return h, m


def getSlots(slotObj, option):
    slot = {}
    for i in slotObj:
        h = int(i[option][0:2])
        m = int(i[option][3:5])
        if h <= 9:
            if m > 9:
                slot[i["key"]] = "0" + str(h) + ":" + str(m)
            else:
                slot[i["key"]] = "0" + str(h) + ":" + "0" + str(m)
        else:
            if m > 9:
                slot[i["key"]] = str(h) + ":" + str(m)
            else:
                slot[i["key"]] = str(h) + ":" + "0" + str(m)
    return slot
