import minqlx
import redis

from collections import Counter

COLLECTED_SOULZ_KEY =\
    "minqlx:players:{}:soulz"
REAPERZ_KEY = "minqlx:players:{}:reaperz"
_name_key = "minqlx:players:{}:last_used_name"


class frag_stats(minqlx.Plugin):

    def __init__(self):
        super().__init__()

        self.set_cvar_once("qlx_fragstats_toplimit", "10")

        self.toplimit = self.get_cvar("qlx_fragstats_toplimit", int)

        self.add_hook("player_disconnect", self.handle_player_disconnect)
        self.add_hook("game_countdown", self.handle_game_countdown)
        self.add_hook("death", self.handle_death)

        self.add_command("mapsoulz", self.cmd_mapsoulz)
        self.add_command("mapreaperz", self.cmd_mapreaperz)
        self.add_command("soulz", self.cmd_soulz)
        self.add_command("reaperz", self.cmd_reaperz)

        self.frag_log = []

    def handle_player_disconnect(self, player, reason):
        self.db.set(_name_key.format(player.steam_id), player.name)

    def handle_game_countdown(self):
        self.frag_log = []

    def handle_death(self, victim, killer, data):
        if not self.game or self.game.state != "in_progress":
            return

        if data["MOD"] == "SWITCHTEAM":
            return

        if killer is not None and victim is not None and victim.steam_id == killer.steam_id:
            return

        recorded_killer = self.determine_killer(killer, data["MOD"])

        self.record_frag(recorded_killer, victim.steam_id)

    def record_frag(self, recorded_killer, victim_sid):
        self.frag_log.append((recorded_killer, victim_sid))

        if redis.VERSION[0] == 2:
            self.db.zincrby(COLLECTED_SOULZ_KEY.format(recorded_killer), victim_sid, 1)
            self.db.zincrby(REAPERZ_KEY.format(victim_sid), recorded_killer, 1)
        else:
            self.db.zincrby(COLLECTED_SOULZ_KEY.format(recorded_killer), 1, victim_sid)
            self.db.zincrby(REAPERZ_KEY.format(victim_sid), 1, recorded_killer)

    def determine_killer(self, killer, means_of_death):
        if killer is not None:
            return killer.steam_id

        if means_of_death == "HURT":
            return "void"

        if means_of_death == "SLIME":
            return "acid"

        if means_of_death == "WATER":
            return "drowning"

        if means_of_death == "CRUSH":
            return "squished"

        return means_of_death.lower()

    def cmd_mapsoulz(self, player, msg, channel):
        if len(msg) == 1:
            fragger_name, fragger_identifier = self.identify_target(player, player)
        else:
            fragger_name, fragger_identifier = self.identify_target(player, msg[1])
            if fragger_name is None and fragger_identifier is None:
                return

        fragged_statistics = self.mapfrag_statistics_for(fragger_identifier)

        reply_channel = self.identify_reply_channel(channel)
        if len(fragged_statistics) == 0:
            reply_channel.reply("{}^7 didn't reap any soulz, yet.".format(fragger_name))
            return

        reply_channel.reply("Top {} reaped soulz for {}^7: {}".format(
            self.toplimit,
            fragger_name,
            ", ".join(
                "{}^7 ({})".format(victim, kill_count) for
                victim, kill_count in fragged_statistics.most_common(self.toplimit))))

    def identify_target(self, player, target):
        if hasattr(target, "name") and hasattr(target, "steam_id"):
            return target.name, target.steam_id

        if target in ["!lava", "!void", "!acid", "!drowning", "!squished", "!unknown", "!grenade", "!grenade_splash"]:
            return target[1:], target[1:]

        try:
            steam_id = int(target)
            if self.db.exists(_name_key.format(steam_id)):
                return self.resolve_player_name(steam_id), steam_id
        except ValueError:
            pass

        fragging_player = self.find_target_player_or_list_alternatives(player, target)
        if fragging_player is None:
            return None, None

        return fragging_player.name, fragging_player.steam_id

    def mapfrag_statistics_for(self, fragger_identifier):
        player_fragged_log = [killed for killer, killed in self.frag_log if killer == fragger_identifier]

        resolved_fragged_log = self.resolve_player_names(player_fragged_log)
        return Counter(resolved_fragged_log)

    def cmd_mapreaperz(self, player, msg, channel):
        if len(msg) == 1:
            fragged_name, fragged_identifier = self.identify_target(player, player)
        else:
            fragged_name, fragged_identifier = self.identify_target(player, msg[1])

        fragged_statistics = self.mapfraggers_of(fragged_identifier)

        reply_channel = self.identify_reply_channel(channel)
        if len(fragged_statistics) == 0:
            reply_channel.reply("{}^7's soul was not reaped by anyone, yet.".format(fragged_name))
            return

        reply_channel.reply("Top {} reaperz of {}^7's soul: {}".format(
            self.toplimit,
            fragged_name,
            ", ".join(
                "{}^7 ({})".format(victim, kill_count) for
                victim, kill_count in fragged_statistics.most_common(self.toplimit))))

    def mapfraggers_of(self, fragged_identifier):
        player_fragged_log = [killer for killer, killed in self.frag_log if killed == fragged_identifier]

        resolved_fragged_log = self.resolve_player_names(player_fragged_log)
        return Counter(resolved_fragged_log)

    def resolve_player_names(self, entries):
        if len(entries) == 0:
            return []
        if isinstance(entries[0], tuple):
            return {self.resolve_player_name(steam_id): int(value) for steam_id, value in entries}
        return [self.resolve_player_name(item) for item in entries]

    def resolve_player_name(self, item):
        try:
            steam_id = int(item)
        except ValueError:
            return item

        player = self.player(steam_id)

        if player is not None:
            return player.name

        if self.db.exists(_name_key.format(steam_id)):
            return self.db.get(_name_key.format(steam_id))

        return item

    def find_target_player_or_list_alternatives(self, player, target):
        # Tell a player which players matched
        def list_alternatives(players, indent=2):
            player.tell("A total of ^6{}^7 players matched for {}:".format(len(players), target))
            out = ""
            for p in players:
                out += " " * indent
                out += "{}^6:^7 {}\n".format(p.id, p.name)
            player.tell(out[:-1])

        try:
            steam_id = int(target)

            target_player = self.player(steam_id)
            if target_player:
                return target_player

        except ValueError:
            pass
        except minqlx.NonexistentPlayerError:
            pass

        target_players = self.find_player(target)

        # If there were absolutely no matches
        if not target_players:
            player.tell("Sorry, but no players matched your tokens: {}.".format(target))
            return None

        # If there were more than 1 matches
        if len(target_players) > 1:
            list_alternatives(target_players)
            return None

        # By now there can only be one person left
        return target_players.pop()

    def cmd_soulz(self, player, msg, channel):
        if len(msg) == 1:
            fragger_name, fragger_identifier = self.identify_target(player, player)
        else:
            fragger_name, fragger_identifier = self.identify_target(player, msg[1])
            if fragger_name is None and fragger_identifier is None:
                return

        fragged_statistics = self.overall_frag_statistics_for(fragger_identifier)

        reply_channel = self.identify_reply_channel(channel)
        if len(fragged_statistics) == 0:
            reply_channel.reply("{}^7 didn't reap any soulz, yet.".format(fragger_name))
            return

        reply_channel.reply("Top {} reaped soulz for {}^7: {}".format(
            self.toplimit,
            fragger_name,
            ", ".join(
                "{}^7 ({})".format(victim, kill_count) for
                victim, kill_count in fragged_statistics.most_common(self.toplimit))))

    def overall_frag_statistics_for(self, fragger_identifier):
        player_fragged_log = self.db.zrevrangebyscore(COLLECTED_SOULZ_KEY.format(fragger_identifier),
                                                      "+INF", "-INF", start=0, num=self.toplimit, withscores=True)

        resolved_fragged_log = self.resolve_player_names(player_fragged_log)
        return Counter(resolved_fragged_log)

    def cmd_reaperz(self, player, msg, channel):
        if len(msg) == 1:
            fragged_name, fragged_identifier = self.identify_target(player, player)
        else:
            fragged_name, fragged_identifier = self.identify_target(player, msg[1])
            if fragged_name is None and fragged_identifier is None:
                return

        fragged_statistics = self.overall_fraggers_of(fragged_identifier)

        reply_channel = self.identify_reply_channel(channel)
        if len(fragged_statistics) == 0:
            reply_channel.reply("{}^7's soul was not reaped by anyone, yet.".format(fragged_name))
            return

        reply_channel.reply("Top {} reaperz of {}^7's soul: {}".format(
            self.toplimit,
            fragged_name,
            ", ".join(
                "{}^7 ({})".format(victim, kill_count) for
                victim, kill_count in fragged_statistics.most_common(self.toplimit))))

    def overall_fraggers_of(self, fragged_identifier):
        player_fragger_log = self.db.zrevrangebyscore(REAPERZ_KEY.format(fragged_identifier), "+INF", "-INF",
                                                      start=0, num=self.toplimit, withscores=True)

        resolved_fragger_log = self.resolve_player_names(player_fragger_log)
        return Counter(resolved_fragger_log)

    def identify_reply_channel(self, channel):
        if channel in [minqlx.RED_TEAM_CHAT_CHANNEL, minqlx.BLUE_TEAM_CHAT_CHANNEL,
                       minqlx.SPECTATOR_CHAT_CHANNEL, minqlx.FREE_CHAT_CHANNEL]:
            return minqlx.CHAT_CHANNEL

        return channel
