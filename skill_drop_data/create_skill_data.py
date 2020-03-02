import numpy as np
import sys
import utils


class DataBuilder:
    def __init__(self, info=False, drops=True, spoils=True, VIP=False):
        self.original_data_path = "./original_data"  # Path of original data (without drop info)
        self.new_data_path = "./new_data"  # Output path of new data (with dorp info)

        self.npcs_xml_dir = "./npcs"  # Directory containing NPC xml files
        self.items_xml_dir = "./items"  # Directory containing item xml files

        self.VIP = VIP  # If VIP is True, adena amount/xp/sp/drop rates are all scaled accordingly
        self.VIP_rate = 1.5  # Multiplier for VIP rate

        self.skill_include = {"Information": info, "Drop": drops, "Spoil": spoils}
        self.skill_ids = {"Information": 20002, "Drop": 20000, "Spoil": 20001}
        self.skill_icons = {
            "Information": "icon.etc_lottery_card_i00",
            "Drop": "icon.etc_adena_i00",
            "Spoil": "icon.skill0254",
        }

    def build(self):
        print("[] Parsing NPC .xml files")
        sys.stdout.flush()
        self.parse_npc_xmls()
        print("[] Updating skillname-e.dat")
        sys.stdout.flush()
        self.modify_skill_name()
        print("[] Updating skillgrp.dat")
        sys.stdout.flush()
        self.modify_skill_grp()
        print("\n[] Build complete")
        sys.stdout.flush()

    def parse_npc_xmls(self):
        parser = utils.NpcParser()
        self.npc_data = parser.parse()

    def modify_skill_grp(self):
        """Takes an unmodified skillgrp.dat and adds the skills which will store
        drop/spoil/other info about mobs

        Returns
        -------
        None
            Outputs updated skillgrp.dat to self.new_data_path

        """

        fname = "skillgrp.dat"

        # Define the format each line takes:
        line_format = "{}\t{}\t2\t0\t-1\t0\t0.00000000\t0\t\t\t{}\t0\t0\t0\t0\t-1\t-1"
        # First decode and convert from .dat to .txt
        lines = utils.read_encrypted(self.original_data_path, fname)

        for npc_id, npc in self.npc_data.items():
            for info_type in self.skill_ids.keys():
                if not self.skill_include[info_type]:
                    # If this type of info isn't to be included, then skip:
                    continue
                # Add info to line_format and append to lines:
                lines.append(
                    line_format.format(
                        self.skill_ids[info_type], npc_id, self.skill_icons[info_type]
                    )
                )

        # Now encrypt and write updated lines:
        utils.write_encrypted(self.new_data_path, fname, lines)

    def modify_skill_name(self):
        """Takes an unmodified skillname-e.dat and adds the skills which will store
        drop/spoil/other info about mobs

        Returns
        -------
        None
            Outputs updated skillname-e.dat to self.new_data_path

        """

        fname = "skillname-e.dat"

        info_header = f"a,{40*'.'}::: {'{}'} :::{40*'.'}\0"  # Format for header of skill desc
        tail = "\\0\ta,none\\0\ta,none\\0"  # Every line ends with this

        # First decode and convert from .dat to .txt
        lines = utils.read_encrypted(self.original_data_path, fname)

        for npc_id, npc in self.npc_data.items():
            for info_type in self.skill_ids.keys():
                if not self.skill_include[info_type]:
                    # If this type of info isn't to be included, then skip:
                    continue
                head = f"{self.skill_ids[info_type]}\t{npc_id}\t{info_header.format(info_type)}\\t\ta,"
                body = ""

                if info_type == "Information":
                    minfo = npc["stats"]

                    if self.VIP is True:
                        # If VIP, then multiply exp and sp by VIP_rate:
                        minfo["exp"] = int(np.floor(eval(minfo["exp"]) * self.VIP_rate))
                        minfo["sp"] = int(np.floor(eval(minfo["sp"]) * self.VIP_rate))

                    body = (
                        f"NPC ID: {npc_id}   "
                        f"Level: {minfo['level']}   "
                        f"Agro: {minfo['agro']}\\n"
                        f"Exp: {minfo['exp']}   SP: {minfo['sp']}   HP: {minfo['hp']}   "
                        f"MP: {minfo['mp']}\\nP. Atk: {minfo['patk']}   P. Def: {minfo['pdef']}   "
                        f"M. Atk: {minfo['matk']}   M. Def: {minfo['mdef']}\\n"
                    )

                elif info_type == "Drop":
                    if "drop" not in npc:
                        continue
                    for drop in npc["drop"]:
                        id, item_min, item_max, chance, name = drop  # Extract relevant info
                        if self.VIP is True:
                            # If VIP, then multiply accordingly:
                            if name != "Adena":
                                # If not adena, then multiply chance by VIP_rate (to a max of 1):
                                chance = min(chance * self.VIP_rate, 1)
                            else:
                                # If adena, then multiply amount by VIP_rate:
                                item_min *= self.VIP_rate
                                item_max *= self.VIP_rate
                            # Note: Need to confirm what happens with seal stones
                            item_min, item_max = (round(item_min), round(item_max))  # Round to int
                        item_amt = (  # If item_min == item_max, then only show one:
                            f"{item_min}-{item_max}" if item_min != item_max else f"{item_min}"
                        )
                        drop_info = f"{name} [{item_amt}] {utils.round_chance(chance, 4)}\\n"

                        # Hacky way of making sure adena is always on the top of the drop list:
                        if name != "Adena":
                            body += drop_info
                        else:
                            body = drop_info + body

                elif info_type == "Spoil":
                    if "spoil" not in npc:
                        continue
                    for spoil in npc["spoil"]:
                        id, item_min, item_max, chance, name = spoil  # Extract relevant info
                        item_min, item_max = (round(item_min), round(item_max))  # Round to int
                        item_amt = (  # If item_min == item_max, then only show one:
                            f"{item_min}-{item_max}" if item_min != item_max else f"{item_min}"
                        )
                        spoil_info = f"{name} [{item_amt}] {utils.round_chance(chance, 4)}\\n"
                        body += spoil_info

                new_line = head + body + tail  # Combine the three parts to get the full line
                lines.append(new_line)

        # Now encrypt and write updated lines:
        utils.write_encrypted(self.new_data_path, fname, lines)


if __name__ == "__main__":
    builder = DataBuilder(info=True, VIP=True)
    builder.build()
