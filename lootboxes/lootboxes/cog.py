import discord
from discord import app_commands
from discord.ext import commands
from django.db.models import F, FloatField, ExpressionWrapper
from bd_models.models import BallInstance, Player, Ball, Special
from typing import TYPE_CHECKING
import asyncio
import random
from asgiref.sync import sync_to_async
from ..models import Lootbox, LootSettings, PlayerLootbox
import numpy

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

class Lootboxes(commands.Cog):
    '''
    Lootboxes Commands and stuff ig uwu idk
    '''
    def __init__(
        self,
        bot: "BallsDexBot",
    ):
        self.bot = bot
        self.bias = 1
        self.economy: bool = False
        self.ball_price = 0
        self.economy_price = 0
    
    lootboxes = app_commands.Group(name="lootbox", description="Lootbox commands")

    async def get_settings(self):
        settings_obj = await sync_to_async(LootSettings.objects.first)()

        if not settings_obj:
            print("no lootbox settings found... Somehow")
            return

        self.bias = settings_obj.rig_multiplier
        self.ball_price = settings_obj.ball_instance_price
        self.economy_price = settings_obj.economy_price
        self.economy = settings_obj.economy


    @app_commands.command(name="rare_balls")
    async def rare_balls(self, interaction: discord.Interaction,):
        rare_balls = await query_ball(interaction)
        emojis = []
        for ball in rare_balls:
            if ball.emoji_id:
                emote = self.bot.get_emoji(ball.emoji_id)
                if emote:
                    emojis.append(str(emote))
        print(rare_balls)
        
        await interaction.response.send_message(f" ".join(emojis))
    async def lootbox_autocomplete(self, interaction: discord.Interaction, current: str):
        qs = await sync_to_async(lambda: list(Lootbox.objects.filter(name__icontains=current)[:25]))()
        return [app_commands.Choice(name=b.name, value=b.name) for b in qs]
    @lootboxes.command(name="purchase")
    @app_commands.describe(lootbox="The lootbox you want to purchase")
    @app_commands.autocomplete(lootbox=lootbox_autocomplete)
    async def purchase(self, interaction: discord.Interaction, lootbox: str):
        await self.get_settings()
        player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
        lootbox_obj = await sync_to_async(lambda: Lootbox.objects.filter(name=lootbox).first())()
        if self.economy == True:
            if player.money < (self.economy_price * lootbox_obj.price_multiplier):
                await interaction.response.send_message(
                    f"You are broke. LMAO. You need {self.economy_price * lootbox_obj.price_multiplier} monies to purchase this. You have {player.money}",
                    ephemeral=False
                )
                return
            
            player.money -= self.economy_price * lootbox_obj.price_multiplier
            await player.asave(update_fields=("money",))
            await PlayerLootbox.objects.acreate(player=player, lootbox=lootbox_obj)
            await interaction.response.send_message(
                f"You purchased the lootbox {lootbox} and lost {self.economy_price * lootbox_obj.price_multiplier} monies. You now have {player.money}.",
                ephemeral=True
            )
        else:
            removed_balls = await get_random(interaction, int(self.ball_price * lootbox_obj.price_multiplier))

            if not removed_balls:
                await interaction.response.send_message(
                    "You are broke. LMAO.",
                    ephemeral=False
                )
                return

            ball_names = ", ".join(ball.countryball.country for ball in removed_balls)
            await PlayerLootbox.objects.acreate(player=player, lootbox=lootbox_obj)
            await interaction.response.send_message(
                f"🌟You purchased the lootbox {lootbox} and lost these expensive ass balls: {ball_names}⭐",
                ephemeral=True
            )
    @lootboxes.command(name="gift")
    @app_commands.describe(lootbox="The lootbox you want to purchase", user="The user you want to gift the lootbox to")
    @app_commands.autocomplete(lootbox=lootbox_autocomplete)
    async def purchase(self, interaction: discord.Interaction, lootbox: str, user:discord.User):
        await self.get_settings()
        player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
        player2 = await Player.objects.aget_or_none(discord_id=user.id)
        lootbox_obj = await sync_to_async(lambda: Lootbox.objects.filter(name=lootbox).first())()

        if user.bot:
            await interaction.response.send_message("You cannot donate to bots.", ephemeral=True)
            return
        if not lootbox_obj:
            await interaction.response.send_message("This isnt a lootbox.", ephemeral=True)
            return

        if user == interaction.user:
            await interaction.response.send_message("You cant give a lootbox to yourself", ephemeral=True)
            return
        
        if self.economy == True:
            if player.money < (self.economy_price * lootbox_obj.price_multiplier):
                await interaction.response.send_message(
                    f"You are broke. LMAO. You need {self.economy_price * lootbox_obj.price_multiplier} monies to purchase this. You have {player.money}",
                    ephemeral=False
                )
                return
            
            player.money -= self.economy_price * lootbox_obj.price_multiplier
            await player.asave(update_fields=("money",))

            await PlayerLootbox.objects.acreate(player=player2, lootbox=lootbox_obj)
            await interaction.response.send_message(
                f"Hey {user.mention}! {interaction.user.mention} purchased you lootbox {lootbox}™ and lost {self.economy_price * lootbox_obj.price_multiplier} monies. Be grateful.",
                ephemeral=False
            )
        else:
            removed_balls = await get_random(interaction, int(self.ball_price * lootbox_obj.price_multiplier))

            if not removed_balls:
                await interaction.response.send_message(
                    "You are broke. LMAO.",
                    ephemeral=False
                )
                return

            ball_names = ", ".join(ball.countryball.country for ball in removed_balls)
            await PlayerLootbox.objects.acreate(player=player2, lootbox=lootbox_obj)
            await interaction.response.send_message(
                f"Hey {user.mention}! {interaction.user.mention} purchased you lootbox {lootbox}™ and lost '{ball_names}'. Be grateful.",
                ephemeral=False
            )
    async def player_lootbox_autocomplete(self, interaction: discord.Interaction, current: str):
        qs = await sync_to_async(lambda: list(
            PlayerLootbox.objects.filter(
                player__discord_id=interaction.user.id,
                lootbox__name__icontains=current
            ).select_related("lootbox")[:25]
        ))()
        return [app_commands.Choice(name=pl.lootbox.name, value=pl.lootbox.name) for pl in qs]
    @lootboxes.command(name="open")
    @app_commands.describe(lootbox="The lootbox you want to open")
    @app_commands.checks.cooldown(1, 20, key=lambda i: i.user.id)
    @app_commands.autocomplete(lootbox=player_lootbox_autocomplete)
    async def open(self, interaction: discord.Interaction, lootbox: str):
        player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
        playerlootbox = await sync_to_async(lambda: PlayerLootbox.objects.filter(
            player=player, lootbox__name=lootbox
        ).select_related("lootbox").first())()
        
        if not playerlootbox:
            await interaction.response.send_message(
                "ples buy lootbox", ephemeral=True
            )
            return
        print(playerlootbox, playerlootbox.pk)
        await playerlootbox.adelete()
        total_spins = 1
        await interaction.response.defer(thinking=True)
        rare_balls = await query_ball(interaction)

        spins = 0

        emojis = []
        for ball in rare_balls:
            if ball.emoji_id:
                emote = self.bot.get_emoji(ball.emoji_id)
                if emote:
                    emojis.append(str(emote))
        rigged_ball = await get_random_ball(interaction, cog=self)
        print(rigged_ball)
        numpy.random.shuffle(emojis)
        emojis.append(str(self.bot.get_emoji(rigged_ball.emoji_id)))
        e = discord.Embed(description=f"hello! Thanks for buying lootbox™.")
        await interaction.edit_original_response(embed=e)
        msg = await interaction.original_response()

        i = 0
        n = len(emojis)
        actual_ball_that_will_get_obtained_index = min(10, len(emojis) - 1)
        lootbox_msg = [
            "Pro tip: This appears to be taking a long time... Go outside!",
            "Pro tip: Gambling is good for you.",
            "Pro tip: 99% of gamblers quit before they win big",
            "Pro tip: Laggron42 would be proud <3",
            "Pro tip: You can always donate a ~~gambling addiction~~ lootbox to someone",
            "Pro tip: Wishlist dante's 9 on steam for good luck",
            "Pro tip: Gruyere made this package! Consider ignoring this message.",
            "Pro tip: If you enter the konami code while the animation is playing laggron42 will come down from the sky and give you a mythic reichtangle",
            "Pro tip: I ran out of protips... 😢",
            "Pro tip: Guess what? Chicken butt 🤣🤣",
            "Pro tip: What am i even doing",
            "Pro tip: Disable pro tips using /protips enable",
            "Pro tip: E = mc²",
            "Pro tip: Ditch school and pursue a career in gambling ✅",
            "Pro tip: Is this taking a long time? DW, the spin will be as long",
        ]
        numpy.random.shuffle(lootbox_msg)
        e.description = "Preparing to open..."
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        e.description = lootbox_msg[1]
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        e.description = lootbox_msg[2]
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        e.description = lootbox_msg[3]
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        e.description = lootbox_msg[4]
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        e.description = "lootbox_msg[5]\n whoops i broke somethin-"
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        e.description = lootbox_msg[5]
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        e.description = lootbox_msg[6]
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        e.description = lootbox_msg[7]
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        lootbox_model: Lootbox = playerlootbox.lootbox
        lootbox_id = lootbox_model.id

        if lootbox_id == 1:
            e.description = "Pro tip: Buy the higher tier lootboxes for a higher chance at a special (if the owners added one)"
            await msg.edit(embed=e)
            await asyncio.sleep(2)
        else:
            e.description = "Pro tip: Keep buying the more expensive lootboxes for more profit"
            await msg.edit(embed=e)
            await asyncio.sleep(2)
            
        e.description = "Finally loading..."
        await msg.edit(embed=e)
        await asyncio.sleep(2)
        
        while spins <= total_spins:
            frame = [
                emojis[(i + 0) % n],
                emojis[(i + 1) % n],
                emojis[(i + 2) % n],
                "\n",
                "<:h_:1487794961817669822>",
                ":arrow_up:",
            ]

            e.color = discord.Color.random()
            e.description = " ".join(frame)
            await msg.edit(embed=e)

            i += 1
            if i % n == 0:
                spins += 1
            middle_pos = (i + 1) % n
            if spins >= total_spins and middle_pos == actual_ball_that_will_get_obtained_index:
                break
            await asyncio.sleep(1)
        

        
        prev_emoji = emojis[(actual_ball_that_will_get_obtained_index - 1) % n]
        rigged_emoji = emojis[actual_ball_that_will_get_obtained_index]
        next_emoji = emojis[(actual_ball_that_will_get_obtained_index + 1) % n]

        get_special = await special(interaction, int(playerlootbox.lootbox.special_chance))

        if get_special == True:
            special_to_give = await get_random_special(interaction)
            final_frame = [f"{prev_emoji} {rigged_emoji} {next_emoji}\n<:h_:1487794961817669822>:arrow_up:\n\n 🎉**Congratulations!** You got **{rigged_ball}**🎉\n {special_to_give.catch_phrase}."]
        else:
            special_to_give = None
            final_frame = [f"{prev_emoji} {rigged_emoji} {next_emoji}\n<:h_:1487794961817669822>:arrow_up:\n\n 🎉**Congratulations!** You got **{rigged_ball}**🎉\n This **ball** doesn't have a special. Your special chance has **doubled!**"]

        print(special_to_give)


        
        e.description = " ".join(final_frame)

        try:
            await msg.edit(embed=e)
        except discord.HTTPException:
            pass



        await BallInstance.objects.acreate(
            ball=rigged_ball,
            player=player,
            attack_bonus=random.randint(-20, 20),
            health_bonus=random.randint(-20, 20),
            special=special_to_give
        )





