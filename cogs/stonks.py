import asyncio
import io
import json
import os
from os import path

import matplotlib.pyplot as plt
import numpy as np

import discord
from discord.ext import commands


def blank():
    return {'buy': {'price': None, 'quantity': None},
            'price': {d: {'am': None, 'pm': None} for d in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']}}


def load(uid):
    if path.exists(f"data/stonks/{uid}"):
        with open(f"data/stonks/{uid}", "r") as f:
            return json.load(f)
    else:
        None


def store(uid, data):
    with open(f"data/stonks/{uid}", "w") as f:
        json.dump(data, f)


def plot_config():
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_axes((0.1, 0.2, 0.8, 0.7))
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.set_xticks(range(12))
    ax.set_xlim(-0.5, 11.5)
    ax.set_xlabel('date')
    ax.set_xticklabels(['mon - am',
                        'mon - pm',
                        'tue - am',
                        'tue - pm',
                        'wed - am',
                        'wed - pm',
                        'thu - am',
                        'thu - pm',
                        'fri - am',
                        'fri - pm',
                        'sat - am',
                        'sat - pm'])
    ax.tick_params(axis='x', labelrotation=90)
    ax.set_ylabel('price (bells)')
    return fig, ax


def data_to_nparr(data, nans=True):
    return np.array([
            np.nan if nans and data['price'][d][t] is None else data['price'][d][t]
            for d in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
            for t in ['am', 'pm']
        ])


def plot_single(data, f):
    with plt.xkcd():
        fig, ax = plot_config()

        d = data_to_nparr(data)

        ax.plot(d, marker=".")

        if data['buy']['price'] is not None:
            ax.hlines(data['buy']['price'], -0.5, 11.5, linestyles='dotted')
            ax.text(11.5, data['buy']['price'], str(data['buy']['price']), alpha=0.5, ha="left", va="center")

        b, t = ax.get_ylim()
        disp = (t - b) / 30

        for i, v in enumerate(data_to_nparr(data, nans=False)):
            if v is None:
                continue
            ax.text(i, v + disp, str(v), alpha=0.5, ha="center", va="bottom")

        fig.savefig(f, format="png")


def plot_multi(data, f):
    with plt.xkcd():
        fig, ax = plot_config()

        for name, _data in data.items():
            d = data_to_nparr(_data)
            ax.plot(d, marker=".", label=name)

        b, t = ax.get_ylim()
        disp = (t - b) / 30

        for _, _data in data.items():
            d = data_to_nparr(_data, nans=False)
            for i, v in enumerate(d):
                if v is None:
                    continue
                ax.text(i, v + disp, str(int(v)), alpha=0.5, ha="center", va="bottom")

        ax.legend()

        fig.savefig(f, format="png")


class Stonks(commands.Cog):
    @commands.command()
    async def buy(self, ctx: commands.Context, price: int, quantity: int):
        post = await ctx.send(
            content=f"Ok lets get you setup!\nFirst remember, this will archive your stocks from last week, hit the ❌ react to abort!\nYou bought {quantity} nips for {price} bells each?\nIf thats right, hit the ✅ react to save!\nIf I got my figures twisted, hit the 🔁 react to swap those numbers around.")
        await post.add_reaction('✅')
        await post.add_reaction('🔁')
        await post.add_reaction('❌')

        def chk(reaction, user):
            return (str(reaction.emoji) in ['❌', '🔁', '✅'] and
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

        await post.edit(
            content=f"Ok awesome! Got you setup this week with a haul of {quantity} nips for {price} each. You have {quantity * price} bells riding on this week, hope it goes well!",
            delete_after=600)

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
        elif day == "sun" or day == "sunday":
            await ctx.send(
                content="Did you mean to say Sunday? If so you probably want the +buy command instead for buying new nips.")
            return
        else:
            await ctx.send(
                content="I'm sorry, I couldn't recognise what day of the week you were saying. Try saying something like mon, tue, wed, thu, fri or sat.")
            return

        if time == "am" or time == "morn" or time == "morning":
            time = "am"
        elif time == "pm" or time == "evening" or time == "afternoon":
            time = "pm"
        else:
            await ctx.send(
                content="I'm sorry, I couldn't recognise what time you said. Try saying something like am or pm.")
            return

        if price <= 0:
            await ctx.send(
                content="I'm sorry, you seem to be trying to set a price of 0 or less, that shouldn't be possible.")
            return

        data['price'][day][time] = price

        if data['buy']['price'] is not None:
            diff = price - data['buy']['price']
            total = diff * data['buy']['quantity']
            await ctx.send(
                content=f"Thanks!\nYou set a price of {price} bells for nips on {day} {time}.\n\nIf you sell your stock today you will get {diff} bells per nip, for a total profit of {total} bells!")
        else:
            await ctx.send(content=f"Thanks!\nYou set a price of {price} bells for nips on {day} {time}.")

        store(ctx.author.id, data)

    @commands.command(hidden=True)
    async def summary(self, ctx: commands.Context):
        pass

    @commands.command()
    async def graph(self, ctx: commands.Context):
        data = load(ctx.author.id)
        tmp = io.BytesIO()
        plot_single(data, tmp)
        tmp.seek(0)
        await ctx.send(file=discord.File(tmp, filename="stonks.png"))

    @commands.command()
    async def graphall(self, ctx: commands.Context):
        data = {}
        for pth in os.listdir('data/stonks'):
            try:
                uid = int(pth)
            except:
                continue
            if ctx.guild.get_member(uid) is not None:
                data[str(ctx.guild.get_member(uid))] = load(uid)
        tmp = io.BytesIO()
        plot_multi(data, tmp)
        tmp.seek(0)
        await ctx.send(file=discord.File(tmp, filename="stonks.png"))
