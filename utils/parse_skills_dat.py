import os
import sys
import json
from bs4 import BeautifulSoup
from collections import namedtuple
import utils


class SkillParser:
    def __init__(self, skill_dir=None):
        self.util_dir = os.path.dirname(os.path.realpath(__file__))
        self.SkillData = namedtuple("SkillData", ["name", "desc", "icon"])
        self.dat_path = os.path.join(self.util_dir, "..", "server_data", "dat_files")
        self.Skill = namedtuple("Skill", ["id", "level"])

    def parse(self):
        self.skill_data = self.create_skill_db()
        self.skill_order = self.get_skill_order()
        return self.skill_data, self.skill_order

    def get_skill_order(self):
        lines = utils.read_encrypted(self.dat_path, "npcgrp.dat")

        header = lines[0].split("\t")
        skill_cols = []
        for i, col in enumerate(header):
            if "dtab" in col:
                skill_cols.append(i)
        skill_cnt_col = skill_cols[0]  # First mention of 'dtab' is the skill count for that npc
        skill_cols = skill_cols[1:]

        skill_order = {}
        for line in lines[1:]:
            line = line.split("\t")

            npc_id = int(line[0])
            skill_order[npc_id] = []

            skill_cnt = int(line[skill_cnt_col])
            if skill_cnt < 2:
                # For some reason in L2Reborn files, treasure chests have 1 skill,
                # whereas at least two skills are needed (skill id + level)
                continue
            for idx in range(0, skill_cnt, 2):
                skill_id = int(line[skill_cols[idx]])
                skill_lvl = int(line[skill_cols[idx + 1]])
                skill_order[npc_id].append(self.Skill(skill_id, skill_lvl))

        return skill_order

    def create_skill_db(self):
        lines = utils.read_encrypted(self.dat_path, "skillgrp.dat")

        skill_icons = {}
        for line in lines[1:]:
            line = line.split("\t")
            id, level, icon = int(line[0]), int(line[1]), line[10]

            if id not in skill_icons:
                skill_icons[id] = {}
            skill_icons[id][level] = icon

        lines = utils.read_encrypted(self.dat_path, "skillname-e.dat")

        skill_data = {}
        for line in lines[1:]:
            line = line.split("\t")
            id, level = int(line[0]), int(line[1])
            name = line[2].strip("\\0").strip("a,")
            desc = line[3].strip("\\0").strip("a,")
            if desc == "none":
                desc = ""

            if id not in skill_data:
                skill_data[id] = {}
            skill_data[id][level] = self.SkillData(name, desc, skill_icons[id][level])

        return skill_data


if __name__ == "__main__":
    parser = NpcParser()
    parser.parse()
    parser.dump()
