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

    def parse(self):
        self.skill_data = self.create_skill_db()
        return self.skill_data

    def create_skill_db(self):
        dat_path = os.path.join(self.util_dir, "..", "server_data", "dat_files")

        lines = utils.read_encrypted(dat_path, "skillgrp.dat")

        skill_icons = {}
        for line in lines[1:]:
            line = line.split("\t")
            id, level, icon = int(line[0]), int(line[1]), line[10]

            if id not in skill_icons:
                skill_icons[id] = {}
            skill_icons[id][level] = icon

        lines = utils.read_encrypted(dat_path, "skillname-e.dat")

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
