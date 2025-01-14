from datetime import datetime
from typing import Any, Dict, List
from bson import ObjectId

from irony.config import config
from irony.exception.WhatsappException import WhatsappException
from irony.models.contact_details import ContactDetails
from irony.models.order import Order
from irony.models.order_request import OrderRequest
from irony.models.order_status import OrderStatus, OrderStatusEnum
from irony.config.logger import logger
from irony.util import background_process, utils
from irony.util import whatsapp_utils
from irony.util.message import Message
from irony.db import db


async def update_order_status(reply, status: OrderStatusEnum):
    logger.info("Collect order logic start")
    order_id = reply.get("id").split("#")[-1]
    # PICKUP_COMPLETE
    order_statuses = []
    where = {"_id": order_id}
    if status == OrderStatusEnum.PICKUP_COMPLETE:
        where["order_status.0.status"] = OrderStatusEnum.PICKUP_PENDING
        order_statuses.append(
            OrderStatus(
                status=OrderStatusEnum.WORK_IN_PROGRESS, created_on=datetime.now()
            ).model_dump(exclude={"_id", "order_id"})
        )
    elif status == OrderStatusEnum.WORK_DONE:
        where["order_status.0.status"] = OrderStatusEnum.WORK_IN_PROGRESS
        order_statuses.append(
            OrderStatus(
                status=OrderStatusEnum.DELIVERY_PENDING, created_on=datetime.now()
            ).model_dump(exclude={"_id", "order_id"})
        )
    elif status == OrderStatusEnum.DELIVERED:
        where["order_status.0.status"] = OrderStatusEnum.DELIVERY_PENDING

    order_statuses.append(
        OrderStatus(status=status, created_on=datetime.now()).model_dump(
            exclude={"_id", "order_id"}
        )
    )
    order_doc: Order = await db.order.find_one_and_update(
        {"_id": order_id},
        {
            "$push": {
                "order_status": {
                    "$each": order_statuses,
                    "$position": 0,
                }
            },
        },
        return_document=True,
    )
    if not order_doc:
        logger.error(
            f"Unable to update status for order where {where} to status {status.value}"
        )


async def process_ironman_response(contact_details: ContactDetails, context, reply):
    # Implement the logic for processing ironman response here
    logger.info("Processing ironman response")
    # Example implementation
    if reply.get("id").startswith(config.IRONMAN_REQUEST + "_ACCEPT"):
        await handle_ironman_accept(contact_details, reply.get("id"))
    elif reply.get("id").startswith(config.IRONMAN_REQUEST + "_REJECT"):
        # we can leave it or trigger the next request to other ironman
        await handle_ironman_reject(contact_details, context)
    else:
        logger.error("Unknown ironman response")
        raise WhatsappException(
            "Unknown ironman response",
            error_code=config.ERROR_CODES["INTERNAL_SERVER_ERROR"],
        )


