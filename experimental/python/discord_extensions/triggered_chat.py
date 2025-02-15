# noinspection PyPackageRequirements
from discord.abc import GuildChannel
# noinspection PyPackageRequirements
from discord import app_commands, Interaction, Color, Embed, Member
# noinspection PyPackageRequirements
from discord.ext.commands import Cog, Bot, Context, Command

import minqlx
from minqlx import Plugin


def int_set(string_set: set[str]) -> set[int]:
    returned = set()

    for item in string_set:
        if item == '':
            continue
        value = int(item)
        returned.add(value)

    return returned


class TriggeredChat(Cog):
    """
    Uses:
    * qlx_discordTriggerTriggeredChannelChat (default: "quakelive") Message prefix for the trigger on triggered relay
    channels.
    * qlx_discordMessagePrefix (default: "[DISCORD]") messages from discord to quake live will be prefixed with this
    prefix
    * qlx_discordTriggeredChannelIds (default: "") Comma separated list of channel ids for triggered relay.
    """
    def __init__(self, bot: Bot):
        self.bot = bot

        Plugin.set_cvar_once("qlx_discordTriggeredChannelIds", "")
        Plugin.set_cvar_once("qlx_discordTriggerTriggeredChannelChat", "quakelive")
        Plugin.set_cvar_once("qlx_discordMessagePrefix", "[DISCORD]")

        self.discord_trigger_triggered_channel_chat: str = Plugin.get_cvar("qlx_discordTriggerTriggeredChannelChat")
        self.discord_message_prefix: str = Plugin.get_cvar("qlx_discordMessagePrefix")
        self.discord_triggered_channel_ids: set[int] = int_set(
            Plugin.get_cvar("qlx_discordTriggeredChannelIds", set))

        self.bot.add_command(Command(self.triggered_chat, name=self.discord_trigger_triggered_channel_chat,
                                     checks=[self.is_message_in_triggered_channel],
                                     pass_context=True,
                                     help="send [message...] to the Quake Live server",
                                     require_var_positional=True))

        # noinspection PyTypeChecker
        slash_triggered_chat_command = app_commands.Command(name=self.discord_trigger_triggered_channel_chat,
                                                            description="send a message to the Quake Live server",
                                                            callback=self.slash_triggered_chat, parent=None, nsfw=False)
        slash_triggered_chat_command.guild_only = True
        self.bot.tree.add_command(slash_triggered_chat_command)

    def is_message_in_triggered_channel(self, ctx: Context) -> bool:
        """
        Checks whether the message originate in a configured triggered channel

        :param: ctx: the context the trigger happened in
        """
        return ctx.message.channel.id in self.discord_triggered_channel_ids

    @staticmethod
    def command_length(ctx: Context) -> int:
        return len(f"{ctx.prefix}{ctx.invoked_with} ")

    async def triggered_chat(self, ctx: Context, *_args, **_kwargs) -> None:
        """
        Relays a message from the triggered channels to minqlx

        :param: ctx: the context the trigger happened in
        :param: _message: the message to send to minqlx
        """
        prefix_length = self.command_length(ctx)
        minqlx.CHAT_CHANNEL.reply(
            self._format_message_to_quake(ctx.message.channel,
                                          ctx.message.author,
                                          ctx.message.clean_content[prefix_length:]))

    @app_commands.describe(message="message to send to the server")
    async def slash_triggered_chat(self, interaction: Interaction, message: str) -> None:
        channel = interaction.channel
        if not isinstance(channel, GuildChannel):
            await interaction.response.send_message(content="tried to send a message from the wrong channel",
                                                    ephemeral=True)
            return

        minqlx.CHAT_CHANNEL.reply(
            self._format_message_to_quake(channel, interaction.user, message))

        embed = Embed(color=Color.red(), title="sent message to Quake Live server", description=message)
        await interaction.response.send_message(embed=embed)

    def _format_message_to_quake(self, channel: GuildChannel, author: Member, content: str) -> str:
        """
        Format the channel, author, and content of a message so that it will be displayed nicely in the Quake Live
        console.

        :param: channel: the channel, the message came from.
        :param: author: the author of the original message.
        :param: content: the message itself, ideally taken from message.clean_content to avoid ids of mentioned users
        and channels on the discord server.
        :return: the formatted message that may be sent back to Quake Live.
        """
        sender = author.name
        if author.nick is not None:
            sender = author.nick

        return f"{self.discord_message_prefix} ^5#{channel.name} ^6{sender}^7:^2 {content}"


async def setup(bot: Bot):
    await bot.add_cog(TriggeredChat(bot))
