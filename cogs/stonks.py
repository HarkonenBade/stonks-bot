import json
import os
from os import path

import discord
from discord.ext import commands


def blank():
    return {'buy': {'price': None, 'quantity': None}, 'price': {d: {'am': None, 'pm': None} for d in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']}}


def load(uid):
    if path.exists(f"data/stonks/{uid}"):
        with open(f"data/stonks/{uid}", "r") as f:
            return json.load(f)
    else:
        None


def store(uid, data):
    with open(f"data/stonks/{uid}", "w") as f:
        json.dump(data, f)


class Stonks(commands.Cog):
    @commands.command()
    async def buy(self, ctx: commands.Context, price: int, quantity: int):
        post = await ctx.send(content=f"Ok lets get you setup!\nFirst remember, this will archive your stocks from last week, hit the ❌ react to abort!\nYou bought {quantity} nips for {price} bells each?\nIf thats right, hit the ✅ react to save!\nIf I got my figures twisted, hit the 🔁 react to swap those numbers around.")
        await post.add_reaction('✅')
        await post.add_reaction('🔁')
        await post.add_reaction('❌')

        def chk(reaction, user):
            return (str(reaction.emoji) in ['❌', '🔁', '✅' ] and
                    user == ctx.author and
                    reaction.message.id == post.id)

        try:
            react, _ = await ctx.bot.wait_for("reaction_add", check=chk, timeout=300)
        except asyncio.TimeoutError:
            await post.delete()

        if str(react.emoji) == "❌":
            await post.edit(content="Ok, see you later!", delete_after=60)
        elif str(react.emoji) == "🔁":
            price, quantity = quantity, price

        data = load(ctx.author.id)
        if data is not None:
            with open("data/stonks/log", "a") as f:
                json.dump(data, f)
                f.write('\n')
        
        data = blank()
        data['buy']['price'] = price
        data['buy']['quantity'] = quantity

        await post.edit(content=f"Ok awesome! Got you setup this week with a haul of {quantity} nips for {price} each. You have {quantity*price} bells riding on this week, hope it goes well!", delete_after=600)

        store(ctx.author.id, data)
        

    @commands.command()
    async def price(self, ctx: commands.Context, day: str, time: str, price: int):
        data = load(ctx.author.id)
       
        if data is None:
            data = blank()

        day = day.lower().strip()
        time = time.lower().strip()

        if day == "mon" or day == "monday":
            day = "mon"
        elif day == "tue" or day == "tuesday":
            day = "tue"
        elif day == "wed" or day == "weds" or day == "wednesday" or day == "wednessday":
            day = "wed"
        elif day == "thu" or day == "thur" or day == "thursday" or day == "thurs":
            day = "thu"
        elif day == "fri" or day == "friday":
            day = "fri"
        elif day == "sat" or day == "saturday":
            day = "sat"
        elif dat == "sun" or day == "sunday":
            await ctx.send(content="Did you mean to say Sunday? If so you probably want the +buy command instead for buying new nips.")
            return
        else:
            await ctx.send(content="I'm sorry, I couldn't recognise what day of the week you were saying. Try saying something like mon, tue, wed, thu, fri or sat.")
            return

        if time == "am" or time == "morn" or time == "morning":
            time = "am"
        elif time == "pm" or time == "evening" or time == "afternoon":
            time = "pm"
        else:
            await ctx.send(content="I'm sorry, I couldn't recognise what time you said. Try saying something like am or pm.")
            return

        if price <= 0:
            await ctx.send(content="I'm sorry, you seem to be trying to set a price of 0 or less, that shouldn't be possible.")
            return

        data['price'][day][time] = price

        if data['buy']['price'] is not None:
            diff = price - data['buy']['price']
            total = diff * data['buy']['quantity']
            await ctx.send(content=f"Thanks!\nYou set a price of {price} bells for nips on {day} {time}.\n\nIf you sell your stock today you will get {diff} bells per nip, for a total profit of {total} bells!")
        else: 
            await ctx.send(content=f"Thanks!\nYou set a price of {price} bells for nips on {day} {time}.")

        store(ctx.author.id, data)

    @commands.command()
    async def summary(self, ctx: commands.Context):
        pass

    @commands.command(hidden=True)
    async def graph(self, ctx: commands.Context, graph_all: str):
        pass
