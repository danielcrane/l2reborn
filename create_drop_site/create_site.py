import os
import sys
import cv2
import numpy as np
from collections import namedtuple
import requests
import urllib.request
from bs4 import BeautifulSoup
import time
import re

sys.path.append("..")
import utils


class PageBuilder:
    def __init__(self):
        self.site_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site")
        self.npc_path = "npc"
        self.item_path = "item"
        self.recipe_path = "recipe"
        self.img_path = "img"
        self.loc_path = "loc"
        self.css_path = "css"
        self.map_path = f"{self.img_path}/etc/world_map_interlude_big.png"
        img = cv2.imread(f"{self.site_path}/{self.map_path}")  # Read map image file
        self.map_size = (img.shape[1], img.shape[0])
        self.set_world_info()

        if not os.path.exists(self.site_path):
            os.makedirs(self.site_path)
        if not os.path.exists(os.path.join(self.site_path, self.npc_path)):
            os.makedirs(os.path.join(self.site_path, self.npc_path))
        if not os.path.exists(os.path.join(self.site_path, self.item_path)):
            os.makedirs(os.path.join(self.site_path, self.item_path))
        if not os.path.exists(os.path.join(self.site_path, self.recipe_path)):
            os.makedirs(os.path.join(self.site_path, self.recipe_path))
        if not os.path.exists(os.path.join(self.site_path, self.loc_path)):
            os.makedirs(os.path.join(self.site_path, self.loc_path))

        self.item_data = utils.ItemParser().parse()
        self.npc_data = utils.NpcSqlParser(item_data=self.item_data).parse()
        self.drop_data = self.create_drop_data()
        self.spawn_data = utils.SpawnParser().parse()
        self.skill_data, self.skill_order = utils.SkillParser().parse()

        self.css = """
        <head>
            <link href="{}/pmfun.css" rel="stylesheet" type="text/css" />
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        </head>
        """

        # Note that self.search as it stands will only work from one directory above the base site:
        self.search = """
            <div class="searchbar">
                <form class="example" action="../search.html">
                  <input type="text" id="searchTxt" placeholder="Search.." name="search">
                  <button id="searchBtn"><i class="fa fa-search"></i></button>
                </form>
            </div>
        """

        self.table_head = """
            <div class="content">
            <table width="100%" border="0" cellspacing="0" cellpadding="0">
              <tbody><tr>
                <td width="17"><img src="{0}/etc/tab_1.gif" width="17" height="21"></td>
                <td background="{0}/etc/tab_1_fon.gif" align="center"><img src="{0}/etc/tab_ornament_top.gif" width="445" height="21"></td>
                <td width="17"><img src="{0}/etc/tab_2.gif" width="17" height="21"></td>
              </tr>
              <tr>
                <td background="{0}/etc/tab_left_fon.gif"></td>
        """
        self.table_foot = """
              </tbody></table>
            </td>
            <td background="{0}/etc/tab_right_fon.gif"></td>
                  </tr>
                  <tr>
                    <td><img src="{0}/etc/tab_3.gif" width="17" height="38"></td>
                    <td background="{0}/etc/tab_bottom_fon.gif">
                      <table width="100%" border="0" cellspacing="0" cellpadding="0">
                        <tbody><tr>
                          <td><img src="{0}/etc/tab_4.gif" width="24" height="38"></td>
                          <td align="right"><img src="{0}/etc/tab_5.gif" width="24" height="38"></td>
                        </tr>
                      </tbody></table>
                    </td>
                    <td><img src="{0}/etc/tab_6.gif" width="17" height="38"></td>
                  </tr>
                </tbody></table>
            </div>
        """

    def set_world_info(self):
        TILE_X_MIN = 16
        TILE_X_MAX = 26
        TILE_Y_MIN = 10
        TILE_Y_MAX = 25

        TILE_SIZE = 32768
        self.WORLD_X_MIN = (TILE_X_MIN - 20) * TILE_SIZE
        self.WORLD_X_MAX = (TILE_X_MAX - 19) * TILE_SIZE
        self.WORLD_Y_MIN = (TILE_Y_MIN - 18) * TILE_SIZE
        self.WORLD_Y_MAX = (TILE_Y_MAX - 17) * TILE_SIZE

    def create_search_page(self):
        img_path = self.img_path
        search_db = {"items": {}, "npcs": {}}
        search_db["items"] = {"names": [], "ids": []}
        search_db["npcs"] = {"names": [], "ids": [], "levels": []}
        names_lower = []

        for id, data in self.item_data.items():
            search_db["items"]["ids"].append(id)
            search_db["items"]["names"].append(data.name)
            names_lower.append(data.name.lower())

        # Now sort the item list in order of names for easier search:
        _, search_db["items"]["names"], search_db["items"]["ids"] = (
            list(t)
            for t in zip(
                *sorted(zip(names_lower, search_db["items"]["names"], search_db["items"]["ids"]))
            )
        )

        names_lower = []
        for id, data in self.npc_data.items():
            search_db["npcs"]["ids"].append(id)
            search_db["npcs"]["names"].append(data["name"])
            search_db["npcs"]["levels"].append(int(data["stats"]["level"]))
            names_lower.append(data["name"].lower())

        # Now sort the NPC list in order of levels for easier search:
        search_db["npcs"]["levels"], search_db["npcs"]["names"], search_db["npcs"]["ids"] = (
            list(t)
            for t in zip(
                *sorted(
                    zip(
                        search_db["npcs"]["levels"],
                        search_db["npcs"]["names"],
                        search_db["npcs"]["ids"],
                    )
                )
            )
        )

        html_top = """
        <html>
        <title>L2Reborn Database Search</title>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        $CSS
        </head>
        <body>

        <div class="searchbar">
            <form id="searchbar" class="example">
                <input type="text" id="searchTxt" placeholder="Search.." name="search">
                <button id="searchBtn"><i class="fa fa-search"></i></button>
            </form>
        </div>
        <div class="content">
        """.replace(
            "$CSS", self.css.format(self.css_path)
        )

        npc_list = """
            <h3 id="npcHead" style='display:none'>NPCs</h3>
            <ul id='npcUL'>
        """
        loc_html = """
                    <a href="{self.loc_path}/{id}.html" title="{npc_name} location on the map">
                        <img src="{img_path}/etc/flag.gif" border="0" align="absmiddle" alt="{npc_name} location on the map" title="{npc_name} location on the map">
                    </a>
        """
        for i, id in enumerate(search_db["npcs"]["ids"]):
            npc_name = search_db["npcs"]["names"][i]
            npc_level = search_db["npcs"]["levels"][i]
            loc = eval(f'f"""{loc_html}"""') if id in self.spawn_data else ""
            npc_list += f"<li style='display:none'><a href='{self.npc_path}/{id}.html'>{npc_name} ({npc_level}) {loc}</a></li>\n"
        npc_list += "\n</ul>"

        item_list = """
            <h3 id="itemHead" style='display:none'>Items</h3>
            <ul id='itemUL'>
        """

        for i, id in enumerate(search_db["items"]["ids"]):
            icon = self.item_data[id].icon.strip("icon.").lower()
            item_list += f"<li style='display:none'><a href='{self.item_path}/{id}.html'><img src='{img_path}/icons/{icon}.png' style='position:relative; top:10px;' class='img_border'>{search_db['items']['names'][i]}</a></li>\n"
        item_list += "\n</ul>"

        html_bottom = """
        </div>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
        <script>
          var urlParams;
          (window.onpopstate = function () {
              var match,
                  pl     = /\+/g,  // Regex for replacing addition symbol with a space
                  search = /([^&=]+)=?([^&]*)/g,
                  decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); },
                  query  = window.location.search.substring(1);

              urlParams = {};
              while (match = search.exec(query))
                 urlParams[decode(match[1])] = decode(match[2]);
          })();
          if (urlParams["search"] !== undefined) {
            var filter, ul, li, a, i, txtValue, listIDs, npcHead, itemHead;

            listIds = ["npcUL", "itemUL"]
            filter = urlParams["search"].toUpperCase();
            document.getElementById("npcHead").style.display = "";
            document.getElementById("itemHead").style.display = "";

            $.each( listIds, function( index, listId) {

            ul = document.getElementById(listId);
            li = ul.getElementsByTagName('li');

            if (filter.slice(0, 3) == "ID=") {
              for (i = 0; i < li.length; i++) {
                a = li[i].getElementsByTagName("a")[0];
                txtValue = a.href.split('/').pop().split('.html')[0];
                if (txtValue.toUpperCase() == filter.split('=').pop()) {
                  li[i].style.display = "";
                } else {
                  li[i].style.display = "none";
                }
            }
            }
            else {
              for (i = 0; i < li.length; i++) {
                a = li[i].getElementsByTagName("a")[0];
                txtValue = a.textContent || a.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                  li[i].style.display = "";
                } else {
                  li[i].style.display = "none";
                }
              }
            };
          });
         }

          $("#searchTxt").keyup(function(event) {
              if (event.keyCode === 13) {
                  $("#myButton").click();
              }
          });

        </script>


        </body>
        </html>
        """

        html = f"{html_top}\n{npc_list}\n{item_list}\n{html_bottom}"
        with open(os.path.join(self.site_path, f"search.html"), "w") as f:
            f.write(html)

    def create_drops(self, data):
        img_path = f"../{self.img_path}"
        header = """
            <tr>
              <td class="first_line" align="left">Item Name</td>
              <td class="first_line">Crystals (Grade)</td>\n
              <td class="first_line">Chance</td>\n
            </tr>
        """
        header_2 = """
            <tr>
              <td colspan="3" align="left"><b>{}</b></td>
            </tr>
        """

        template = """
                <tr $COLOR>
                  <td align="left"><img src="{img_path}/icons/{icon}.png" align="absmiddle" class="img_border" alt="{drop[4]}" title="{drop[4]}"> <a href="../{self.item_path}/{drop[0]}.html" title="{drop[4]}">{drop[4]}</a> ($DROP)</td>
                  <td>$CRYSTALS</td>
                  <td>{format_probability(drop[3])}</td>
                </tr>
        """

        drops = []
        chances = []
        for i, drop in enumerate(data["drop"]):
            icon = self.item_data[drop[0]].icon.strip("icon.").lower()
            crystal = self.item_data[drop[0]].crystal
            drops.append(
                eval(f'f"""{template}"""')
                .replace("$DROP", f"{drop[1]}-{drop[2]}" if drop[1] != drop[2] else f"{drop[1]}")
                .replace(
                    "$CRYSTALS",
                    f"{crystal.count} {crystal.type}" if crystal.count is not None else "-",
                )
            )
            chances.append(drop[3])

        # Now sort the drop list in order of chance:
        if len(drops) > 0:
            _, drops = (list(t) for t in zip(*sorted(zip(chances, drops), reverse=True)))
            for i, drop in enumerate(drops):
                drops[i] = drop.replace(" $COLOR", " bgcolor=#1C425B" if i % 2 == 0 else "")

        drops = header_2.format("Drop") + "\n" + "\n".join(drops)

        spoils = []
        chances = []
        for i, drop in enumerate(data["spoil"]):
            icon = self.item_data[drop[0]].icon.strip("icon.").lower()
            crystal = self.item_data[drop[0]].crystal
            spoils.append(
                eval(f'f"""{template}"""')
                .replace("$DROP", f"{drop[1]}-{drop[2]}" if drop[1] != drop[2] else f"{drop[1]}")
                .replace(
                    "$CRYSTALS",
                    f"{crystal.count} {crystal.type}" if crystal.count is not None else "-",
                )
            )
            chances.append(drop[3])

        # Now sort the spoil list in order of chance:
        if len(spoils) > 0:
            _, spoils = (list(t) for t in zip(*sorted(zip(chances, spoils), reverse=True)))
            for i, spoil in enumerate(spoils):
                spoils[i] = spoil.replace(" $COLOR", " bgcolor=#1C425B" if i % 2 == 0 else "")

        spoils = header_2.format("<br>Spoils") + "\n" + "\n".join(spoils)

        return f"{header}\n{drops}\n{spoils}"

    def create_npc_pages(self):
        img_path = f"../{self.img_path}"
        header_template = """
        <td valign="top" bgcolor="#1E4863">
            <table width="100%" border="0" cellpadding="5" cellspacing="0" class="show_list">
                <tbody>
                    <tr>
                        <td colspan="3">
                            <img src="{img_path}/etc/blank.gif" height="8">
                            <br>
                            <span class="txtbig"><b>{name}</b> ({stats["level"]})</span>
                            &nbsp;&nbsp;&nbsp;
                            $LOC
                            <br>
                            <img src="{img_path}/etc/blank.gif" height="10">
                            <br>
        """

        loc_html = """
        <a href="../{self.loc_path}/{id}.html" title="{name} location on the map">
        <img src="{img_path}/etc/flag.gif" border="0" align="absmiddle" alt="{name} location on the map" title="{name} location on the map">
        Location
        </a>
        """
        skill_template = """<img src="{0}/icons/{1}.png" width="16" align="absmiddle" class="img_border" alt="{2} ({3})\n{4}" title="{2} ({3})\n{4}">"""
        stats_template = """
            <b>Exp: {stats["exp"]}, SP: {stats["sp"]}</b><br>
            Aggressive: {stats["agro"]}, Herbs: {stats["herbs"]}<br>
            HP: {stats["hp"]}, P.Atk: {stats["patk"]}, M.Atk: {stats["matk"]}, RunSpd: {stats["runspd"]}
            </td>
            </tr>
        """
        footer = "</tbody></table>\n</td>"

        for id, data in self.npc_data.items():
            name = data["name"]
            stats = data["stats"]
            try:
                # First try to get correct skill order from game files:
                skills = self.skill_order[id]
            except KeyError:
                try:
                    # If not available, get from xml files:
                    skills = data["skills"]
                except KeyError:
                    # If not available, then pass:
                    pass

            title = f"<title>{name}</title>"
            header = eval(f'f"""{header_template}"""').replace(
                "$LOC", eval(f'f"""{loc_html}"""') if id in self.spawn_data else ""
            )
            # skills = Add skills here later
            stat_list = eval(f'f"""{stats_template}"""')

            skill_list = ""
            for skill in skills:
                skill_data = self.skill_data[skill.id][skill.level]
                icon = skill_data.icon.lower().replace("icon.", "")
                skill_list += skill_template.format(
                    img_path, icon, skill_data.name, skill.level, skill_data.desc
                )
            skill_list += "\n<br><br>"

            drops = self.create_drops(data)

            css = self.css.format(f"../{self.css_path}")

            html = f"<html>\n{title}\n{css}\n{self.search}\n{self.table_head.format(img_path)}\n{header}\n{skill_list}\n{stat_list}\n{drops}\n{self.table_foot.format(img_path)}\n{footer}</html>"
            with open(
                os.path.join(self.site_path, self.npc_path, f"{id}.html"), "w", encoding="utf-8"
            ) as f:
                f.write(html)

    def create_drop_data(self):
        Drop = namedtuple("Drop", ["npc", "min", "max", "chance"])
        Npc = namedtuple("Npc", ["id", "name", "level", "agro"])
        drop_data = {}

        for npc_id, npc in self.npc_data.items():
            stats = npc["stats"]
            npc_tuple = Npc(
                npc_id,
                npc["name"],
                stats["level"],
                "Passive" if stats["agro"] is "No" else "Aggressive",
            )

            for drop_type in ["drop", "spoil"]:
                for drop in npc[drop_type]:
                    id, min_amt, max_amt, chance, name = drop

                    if id not in drop_data:
                        drop_data[id] = {}
                        drop_data[id]["name"] = name
                        drop_data[id]["type"] = self.item_data[id].type
                        drop_data[id]["crystal"] = self.item_data[id].crystal
                        drop_data[id]["info"] = []
                        drop_data[id]["drop"] = []
                        drop_data[id]["spoil"] = []

                    drop_data[id][drop_type].append(Drop(npc_tuple, min_amt, max_amt, chance))

        return drop_data

    def create_item_drops(self, id):
        img_path = f"../{self.img_path}"

        try:
            data = self.drop_data[id]
        except KeyError:
            data = {"drop": [], "spoil": []}

        header = """
                    <tr>
                      <td class="first_line" align="left">NPC Name</td>
                      <td class="first_line" align="left">Level
                      <div class="popup">
                          <img src="../img/etc/filter.png" height="15" style="cursor:pointer" onclick="myFunction()">
                          <span class="popuptext" id="myPopup" style=>
                            <div>
                              <div>
                                <input id="levelMin" type="number" min="1" max="90" value="1" onchange="levelFilter()"/> - <input id="levelMax" type="number" min="1" max="90" value="90" onchange="levelFilter()"/>
                              </div>
                            </div>
                          </span>
                      </div>
                      </td>
                      <td class="first_line">Type</td>
                      <td class="first_line">Quantity</td>
                      <td class="first_line">Chance</td>
                    </tr>
        """
        # Removed sorting for now:
        # header = """
        #             <tr>
        #               <td class="first_line" align="left">NPC Name</td>
        #               <td class="first_line"><a href="{0}/{1}.html?sort=aggro">Type</a></td>
        #               <td class="first_line"><a href="{0}/{1}.html?sort=quantity">Quantity</a></td>
        #               <td class="first_line"><a href="{0}/{1}.html?sort=chance">Chance</a></td>
        #             </tr>
        # """
        header_2 = """
                <tr>
                  <td colspan="4" align="left"><b>{}</b></td>
                </tr>
        """

        template = """
                <tr class="itemData" $COLOR>
                  <td class="npcName" align="left">
                    <a href="../{self.npc_path}/{drop.npc.id}.html" title="View {drop.npc.name} drop and spoil">
                        {drop.npc.name}
                    </a>
                  $LOC
                  </td>
                  <td class="npcLevel" align="left">{drop.npc.level}</td>
                  <td class="npcAgro">{drop.npc.agro}</td>
                  <td class="dropCount">$DROP</td>
                  <td class="dropChance">{format_probability(drop.chance)}</td>
                </tr>
        """
        # Removed location from drop portion of template:
        #  <a href="/loc/{drop.npc.id}/{drop.npc.name.lower().replace(" ", "-")}.html" title="{drop.npc.name} location on the map"><img src="{img_path}/etc/flag.gif" border="0" align="absmiddle" alt="{drop.npc.name} location on the map" title="{drop.npc.name} location on the map"></a>

        drops = []
        levels = []
        loc_html = """
                    <a href="../{self.loc_path}/{drop.npc.id}.html" title="{drop.npc.name} location on the map">
                        <img src="{img_path}/etc/flag.gif" border="0" align="absmiddle" alt="{drop.npc.name} location on the map" title="{drop.npc.name} location on the map">
                    </a>
        """
        for i, drop in enumerate(data["drop"]):
            drops.append(
                eval(f'f"""{template}"""')
                .replace(
                    "$DROP", f"{drop.min}-{drop.max}" if drop.min != drop.max else f"{drop.min}"
                )
                .replace(
                    "$LOC", eval(f'f"""{loc_html}"""') if drop.npc.id in self.spawn_data else ""
                )
            )
            levels.append(int(drop.npc.level))

        # Now sort the drop list in order of chance:
        if len(drops) > 0:
            _, drops = (list(t) for t in zip(*sorted(zip(levels, drops))))
            for i, drop in enumerate(drops):
                drops[i] = drop.replace(" $COLOR", " bgcolor=#1C425B" if i % 2 == 0 else "")

        drops = header_2.format("Drop") + "\n" + "\n".join(drops)

        spoils = []
        levels = []
        for i, drop in enumerate(data["spoil"]):
            spoils.append(
                eval(f'f"""{template}"""')
                .replace(
                    "$DROP", f"{drop.min}-{drop.max}" if drop.min != drop.max else f"{drop.min}"
                )
                .replace(
                    "$LOC", eval(f'f"""{loc_html}"""') if drop.npc.id in self.spawn_data else ""
                )
            )
            levels.append(int(drop.npc.level))

        # Now sort the spoil list in order of chance:
        if len(spoils) > 0:
            _, spoils = (list(t) for t in zip(*sorted(zip(levels, spoils))))
            for i, spoil in enumerate(spoils):
                spoils[i] = spoil.replace(" $COLOR", " bgcolor=#1C425B" if i % 2 == 0 else "")

        spoils = header_2.format("Spoil") + "\n" + "\n".join(spoils)

        # return f"{header.format(self.item_path, data['name'].lower().replace(' ', '-'))}\n{drops}<tr></tr>\n{spoils}"
        return f"{header}\n{drops}<tr></tr>\n{spoils}"

    def create_item_pages(self):
        img_path = f"../{self.img_path}"
        header_template = """
        <td valign="top" bgcolor="#1E4863">
              <table width="100%" border="0" cellpadding="5" cellspacing="0" class="show_list">
                <tbody id="itemDataTable"><tr><td colspan="4"><img src="{img_path}/etc/blank.gif" height="8"><br><img src="{img_path}/icons/{icon}.png" align="absmiddle" class="img_border" alt="{name}" title="{name}">
        		<b class="txtbig">{name}</b>{crystals}<br><img src="{img_path}/etc/blank.gif" height="8"><br>
        """
        desc_template = 'Type: Blunt, P.Atk/Def: 175, M.Atk/Def: 91		<br><img src="{img_path}/etc/blank.gif" height="8"><br>Bestows either Anger, Health, or Rsk. Focus.</td></tr>'
        footer = "</tbody></table>\n</td>"

        for id, data in self.item_data.items():
            name = data.name
            title = f"<title>{name}</title>"
            crystals = (
                ""
                if data.crystal.count == None
                else f" (crystals: {data.crystal.count} {data.crystal.type}) "
            )
            icon = data.icon.strip("icon.").lower()
            header = eval(f'f"""{header_template}"""')
            # Need to scrape descriptions from game files before enabling this:
            desc = ""  # eval(f'f"""{desc_template}"""')

            drops = self.create_item_drops(id)

            css = self.css.format(f"../{self.css_path}")
            jquery = """
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
                <script>
                function myFunction() {
                  var popup = document.getElementById("myPopup");
                  popup.classList.toggle("show");
                };

                var itemDataTable = document.getElementById("itemDataTable");
                var itemDatas = itemDataTable.getElementsByClassName("itemData");

                function levelFilter() {
                  var npcLevel;
                  var levelMin = parseInt(document.getElementById("levelMin").value);
                  var levelMax = parseInt(document.getElementById("levelMax").value);
                  $.each(itemDatas, function(index, itemData) {
                    npcLevel = parseInt($(itemData.getElementsByClassName("npcLevel")[0]).text());
                    if ((npcLevel < levelMin) || (npcLevel > levelMax)) { itemData.style.display = "none" }
                    else { itemData.style.display = "" };
                  });
                }

                $(document).ready(function() {
                  var levelMin = 100;
                  var levelMax = 0;
                  $.each(itemDatas, function(index, itemData) {
                    npcLevel = parseInt($(itemData.getElementsByClassName("npcLevel")[0]).text());
                    if (npcLevel < levelMin) { levelMin = npcLevel };
                    if (npcLevel > levelMax) { levelMax = npcLevel };

                    document.getElementById("levelMin").value = levelMin;
                    document.getElementById("levelMax").value = levelMax;
                  });
                })
                </script>
            """

            html = f"<html>\n{title}\n{css}\n<body>\n{self.search}\n{self.table_head.format(img_path)}\n{header}\n{desc}\n{drops}\n{self.table_foot.format(img_path)}\n{footer}\n</body>\n{jquery}\n</html>"
            with open(os.path.join(self.site_path, self.item_path, f"{id}.html"), "w") as f:
                f.write(html)

    def spawn2map(self, spawn_point):
        x_map = (
            (spawn_point.x - self.WORLD_X_MIN) / (self.WORLD_X_MAX - self.WORLD_X_MIN)
        ) * self.map_size[0]
        y_map = (
            self.map_size[1]
            - ((spawn_point.y - self.WORLD_Y_MIN) / (self.WORLD_Y_MAX - self.WORLD_Y_MIN))
            * self.map_size[1]
        )
        return x_map, y_map

    def create_loc_pages(self):
        img_path = f"../{self.img_path}"

        for id, data in self.npc_data.items():
            if id not in self.spawn_data:
                continue

            name = data["name"]
            title = f"<title>{name} Location</title>"
            # css = self.css.format(f"../{self.css_path}")
            css = """
                    <head>
                        <link href="{0}/pmfun.css" rel="stylesheet" type="text/css" />
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
                        <style>
                        #map {{
                          margin: auto;
                          height: 874px;
                          width: 604px;
                        }}
                        </style>
                    </head>
            """.format(
                f"../{self.css_path}"
            )

            spawn_points = self.spawn_data[id]
            spawn_list = "<ul id='coords' style='display:none;'>"
            for spawn_point in spawn_points:
                x_map, y_map = self.spawn2map(spawn_point)
                spawn_list += f"\n\t<li x={x_map} y={y_map}></li>"
            spawn_list += "\n</ul>"

            npc_title = f"<div align='center'><a href='../{self.npc_path}/{id}.html' title='View {name} drop and spoil'><h2>{name} ({data['stats']['level']})</h2></a></div>"
            map = '<div id="map" align="center"></div>'

            jquery = """
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.6.0/dist/leaflet.css"   integrity="sha512-xwE/Az9zrjBIphAcBb3F6JVqxf46+CDLwfLMHloNu6KEQCAWi6HcDUbeOfBIptF7tcCzusKFjFw2yuvEpDL9wQ=="   crossorigin=""/>
                <script src="https://unpkg.com/leaflet@1.6.0/dist/leaflet.js"  integrity="sha512-gZwIG9x3wUXg2hdXF6+rVkLF/0Vi9U8D2Ntg4Ga5I5BZpVkVxlJWbSQtXPSiUTtC0TjtGOmxa1AJPuV0CPthew=="  crossorigin=""></script>
              	<script type="text/javascript" src="https://code.jquery.com/jquery-3.2.1.min.js"></script>
              	<script type="text/javascript" src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script>
                <script>

                  var map = L.map('map', {{
                      crs: L.CRS.Simple,
                      nowrap: true,
                      minZoom: -1.6
                  }});

                  var redIcon = new L.Icon({{
                    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                  }});

                  var bounds = [[0, 0], [{0}, {1}]];
                  var image = L.imageOverlay("../img/etc/world_map_interlude_big.png", bounds).addTo(map);
                  map.fitBounds(bounds);

                  var bigIcon = new L.Icon({{
                    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                  }});

                  var smallIcon = new L.Icon({{
                    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    iconSize: [12.5, 20.5],
                    iconAnchor: [6, 20.5],
                    popupAnchor: [1, -34],
                  }});

                  var ul = document.getElementById("coords");
                  var li = ul.getElementsByTagName('li');
                  var markers = []
                  for (i = 0; i < li.length; i++) {{
                    x = li[i].getAttribute("x");
                    y = li[i].getAttribute("y");
                    markers.push(L.marker(L.latLng(y, x), {{icon: smallIcon}}).addTo(map));
                  }}

                  map.setMaxBounds(bounds);
                  map.on('drag', function() {{ map.panInsideBounds(bounds, {{ animate: false }}); }});

                  map.on('zoomend', function(ev){{
                    for (i = 0; i < markers.length; i++) {{
                      marker = markers[i];
                      if (map.getZoom() > 1) {{
                        marker.setIcon(bigIcon);
                      }} else {{
                        marker.setIcon(smallIcon);
                      }}
                    }}
                  }})
              	</script>
            """.format(
                self.map_size[1], self.map_size[0]
            )
            html = f"<html>\n{title}\n{css}\n{self.search}\n<br><br><br><br>\n{spawn_list}\n{npc_title}\n{map}\n{jquery}</html>"
            with open(os.path.join(self.site_path, self.loc_path, f"{id}.html"), "w") as f:
                f.write(html)

    def create_ingredient_table(self, recipe, first=True):
        img_path = f"../{self.img_path}"
        ingredient_list = set()

        if first:
            ingredients = f"<ul class='{recipe.result.id}'>\n"
        else:
            ingredients = f"<ul class='{recipe.result.id}' style = 'display:none'>\n"

        for ingredient in recipe.ingredients:
            icon = self.item_data[ingredient.id].icon.strip("icon.").lower()
            ingredients += f"\t<li class='{ingredient.id}'><img src='{img_path}/icons/{icon}.png' style='position:relative; top:10px;' class='img_border'> <text class='item_count'>{ingredient.count}</text>x <a href='../item/{ingredient.id}.html'>{ingredient.name}</a>"
            ingredient_list.add(ingredient.id)

            if ingredient.id in self.recipe_results and ingredient.id != recipe.id:
                ingredients += f" (<a href='../{self.recipe_path}/{ingredient.id}.html'>recipe</a>) <img src='../img/etc/expand.png' id='{ingredient.id}' height='12' style='cursor:pointer; position:relative; top:3px;' onclick='myFunction(this)'></li>\n"
                ingredients_, ingredient_list_ = self.create_ingredient_table(
                    self.recipe_data[self.recipe_results[ingredient.id]], first=False
                )
                ingredients += ingredients_
                ingredients += "</details>"
                ingredient_list = ingredient_list.union(ingredient_list_)
            else:
                ingredients += "</li>\n"
        ingredients += "</ul>"
        return ingredients, ingredient_list

    def create_recipe_pages(self):
        img_path = f"../{self.img_path}"
        css = self.css.format(f"../{self.css_path}")

        self.recipe_data = utils.RecipeParser(item_data=self.item_data).parse()
        self.recipe_results = {}
        for recipe_id, recipe in self.recipe_data.items():
            self.recipe_results[recipe.result.id] = recipe_id

        for recipe in self.recipe_data.values():
            title = f"<title>{recipe.name}</title>"
            info = f"<b>{recipe.name}</b> (level {recipe.level}, quantity {recipe.result.count}, sucess chance {recipe.chance}, MP {recipe.mp}"
            ingredients, ingredient_list = self.create_ingredient_table(recipe)

            table_0 = """
            <td align="center" valign="top" bgcolor="#1E4863">
            <img src="{0}/etc/blank.gif" height="8"><br>
            <b class="txtbig"><a href='../item/{1}.html'>Recipe</a>:
            <a href='../item/{2}.html'>{3}</a> ({4})</b><br><img src="{0}/etc/blank.gif" height="8"><br>
            <table cellspacing='0' cellpadding='0' border='0' width='100%' class='txt'>\n<tbody>\n<tr>\n<td>
            """.format(
                img_path, recipe.id, recipe.result.id, recipe.result.name, recipe.chance
            )
            table_1 = "</td>\n<td valign='top'><h3>Totals:</h3>"
            table_2 = "</td>\n</tr>\n</tbody>\n</table>"

            totals = "<ul id='totals'>\n"
            base_ingredients = [ingredient.id for ingredient in recipe.ingredients]
            base_ingredient_counts = [ingredient.count for ingredient in recipe.ingredients]

            for ingredient_id in ingredient_list:
                ingredient_data = self.item_data[ingredient_id]
                ingredient_name = ingredient_data.name
                icon = ingredient_data.icon.strip("icon.").lower()

                if ingredient_id in base_ingredients:
                    ingredient_count = base_ingredient_counts[
                        base_ingredients.index(ingredient_id)
                    ]
                    style = "style = ''"
                else:
                    ingredient_count = 0
                    style = "style='display:none'"

                totals += f"\t<li {style} id='total_{ingredient_id}' ><img src='{img_path}/icons/{icon}.png' style='position:relative; top:10px;' class='img_border'><text class='item_count'>{ingredient_count}</text>x <a href='../item/{ingredient_id}.html'>{ingredient_name}</a>\n"
            totals += "</ul>\n"

            jquery = """
<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
<script>
  var totalUL = document.getElementById("totals");
  var totalLIs = totalUL.getElementsByTagName('li');
  var i, childNode, childNodes, findID, findLI, parentVal, childVal, totalVal, childID;

  function expand(elem, ul) {
    ul.style.display = "";
    elem.src = '../img/etc/collapse.png';

    parentVal = parseInt($(ul).parent().find("li."+elem.id+" text.item_count").text());

    findLI = document.getElementById("total_"+elem.id);
    totalVal = parseInt($(findLI).find('text.item_count').text());
    totalVal -= parentVal;
    if (totalVal === 0) {
      $(findLI).find('text.item_count').text(totalVal);
      findLI.style.display = "none";
    };

    childNodes = ul.childNodes;
    for(i = 0; i < childNodes.length; i++) {
      childNode = childNodes[i];
      if (childNodes[i].nodeName === "LI") {
        childID = childNode.getAttribute("class");
        childVal = parseInt($(childNode).find("text.item_count").text());
        findLI = document.getElementById("total_"+childID);

        totalVal = parseInt($(document.getElementById("total_"+childID)).find('text.item_count').text());
        totalVal += childVal;
        $(findLI).find('text.item_count').text(totalVal);
        if (findLI.style.display == "none") {
          findLI.style.display = "";
        }
      }
    }
  };

  function contract(elem, ul) {
    var i, childNode, childNodes, findID, findLI, parentVal, childVal, totalVal, childID;
    ul.style.display = "none";
    elem.src = '../img/etc/expand.png';

    parentVal = parseInt($(ul).parent().find("li."+elem.id+" text.item_count").text());

    findLI = document.getElementById("total_"+elem.id);
    totalVal = parseInt($(findLI).find('text.item_count').text());
    childNodes = ul.childNodes;

    for(i = 0; i < childNodes.length; i++) {
      childNode = childNodes[i];
      if (childNode.nodeName === "UL") {
        if (childNode.style.display === "") {
          childID = childNode.getAttribute("class");
          elem = document.getElementById(childID);
          ul = $(elem).parent().parent().find('ul.'+elem.id)[0];
          contract(elem, ul);
        }
      }
    }

    totalVal += parentVal;
    if (totalVal > 0) {
      findLI.style.display = "";
      $(findLI).find('text.item_count').text(totalVal);
    }


    for(i = 0; i < childNodes.length; i++) {
      childNode = childNodes[i];
      if (childNode.nodeName === "LI") {
        childID = childNode.getAttribute("class");
        childVal = parseInt($(childNode).find("text.item_count").text());
        findLI = document.getElementById("total_"+childID);

        totalVal = parseInt($(document.getElementById("total_"+childID)).find('text.item_count').text());
        totalVal -= childVal;
        $(findLI).find('text.item_count').text(totalVal);
        if (totalVal === 0) {
          findLI.style.display = "none";
        }
      }
    }
  };

  function myFunction(elem) {
    var ul = $(elem).parent().parent().find('ul.'+elem.id)[0];
    if (ul.style.display == "none") {
      // Expand
      expand(elem, ul);
    }
    else {
      // Contract
      contract(elem, ul)
    }
  };
</script>
            """

            html = f"<html>\n{title}\n{css}\n{self.search}\n{'<br>'*4}\n{self.table_head.format(img_path)}\n{table_0}\n{ingredients}\n{table_1}\n{totals}\n{self.table_foot.format(img_path)}\n{table_2}\n{jquery}\n</html>"
            with open(
                os.path.join(self.site_path, self.recipe_path, f"{recipe.id}.html"), "w"
            ) as f:
                f.write(html)

    def scrape_pmfun_images(self):
        for id, data in self.item_data.items():
            file_path = os.path.join(self.site_path, self.img_path, self.item_path, f"{id}.png")

            if os.path.isfile(file_path):
                continue

            url = f"https://lineage.pmfun.com/item/{id}"
            r = requests.get(url)
            soup = BeautifulSoup(r.text, features="html.parser")
            loc = soup.find("img", {"src": re.compile(r"^data/img/")})["src"]
            image_url = f"https://lineage.pmfun.com/{loc}"
            with open(file_path, "wb") as f:
                f.write(requests.get(image_url).content)
            time.sleep(0.1)


def icons_to_lower():
    dir = r"C:\git\l2reborn\create_drop_site\site\img\icons"
    os.chdir(dir)
    first = os.listdir()

    for file in os.listdir():
        # if you do not want to change the name of the .py file too uncomment the next line
        # if not file.endswith(".py") # and indent the next one (of four spaces)
        os.rename(file, file.lower())  # use upper() for the opposite goal


def format_probability(chance, n=4):
    """Format the inputted probability as a percent or fraction depending size

    Parameters
    ----------
    chance : float
        Probability value between 0 and 1

    Returns
    -------
    string
        Formatted chance (percent if > 1%, fraction otherwise)

    """
    if chance >= 0.01:
        return utils.round_chance(chance, n)
    else:
        return f"1 / {round(1/chance):,}"


if __name__ == "__main__":
    pb = PageBuilder()
    print("Creating NPC pages")
    pb.create_npc_pages()
    print("Creating Item pages")
    pb.create_item_pages()
    print("Creating search page")
    pb.create_search_page()
    print("Creating loc pages")
    pb.create_loc_pages()
    print("Creating recipe pages")
    pb.create_recipe_pages()
