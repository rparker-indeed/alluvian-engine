#!/usr/bin/env python

"""A simple Multi-User Dungeon (MUD) game. Players can talk to each
other, examine their surroundings and move between rooms.

Some ideas for things to try adding:
    * More rooms to explore
    * An 'emote' command e.g. 'emote laughs out loud' -> 'Mark laughs
        out loud'
    * A 'whisper' command for talking to individual players
    * A 'shout' command for yelling to players in all rooms
    * Items to look at in rooms e.g. 'look fireplace' -> 'You see a
        roaring, glowing fire'
    * Items to pick up e.g. 'take rock' -> 'You pick up the rock'
    * Monsters to fight
    * Loot to collect
    * Saving players accounts between sessions
    * A password login
    * A shop from which to buy items

author: Mark Frimston - mfrimston@gmail.com
"""

import json
import os

# import the MUD server class
from alluvian.server.mudserver import MudServer
from alluvian.constants import PROJECT_ROOT
from alluvian.commands.command_interpreter import CommandInterpreter
from players.models import Player
from alluvian.server.connection_session import ConnectionSession

# structure defining the rooms in the game. Try adding more rooms to the game!
with open(os.path.join(PROJECT_ROOT, 'lib/world/rooms.json')) as roomfile:
    rooms = json.loads(roomfile.read())


# stores the players in the game
players = {}

# start the server
mud = MudServer()

COMMANDS = CommandInterpreter.build_cmd_list()

# main game loop. We loop forever (i.e. until the program is terminated)
while True:

    # 'update' must be called in the loop to keep the game running and give
    # us up-to-date information
    mud.update()

    # go through any newly connected players
    for id in mud.get_new_players():

        # add the new player to the dictionary, noting that they've not been
        # named yet.
        # The dictionary key is the player's id number. We set their room to
        # None initially until they have entered a name
        # Try adding more player stats - level, gold, inventory, etc
        players[id] = ConnectionSession()

        # send the new player a prompt for their name
        mud.send_message(id, "By what name do you wish to be known?")

    # go through any recently disconnected players
    for id in mud.get_disconnected_players():

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        # go through all the players in the game
        for pid, pl in players.items():
            # send each player a message to tell them about the diconnected
            # player
            mud.send_message(pid, "{} quit the game".format(
                                                        players[id].name))

        # remove the player's entry in the player dictionary
        del(players[id])

    # go through any new commands sent from players
    for id, command, params in mud.get_commands():

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        connection_session = players[id]
        # if the player hasn't given their name yet, use this first command as
        # their name and move them to the starting room.
        if not connection_session.room:  # Has not been assigned start room, hasn't made it passed auth.
            if not connection_session.name:
                connection_session.name = command
                if Player.objects.filter(name=command).count() == 0:
                    connection_session.new_player = True
                    mud.send_message(id, f"Give me a password for \"{connection_session.name}\": ")
                else:
                    mud.send_message(id, "Password:")
                continue
            elif not connection_session.password:
                if connection_session.new_player:
                    connection_session.password = command
                    try:
                        Player.objects.create(name=connection_session.name,
                                              password=connection_session.password)
                        mud.send_message(id, "Ok... registered")
                    except:
                        mud.send_message(id, "Error creating player.")
                else:
                    connection_session.password = command
                    player = Player.objects.get(name=connection_session.name)
                    if player.check_pw(command):
                        mud.send_message(id, "Bad Password, Goodbye")
                        mud.close_socket(id)
                        del(players[id])
                    else:
                        mud.send_message(id, "Success!  PRESS ANY KEY TO CONTINUE")
                        connection_session.room = "Tavern"
                    continue

            # go through all the players in the game
            for pid, pl in players.items():
                # send each player a message to tell them about the new player
                mud.send_message(pid, "{} entered the game".format(
                                                        players[id].name))

            # send the new player a welcome message
            mud.send_message(id, "Welcome to the game, {}. ".format(
                                                           players[id].name)
                             + "Type 'help' for a list of commands. Have fun!")

            # send the new player the description of their current room
            mud.send_message(id, rooms[players[id].room]["description"])

        # each of the possible commands is handled below. Try adding new
        # commands to the game!
        else:
            if not command:
                mud.send_message(id, "\n")
                continue
            cmd = CommandInterpreter.cmd_search(command)
            if cmd:
                cmd(mud_server=mud, sessions=connection_session, actor=id).execute()
            else:
                mud.send_message(id, "Huh?!")