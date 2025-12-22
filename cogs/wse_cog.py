import discord
from discord import utils
from discord.ext.commands import Cog
from discord.ext import commands
import database as db
from models import WSESession
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
from globals import live_wse_sessions


class WSECog(Cog, name="Walarus Stock Exchange"):
    """ Class containing commands pertaining to Walarus Stock Exchange """

    # region Commands

    @commands.command(name="wse", aliases=["currentstockprice", "currentprice", "price"])
    async def wse_details(self, ctx: commands.Context):
        """ Displays details about current state of Walarus Stock Exchange """
        guild: discord.Guild | None = ctx.guild  # type: ignore
        if guild is None:
            raise Exception("wse_details(): guild is None")
        wse_status = db.get_wse_status(guild)

        if not wse_status:
            await ctx.send("The Walarus Stock Exchange is not currently open")
            return

        price = db.get_current_wse_price(guild)
        job = live_wse_sessions[guild].job
        await ctx.send(f"**Price**: ${round(price, 2):,.2f}\n"
                       f"**Next Price Update**: {job.next_run_time}\n"
                       f"**Stock Price Graph**:")
        await self.__show_graph(ctx)

    @commands.command(name="wsebuy", aliases=["buy", "buyin", "buystock"])
    async def wse_buy(self, ctx: commands.Context):
        """ Buy into the Walarus Stock Exchange at the current stock price """
        guild: discord.Guild | None = ctx.guild  # type: ignore
        if guild is None:
            raise Exception("wse_buy(): guild is None")
        wse_status = db.get_wse_status(guild)

        if not wse_status:
            await ctx.send("The Walarus Stock Exchange is not currently open")
            return

        author: discord.Member = ctx.author  # type: ignore
        last_transaction = db.get_last_transaction(author)["action"]

        if last_transaction == "buy":
            await ctx.send("You are already bought into the WSE!")
            return

        curr_price = db.get_current_wse_price(guild)
        db.set_transaction(
            member=author, curr_price=curr_price, transaction_type="buy")
        await ctx.send(f"{ctx.author.name} just bought into the Walarus Stock Exchange for "
                       f"${round(curr_price, 2):,.2f}")

    @commands.command(name="wsesell", aliases=["sell", "sellstock"])
    async def wse_sell(self, ctx: commands.Context):
        """ Sell your share of the Walarus Stock Exchange at the current stock price """
        guild: discord.Guild | None = ctx.guild  # type: ignore
        if guild is None:
            raise Exception("wse_sell(): guild is None")
        wse_status = db.get_wse_status(guild)

        if not wse_status:
            await ctx.send("The Walarus Stock Exchange is not currently open")
            return

        author: discord.Member = ctx.author  # type: ignore
        last_transaction = db.get_last_transaction(author)["action"]

        if last_transaction == "sell":
            await ctx.send("You haven't bought into the WSE yet!")
            return

        curr_price = db.get_current_wse_price(guild)
        db.set_transaction(
            member=author, curr_price=curr_price, transaction_type="sell")
        await ctx.send(f"{ctx.author.name} just sold share in the Walarus Stock Exchange for "
                       f"${round(curr_price, 2):,.2f}")

    @commands.command(name="wseopen", aliases=["wsestart"])
    async def wse_start(self, ctx: commands.Context, user_id: int):
        """ Open the Walarus Stock Exchange for business """
        if ctx.author.id != ctx.guild.owner_id:
            await ctx.send("Only the server owner can use this command")
            return

        guild: discord.Guild | None = ctx.guild  # type: ignore
        if guild is None:
            raise Exception("wse_start(): guild is None")
        wse_status = db.get_wse_status(guild)

        if wse_status:
            await ctx.send("The Walarus Stock Exchange is already open!")
            return

        OPENING_PRICE = 1.00
        db.set_wse_status(guild, status=True, user_id=user_id)
        db.set_current_wse_price(guild, OPENING_PRICE)
        price = db.get_current_wse_price(guild)
        await ctx.send("@everyone The Walarus Stock Exchange is now open for business at "
                       f"price of ${round(price, 2):,.2f}!")

        live_wse_sessions[guild] = WSESession(guild, user_id, "0 9 * * *")

    @commands.command(name="wseclose", aliases=["wsestop", "wseend"])
    async def wse_end(self, ctx: commands.Context):
        """ Close the Walarus Stock Exchange """
        if ctx.author.id != ctx.guild.owner_id:
            await ctx.send("Only the server owner can use this command")
            return

        guild: discord.Guild | None = ctx.guild  # type: ignore
        if guild is None:
            raise Exception("wse_end(): guild is None")
        wse_status = db.get_wse_status(guild)

        if not wse_status:
            await ctx.send("The Walarus Stock Exchange is not currently open")
            return

        db.set_wse_status(guild, status=False)
        await ctx.send("@everyone The Walarus Stock Exchange is now closed")

        del live_wse_sessions[guild]

    @commands.command(name="lasttransaction")
    async def wse_last_transaction(self, ctx: commands.Context, member: discord.Member | None = None):
        """ View details about your last WSE transaction """
        if member is None:
            member = ctx.author
        transaction = db.get_last_transaction(member)
        if transaction is None:
            who = "You haven't" if member.id == ctx.author.id else f"{member.name} hasn't"
            await ctx.send(f"{who} made any transactions yet. Try the 'wsebuy' or 'wsesell' commands.")
            return
        who = "your" if member.id == ctx.author.id else f"{member.name}'s"
        await ctx.send(f"Here are the details of {who} last transaction:\n"
                       f"\t**Timestamp**: {transaction['timestamp']}\n"
                       f"\t**Transaction Type**: {transaction['action']}\n"
                       f"\t**Price**: ${round(transaction['price'], 2):,.2f}")

    @commands.command(name="wseportfolio", aliases=["myportfolio", "seeportfolio", "portfolio"])
    async def wse_portfolio(self, ctx: commands.Context, member: discord.Member | None = None):
        """ View details about your WSE portfolio """
        if member is None:
            member = ctx.author

        transaction = db.get_last_transaction(member)
        curr_price = db.get_current_wse_price(ctx.guild)
        stock = curr_price if transaction["action"] == "buy" else 0
        cash = transaction["cash_value"]
        total = stock + cash
        who = "Your" if member.id == ctx.author.id else f"{member.name}'s"

        await ctx.send(f"```{who} Portfolio Breakdown:\n"
                       f"\tStock Value: ${round(stock, 2):,.2f}\n"
                       f"\tCash Value: ${round(cash, 2):,.2f}\n"
                       f"\tTotal Portfolio Value: ${round(total, 2):,.2f}\n"
                       f"\tOverall Net: ${round(total - 1, 2):,.2f}```")

    @commands.command(name="wseleaderboard")
    async def wse_leaderboard(self, ctx: commands.Context):
        """ View the WSE leaderboard """
        transactions = db.get_transactions(guild=ctx.guild)
        participants = np.unique([transaction["user_id"]
                                 for transaction in transactions])
        curr_price = db.get_current_wse_price(ctx.guild)
        portfolios = []

        for participant in participants:
            member = utils.find(
                lambda m: m.id == participant, ctx.guild.members)
            last_transaction = db.get_last_transaction(member)
            name = last_transaction["user_name"]
            stock = curr_price if last_transaction["action"] == "buy" else 0
            cash = last_transaction["cash_value"]
            portfolio = {
                "name": name,
                "stock_value": stock,
                "cash_value": cash,
                "total": stock + cash,
                "net": (stock + cash) - 1
            }
            portfolios.append((last_transaction, portfolio))

        message = "```WALARUS STOCK EXCHANGE LEADERBOARD\n\n"
        portfolios = sorted(
            portfolios, key=lambda p: (-p[1]["total"], p[1]["name"]))
        for item in portfolios:
            last_transaction = item[0]
            portfolio = item[1]
            message += (f"{last_transaction['user_name']}\n"
                        f"\tStock Value: ${round(portfolio['stock_value'], 2):,.2f}\n"
                        f"\tCash Value: ${round(portfolio['cash_value'], 2):,.2f}\n"
                        f"\tTotal Portfolio Value: ${round(portfolio['total'], 2):,.2f}\n"
                        f"\tOverall Net: ${round(portfolio['net'], 2):,.2f}\n")
        message += "```"

        await ctx.send(message)

    # @commands.command(name="wsetest")
    # async def wse_test(self, ctx: commands.Context, member: discord.Member | None):
    #     """ Test command for the Walarus Stock Exchange """
    #     db.get_transactions(member)

    # endregion

    # region Helper Functions

    async def __show_graph(self, ctx: commands.Context):
        matplotlib.use('Agg')
        timestamps, prices = db.get_prices(ctx.guild)

        fig, ax = plt.subplots()
        fig.set_figwidth(15)
        ax.set_ylabel("Price", labelpad=25)
        ax.yaxis.set_major_formatter('${x:1.2f}')
        ax.set_xlabel("Date", labelpad=25)
        ax.tick_params(axis='x', labelrotation=90)
        ax.plot(timestamps, prices, marker="o")

        image_name = "prices.jpg"
        plt.savefig(image_name, bbox_inches='tight')
        plt.close()
        await ctx.send(file=discord.File(image_name))
        os.remove(image_name)

    # endregion
