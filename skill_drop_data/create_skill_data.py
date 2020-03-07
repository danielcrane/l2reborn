import getopt
import numpy as np
import sys
import utils


class DataBuilder:
    def __init__(self, info=True, drops=True, spoils=True, VIP=False, drop_display="percent"):
        self.original_data_path = "./original_data"  # Path of original data (without drop info)
        self.new_data_path = "./new_data"  # Output path of new data (with drop info)

        self.npcs_xml_dir = "./npcs"  # Directory containing NPC xml files
        self.items_xml_dir = "./items"  # Directory containing item xml files

        self.drop_display = drop_display  # drop_display describes how drop rates are shown

        self.VIP = VIP  # If True, currency amount/xp/sp/drop rates are all scaled accordingly
        self.VIP_xp_sp_rate = 1.5  # Experience and SP multiplier
        self.VIP_drop_rate = 1.5  # Drop chance multipler increase for items
        self.VIP_adena_rate = 1.0  # Drop chance increase multiplier for adena
        self.VIP_adena_amount = 1.5  # Drop amount increase multiplier for adena

        self.skill_include = {"Information": info, "Drop": drops, "Spoil": spoils}
        self.skill_ids = {"Information": 20000, "Drop": 20001, "Spoil": 20002}
        self.skill_icons = {
            "Information": "icon.etc_lottery_card_i00",
            "Drop": "icon.etc_adena_i00",
            "Spoil": "icon.skill0254",
        }

    def build(self):
        """This is the main class method that performs the actions required
        to build the new .dat files from scratch

        Returns
        -------
        None
            Outputs updated skillname-e.dat and skillgrp.dat to self.new_data_path

        """
        print("[] Parsing NPC .xml files")
        sys.stdout.flush()
        self.parse_npc_xmls()
        print("[] Updating skillname-e.dat")
        sys.stdout.flush()
        self.modify_skill_name()
        print("[] Updating skillgrp.dat")
        sys.stdout.flush()
        self.modify_skill_grp()
        print("[] Updating npcgrp.dat")
        sys.stdout.flush()
        self.modify_npc_grp()
        print("\n[] Build complete")
        sys.stdout.flush()

    def format_probability(self, chance, n=4):
        """Format the inputted probability as a percent or fraction depending on self.drop_display

        Parameters
        ----------
        chance : float
            Probability value between 0 and 1

        Returns
        -------
        type
            Description of returned object.

        """
        if self.drop_display == "percent":
            return utils.round_chance(chance, n)
        elif self.drop_display == "fraction":
            return f"1 / {utils.round_sf(1/chance, n)}"
        else:
            raise ValueError("drop_display must be one of either 'percent' or 'fraction'")

    def parse_npc_xmls(self):
        """Parses the server XML files and creates a dict of NPC data
        including drops, spoils, stats, etc.

        Returns
        -------
        None
            Stores self.npc_data - a dict containing the information of each NPC

        """
        parser = utils.NpcParser()
        self.npc_data = parser.parse()

    def modify_npc_grp(self):
        """Takes an unmodified npcgrp.dat and first increases the number of possible
        passive skills from 13 to 16 - an extra 3 spots to accomodate for the 3 new types
        of info, and adds the skills which will store drop/spoil/other to each mob

        Note that the size of dtab_base/dtab_max are 2x the number of skills,
        since the skill id and skill level both consist of one entry each

        Returns
        -------
        None
            Outputs updated npcdrp.dat to self.new_data_path

        """

        fname = "npcgrp.dat"

        # Calculate number of additional skills needed to display required info:
        additional_skills = list(self.skill_include.values()).count(True)

        dtab_base = 26  # Original max number of allowed skills = 13 (x2)
        dtab_max = 32  # New max number of allowed skills = 16 (x2)

        # Decode and convert from .dat to .txt
        lines = utils.read_encrypted(self.original_data_path, fname)

        # Now modify each line to add the skill slots, and data where appropriate:
        for i, line in enumerate(lines):
            line = line.split("\t")  # Split the tab-delimited string into a list

            if i == 0:
                # Modify the header
                dtab_loc = line.index("dtab1[0]")  # Index of first skill, denoted by dtab[0]
                for idx in range(dtab_base, dtab_max):
                    loc = dtab_loc + idx  # Offset idx by starting index, dtab_loc
                    line.insert(loc, f"dtab1[{idx}]")  # Insert new skill header element
                lines[i] = "\t".join(line)  # Now rejoin the list to form a tab-delimited string
                continue  # Move on to the next line

            # If not the header, then first add empty string to each new skill slot:
            for idx in range(dtab_base, dtab_max):
                loc = dtab_loc + idx  # Offset idx by starting index, dtab_loc
                line.insert(loc, "")  # Insert blank skill data for now

            npc_id = eval(line[0])
            # Now, if the NPC is in our data parsed from XML:
            if npc_id in self.npc_data:
                # Add the skills containing the additional information to the mob data
                n_skill = eval(line[dtab_loc - 1])  # Find how many skills the NPC has
                # Note that mobs with no passives have "1", so we must change to 0 before proceeding:
                n_skill = 0 if n_skill == 1 else n_skill

                # Now we must increase the number of skills the NPC has by 2 for each additional
                # field of information that we wish to add:
                line[dtab_loc - 1] = str(n_skill + 2 * additional_skills)

                for idx, skill_id in enumerate(self.skill_ids.values()):
                    loc = dtab_loc + n_skill + 2 * idx  # Select first empty skill index
                    line[loc : loc + 2] = [str(skill_id), str(npc_id)]  # Insert skill and npc id

            lines[i] = "\t".join(line)  # Now rejoin the list to form a tab-delimited string

        # Since we'll add new skills, we must write with a custom ddf file:
        fname_ddf = fname.replace(".dat", "-custom.ddf")
        # Now encrypt and write updated lines:
        utils.write_encrypted(self.new_data_path, fname, lines, ddf=fname_ddf)

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
                        # If VIP, then multiply exp and sp by VIP_xp_sp_rate:
                        minfo["exp"] = int(np.floor(eval(minfo["exp"]) * self.VIP_xp_sp_rate))
                        minfo["sp"] = int(np.floor(eval(minfo["sp"]) * self.VIP_xp_sp_rate))

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
                    npc_type = npc["stats"]["type"]
                    for drop in npc["drop"]:
                        id, item_min, item_max, chance, name = drop  # Extract relevant info
                        if self.VIP is True:
                            # If VIP, then multiply accordingly:
                            if name == "Adena":
                                # If adena, then multiply amount by VIP_adena_amount:
                                item_min *= self.VIP_adena_amount
                                item_max *= self.VIP_adena_amount
                                # And multiply chance by VIP_adena_rate:
                                chance = min(chance * self.VIP_adena_rate, 1)
                            elif npc_type not in ["RaidBoss", "GrandBoss"]:
                                # If not adena or raid boss, then multiply chance by VIP_drop_rate (to a max of 1):
                                chance = min(chance * self.VIP_drop_rate, 1)
                            item_min, item_max = (round(item_min), round(item_max))  # Round to int

                        item_amt = (  # If item_min == item_max, then only show one:
                            f"{item_min}-{item_max}" if item_min != item_max else f"{item_min}"
                        )
                        drop_info = f"{name} [{item_amt}] {self.format_probability(chance)}\\n"

                        # Hacky way of making sure adena is always on the top of the drop list:
                        body = body + drop_info if name != "Adena" else drop_info + body

                elif info_type == "Spoil":
                    if "spoil" not in npc:
                        continue
                    for spoil in npc["spoil"]:
                        id, item_min, item_max, chance, name = spoil  # Extract relevant info
                        item_min, item_max = (round(item_min), round(item_max))  # Round to int
                        item_amt = (  # If item_min == item_max, then only show one:
                            f"{item_min}-{item_max}" if item_min != item_max else f"{item_min}"
                        )
                        spoil_info = f"{name} [{item_amt}] {self.format_probability(chance)}\\n"
                        body += spoil_info

                new_line = head + body + tail  # Combine the three parts to get the full line
                lines.append(new_line)

        # Now encrypt and write updated lines:
        utils.write_encrypted(self.new_data_path, fname, lines)


