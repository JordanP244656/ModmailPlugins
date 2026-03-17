import time
import csv
from collections import defaultdict

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class TicketAnalytics(commands.Cog):
    """
    Provides basic analytics for Modmail tickets.

    Features:
    - Tracks opened and closed tickets
    - Calculates average ticket duration
    - Generates weekly/monthly reports
    - Exports data as CSV
    """

    def __init__(self, bot):
        self.bot = bot
        self.coll = bot.api.get_plugin_partition(self)

    # Utility

    @staticmethod
    def _format_duration(seconds: float) -> str:
        minutes, seconds = divmod(int(seconds), 60)
        return f"{minutes}m {seconds}s"

    async def _fetch_data(self, seconds_back: int):
        now = int(time.time())
        cutoff = now - seconds_back

        docs = await self.coll.find({
            "$or": [
                {"type": "closed", "closed_at": {"$gte": cutoff}},
                {"type": "opened", "opened_at": {"$gte": cutoff}}
            ]
        }).to_list(None)

        durations = defaultdict(list)
        opened_counts = defaultdict(int)
        closed_counts = defaultdict(int)

        for doc in docs:
            category_id = doc.get("category_id")

            if doc["type"] == "closed":
                durations[category_id].append(doc["duration"])
                closed_counts[category_id] += 1

            elif doc["type"] == "opened":
                opened_counts[category_id] += 1

        return durations, opened_counts, closed_counts

    async def _build_embed(self, seconds_back: int, label: str):
        durations, opened, closed = await self._fetch_data(seconds_back)

        embed = discord.Embed(
            title=f"Ticket Analytics ({label})",
            color=discord.Color.blurple()
        )

        total_opened = sum(opened.values())
        total_closed = sum(closed.values())

        embed.description = f"Opened: {total_opened} | Closed: {total_closed}"

        all_categories = set(opened.keys()) | set(closed.keys())

        for category_id in all_categories:
            times = durations.get(category_id, [])
            avg = self._format_duration(sum(times) / len(times)) if times else "N/A"

            channel = self.bot.get_channel(int(category_id)) if category_id else None
            name = channel.name if channel else "Uncategorized"

            embed.add_field(
                name=name,
                value=(
                    f"Opened: {opened.get(category_id, 0)}\n"
                    f"Closed: {closed.get(category_id, 0)}\n"
                    f"Avg Time: {avg}"
                ),
                inline=False
            )

        return embed

    async def _generate_csv(self, seconds_back: int):
        durations, opened, closed = await self._fetch_data(seconds_back)

        filename = "analytics.csv"

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Opened", "Closed", "Average Time"])

            all_categories = set(opened.keys()) | set(closed.keys())

            for category_id in all_categories:
                times = durations.get(category_id, [])
                avg = self._format_duration(sum(times) / len(times)) if times else "N/A"

                channel = self.bot.get_channel(int(category_id)) if category_id else None
                name = channel.name if channel else "Uncategorized"

                writer.writerow([
                    name,
                    opened.get(category_id, 0),
                    closed.get(category_id, 0),
                    avg
                ])

        return filename

    # Events

    @commands.Cog.listener()
    async def on_thread_ready(self, thread, creator, category, initial_message):
        timestamp = int(time.time())

        await self.coll.insert_one({
            "type": "open",
            "channel_id": str(thread.channel.id),
            "category_id": str(category.id) if category else None,
            "opened_at": timestamp
        })

        await self.coll.insert_one({
            "type": "opened",
            "category_id": str(category.id) if category else None,
            "opened_at": timestamp
        })

    @commands.Cog.listener()
    async def on_thread_close(self, thread, closer, silent, delete_channel, message, scheduled):
        now = int(time.time())

        record = await self.coll.find_one({
            "type": "open",
            "channel_id": str(thread.channel.id)
        })

        if not record:
            return

        duration = now - record["opened_at"]

        await self.coll.insert_one({
            "type": "closed",
            "category_id": record.get("category_id"),
            "duration": duration,
            "closed_at": now
        })

        await self.coll.delete_one({"_id": record["_id"]})

    # Commands

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.group(invoke_without_command=True)
    async def analytics(self, ctx):
        """View ticket analytics (weekly, monthly, export)"""
        await ctx.send("Usage: `.analytics weekly | monthly | export`")

    @analytics.command()
    async def weekly(self, ctx):
        """Show analytics for the past 7 days"""
        embed = await self._build_embed(7 * 86400, "Weekly")
        await ctx.send(embed=embed)

    @analytics.command()
    async def monthly(self, ctx):
        """Show analytics for the past 30 days"""
        embed = await self._build_embed(30 * 86400, "Monthly")
        await ctx.send(embed=embed)

    @analytics.command()
    async def export(self, ctx):
        """Export analytics data as a CSV file (7 days)"""
        filename = await self._generate_csv(7 * 86400)
        await ctx.send(file=discord.File(filename))


async def setup(bot):
    await bot.add_cog(TicketAnalytics(bot))