async def query_ball(interaction):
    rareballtotrickpeople = Ball.objects.filter(enabled=True).order_by('rarity')[:10]
    theballs = [ball async for ball in rareballtotrickpeople.aiterator()]
    return theballs

async def get_random_ball(interaction, cog):
    bias = cog.bias
    all_balls = await sync_to_async(list)(Ball.objects.filter(enabled=True))
    if not all_balls:
        return None
    weights = []
    for ball in all_balls:
        weight = ball.rarity
        if ball.rarity >= 3:
            weight *= bias
        weights.append(weight)

    rigged_i_mean_totally_normal_ball = random.choices(all_balls, weights=weights, k=1)[0]
    return rigged_i_mean_totally_normal_ball


async def get_random(interaction: discord.Interaction, amount: int):
    player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
    if not player:
        return []

    all_balls = await sync_to_async(list)(
        BallInstance.objects.filter(player=player, deleted=False, special_id=None)
    )
    if len(all_balls) < amount:
        return []

    selected = random.sample(all_balls, amount)
    print(selected)
    for ball in selected:
        ball.deleted = True
        await ball.asave(update_fields=("deleted",))
    return selected


async def get_random_special(interaction,):
    all_specials = await sync_to_async(list)(Special.objects.filter(hidden=False))
    if not all_specials:
        return None
    weights = []
    for special in all_specials:
        weight = special.rarity
        weights.append(weight)

    special_that_will_get_applied = random.choices(all_specials, weights=weights, k=1)[0]


    return special_that_will_get_applied


async def special(interaction, procent):

    return random.randint(0, 100) <= procent