import time
import csv
from collections import defaultdict

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class TicketAnalytics(commands.Cog):
    """Modmail Ticket Analytics Plugin"""

    def __init__(self, bot):
        self.bot = bot
        self.coll = bot.api.get_plugin_partition(self)

    # ----------------------------
    # Helpers
    # ----------------------------

    def format_time(self, seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s}s"

    async def get_data(self, seconds_back: int):
        now = int(time.time())
        cutoff = now - seconds_back

        docs = await self.coll.find({
            "$or": [
                {"type": "closed", "closed_at": {"$gte": cutoff}},
                {"type": "opened", "opened_at": {"$gte": cutoff}}
            ]
        }).to_list(None)

        durations = defaultdict(list)
        opened = defaultdict(int)
        closed = defaultdict(int)

        for d in docs:
            cat = d.get("category_id")

            if d["type"] == "closed":
                durations[cat].append(d["duration"])
                closed[cat] += 1

            elif d["type"] == "opened":
                opened[cat] += 1

        return durations, opened, closed

    async def build_report(self, seconds_back: int):
        durations, opened, closed = await self.get_data(seconds_back)

        embed = discord.Embed(
            title="📊 Ticket Analytics",
            color=0x2b2d31
        )

        total_opened = sum(opened.values())
        total_closed = sum(closed.values())

        embed.description = f"📈 Opened: {total_opened} | ✅ Closed: {total_closed}"

        for cat in set(list(opened.keys()) + list(closed.keys())):
            times = durations.get(cat, [])

            avg = self.format_time(sum(times) / len(times)) if times else "N/A"

            channel = self.bot.get_channel(int(cat)) if cat else None
            name = channel.name if channel else f"Category {cat}"

            embed.add_field(
                name=name,
                value=(
                    f"📈 Opened: {opened.get(cat, 0)}\n"
                    f"✅ Closed: {closed.get(cat, 0)}\n"
                    f"⏱️ Avg Time: {avg}"
                ),
                inline=False
            )

        return embed

    async def export_csv(self, seconds_back: int):
        durations, opened, closed = await self.get_data(seconds_back)

        filename = "analytics.csv"

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Opened", "Closed", "Avg Time"])

            for cat in set(list(opened.keys()) + list(closed.keys())):
                times = durations.get(cat, [])
                avg = self.format_time(sum(times) / len(times)) if times else "N/A"

                channel = self.bot.get_channel(int(cat)) if cat else None
                name = channel.name if channel else cat

                writer.writerow([
                    name,
                    opened.get(cat, 0),
                    closed.get(cat, 0),
                    avg
                ])

        return filename

    # ----------------------------
    # Events
    # ----------------------------

    @commands.Cog.listener()
    async def on_thread_ready(self, thread, creator, category, initial_message):
        await self.coll.insert_one({
            "type": "open",
            "channel_id": str(thread.channel.id),
            "category_id": str(category.id) if category else None,
            "opened_at": int(time.time())
        })

        # count opened
        await self.coll.insert_one({
            "type": "opened",
            "category_id": str(category.id) if category else None,
            "opened_at": int(time.time())
        })

    @commands.Cog.listener()
    async def on_thread_close(self, thread, closer, silent, delete_channel, message, scheduled):
        now = int(time.time())

        open_doc = await self.coll.find_one({
            "type": "open",
            "channel_id": str(thread.channel.id)
        })

        if not open_doc:
            return

        duration = now - open_doc["opened_at"]

        await self.coll.insert_one({
            "type": "closed",
            "category_id": open_doc.get("category_id"),
            "duration": duration,
            "closed_at": now
        })

        await self.coll.delete_one({"_id": open_doc["_id"]})

    # ----------------------------
    # Commands
    # ----------------------------

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    async def analytics(self, ctx, mode: str = "weekly"):
        """View analytics (weekly/monthly/export)"""

        if mode.lower() == "weekly":
            embed = await self.build_report(7 * 86400)
            await ctx.send(embed=embed)

        elif mode.lower() == "monthly":
            embed = await self.build_report(30 * 86400)
            await ctx.send(embed=embed)

        elif mode.lower() == "export":
            file = await self.export_csv(7 * 86400)
            await ctx.send(file=discord.File(file))

        else:
            await ctx.send("Usage: .analytics [weekly|monthly|export]")


async def setup(bot):
    await bot.add_cog(TicketAnalytics(bot))