async def handle_ironman_accept(contact_details: ContactDetails, reply_id):
    order_request_id = reply_id.split("#")[-1]

    pipeline: List[Dict[str, Any]] = [
        {"$match": {"_id": ObjectId(order_request_id)}},
        {
            "$lookup": {
                "from": "service_locations",  # the collection to join
                "localField": "service_location_id",  # field in orders referencing service_locations._id
                "foreignField": "_id",  # field in service_locations to match
                "as": "service_location",  # output array field for matched documents
            }
        },
        {
            "$unwind": "$service_location"  # flatten if each order has only one service location
        },
        {
            "$lookup": {
                "from": "order",  # the collection to join
                "localField": "order_id",
                "foreignField": "_id",
                "as": "order",
            }
        },
        {"$unwind": "$order"},
        {
            "$lookup": {
                "from": "timeslot_volume",  # the collection to join
                "localField": "_id",  # field in orders referencing service_locations._id
                "foreignField": "service_location_id",  # field in service_locations to match
                "as": "timeslot_volumes",  # output array field for matched documents
            }
        },
    ]

    order_request_list = await db.order_request.aggregate(pipeline=pipeline).to_list(
        length=1
    )
    order_request: OrderRequest = OrderRequest(**order_request_list[0])
    order = order_request.order
    if order_request and order:
        if order.auto_alloted or order.service_location_id:
            # Order already accepted by another ironman : send ironman message that order is already accepted.
            logger.info(f"Order:{order.id} already accepted by another ironman")
            await send_service_location_message(
                order_request, "Sorry, order already accepted by another ironman"
            )
            return

        # TODO check if this logic is right.
        if utils.is_time_slot_expired(order.time_slot):
            # Time slot expired: send ironman message that time slot is expired.
            logger.info(f"Order:{order.id} time slot expired")
            await send_service_location_message(
                order_request, "Sorry, accepting time slot expired for this order"
            )
            return

        # Implement the logic for handling ironman accept response
        if (
            order_request.service_location
            and await background_process.check_limit_and_allot_order(
                order, order_request.service_location
            )
        ):
            await db.order.replace_one(
                {"_id": order.id},
                order.model_dump(exclude_unset=True, by_alias=True),
            )

            logger.info(
                f"Order:{order.id} accepted by service_location: {order_request.service_location_id} ,ironman:{contact_details.wa_id}"
            )

            # Send message to user that ironman accepted the order.
            user_ironman_alloted_msg = whatsapp_utils.get_reply_message(
                message_key="new_order_ironman_alloted",
                message_sub_type="reply",
            )

            utils.replace_message_keys_with_values(
                user_ironman_alloted_msg,
                {
                    "{service_location_name}": str(
                        getattr(
                            order_request.service_location,
                            "name",
                            "Our Service Provider",
                        )
                    ),
                    "{time}": config.DB_CACHE["call_to_action"]
                    .get(order.time_slot, {})
                    .get("title", "N/A"),
                },
            )
            await Message(user_ironman_alloted_msg).send_message(order.user_wa_id)

            # Send message to ironman that order is assigened to him.
            ironman_order_alloted_message = whatsapp_utils.get_reply_message(
                message_key="ironman_order_alloted", message_type="text"
            )

            ironman_order_alloted_message["text"]["body"] = (
                utils.replace_keys_with_values(
                    ironman_order_alloted_message["text"]["body"],
                    {
                        "{time}": config.DB_CACHE["call_to_action"]
                        .get(order.time_slot, {})
                        .get("title", "N/A"),
                    },
                )
            )

            await Message(ironman_order_alloted_message).send_message(
                contact_details.wa_id
            )
        # service_ids: List[ObjectId] = []
        # if order_request.service_location and order_request.service_location.services:
        #     service_ids = order_request.service_location.services

        # for i, service_entry in enumerate(service_ids):
        #     order_clothes_count = cache.get_clothes_cta_count(order.count_range)
        #     if (
        #         order.services is not None
        #         and order.services[0].id
        #         == service_entry.service_id  # Assuming only one service in order
        #         and service_entry.assigned_pieces_today + order_clothes_count
        #         < service_entry.daily_piece_limit
        #     ):
        #         # assign the order to service location.
        #         service_ids[i].assigned_pieces_today += order_clothes_count

        #         # check if service_location is updating as service_entries is fetches from order_request.service_location. python reference issue.
        #         await db.service_location.replace_one(
        #             {"_id": order_request.service_location_id},
        #             order_request.service_location.model_dump(
        #                 exclude_defaults=True, exclude_unset=True, by_alias=True
        #             ),
        #         )

        #         order_status = await whatsapp_utils.get_new_order_status(
        #             order.id, OrderStatusEnum.PICKUP_PENDING
        #         )
        #         order.service_location_id = order_request.service_location_id
        #         if not order.auto_alloted:
        #             order.order_status.insert(0, order_status)
        #         order.updated_on = datetime.now()

        #         # update the order in the database
        #         if order.auto_alloted:
        #             timeslot_volume: TimeslotVolume = await db.timeslot_volume.find_one(
        #                 {
        #                     "service_location_id": service_location["_id"],
        #                     "$expr": {
        #                         "$eq": [
        #                             {
        #                                 "$dateToString": {
        #                                     "format": "%Y-%m-%d",
        #                                     "date": "$operation_date",
        #                                 }
        #                             },
        #                             {
        #                                 "$dateToString": {
        #                                     "format": "%Y-%m-%d",
        #                                     "date": order.pick_up_time.start,
        #                                 }
        #                             },
        #                         ]
        #                     },
        #                 }
        #             )
        #             timeslot = timeslot_volume["timeslot_distributions"][
        #                 order.time_slot
        #             ]

        #             timeslot_volume["timeslot_distributions"][order.time_slot][
        #                 "current"
        #             ] -= cache.get_clothes_cta_count(order.count_range)
        #             timeslot_volume["current_cloths"] -= cache.get_clothes_cta_count(
        #                 order.count_range
        #             )

        #             await db.timeslot_volume.replace_one(
        #                 {"_id": timeslot_volume["id"]},
        #                 timeslot_volume.model_dump(
        #                     exclude_defaults=True, by_alias=True
        #                 ),
        #             )

        #         await db.order.replace_one(
        #             {"_id": order.id},
        #             order.model_dump(exclude_defaults=True, by_alias=True),
        #         )

        #         logger.info(
        #             f"Order:{order.id} accepted by service_location: {order_request.service_location_id} ,ironman:{contact_details.wa_id}"
        #         )

        #         # Send message to user that ironman accepted the order.
        #         user_ironman_alloted_msg = whatsapp_utils.get_reply_message(
        #             message_key="new_order_ironman_alloted",
        #             message_sub_type="reply",
        #         )

        #         utils.replace_message_keys_with_values(
        #             user_ironman_alloted_msg,
        #             {
        #                 "{service_location_name}": str(
        #                     getattr(
        #                         order_request.service_location,
        #                         "name",
        #                         "Our Service Provider",
        #                     )
        #                 ),
        #                 "{time}": config.DB_CACHE["call_to_action"]
        #                 .get(order_request.order.time_slot, {})
        #                 .get("title", "N/A"),
        #             },
        #         )
        #         if not order.auto_alloted:
        #             await Message(user_ironman_alloted_msg).send_message(
        #                 order_request.order.user_wa_id
        #             )

        #         # Send message to ironman that order is assigened to him.
        #         ironman_order_alloted_message = whatsapp_utils.get_reply_message(
        #             message_key="ironman_order_alloted", message_type="text"
        #         )

        #         ironman_order_alloted_message["text"]["body"] = (
        #             utils.replace_keys_with_values(
        #                 ironman_order_alloted_message["text"]["body"],
        #                 {
        #                     "{time}": config.DB_CACHE["call_to_action"]
        #                     .get(order_request.order.time_slot, {})
        #                     .get("title", "N/A"),
        #                 },
        #             )
        #         )

        #         await Message(ironman_order_alloted_message).send_message(
        #             contact_details.wa_id
        #         )

        logger.info("Ironman accepted completed")


async def send_service_location_message(order_request: OrderRequest, message: str):
    if order_request.service_location is not None:
        await Message(whatsapp_utils.get_free_text_message(message)).send_message(
            order_request.service_location.wa_id
        )


async def handle_ironman_reject(contact_details: ContactDetails, context):
    # Implement the logic for handling ironman reject response
    logger.info("Ironman rejected the request")
