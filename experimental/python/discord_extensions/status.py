# noinspection PyPackageRequirements
import discord
# noinspection PyPackageRequirements
from discord import app_commands, Interaction
# noinspection PyPackageRequirements
from discord.ext.commands import Cog, Bot, Context, Command

import minqlx
from minqlx import Plugin


def get_game_info(game: minqlx.Game) -> str:
    """
    Helper to format the current ```game.state``` that may be used in status messages and setting of channel topics.

    :param: game: the game object to derive the information from

    :return: the current text representation of the game state
    """
    if game.state == "warmup":
        return "Warmup"
    if game.state == "countdown":
        return "Match starting"
    if game.roundlimit in [game.blue_score, game.red_score] or game.red_score < 0 or game.blue_score < 0:
        return f"Match ended: **{game.red_score}** - **{game.blue_score}**"
    if game.state == "in_progress":
        return f"Match in progress: **{game.red_score}** - **{game.blue_score}**"

    return "Warmup"


def game_status_information(game: minqlx.Game) -> str:
    """
    Generate the text for the topic set on discord channels.

    :param: game: the game to derive the status information from

    :return: the topic that represents the current game state.
    """
    ginfo = get_game_info(game)

    num_players = len(Plugin.players())
    max_players = game.maxclients

    maptitle = game.map_title if game.map_title else game.map
    gametype = game.type_short.upper()

    # CAUTION: if you change anything on the next line, you may need to change the topic_ending logic in
    #          :func:`TopicUpdater.update_topic_on_triggered_channels(self, topic)` to keep the right portion
    #          of the triggered relay channels' topics!
    return f"{ginfo} on **{Plugin.clean_text(maptitle)}** ({gametype}) " \
           f"with **{num_players}/{max_players}** players. "


def player_data() -> str:
    """
    Formats the top 5 scorers connected to the server in a string. The return value may be used for status messages
    and used in topics to indicate reveal more data about the server and its current game.

    :return: string of the current top5 scorers with the scores and connection time to the server
    """
    _player_data = ""
    teams = Plugin.teams()
    if len(teams['red']) > 0:
        _player_data += f"\n**R:** {team_data(teams['red'])}"
    if len(teams['blue']) > 0:
        _player_data += f"\n**B:** {team_data(teams['blue'])}"

    return _player_data


def team_data(player_list: list[minqlx.Player], limit: int = None) -> str:
    """
    generates a sorted output of the team's player by their score

    :param: player_list: the list of players to generate the team output for
    :param: limit: (default: None) just list the top players up to the given limit
    :return: a discord ready text representation of the player's of that team by their score
    """
    if len(player_list) == 0:
        return ""

    players_by_score = sorted(player_list, key=lambda k: k.score, reverse=True)
    if limit:
        players_by_score = players_by_score[:limit]

    _team_data = ""
    for player in players_by_score:
        _team_data += f"**{discord.utils.escape_markdown(player.clean_name)}**({player.score}) "

    return _team_data


def game_status_with_teams() -> str:
    try:
        game = minqlx.Game()
    except minqlx.NonexistentGameError:
        return "Currently no game running."

    ginfo = get_game_info(game)

    num_players = len(Plugin.players())
    max_players = game.maxclients

    maptitle = game.map_title if game.map_title else game.map
    gametype = game.type_short.upper()

    return f"{ginfo} on **{Plugin.clean_text(maptitle)}** ({gametype}) " \
           f"with **{num_players}/{max_players}** players. {player_data()}"


def int_set(string_set: set[str]) -> set[int]:
    returned = set()

    for item in string_set:
        if item == '':
            continue
        value = int(item)
        returned.add(value)

    return returned


class Status(Cog):
    """
    Uses:
    * qlx_discordTriggerStatus (default: "status") Trigger for having the bot send the current status of the game
    server.
    * qlx_discordRelayChannelIds (default: "") Comma separated list of channel ids for full relay.
    * qlx_discordTriggeredChannelIds (default: "") Comma separated list of channel ids for triggered relay.
    * qlx_discordTriggeredChatMessagePrefix (default: "") Prefix any triggered message from QL with this text portion.
    Useful when running multiple servers on the same host with the same discord connected to.
    """
    def __init__(self, bot: Bot):
        self.bot = bot

        Plugin.set_cvar_once("qlx_discordTriggerStatus", "status")
        Plugin.set_cvar_once("qlx_discordTriggeredChatMessagePrefix", "")
        Plugin.set_cvar_once("qlx_discordRelayChannelIds", "")
        Plugin.set_cvar_once("qlx_discordTriggeredChannelIds", "")

        self.discord_trigger_status: str = Plugin.get_cvar("qlx_discordTriggerStatus")
        self.discord_triggered_channel_message_prefix: str = Plugin.get_cvar("qlx_discordTriggeredChatMessagePrefix")
        self.discord_relay_channel_ids: set[int] = \
            int_set(Plugin.get_cvar("qlx_discordRelayChannelIds", set))
        self.discord_triggered_channel_ids: set[int] = int_set(
            Plugin.get_cvar("qlx_discordTriggeredChannelIds", set))

        self.bot.add_command(Command(self.trigger_status, name=self.discord_trigger_status,
                                     checks=[self.is_message_in_relay_or_triggered_channel],
                                     pass_context=True,
                                     ignore_extra=False,
                                     help="display current game status information"))

        # noinspection PyTypeChecker
        slash_status_command = app_commands.Command(name=self.discord_trigger_status,
                                                    description="display current game status information",
                                                    callback=self.slash_trigger_status, parent=None, nsfw=False)
        slash_status_command.guild_only = True
        self.bot.tree.add_command(slash_status_command)

        super().__init__()

    def is_message_in_relay_or_triggered_channel(self, ctx: Context) -> bool:
        """
        Checks whether a message was either sent in a configured relay or triggered channel

        :param: ctx: the context the trigger happened in
        """
        return ctx.message.channel.id in self.discord_relay_channel_ids | self.discord_triggered_channel_ids

    async def trigger_status(self, ctx: Context, *_args, **_kwargs) -> None:
        """
        Triggers game status information sent towards the originating channel

        :param: ctx: the context the trigger happened in
        """
        reply = game_status_with_teams()

        if self.is_message_in_triggered_channel(ctx):
            reply = f"{self.discord_triggered_channel_message_prefix} {reply}"

        await ctx.reply(reply)

    # noinspection PyMethodMayBeStatic
    async def slash_trigger_status(self, interaction: Interaction) -> None:
        """
        Triggers game status information sent towards the originating channel

        :param: interaction: the interaction that triggered the status request
        """
        reply = game_status_with_teams()

        await interaction.response.send_message(content=reply)

    def is_message_in_triggered_channel(self, ctx: Context) -> bool:
        """
        Checks whether the message originate in a configured triggered channel

        :param: ctx: the context the trigger happened in
        """
        return ctx.message.channel.id in self.discord_triggered_channel_ids


async def setup(bot: Bot):
    await bot.add_cog(Status(bot))
