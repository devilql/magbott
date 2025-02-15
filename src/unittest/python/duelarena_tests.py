from minqlx_plugin_test import *

import unittest
from mockito import *
from mockito.matchers import *
from hamcrest import *

from undecorated import undecorated

from duelarena import *


class DuelArenaTests(unittest.TestCase):

    def setUp(self):
        setup_plugin()
        setup_cvars({
            "qlx_duelarenaDuelToNormalThreshold": "6",
            "qlx_duelarenaNormalToDuelThreshold": "11",
            "g_roundWarmupDelay": "2000"
        })
        setup_game_in_progress("ca")
        connected_players()
        self.plugin = duelarena()
        spy2(self.plugin.duelarena_game.reset)
        self.plugin.ensure_duel_players = lambda: None
        self.activate_duelarena()

    def activate_duelarena(self):
        self.plugin.duelarena_game.duelmode = True

    def tearDown(self):
        unstub()

    def test_when_map_changed_duelarena_is_reset(self):
        self.plugin.handle_map_change("thunderstruck", "ca")

        verify(self.plugin.duelarena_game).reset()

    def test_when_player_was_loaded_with_no_game_running(self):
        setup_no_game()
        loaded_player = fake_player(3, "Loaded Player", "spectator")
        connected_players(loaded_player)
        self.deactivate_duelarena()

        undecorated(self.plugin.handle_player_loaded)(self.plugin, loaded_player)

        assert_player_was_told(loaded_player, any, times=0)

    def deactivate_duelarena(self):
        self.plugin.duelarena_game.duelmode = False

    def test_when_player_was_loaded_directly_on_team(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        loaded_player = fake_player(3, "Loaded Player", "red")
        connected_players(red_player, blue_player, loaded_player)
        self.setup_duelarena_players(red_player, blue_player)
        self.deactivate_duelarena()

        undecorated(self.plugin.handle_player_loaded)(self.plugin, loaded_player)

        assert_player_was_told(loaded_player, any, times=0)

    def setup_duelarena_players(self, *players):
        for player in players:
            self.plugin.duelarena_game.playerset.append(player.steam_id)

    def test_when_first_player_was_loaded(self):
        loaded_player = fake_player(4, "Loaded Player", "spectator")
        connected_players(loaded_player)

        undecorated(self.plugin.handle_player_loaded)(self.plugin, loaded_player)

        assert_player_was_told(loaded_player, any(str), times=0)

    def test_when_second_player_was_loaded(self):
        red_player = fake_player(1, "Red Player", "red")
        loaded_player = fake_player(3, "Loaded Player", "spectator")
        connected_players(red_player, loaded_player)
        self.setup_duelarena_players(red_player)
        self.deactivate_duelarena()

        undecorated(self.plugin.handle_player_loaded)(self.plugin, loaded_player)

        assert_player_was_told(loaded_player, any, times=0)

    def test_when_third_player_was_loaded(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        loaded_player = fake_player(4, "Loaded Player", "spectator")
        connected_players(red_player, blue_player, loaded_player)
        self.setup_duelarena_players(red_player, blue_player)
        self.deactivate_duelarena()

        undecorated(self.plugin.handle_player_loaded)(self.plugin, loaded_player)

        assert_player_was_told(
            loaded_player,
            "Loaded Player, join to activate DuelArena! Round winner stays in, loser rotates with spectator.")

    def test_when_fourth_player_was_loaded_during_warmup(self):
        setup_game_in_warmup()
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "spectator")
        loaded_player = fake_player(4, "Loaded Player")
        connected_players(red_player, blue_player, spec_player, loaded_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)

        undecorated(self.plugin.handle_player_loaded)(self.plugin, loaded_player)

        assert_player_was_told(loaded_player, any, times=0)

    def queue_up_players(self, *players):
        for player in players:
            self.plugin.duelarena_game.queue.insert(0, player.steam_id)

    def test_when_fourth_player_was_loaded_while_duelarena_activated(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "spectator")
        loaded_player = fake_player(4, "Loaded Player")
        connected_players(red_player, blue_player, spec_player, loaded_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)

        undecorated(self.plugin.handle_player_loaded)(self.plugin, loaded_player)

        assert_player_was_told(
            loaded_player,
            "Loaded Player^7, type !join to join Duel Arena or press join button to force switch to Clan Arena!")

    def test_when_fourth_player_was_loaded_while_duelarena_deactivated(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "spectator")
        loaded_player = fake_player(4, "Loaded Player")
        connected_players(red_player, blue_player, spec_player, loaded_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)
        self.deactivate_duelarena()

        undecorated(self.plugin.handle_player_loaded)(self.plugin, loaded_player)

        assert_player_was_told(loaded_player, any, times=0)

    def test_when_sixth_player_was_loaded(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player1 = fake_player(3, "Speccing Player1", "spectator")
        spec_player2 = fake_player(4, "Speccing Player2", "spectator")
        spec_player3 = fake_player(5, "Speccing Player3", "spectator")
        loaded_player = fake_player(6, "Loaded Player")
        connected_players(red_player, blue_player, spec_player1, spec_player2, spec_player3, loaded_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player1)
        self.plugin.player_agree_to_join = [spec_player2.steam_id, spec_player3.steam_id]
        self.queue_up_players(spec_player1)

        undecorated(self.plugin.handle_player_loaded)(self.plugin, loaded_player)

        assert_player_was_told(loaded_player,
                               "Loaded Player^7, type !join to join Duel Arena "
                               "or press join button to force switch to Clan Arena!")

    def test_when_no_running_game_allow_player_switch_attempt(self):
        switching_player = fake_player(1, "Switching Player")
        connected_players(switching_player)
        setup_no_game()

        return_code = self.plugin.handle_team_switch_event(switching_player, "red", "spectator")

        assert_that(return_code, is_(None))

    def test_when_first_player_tries_to_join_any_team_she_gets_added_to_playerset(self):
        switching_player = fake_player(1, "Switching Player")
        connected_players(switching_player)

        self.plugin.handle_team_switch_event(switching_player, "spectator", "any")

        self.assert_playerset_contains(switching_player)

    def assert_playerset_contains(self, *players):
        player_ids = list(player.steam_id for player in players)
        assert_that(self.plugin.duelarena_game.playerset, has_items(*player_ids))

    def test_when_third_player_tries_to_join_duelarena_gets_activated(self):
        switching_player = fake_player(3, "Switching Player")
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        connected_players(red_player,
                          blue_player,
                          switching_player)
        self.setup_duelarena_players(red_player, blue_player)
        self.deactivate_duelarena()

        return_code = self.plugin.handle_team_switch_event(switching_player, "spectator", "blue")

        self.assert_duelarena_has_been_activated()
        assert_player_was_told(switching_player, DUELARENA_JOIN_MSG)
        assert_that(return_code, is_(minqlx.RET_STOP_ALL))

    def assert_duelarena_has_been_activated(self):
        assert_that(self.plugin.duelarena_game.is_activated(), is_(True))
        assert_plugin_center_printed("DuelArena activated!")
        assert_plugin_sent_to_console(
            "DuelArena activated! Round winner stays in, loser rotates with spectator. Hit 8 rounds first to win!")

    def test_when_red_player_switches_to_spec_she_is_removed_from_playerset(self):
        switching_player = fake_player(1, "Switching Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(spec_player,
                          blue_player,
                          switching_player)
        self.setup_duelarena_players(switching_player, blue_player, spec_player)
        self.setup_scores({switching_player: 5, blue_player: 2, spec_player: 2})
        self.activate_duelarena()

        self.plugin.handle_team_switch_event(switching_player, "red", "spectator")

        self.assert_playerset_does_not_contain(switching_player)
        self.assert_duelarena_has_been_deactivated()

    def setup_scores(self, scores):
        for player in scores.keys():
            self.plugin.duelarena_game.scores[player.steam_id] = scores[player]

    def assert_playerset_does_not_contain(self, *players):
        assert_that(self.plugin.duelarena_game.playerset, not_(has_items([player.steam_id for player in players])))

    def assert_duelarena_has_been_deactivated(self):
        assert_that(self.plugin.duelarena_game.is_activated(), is_(False))
        assert_that(self.plugin.duelarena_game.is_pending_initialization(), is_(False))
        assert_plugin_center_printed("DuelArena deactivated!")
        assert_plugin_sent_to_console("DuelArena has been deactivated!")

    def test_when_player_switches_to_spec_during_warmup_she_is_removed_from_queue(self):
        setup_game_in_warmup()
        switching_player = fake_player(2, "Switching Player", "blue")
        red_player = fake_player(1, "Red Player", "red")
        spec_player = fake_player(3, "Speccingg Player")
        connected_players(switching_player, red_player, spec_player)
        self.setup_duelarena_players(switching_player, red_player)
        self.activate_duelarena()

        self.plugin.handle_team_switch_event(switching_player, "blue", "spectator")

        self.assert_queue_does_not_contain(switching_player)
        self.assert_playerset_does_not_contain(switching_player)

    def assert_queue_does_not_contain(self, *players):
        assert_that(self.plugin.duelarena_game.queue, not_(has_items([player.steam_id for player in players])))

    def test_when_player_switch_to_spec_inititiated_by_plugin_clear_field(self):
        switching_player = fake_player(1, "Switching Player", "blue")
        red_player = fake_player(2, "Blue Player", "red")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(spec_player,
                          red_player,
                          switching_player)
        self.setup_duelarena_players(switching_player, red_player, spec_player)
        self.plugin.duelarena_game.player_spec.append(switching_player.steam_id)
        self.activate_duelarena()

        self.plugin.handle_team_switch_event(switching_player, "red", "spectator")

        assert_that(self.plugin.duelarena_game.player_spec, is_(list()))

    def test_when_game_in_warmup_announcement_is_shown(self):
        setup_game_in_warmup()
        switching_player = fake_player(3, "Switching Player")
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        connected_players(red_player,
                          blue_player,
                          switching_player)
        self.setup_duelarena_players(red_player, blue_player, switching_player)

        self.plugin.handle_team_switch_event(switching_player, "spectator", "any")

        assert_plugin_center_printed("Ready up for ^6DuelArena^7!")
        assert_plugin_sent_to_console(
            "Ready up for ^6DuelArena^7!")

    def test_plugin_initiated_switch_to_red(self):
        switching_player = fake_player(1, "Switching Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "red")
        connected_players(switching_player,
                          blue_player,
                          spec_player)
        self.plugin.duelarena_game.player_red = switching_player.steam_id
        self.setup_duelarena_players(switching_player, blue_player, spec_player)

        self.plugin.handle_team_switch_event(switching_player, "spectator", "red")

        assert_that(self.plugin.duelarena_game.player_red, is_(None))

    def test_plugin_initiated_switch_to_blue(self):
        red_player = fake_player(1, "Red Player", "red")
        switching_player = fake_player(2, "Switching Player")
        spec_player = fake_player(3, "Speccing Player", "blue")
        connected_players(red_player,
                          switching_player,
                          spec_player)
        self.plugin.duelarena_game.player_blue = switching_player.steam_id
        self.setup_duelarena_players(red_player, switching_player, spec_player)

        self.plugin.handle_team_switch_event(switching_player, "spectator", "blue")

        assert_that(self.plugin.duelarena_game.player_blue, is_(None))

    def test_when_player_disconnects_she_gets_removed_from_playerset(self):
        red_player = fake_player(1, "Red Player", "red")
        disconnecting_player = fake_player(2, "Disconnecting Player")
        spec_player = fake_player(3, "Speccing Player", "blue")
        connected_players(red_player,
                          disconnecting_player,
                          spec_player)
        self.setup_duelarena_players(red_player, disconnecting_player, spec_player)

        self.plugin.handle_player_disconnect(disconnecting_player, "ragequit")

        self.assert_playerset_does_not_contain(disconnecting_player)

    def test_when_player_not_in_playerset_disconnects_nothing_happens(self):
        red_player = fake_player(1, "Red Player", "red")
        disconnecting_player = fake_player(2, "Disconnecting Player")
        spec_player = fake_player(3, "Speccing Player", "blue")
        connected_players(red_player,
                          disconnecting_player,
                          spec_player)
        self.setup_duelarena_players(red_player, spec_player)
        self.activate_duelarena()

        self.plugin.handle_player_disconnect(disconnecting_player, "ragequit")

        self.assert_playerset_does_not_contain(disconnecting_player)

    def test_when_in_duelarena_third_player_disconnects_duelarena_deactivates(self):
        red_player = fake_player(1, "Red Player", "red")
        disconnecting_player = fake_player(2, "Disconnecting Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(red_player, disconnecting_player, spec_player)
        self.setup_duelarena_players(red_player, disconnecting_player, spec_player)
        self.queue_up_players(spec_player)
        self.setup_scores({red_player: 5, disconnecting_player: 3, spec_player: 4})
        self.activate_duelarena()

        self.plugin.handle_player_disconnect(disconnecting_player, "ragequit")

        self.assert_duelarena_has_been_deactivated()

    def test_when_not_in_duelarena_fourth_player_disconnects_duelarena_activates(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        disconnecting_player = fake_player(4, "Disconnecting Player")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player, disconnecting_player)
        self.queue_up_players(spec_player, disconnecting_player)
        self.deactivate_duelarena()

        self.plugin.handle_player_disconnect(disconnecting_player, "ragequit")

        self.assert_duelarena_has_been_activated()
        self.assert_playerset_does_not_contain(disconnecting_player)

    def test_when_not_in_duelarena_fourth_player_disconnects_duelarena_activates_during_warmup(self):
        setup_game_in_warmup()
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        disconnecting_player = fake_player(4, "Disconnecting Player")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player, disconnecting_player)
        self.queue_up_players(spec_player, disconnecting_player)
        self.deactivate_duelarena()

        self.plugin.handle_player_disconnect(disconnecting_player, "ragequit")

        self.assert_duelarena_has_been_activated()
        self.assert_playerset_does_not_contain(disconnecting_player)

    def test_inits_duelmode_when_game_countdown_starts(self):
        red_player = fake_player(1, "Red Player" "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)

        undecorated(self.plugin.handle_game_countdown)(self.plugin)

        assert_that(self.plugin.duelarena_game.is_activated(), is_(True))

    def test_deactivates_duelarena_when_game_countdown_starts_with_too_few_players(self):
        red_player = fake_player(1, "Red Player" "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        connected_players(red_player, blue_player)
        self.setup_duelarena_players(red_player, blue_player)

        undecorated(self.plugin.handle_game_countdown)(self.plugin)

        self.assert_duelarena_has_been_deactivated()

    def test_leaves_duelarena_deactivated_when_game_countdown_starts_with_too_few_players(self):
        red_player = fake_player(1, "Red Player" "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        connected_players(red_player, blue_player)
        self.setup_duelarena_players(red_player, blue_player)
        self.deactivate_duelarena()

        undecorated(self.plugin.handle_game_countdown)(self.plugin)

        assert_that(self.plugin.duelarena_game.is_activated(), is_(False))

    def test_leaves_duelarena_activated_when_game_countdown_starts_with_three_players(self):
        red_player = fake_player(1, "Red Player" "red")
        blue_player1 = fake_player(2, "Blue Player1", "blue")
        blue_player2 = fake_player(3, "Blue Player2", "blue")
        connected_players(red_player, blue_player1, blue_player2)
        self.setup_duelarena_players(red_player, blue_player1, blue_player2)

        undecorated(self.plugin.handle_game_countdown)(self.plugin)

        assert_that(self.plugin.duelarena_game.is_activated(), is_(True))

    def test_activates_duelarena_when_not_activated_during_game_countdown_with_three_players(self):
        red_player = fake_player(1, "Red Player" "red")
        blue_player1 = fake_player(2, "Blue Player1", "blue")
        blue_player2 = fake_player(3, "Blue Player2", "blue")
        connected_players(red_player, blue_player1, blue_player2)
        self.setup_duelarena_players(red_player, blue_player1, blue_player2)
        self.deactivate_duelarena()

        undecorated(self.plugin.handle_game_countdown)(self.plugin)

        self.assert_duelarena_has_been_activated()

    def test_does_nothing_when_game_countdown_starts_with_too_many_players(self):
        red_player = fake_player(1, "Red Player" "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player1 = fake_player(3, "Speccing Player1")
        spec_player2 = fake_player(4, "Speccing Player2")

        connected_players(red_player, blue_player, spec_player1, spec_player2)
        self.setup_duelarena_players(red_player, blue_player)

        undecorated(self.plugin.handle_game_countdown)(self.plugin)

        self.assert_duelarena_has_been_deactivated()

    def test_handle_round_countdown_when_not_in_duelmode(self):
        self.deactivate_duelarena()

        self.plugin.handle_round_countdown(42)

        assert_plugin_center_printed(any(str), times=0)
        assert_plugin_sent_to_console(any(str), times=0)

    def test_handle_round_countdown_announces_matching_parties(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        speccing_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, speccing_player)
        self.setup_duelarena_players(red_player, blue_player, speccing_player)
        self.queue_up_players(speccing_player)

        self.plugin.handle_round_countdown(3)

        assert_plugin_center_printed("Red Player ^2vs^7 Blue Player")
        assert_plugin_sent_to_console("DuelArena: Red Player ^2vs^7 Blue Player")

    def test_handle_round_countdown_with_one_team_empty(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "spectator")
        speccing_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, speccing_player)
        self.setup_duelarena_players(red_player, blue_player, speccing_player)
        self.queue_up_players(speccing_player)

        self.plugin.handle_round_countdown(3)

        assert_plugin_center_printed(any(str), times=0)
        assert_plugin_sent_to_console(any(str), times=0)

    def test_handle_round_end_with_no_game(self):
        setup_no_game()

        return_code = undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "DRAW"})

        assert_that(return_code, is_(None))

    def test_handle_round_end_with_wrong_gametype(self):
        setup_game_in_progress("ft")

        return_code = undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "DRAW"})

        assert_that(return_code, is_(None))

    def test_handle_round_end_with_red_team_hit_roundlimit(self):
        setup_game_in_progress(roundlimit=8, red_score=8, blue_score=4)

        return_code = undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "RED"})

        assert_that(return_code, is_(None))

    def test_handle_round_end_with_blue_team_hit_roundlimit(self):
        setup_game_in_progress(roundlimit=8, red_score=3, blue_score=8)

        return_code = undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "RED"})

        assert_that(return_code, is_(None))

    def test_handle_round_end_when_duel_was_aborted(self):
        setup_game_in_progress(red_score=5, blue_score=2)
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "spectator")
        speccing_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, speccing_player)
        self.setup_duelarena_players(red_player, blue_player, speccing_player)
        self.queue_up_players(speccing_player)
        self.setup_scores({red_player: 5, blue_player: 2, speccing_player: 2})
        self.plugin.duelarena_game.print_reset_scores = True

        undecorated(self.plugin.handle_round_end)(self.plugin, None)

        assert_plugin_sent_to_console("DuelArena results:")
        assert_plugin_sent_to_console("Place ^31.^7 Red Player ^7(Wins:^25^7)")
        assert_plugin_sent_to_console("Place ^32.^7 Blue Player ^7(Wins:^22^7)")
        assert_plugin_sent_to_console("Place ^32.^7 Speccing Player ^7(Wins:^22^7)")

    def test_handle_round_end_inits_duelarena(self):
        setup_game_in_progress(red_score=5, blue_score=3)
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "spectator")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player, spec_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_that(self.plugin.duelarena_game.is_activated(), is_(True))
        assert_that(self.plugin.duelarena_game.initduel, is_(False))
        self.assert_scores_are({red_player: 5, blue_player: 3, spec_player: 0})
        assert_player_was_put_on(red_player, "spectator")
        assert_player_was_put_on(spec_player, "red")

    def test_handle_round_end_puts_playerset_to_queue_if_not_enqueued(self):
        red_player = fake_player(1, "Red Player" "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, spec_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        self.assert_queue_contains(spec_player)

    def test_handle_round_end_puts_specs_on_teams_to_spec(self):
        red_player = fake_player(1, "Red Player" "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "blue")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player, spec_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_player_was_put_on(spec_player, "spectator")

    def test_handle_round_end_players_already_on_correct_teams(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "spectator")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player, spec_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_player_was_put_on(red_player, "spectator")
        assert_player_was_put_on(blue_player, any(str), times=0)
        assert_player_was_put_on(spec_player, "red")

    def test_handle_round_end_players_already_on_opposing_teams(self):
        red_player = fake_player(1, "Red Player", "blue")
        blue_player = fake_player(2, "Blue Player", "red")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player, spec_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_player_was_put_on(blue_player, "spectator")
        assert_player_was_put_on(red_player, any(str), times=0)
        assert_player_was_put_on(spec_player, "red")

    def test_handle_round_end_both_players_on_red(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "red")
        spec_player = fake_player(3, "Speccing Player", "blue")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player, spec_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_player_was_put_on(red_player, any(str), times=0)
        assert_player_was_put_on(blue_player, "blue")

    def test_handle_round_end_just_red_player_on_blue_team(self):
        red_player = fake_player(1, "Red Player", "blue")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "red")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player, spec_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_player_was_put_on(red_player, any(str), times=0)
        assert_player_was_put_on(blue_player, "red")

    def test_handle_round_end_just_blue_player_on_blue_team_red_on_spec(self):
        red_player = fake_player(1, "Red Player", "spectator")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "red")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player, spec_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_player_was_put_on(red_player, "red")
        assert_player_was_put_on(blue_player, any(str), times=0)

    def test_handle_round_end_just_blue_player_on_red_team_red_on_spec(self):
        red_player = fake_player(1, "Red Player", "spectator")
        blue_player = fake_player(2, "Blue Player", "red")
        spec_player = fake_player(3, "Speccing Player", "blue")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player, spec_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_player_was_put_on(red_player, "red")
        assert_player_was_put_on(blue_player, "spectator")
        assert_player_was_put_on(spec_player, any(str), times=0)

    def test_handle_round_end_both_players_on_spec(self):
        red_player = fake_player(1, "Red Player", "spectator")
        blue_player = fake_player(2, "Blue Player", "spectator")
        spec_player = fake_player(3, "Speccing Player", "blue")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(red_player, blue_player, spec_player)
        self.plugin.duelarena_game.initduel = True

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_player_was_put_on(red_player, "red")
        assert_player_was_put_on(blue_player, "blue")

    def test_handle_round_end_with_no_duelarena_active(self):
        self.deactivate_duelarena()

        return_code = undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        assert_that(return_code, is_(None))

    def test_handle_round_end_with_a_draw(self):
        return_code = undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "DRAW"})

        assert_that(return_code, is_(None))

    def test_handle_round_end_red_player_won_stores_red_score(self):
        setup_game_in_progress(red_score=6, blue_score=3)
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)
        self.setup_scores({red_player: 5, blue_player: 3, spec_player: 7})

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "RED"})

        self.assert_scores_are({red_player: 6, blue_player: 3, spec_player: 7})

    def assert_scores_are(self, scores):
        scores_with_steam_ids = {player.steam_id: value for player, value in scores.items()}
        assert_that(self.plugin.duelarena_game.scores, is_(scores_with_steam_ids))

    def test_handle_round_end_blue_player_won_stores_blue_score(self):
        setup_game_in_progress(red_score=5, blue_score=4)
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)
        self.setup_scores({red_player: 5, blue_player: 3, spec_player: 7})

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "BLUE"})

        self.assert_scores_are({red_player: 5, blue_player: 4, spec_player: 7})

    def test_handle_round_end_next_player_already_on_team(self):
        setup_game_in_progress(red_score=6, blue_score=3)
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "red")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)
        self.setup_scores({red_player: 5, blue_player: 3, spec_player: 7})

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "RED"})

        assert_that(self.plugin.duelarena_game.is_activated(), is_(True))

    def test_handle_round_end_red_player_won_puts_switching_queued_player_to_losing_team(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)
        self.setup_scores({red_player: 5, blue_player: 3, spec_player: 7})

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "RED"})

        assert_player_was_put_on(spec_player, "blue")
        assert_player_was_put_on(blue_player, "spectator")
        assert_player_was_told(
            blue_player, "Blue Player, you've been put back to DuelArena queue. Prepare for your next duel!")
        self.assert_queue_contains(blue_player)

    def test_handle_round_end_red_player_won_puts_blue_player_on_spec(self):
        setup_game_in_progress(red_score=6, blue_score=3)
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)
        self.setup_scores({red_player: 5, blue_player: 3, spec_player: 7})

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "RED"})

        assert_game_addteamscore("blue", 4)

    def test_handle_round_end_when_player_queue_empty_duelarena_is_deactivated(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        connected_players(red_player, blue_player)
        self.setup_duelarena_players(red_player, blue_player)
        self.setup_scores({red_player: 5, blue_player: 3})

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "RED"})

        self.assert_duelarena_has_been_deactivated()

    def test_handle_round_end_when_next_player_no_longer_available(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        connected_players(red_player, blue_player)
        self.setup_duelarena_players(red_player, blue_player)
        self.queue_up_players(fake_player(42, "no longer connected Player"))
        self.setup_scores({red_player: 5, blue_player: 3})

        undecorated(self.plugin.handle_round_end)(self.plugin, {"TEAM_WON": "RED"})

        self.assert_duelarena_has_been_deactivated()

    def test_handle_game_end_with_no_game_ending(self):
        setup_no_game()

        return_code = self.plugin.handle_game_end({})

        assert_that(return_code, is_(None))

    def test_handle_game_end_which_was_aborted(self):
        self.activate_duelarena()

        return_code = self.plugin.handle_game_end({"ABORTED": True})

        assert_that(return_code, is_(None))

    def test_handle_game_end_with_not_duelarena_active(self):
        self.deactivate_duelarena()

        return_code = self.plugin.handle_game_end({"ABORTED": False})

        assert_that(return_code, is_(None))

    def assert_queue_contains(self, *players):
        player_ids = [player.steam_id for player in players]
        player_ids.reverse()
        assert_that(self.plugin.duelarena_game.queue, is_(player_ids))

    def test_handle_game_end_prints_results(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(red_player, blue_player, spec_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)
        self.setup_scores({red_player: 7, blue_player: 5, spec_player: 7})

        self.plugin.handle_game_end({"ABORTED": False, "TSCORE0": 8, "TSCORE1": 5})

        assert_plugin_sent_to_console("DuelArena results:")
        assert_plugin_sent_to_console("Place ^31.^7 Red Player ^7(Wins:^28^7)")
        assert_plugin_sent_to_console("Place ^32.^7 Speccing Player ^7(Wins:^27^7)")
        assert_plugin_sent_to_console("Place ^33.^7 Blue Player ^7(Wins:^25^7)")

    def test_handle_game_end_winner_already_quit(self):
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(blue_player, spec_player)
        self.setup_duelarena_players(fake_player(1, "Red Player", "red"), blue_player, spec_player)
        self.queue_up_players(spec_player)

        return_code = self.plugin.handle_game_end({"ABORTED": False, "TSCORE0": 8, "TSCORE1": 3})

        assert_that(return_code, is_(None))

    def test_handle_game_end_loser_already_quit(self):
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player")
        connected_players(blue_player, spec_player)
        self.setup_duelarena_players(fake_player(1, "Red Player", "red"), blue_player, spec_player)
        self.queue_up_players(spec_player)

        return_code = self.plugin.handle_game_end({"ABORTED": False, "TSCORE0": 6, "TSCORE1": 8})

        assert_that(return_code, is_(None))

    def test_join_cmd_while_duelarena_is_deactivated(self):
        self.deactivate_duelarena()

        return_code = self.plugin.cmd_join(None, None, None)

        assert_that(return_code, is_(None))

    def test_join_cmd_player_already_player_in_duelarena(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "spectator")
        joining_player = fake_player(42, "!joining Player", "spectator")
        connected_players(red_player, blue_player, spec_player, joining_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player, joining_player)
        self.queue_up_players(spec_player, joining_player)

        return_code = self.plugin.cmd_join(joining_player, None, None)

        assert_that(return_code, is_(None))

    def test_join_cmd_player_on_wrong_team(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "spectator")
        joining_player = fake_player(42, "!joining Player", "red")
        connected_players(red_player, blue_player, spec_player, joining_player)
        self.setup_duelarena_players(red_player, blue_player)
        self.queue_up_players(spec_player)

        return_code = self.plugin.cmd_join(joining_player, None, None)

        assert_that(return_code, is_(None))

    def test_join_cmd_player_pending_to_join(self):
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        spec_player = fake_player(3, "Speccing Player", "spectator")
        joining_player = fake_player(42, "!joining Player", "spectator")
        connected_players(red_player, blue_player, spec_player, joining_player)
        self.setup_duelarena_players(red_player, blue_player, spec_player)
        self.queue_up_players(spec_player)

        self.plugin.cmd_join(joining_player, "!join", mocked_channel())

        self.assert_playerset_contains(red_player, blue_player, spec_player, joining_player)
        self.assert_queue_contains(spec_player, joining_player)
        assert_player_was_told(joining_player, "You successfully joined the DuelArena queue. Prepare for your duel!")
        assert_plugin_sent_to_console(matches(".*joined DuelArena!"))


class DuelArenaGameTests(unittest.TestCase):

    def setUp(self):
        setup_plugin()
        setup_cvars({
            "qlx_duelarenaDuelToNormalThreshold": "6",
            "qlx_duelarenaNormalToDuelThreshold": "11"
        })
        setup_game_in_progress("ca")
        connected_players()
        self.duelarena_game = DuelArenaGame()

    def tearDown(self):
        unstub()

    def test_add_player_adds_player_that_is_not_in_playerset(self):
        player_sid = 42

        self.duelarena_game.add_player(player_sid)

        self.assert_playerset_contains(player_sid)

    def assert_playerset_contains(self, *items):
        assert_that(self.duelarena_game.playerset, has_items(*items))

    def test_add_player_when_player_already_in_playerset(self):
        player_sid = 42
        self.duelarena_game.playerset = [player_sid]

        self.duelarena_game.add_player(player_sid)

        assert_that(self.duelarena_game.playerset, is_([player_sid]))

    def test_add_player_when_duelarena_activated_queues_player(self):
        player_sid = 42
        self.duelarena_game.duelmode = True

        self.duelarena_game.add_player(player_sid)

        self.assert_players_are_enqueued(player_sid)

    def assert_players_are_enqueued(self, *items):
        assert_that(self.duelarena_game.queue, has_items(*items))

    def test_add_player_when_duelarena_activated_and_player_already_in_queue(self):
        player_sid = 42
        self.duelarena_game.duelmode = True
        self.duelarena_game.queue = [1, player_sid, 2]

        self.duelarena_game.add_player(player_sid)

        assert_that(self.duelarena_game.queue, is_([1, player_sid, 2]))

    def test_add_player_when_duelarena_activated_initializes_score(self):
        player_sid = 42
        self.duelarena_game.duelmode = True

        self.duelarena_game.add_player(player_sid)

        self.assert_players_is_in_scorelist(player_sid)

    def assert_players_is_in_scorelist(self, *items):
        assert_that(self.duelarena_game.scores, has_items(*items))

    def test_add_player_when_duelarena_activated_and_player_already_has_score(self):
        player_sid = 42
        self.duelarena_game.duelmode = True
        self.duelarena_game.scores[player_sid] = 5

        self.duelarena_game.add_player(player_sid)

        assert_that(self.duelarena_game.scores[player_sid], is_(5))

    def test_remove_player_when_player_is_in_playerset(self):
        player_sid = 42
        self.duelarena_game.playerset = [player_sid]

        self.duelarena_game.remove_player(player_sid)

        self.assert_playerset_does_not_contain(player_sid)

    def assert_playerset_does_not_contain(self, *items):
        assert_that(self.duelarena_game.playerset, not_(has_items(*items)))

    def test_remove_player_when_player_is_in_playerset_and_in_queue(self):
        player_sid = 42
        removed_player = fake_player(player_sid, "Removed Players")
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        connected_players(removed_player, red_player, blue_player)
        self.duelarena_game.playerset = [1, 2, player_sid]
        self.duelarena_game.queue = [1, player_sid, 2]

        self.duelarena_game.remove_player(player_sid)

        self.assert_playerset_does_not_contain(player_sid)
        self.assert_players_are_not_enqueued(player_sid)

    def assert_players_are_not_enqueued(self, *items):
        assert_that(self.duelarena_game.queue, not_(has_items(*items)))

    def test_remove_player_when_player_is_not_in_playerset(self):
        player_sid = 42
        self.duelarena_game.playerset = [1, 2]

        self.duelarena_game.remove_player(player_sid)

        self.assert_playerset_does_not_contain(player_sid)

    def test_remove_player_when_player_should_be_emergency_replaced(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True

        player_sid = 42
        removed_player = fake_player(player_sid, "Removed Players", "red")
        spec_player = fake_player(1, "Red Player", "spectator")
        blue_player = fake_player(2, "Blue Player", "blue")
        connected_players(removed_player, spec_player, blue_player)
        self.duelarena_game.playerset = [1, 2, player_sid]
        self.duelarena_game.queue = [1]
        self.duelarena_game.scores = {player_sid: 3, spec_player.steam_id: 5, blue_player: 1}

        self.duelarena_game.remove_player(player_sid)

        assert_player_was_put_on(spec_player, "red")

    def test_should_emergency_replace_with_no_game(self):
        setup_no_game()

        return_code = self.duelarena_game.should_emergency_replace_player(123)

        assert_that(return_code, is_(False))

    def test_should_emergency_replace_with_game_in_warmup(self):
        setup_game_in_warmup()

        return_code = self.duelarena_game.should_emergency_replace_player(123)

        assert_that(return_code, is_(False))

    def test_should_emergency_replace_with_duelarena_deactivated(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = False

        return_code = self.duelarena_game.should_emergency_replace_player(123)

        assert_that(return_code, is_(False))

    def test_should_emergency_replace_with_player_not_in_duelarena(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True

        return_code = self.duelarena_game.should_emergency_replace_player(123)

        assert_that(return_code, is_(False))

    def test_should_emergency_replace_with_player_already_disconnected(self):
        player_sid = 42
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.playerset = [player_sid, 1, 2]

        return_code = self.duelarena_game.should_emergency_replace_player(player_sid)

        assert_that(return_code, is_(False))

    def test_should_emergency_replace_with_player_in_spec(self):
        player_sid = 42
        spec_player = fake_player(player_sid, "Spec Player", "spectator")
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(2, "Blue Player", "blue")
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.playerset = [player_sid, red_player.steam_id, blue_player.steam_id]
        connected_players(spec_player, red_player, blue_player)

        return_code = self.duelarena_game.should_emergency_replace_player(player_sid)

        assert_that(return_code, is_(False))

    def test_should_emergency_replace_with_player_in_red(self):
        player_sid = 42
        spec_player = fake_player(2, "Spec Player", "spectator")
        red_player = fake_player(player_sid, "Red Player", "red")
        blue_player = fake_player(1, "Blue Player", "blue")
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.playerset = [spec_player.steam_id, red_player.steam_id, blue_player.steam_id]
        connected_players(spec_player, red_player, blue_player)

        return_code = self.duelarena_game.should_emergency_replace_player(player_sid)

        assert_that(return_code, is_(True))

    def test_should_emergency_replace_with_player_in_blue(self):
        player_sid = 42
        spec_player = fake_player(2, "Spec Player", "spectator")
        red_player = fake_player(1, "Red Player", "red")
        blue_player = fake_player(player_sid, "Blue Player", "blue")
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.playerset = [spec_player.steam_id, red_player.steam_id, blue_player.steam_id]
        connected_players(spec_player, red_player, blue_player)

        return_code = self.duelarena_game.should_emergency_replace_player(player_sid)

        assert_that(return_code, is_(True))

    def test_next_player_sid_gives_top_of_queue(self):
        self.duelarena_game.queue = [42]

        next_sid = self.duelarena_game.next_player_sid()

        assert_that(next_sid, is_(42))

    def test_next_player_sid_with_empty_queue(self):
        self.duelarena_game.queue = []

        next_sid = self.duelarena_game.next_player_sid()

        assert_that(next_sid, is_(None))

    def test_is_player_for_steam_id_in_playerset(self):
        self.duelarena_game.playerset = [1, 2, 42]

        return_code = self.duelarena_game.is_player(42)

        assert_that(return_code, is_(True))

    def test_is_player_for_steam_id_not_in_playerset(self):
        self.duelarena_game.playerset = [1, 2, 4]

        return_code = self.duelarena_game.is_player(42)

        assert_that(return_code, is_(False))

    def test_activate_when_duelarena_already_activated(self):
        self.duelarena_game.duelmode = True

        self.duelarena_game.activate()

        assert_that(self.duelarena_game.is_activated(), is_(True))

    def test_activate_activates_duelmode(self):
        self.duelarena_game.duelmode = False

        self.duelarena_game.activate()

        assert_that(self.duelarena_game.is_activated(), is_(True))

    def test_activate_reset_print_reset_scores(self):
        self.duelarena_game.duelmode = False
        self.duelarena_game.print_reset_scores = True

        self.duelarena_game.activate()

        assert_that(self.duelarena_game.print_reset_scores, is_(False))

    def test_activate_announces_activation(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = False

        self.duelarena_game.activate()

        assert_plugin_center_printed(matches("DuelArena activated.*"))

    def test_activate_schedules_initialization(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = False
        self.duelarena_game.scores = {}

        self.duelarena_game.activate()

        assert_that(self.duelarena_game.initduel, is_(True))

    def test_activate_leaves_existing_scores_untouched(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = False
        self.duelarena_game.scores = {123: 3, 456: 2, 789: 1}

        self.duelarena_game.activate()

        assert_that(self.duelarena_game.initduel, is_(False))

    def test_activate_with_no_game_running_does_not_init_duelmode(self):
        setup_no_game()
        self.duelarena_game.duelmode = False

        self.duelarena_game.activate()

        assert_that(self.duelarena_game.initduel, is_(False))

    def test_announce_activation_with_no_game(self):
        setup_no_game()

        self.duelarena_game.announce_activation()

        assert_plugin_center_printed(any(str), times=0)
        assert_plugin_sent_to_console(any(str), times=0)

    def test_announce_activation_announces_activation_of_duelarena(self):
        setup_game_in_progress()

        self.duelarena_game.announce_activation()

        assert_plugin_center_printed(matches("DuelArena activated.*"))
        assert_plugin_sent_to_console(matches("DuelArena activated.*"))

    def test_should_not_be_activated_with_too_few_players(self):
        self.duelarena_game.playerset = [123, 455]

        return_code = self.duelarena_game.should_be_activated()

        assert_that(return_code, is_(False))

    def test_should_not_be_activated_with_too_many_players(self):
        self.duelarena_game.playerset = [123, 455, 789, 1337]

        return_code = self.duelarena_game.should_be_activated()

        assert_that(return_code, is_(False))

    def test_should_be_activated_with_no_game_running(self):
        setup_no_game()
        self.duelarena_game.playerset = [123, 455, 789]

        return_code = self.duelarena_game.should_be_activated()

        assert_that(return_code, is_(True))

    def test_should_be_activated_with_game_in_warmup(self):
        setup_game_in_warmup()
        self.duelarena_game.playerset = [123, 455, 789]

        return_code = self.duelarena_game.should_be_activated()

        assert_that(return_code, is_(True))

    def test_should_not_be_activated_when_game_progressed_too_far_already(self):
        setup_game_in_progress(red_score=6, blue_score=6)
        self.duelarena_game.playerset = [123, 455, 789]

        return_code = self.duelarena_game.should_be_activated()

        assert_that(return_code, is_(False))

    def test_should_be_activated_when_game_did_not_progress_far_enough(self):
        setup_game_in_progress(red_score=5, blue_score=5)
        self.duelarena_game.playerset = [123, 455, 789]

        return_code = self.duelarena_game.should_be_activated()

        assert_that(return_code, is_(True))

    def test_deactivate_when_already_deactivated(self):
        self.duelarena_game.duelmode = False

        self.duelarena_game.deactivate()

        assert_that(self.duelarena_game.is_activated(), is_(False))

    def test_deactivate_deactivates_and_resets_duelarena(self):
        self.duelarena_game.duelmode = True

        self.duelarena_game.deactivate()

        assert_that(self.duelarena_game.is_activated(), is_(False))
        assert_that(self.duelarena_game.is_pending_initialization(), is_(False))
        assert_that(self.duelarena_game.player_red, is_(None))
        assert_that(self.duelarena_game.player_blue, is_(None))
        assert_that(self.duelarena_game.player_spec, empty())
        assert_plugin_center_printed(matches("DuelArena deactivated.*"))
        assert_plugin_sent_to_console(matches("DuelArena .*deactivated.*"))

    def test_deactivate_schedules_printing_final_scores(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.scores = {123: 3, 456: 2, 789: 1}

        self.duelarena_game.deactivate()

        assert_that(self.duelarena_game.print_reset_scores, is_(True))

    def test_deactivate_resets_scores_with_no_game_running(self):
        setup_no_game()
        self.duelarena_game.duelmode = True
        self.duelarena_game.scores = {123: 3, 456: 2, 789: 1}

        self.duelarena_game.deactivate()

        assert_that(self.duelarena_game.print_reset_scores, is_(False))
        assert_that(self.duelarena_game.scores, is_({}))

    def test_deactivate_resets_scores_with_game_in_warmup(self):
        setup_game_in_warmup()
        self.duelarena_game.duelmode = True
        self.duelarena_game.scores = {123: 3, 456: 2, 789: 1}

        self.duelarena_game.deactivate()

        assert_that(self.duelarena_game.print_reset_scores, is_(False))
        assert_that(self.duelarena_game.scores, is_({}))

    def test_deactivate_leaves_scores_with_duelarena_pending_init(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.initduel = True
        self.duelarena_game.scores = {123: 3, 456: 2, 789: 1}

        self.duelarena_game.deactivate()

        assert_that(self.duelarena_game.print_reset_scores, is_(False))
        assert_that(self.duelarena_game.scores, is_({123: 3, 456: 2, 789: 1}))

    def test_deactivate_resets_scores_with_no_scores_initialized(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.scores = {}

        self.duelarena_game.deactivate()

        assert_that(self.duelarena_game.print_reset_scores, is_(False))
        assert_that(self.duelarena_game.scores, is_({}))

    def test_announce_deactivation_with_no_game(self):
        setup_no_game()

        self.duelarena_game.announce_deactivation()

        assert_plugin_center_printed(any(str), times=0)
        assert_plugin_sent_to_console(any(str), times=0)

    def test_announce_deactivation_announces_duelarena_deactivation(self):
        self.duelarena_game.announce_deactivation()

        assert_plugin_center_printed(matches("DuelArena deactivated.*"))
        assert_plugin_sent_to_console(matches("DuelArena .*deactivated.*"))

    def test_should_not_be_aborted_when_deactivated(self):
        self.duelarena_game.duelmode = False

        return_code = self.duelarena_game.should_be_aborted()

        assert_that(return_code, is_(False))

    def test_should_not_be_aborted_when_no_game_running(self):
        setup_no_game()
        self.duelarena_game.duelmode = True

        return_code = self.duelarena_game.should_be_aborted()

        assert_that(return_code, is_(True))

    def test_should_not_be_aborted_when_game_in_warmup(self):
        setup_game_in_warmup()
        self.duelarena_game.duelmode = True

        return_code = self.duelarena_game.should_be_aborted()

        assert_that(return_code, is_(True))

    def test_should_not_be_aborted_with_right_amount_of_players(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.playerset = [123, 456, 789]

        return_code = self.duelarena_game.should_be_aborted()

        assert_that(return_code, is_(False))

    def test_should_be_aborted_with_too_few_players(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.playerset = [123, 789]

        return_code = self.duelarena_game.should_be_aborted()

        assert_that(return_code, is_(True))

    def test_should_be_aborted_with_too_many_players(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.playerset = [123, 456, 789, 246, 135]

        return_code = self.duelarena_game.should_be_aborted()

        assert_that(return_code, is_(True))

    def test_should_be_aborted_with_too_few_rounds_played(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.playerset = [123, 456]
        self.duelarena_game.scores = {123: 3, 456: 2}

        return_code = self.duelarena_game.should_be_aborted()

        assert_that(return_code, is_(True))

    def test_should_not_be_aborted_with_too_many_rounds_played(self):
        setup_game_in_progress()
        self.duelarena_game.duelmode = True
        self.duelarena_game.playerset = [123, 456]
        self.duelarena_game.scores = {123: 4, 456: 6}

        return_code = self.duelarena_game.should_be_aborted()

        assert_that(return_code, is_(False))

    def test_reset_resets_duelarena(self):
        self.duelarena_game.duelmode = True
        self.duelarena_game.initduel = True
        self.duelarena_game.playerset = [123, 456, 789]
        self.duelarena_game.queue = [123]

        self.duelarena_game.reset()

        assert_that(self.duelarena_game.duelmode, is_(False))
        assert_that(self.duelarena_game.initduel, is_(False))
        assert_that(self.duelarena_game.playerset, is_([]))
        assert_that(self.duelarena_game.queue, is_([]))

    def test_put_active_players_on_the_right_teams_both_on_right_team(self):
        setup_game_in_progress(red_score=6, blue_score=1)
        player1 = fake_player(1, "Red Player", "red")
        player2 = fake_player(2, "Blue Player", "blue")
        connected_players(player1, player2)
        self.duelarena_game.scores = {player1.steam_id: 4, player2.steam_id: 2}

        self.duelarena_game.put_active_players_on_the_right_teams(player1.steam_id, player2.steam_id)

        assert_game_addteamscore("red", -2)
        assert_game_addteamscore("blue", 1)
        assert_player_was_put_on(player1, any(str), times=0)
        assert_player_was_put_on(player2, any(str), times=0)

    def test_put_active_players_on_the_right_teams_both_on_opposing_teams(self):
        setup_game_in_progress(red_score=6, blue_score=1)
        player1 = fake_player(1, "Blue Player", "blue")
        player2 = fake_player(2, "Red Player", "red")
        connected_players(player1, player2)
        self.duelarena_game.scores = {player1.steam_id: 4, player2.steam_id: 2}

        self.duelarena_game.put_active_players_on_the_right_teams(player1.steam_id, player2.steam_id)

        assert_game_addteamscore("red", -4)
        assert_game_addteamscore("blue", 3)
        assert_player_was_put_on(player1, any(str), times=0)
        assert_player_was_put_on(player2, any(str), times=0)

    def test_put_active_players_on_the_right_teams_red_in_red_blue_in_spec(self):
        setup_game_in_progress(red_score=6, blue_score=1)
        player1 = fake_player(1, "Red Player", "red")
        player2 = fake_player(2, "Blue Player", "spectator")
        connected_players(player1, player2)
        self.duelarena_game.scores = {player1.steam_id: 4, player2.steam_id: 2}

        self.duelarena_game.put_active_players_on_the_right_teams(player1.steam_id, player2.steam_id)

        assert_game_addteamscore("red", -2)
        assert_game_addteamscore("blue", 1)
        assert_player_was_put_on(player1, any(str), times=0)
        assert_that(self.duelarena_game.player_blue, is_(player2.steam_id))
        assert_player_was_put_on(player2, "blue")

    def test_put_active_players_on_the_right_teams_red_in_blue_blue_in_spec(self):
        setup_game_in_progress(red_score=6, blue_score=1)
        player1 = fake_player(1, "Red Player", "blue")
        player2 = fake_player(2, "Blue Player", "spectator")
        connected_players(player1, player2)
        self.duelarena_game.scores = {player1.steam_id: 4, player2.steam_id: 2}

        self.duelarena_game.put_active_players_on_the_right_teams(player1.steam_id, player2.steam_id)

        assert_game_addteamscore("red", -4)
        assert_game_addteamscore("blue", 3)
        assert_player_was_put_on(player1, any(str), times=0)
        assert_that(self.duelarena_game.player_red, is_(player2.steam_id))
        assert_player_was_put_on(player2, "red")

    def test_put_active_players_on_the_right_teams_blue_in_blue_red_in_spec(self):
        setup_game_in_progress(red_score=6, blue_score=1)
        player1 = fake_player(1, "Red Player", "spectator")
        player2 = fake_player(2, "Blue Player", "blue")
        connected_players(player1, player2)
        self.duelarena_game.scores = {player1.steam_id: 4, player2.steam_id: 2}

        self.duelarena_game.put_active_players_on_the_right_teams(player1.steam_id, player2.steam_id)

        assert_game_addteamscore("red", -2)
        assert_game_addteamscore("blue", 1)
        assert_player_was_put_on(player1, "red")
        assert_that(self.duelarena_game.player_red, is_(player1.steam_id))
        assert_player_was_put_on(player2, any(str), times=0)

    def test_put_active_players_on_the_right_teams_blue_in_red_red_in_spec(self):
        setup_game_in_progress(red_score=6, blue_score=1)
        player1 = fake_player(1, "Red Player", "spectator")
        player2 = fake_player(2, "Blue Player", "red")
        connected_players(player1, player2)
        self.duelarena_game.scores = {player1.steam_id: 4, player2.steam_id: 2}

        self.duelarena_game.put_active_players_on_the_right_teams(player1.steam_id, player2.steam_id)

        assert_game_addteamscore("red", -4)
        assert_game_addteamscore("blue", 3)
        assert_player_was_put_on(player1, "blue")
        assert_that(self.duelarena_game.player_blue, is_(player1.steam_id))
        assert_player_was_put_on(player2, any(str), times=0)

    def test_put_active_players_on_the_right_teams_both_players_in_spec(self):
        setup_game_in_progress(red_score=6, blue_score=1)
        player1 = fake_player(1, "Red Player", "spectator")
        player2 = fake_player(2, "Blue Player", "spectator")
        connected_players(player1, player2)
        self.duelarena_game.scores = {player1.steam_id: 4, player2.steam_id: 2}

        self.duelarena_game.put_active_players_on_the_right_teams(player1.steam_id, player2.steam_id)

        assert_game_addteamscore("red", -2)
        assert_game_addteamscore("blue", 1)
        assert_that(self.duelarena_game.player_red, is_(player1.steam_id))
        assert_player_was_put_on(player1, "red")
        assert_that(self.duelarena_game.player_blue, is_(player2.steam_id))
        assert_player_was_put_on(player2, "blue")

    def test_ensure_duelarena_players_with_plugin_deactivated(self):
        self.duelarena_game.duelmode = False

        return_code = self.duelarena_game.ensure_duelarena_players()

        assert_that(return_code, is_(None))

    def test_ensure_duelarena_player_with_too_few_players(self):
        self.duelarena_game.duelmode = True

        connected_players(fake_player(1, "Red Player", "red"), fake_player(2, "Blue Player", "blue"))

        return_code = self.duelarena_game.ensure_duelarena_players()

        assert_that(return_code, is_(None))

    def test_ensure_duelarena_player_with_too_many_players(self):
        self.duelarena_game.duelmode = True

        connected_players(fake_player(1, "Red Player1", "red"), fake_player(2, "Blue Player1", "blue"),
                          fake_player(3, "Red Player2", "red"), fake_player(4, "Blue Player2", "blue"))

        return_code = self.duelarena_game.ensure_duelarena_players()

        assert_that(return_code, is_(None))

    def test_ensure_duelarena_player_with_one_extra_player_in_red(self):
        self.duelarena_game.duelmode = True

        red_player = fake_player(1, "Red Player1", "red")
        blue_player = fake_player(2, "Blue Player1", "blue")
        extra_player = fake_player(3, "Red Player2", "red")
        connected_players(red_player, blue_player, extra_player)
        self.duelarena_game.playerset = [red_player.steam_id, blue_player.steam_id]

        self.duelarena_game.ensure_duelarena_players()

        assert_player_was_put_on(extra_player, "spectator")
        assert_that(self.duelarena_game.player_spec, has_item(extra_player.steam_id))
        assert_player_was_put_on(red_player, any(str), times=0)
        assert_player_was_put_on(blue_player, any(str), times=0)

    def test_ensure_duelarena_player_with_one_enqueued_player_in_red(self):
        self.duelarena_game.duelmode = True

        red_player = fake_player(1, "Red Player1", "red")
        blue_player = fake_player(2, "Blue Player1", "blue")
        extra_player = fake_player(3, "Red Player2", "red")
        connected_players(red_player, blue_player, extra_player)
        self.duelarena_game.playerset = [red_player.steam_id, blue_player.steam_id, extra_player.steam_id]
        self.duelarena_game.queue = [extra_player.steam_id]

        self.duelarena_game.ensure_duelarena_players()

        assert_player_was_put_on(extra_player, "spectator")
        assert_that(self.duelarena_game.player_spec, has_item(extra_player.steam_id))
        assert_player_was_put_on(red_player, any(str), times=0)
        assert_player_was_put_on(blue_player, any(str), times=0)

    def test_ensure_duelarena_player_with_one_extra_player_in_blue(self):
        self.duelarena_game.duelmode = True

        red_player = fake_player(1, "Red Player1", "red")
        blue_player = fake_player(2, "Blue Player1", "blue")
        extra_player = fake_player(3, "Blue Player2", "blue")
        connected_players(red_player, blue_player, extra_player)
        self.duelarena_game.playerset = [red_player.steam_id, blue_player.steam_id]

        self.duelarena_game.ensure_duelarena_players()

        assert_player_was_put_on(extra_player, "spectator")
        assert_that(self.duelarena_game.player_spec, has_item(extra_player.steam_id))
        assert_player_was_put_on(red_player, any(str), times=0)
        assert_player_was_put_on(blue_player, any(str), times=0)

    def test_ensure_duelarena_player_with_one_enqueued_player_in_blue(self):
        self.duelarena_game.duelmode = True

        red_player = fake_player(1, "Red Player1", "red")
        blue_player = fake_player(2, "Blue Player1", "blue")
        extra_player = fake_player(3, "Red Player2", "blue")
        connected_players(red_player, blue_player, extra_player)
        self.duelarena_game.playerset = [red_player.steam_id, blue_player.steam_id, extra_player.steam_id]
        self.duelarena_game.queue = [extra_player.steam_id]

        self.duelarena_game.ensure_duelarena_players()

        assert_player_was_put_on(extra_player, "spectator")
        assert_that(self.duelarena_game.player_spec, has_item(extra_player.steam_id))
        assert_player_was_put_on(red_player, any(str), times=0)
        assert_player_was_put_on(blue_player, any(str), times=0)
