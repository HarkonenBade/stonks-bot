import asyncio
import datetime
import io
import json
import os
from os import path
import threading
import time

import matplotlib.pyplot as plt
import numpy as np

import schedule

import discord
from discord.ext import commands


LOAD_STORE = threading.Lock()


def load(uid):
    if path.exists(f"data/stonks/{uid}"):
        with open(f"data/stonks/{uid}", "r") as f:
            return json.load(f)
    else:
        return {'buy': {'price': None, 'quantity': None},
                'price': {d: {'am': None, 'pm': None} for d in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']}}


def store(uid, data):
    with open(f"data/stonks/{uid}", "w") as f:
        json.dump(data, f)


def day_norm(val):
    dmap = {'mon': ['monday'],
            'tue': ['tues', 'tuesday'],
            'wed': ['weds', 'wednesday', 'wednessday'],
            'thu': ['thur', 'thurs', 'thursday'],
            'fri': ['friday'],
            'sat': ['saturday'],
            'sun': ['sunday']}

    # Creates the reverse day map, where each key maps to itself, and every entry in the value list maps to it's key
    idmap = {k:k for k in dmap.keys()}
    idmap.update({v:k for k, vl in dmap.items() for v in vl})

    val = val.lower().strip()

    if val in idmap:
        return idmap[val]
    else:
        raise ValueError


def time_norm(val):
    tmap = {'am': ['morn', 'morning', 'day'],
            'pm': ['afternoon', 'evening', 'night']}

    # Creates the reverse time map, where each key maps to itself, and every entry in the value list maps to it's key
    itmap = {k: k for k in tmap.keys()}
    itmap.update({v: k for k, vl in tmap.items() for v in vl})

    val = val.lower().strip()

    if val in itmap:
        return itmap[val]
    else:
        raise ValueError


def ax_config(ax):
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


def data_to_nparr(data):
    return np.array([
        np.nan if data['price'][d][t] is None else data['price'][d][t]
        for d in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        for t in ['am', 'pm']
    ])


def plot_single(data, f, hline=None):
    with plt.xkcd():
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_axes((0.1, 0.2, 0.8, 0.7))
        ax_config(ax)

        d = data_to_nparr(data)
        x = np.arange(0, len(d))
        mask = np.isfinite(d)

        line, = ax.plot(x[mask], d[mask], ls="--")
        ax.plot(x, d, marker=".", color=line.get_color())

        if data['buy']['price'] is not None:
            ax.hlines(data['buy']['price'], -0.5, 11.5, linestyles='dotted')
            ax.text(11.5, data['buy']['price'], str(data['buy']['price']), alpha=0.5, ha="left", va="center")

        if hline is not None:
            ax.hlines(hline, -0.5, 11.5, linestyles='dotted', color='r')
            ax.text(11.5, hline, str(hline), alpha=0.5, ha="left", va="center")

        for i, v in enumerate(d):
            if np.isnan(v):
                continue
            ax.text(i-0.1, v, str(int(v)), alpha=0.5, ha="right", va="center")

        fig.savefig(f, format="png")
        plt.close(fig)


def plot_multi(data, f):
    with plt.xkcd():
        fig = plt.figure(figsize=(13, 7))
        ax = fig.add_axes((0.1, 0.2, 0.6, 0.7))
        ax_config(ax)

        for name, _data in data.items():
            d = data_to_nparr(_data)
            x = np.arange(0, len(d))
            mask = np.isfinite(d)

            line, = ax.plot(x[mask], d[mask], ls="--")
            ax.plot(x, d, marker=".", color=line.get_color(), label=name)

        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        fig.savefig(f, format="png")
        plt.close(fig)


class Stonks(commands.Cog):
    def __init__(self):
        def stonk_rollover():
            with LOAD_STORE:
                with open('data/stonks/log', 'a') as lg:
                    for pth in os.listdir('data/stonks'):
                        try:
                            _ = int(pth)
                        except:
                            continue
                        with open(f'data/stonks/{pth}') as f:
                            data = json.load(f)
                        data['userid'] = pth
                        data['date'] = datetime.date.today().strftime('%Y-%m-%d')
                        json.dump(data, lg)
                        lg.write('\n')
                        os.remove(f'data/stonks/{pth}')
        self.stonk_rollover = stonk_rollover

        schedule.every().sunday.at("04:00").do(stonk_rollover)

        def sch_runner():
            while True:
                schedule.run_pending()
                time.sleep(60)

        self.sch_thr = threading.Thread(target=sch_runner, daemon=True)
        self.sch_thr.start()

    @commands.command()
    async def buy(self, ctx: commands.Context, price: int, quantity: int):
        post = await ctx.send(
            content=f"Ok lets get you setup!\n"
                    f"You bought {quantity} nips for {price} bells each?\n"
                    f"If that's right, hit the ✅ react to save!\n"
                    f"If I got my figures twisted, hit the 🔁 react to swap those numbers around.\n"
                    f"If you just want to bail hit the ❌ react.")
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
            return

        if str(react.emoji) == "❌":
            await post.edit(content="Ok, see you later!", delete_after=60)
        elif str(react.emoji) == "🔁":
            price, quantity = quantity, price

        with LOAD_STORE:
            data = load(ctx.author.id)

            data['buy']['price'] = price
            data['buy']['quantity'] = quantity

            store(ctx.author.id, data)

        await post.edit(
            content=f"Ok awesome! "
                    f"Got you setup this week with a haul of {quantity} nips for {price} each. "
                    f"You have {quantity * price} bells riding on this week, hope it goes well!",
            delete_after=600)

    @commands.command()
    async def price(self, ctx: commands.Context, day: str, time: str, price: int):
        try:
            day = day_norm(day)

            if day == "sun":
                await ctx.send(
                    content="Did you mean to say Sunday? "
                            "If so you probably want the +buy command instead for buying new nips.")
                return
        except ValueError:
            await ctx.send(
                content="I'm sorry, I couldn't recognise what day of the week you were saying. "
                        "Try saying something like mon, tue, wed, thu, fri or sat.")
            return

        try:
            time = time_norm(time)
        except ValueError:
            await ctx.send(
                content="I'm sorry, I couldn't recognise what time you said. Try saying something like am or pm.")
            return

        if price <= 0:
            await ctx.send(
                content="I'm sorry, you seem to be trying to set a price of 0 or less, that shouldn't be possible.")
            return

        with LOAD_STORE:
            data = load(ctx.author.id)

            data['price'][day][time] = price

            store(ctx.author.id, data)

        if data['buy']['price'] is not None:
            diff = price - data['buy']['price']
            total = diff * data['buy']['quantity']
            await ctx.send(
                content=f"Thanks!\n"
                        f"You set a price of {price} bells for nips on {day} {time}.\n\n"
                        f"If you sell your stalks today you will make a profit of {diff} bells per nip, "
                        f"for a total profit of {total} bells!")
        else:
            await ctx.send(content=f"Thanks!\n"
                                   f"You set a price of {price} bells for nips on {day} {time}.")

    @commands.command(hidden=True)
    async def summary(self, ctx: commands.Context):
        pass

    @commands.command()
    async def graph(self, ctx: commands.Context, other: discord.Member = None):
        with LOAD_STORE:
            data = load(ctx.author.id)

        tmp = io.BytesIO()

        if other is not None:
            with LOAD_STORE:
                odata = load(other.id)
            plot_single(odata, tmp, hline=data['buy']['price'])
        else:
            plot_single(data, tmp)

        tmp.seek(0)
        await ctx.send(file=discord.File(tmp, filename="stonks.png"))

    @commands.command()
    @commands.guild_only()
    async def graphall(self, ctx: commands.Context):
        with LOAD_STORE:
            data = {}
            for pth in os.listdir('data/stonks'):
                try:
                    uid = int(pth)
                except:
                    continue
                if ctx.guild.get_member(uid) is not None:
                    data[ctx.guild.get_member(uid).name] = load(uid)

        tmp = io.BytesIO()
        plot_multi(data, tmp)
        tmp.seek(0)
        await ctx.send(file=discord.File(tmp, filename="stonks.png"))
