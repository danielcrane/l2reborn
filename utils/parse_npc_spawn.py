import os
import re
from collections import namedtuple


class SpawnParser:
    def __init__(self, sql_path=None):
        self.SpawnData = namedtuple("SpawnData", ["x", "y"])

        self.util_dir = os.path.dirname(os.path.realpath(__file__))
        if sql_path is None:
            self.sql_path = os.path.join(self.util_dir, "..", "server_data", "sql")

    def parse(self):
        self.spawn_data = {}

        self.parse_spawn_normal()
        self.parse_spawn_raidboss()
        self.parse_spawn_grandboss()

        return self.spawn_data

    def parse_spawn_normal(self):
        regex = "\(('-?[0-9]{1,9}', ){7}('-?[0-9]')\)"
        with open(f"{self.sql_path}/spawnlist.sql", "r") as f:
            lines = f.readlines()

        for line in lines:
            match = re.match(regex, line)
            if match:
                data = eval(match.group())  # Evaluate the matched line as a tuple
                data = tuple(int(d) for d in data)  # Convert data points from str to numbers

                npc_id, loc_x, loc_y = data[0], data[1], data[2]
                if npc_id not in self.spawn_data:
                    self.spawn_data[npc_id] = []

                # Convert data to SpawnData named tuple format, then add to dict:
                self.spawn_data[npc_id].append(self.SpawnData(loc_x, loc_y))

    def parse_spawn_raidboss(self):
        regex = "\((-?[0-9]{1,9},){9}(-?[0-9])\)"
        with open(f"{self.sql_path}/raidboss_spawnlist.sql", "r") as f:
            lines = f.readlines()

        for line in lines:
            match = re.match(regex, line)
            if match:
                data = eval(match.group())  # Evaluate the matched line as a tuple
                data = tuple(int(d) for d in data)  # Convert data points from str to numbers

                npc_id, loc_x, loc_y = data[0], data[1], data[2]
                if npc_id not in self.spawn_data:
                    self.spawn_data[npc_id] = []

                # Convert data to SpawnData named tuple format, then add to dict:
                self.spawn_data[npc_id].append(self.SpawnData(loc_x, loc_y))

    def parse_spawn_grandboss(self):
        regex = "\((-?[0-9]{1,9}, ){8}(-?[0-9])\)"
        with open(f"{self.sql_path}/grandboss_data.sql", "r") as f:
            lines = f.readlines()

        for line in lines:
            match = re.match(regex, line)
            if match:
                data = eval(match.group())  # Evaluate the matched line as a tuple
                data = tuple(int(d) for d in data)  # Convert data points from str to numbers

                npc_id, loc_x, loc_y = data[0], data[1], data[2]
                if npc_id not in self.spawn_data:
                    self.spawn_data[npc_id] = []

                # Convert data to SpawnData named tuple format, then add to dict:
                self.spawn_data[npc_id].append(self.SpawnData(loc_x, loc_y))