def main(argv):
    """Executes the builder with the specified command line arguments

    Parameters
    ----------
    argv : list
        List of command line arguments to be parsed

    """
    usage = "Usage: create_skill_data.py <--no-info | --no-drops | --no-spoils | --vip | --drop_display=<percent|fraction> >"
    try:
        opts, args = getopt.getopt(
            argv, "h", ["no-info", "no-drops", "no-spoils", "vip", "help", "drop_display="]
        )
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)

    info, drops, spoils, vip, drop_display = True, True, True, False, "percent"
    for opt, arg in opts:
        if opt == "--no-info":
            info = False
        elif opt == "--no-drops":
            drops = False
        elif opt == "--no-spoils":
            spoils = False
        elif opt == "--vip":
            vip = True
        elif opt == "--drop_display":
            print(arg)
            if arg == "fraction":
                drop_display = "fraction"
            elif arg != "percent":
                raise ValueError("drop_display must be one of either 'percent' or 'fraction'")
        elif opt in ["--help", "-h"]:
            print(usage)
            sys.exit(2)

    print(
        f"[] Running with setup: info={info}, drops={drops}, spoils={spoils}, "
        f"drop_display={drop_display}, VIP={vip}"
    )
    builder = DataBuilder(
        info=info, drops=drops, spoils=spoils, VIP=vip, drop_display=drop_display
    )
    builder.build()


if __name__ == "__main__":
    main(sys.argv[1:])
