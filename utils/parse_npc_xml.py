import os
import sys
import json
from bs4 import BeautifulSoup
from collections import namedtuple


class NpcParser:
    def __init__(self, item_dir=None, npc_dir=None):
        self.util_dir = os.path.dirname(os.path.realpath(__file__))

        if item_dir is None:
            self.item_dir = os.path.join(self.util_dir, "..", "server_data", "items")
        if npc_dir is None:
            self.npc_dir = os.path.join(self.util_dir, "..", "server_data", "npcs")

        # Stats to extract from NPC XMLs:
        self.stats = {
            "level",
            "type",
            "hp",
            "mp",
            "exp",
            "sp",
            "patk",
            "pdef",
            "matk",
            "mdef",
            "runspd",
        }

        self.item_data = None
        self.drop_data = None

    def parse(self):
        self.item_data = self.parse_item_xml()
        self.drop_data = self.parse_npc_xml()
        return self.drop_data

    def dump(self, out_file="drop_data_xml.json"):
        json.dump(self.drop_data, open("drop_data_xml.json", "w"))

    def parse_item_xml(self):
        Item = namedtuple("Item", ["name", "type", "crystal"])
        Crystal = namedtuple("Crystal", ["count", "type"])

        item_files = []
        for file in os.listdir(self.item_dir):
            if file.endswith(".xml"):
                item_files.append(file)
        item_data = {}

        for file in item_files:
            with open(os.path.join(self.item_dir, file), "r") as f:
                contents = f.read()
            soup = BeautifulSoup(contents, features="html.parser")

            items = soup.find_all("item")
            for item in items:
                item_id = eval(item["id"])
                item_name = item["name"]
                item_type = item["type"]
                try:
                    crystal_count = int(item.find("set", {"name": "crystal_count"})["val"])
                    crystal_type = item.find("set", {"name": "crystal_type"})["val"]
                except:
                    crystal_count = crystal_type = None

                crystal = Crystal(crystal_count, crystal_type)
                item_data[item_id] = Item(item_name, item_type, crystal)
        return item_data

    def parse_npc_xml(self):
        Skill = namedtuple("Skill", ["id", "level"])
        if self.item_data is None:
            assert ValueError("self.item_data is None, first parse item xml")
        npc_files = []
        for file in os.listdir(self.npc_dir):
            if file.endswith(".xml"):
                npc_files.append(file)

        npc_data = {}
        for file in npc_files:
            with open(os.path.join(self.npc_dir, file), "r") as f:
                contents = f.read()
            soup = BeautifulSoup(contents, features="html.parser")

            npcs = soup.find_all("npc")

            for npc in npcs:
                npc_id = eval(npc["id"])
                npc_name = npc["name"]
                npc_title = npc["title"]

                npc_data[npc_id] = {
                    "name": npc_name,
                    "title": npc_title,
                    "file": file,
                    "stats": [],
                    "drop": [],
                    "spoil": [],
                }

                stat_list = npc.find_all("set")

                stats = {}
                for stat in stat_list:
                    stat_name = stat["name"].lower()
                    if stat_name in self.stats:  # If it's a stat we're interested in:
                        try:  # If stat is numerical, then round:
                            stats[stat_name] = str(round(eval(stat["val"])))
                        except NameError:  # Otherwise:
                            stats[stat_name] = stat["val"]
                    elif stat_name == "dropherbgroup":
                        if stat["val"] != "0":
                            stats["herbs"] = "Yes"
                        else:
                            stats["herbs"] = "No"

                ai = npc.find("ai")
                if ai.has_attr("aggro") and ai["aggro"] != "0":
                    stats["agro"] = "Yes"
                else:
                    stats["agro"] = "No"

                skills = []
                skill_list = npc.find("skills")
                for skill in skill_list.find_all("skill"):
                    skills.append(Skill(int(skill["id"]), int(skill["level"])))
                npc_data[npc_id]["skills"] = skills

                npc_data[npc_id]["stats"] = stats

                drop_list = npc.find("drops")

                if drop_list is None:
                    continue

                categories = drop_list.find_all("category")
                for category in categories:
                    drops = category.find_all("drop")
                    for drop in drops:

                        id = eval(drop["itemid"])
                        min_amt = eval(drop["min"])
                        max_amt = eval(drop["max"])
                        chance = eval(drop["chance"]) / 1e6

                        cat = eval(category["id"])
                        if cat != -1:
                            npc_data[npc_id]["drop"].append(
                                [id, min_amt, max_amt, chance, self.item_data[id].name]
                            )
                        else:
                            # id == -1 means spoil
                            npc_data[npc_id]["spoil"].append(
                                [id, min_amt, max_amt, chance, self.item_data[id].name]
                            )

        return npc_data


if __name__ == "__main__":
    parser = NpcParser()
    parser.parse()
    parser.dump()
