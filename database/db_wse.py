import discord
from .db_globals import *
from datetime import datetime
from typing import cast, Literal
from bson.timestamp import Timestamp


def get_current_wse_price(discord_server: discord.Guild) -> float:
    price_log = db.wse_price_log
    query = price_log.find_one({"_id.server_id": discord_server.id}, {"_id": 0, "price": 1},
                               sort=[("_id.timestamp", -1)])
    query_dict = cast(dict, query)
    price = float(query_dict["price"])
    return price


def set_current_wse_price(discord_server: discord.Guild, new_price: float) -> bool:
    price_log = db.wse_price_log
    timestamp = datetime.now()
    return price_log.insert_one({
        "_id": {
            "server_id": discord_server.id,
            "timestamp": timestamp
        },
        "price": new_price,
    }).acknowledged


def get_prices(discord_server: discord.Guild):
    timestamps = []
    prices = []

    price_log = db.wse_price_log
    results = price_log.find({"_id.server_id": discord_server.id}, {
                             "_id.timestamp": 1, "price": 1}, sort=[("_id.timestamp", 1)])

    for result in results:
        timestamps.append(str(result["_id"]["timestamp"].date()))
        prices.append(result["price"])

    return (timestamps, prices)


def set_transaction(member: discord.Member, curr_price: float, transaction_type: Literal["buy", "sell"]) -> bool:
    transaction_log = db.wse_transaction_log
    timestamp = datetime.now()
    guild = member.guild
    last_transaction = get_last_transaction(member)
    stock_value = 1
    cash_value = 0

    if last_transaction["action"] is not None:
        if transaction_type == "buy":
            stock_value = curr_price
            cash_value = last_transaction["cash_value"] - curr_price
        elif transaction_type == "sell":
            stock_value = 0
            cash_value = last_transaction["cash_value"] + curr_price

    return transaction_log.insert_one({
        "server_id": guild.id,
        "server_name": guild.name,
        "user_id": member.id,
        "user_name": member.name,
        "timestamp": timestamp,
        "action": transaction_type,
        "price": curr_price,
        "cash_value": cash_value,
        "stock_value": stock_value
    }).acknowledged


def get_last_transaction(member: discord.Member):
    transaction_log = db.wse_transaction_log
    guild = member.guild
    query = transaction_log.find_one(
        {"server_id": guild.id, "user_id": member.id}, sort=[("timestamp", -1)])
    query_dict = {"action": None} if query is None else cast(dict, query)
    return query_dict


def get_transactions(member: discord.Member | None = None, guild: discord.Guild | None = None):
    transaction_log = db.wse_transaction_log
    result = None

    if member is None and guild is None:
        raise Exception("Need to provide either a member or guild")

    if member is not None:
        guild = member.guild
        query = transaction_log.find(
            {"server_id": guild.id, "user_id": member.id}, sort=[("timestamp", 1)])
        result = [transaction for transaction in query]
    elif guild is not None:
        query = transaction_log.find(
            {"server_id": guild.id}, sort=[("timestamp", 1)])
        result = [transaction for transaction in query]

    return result
