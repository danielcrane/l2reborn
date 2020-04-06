import os
import sys
from collections import namedtuple

sys.path.append("..")
import utils


class PageBuilder:
    def __init__(self):
        self.site_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site")
        self.npc_path = "npc"
        self.item_path = "item"
        self.img_path = "img"
        self.css_path = "css"

        if not os.path.exists(self.site_path):
            os.makedirs(self.site_path)
        if not os.path.exists(os.path.join(self.site_path, self.npc_path)):
            os.makedirs(os.path.join(self.site_path, self.npc_path))
        if not os.path.exists(os.path.join(self.site_path, self.item_path)):
            os.makedirs(os.path.join(self.site_path, self.item_path))

        self.parser = utils.NpcParser()
        self.npc_data = self.parser.parse()
        self.item_data = self.create_item_db()
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

    def create_search_page(self):
        search_db = {"items": {}, "npcs": {}}
        search_db["items"] = {"names": [], "ids": []}
        search_db["npcs"] = {"names": [], "ids": [], "levels": []}
        names_lower = []

        for id, data in self.item_data.items():
            search_db["items"]["ids"].append(id)
            search_db["items"]["names"].append(data["name"])
            names_lower.append(data["name"].lower())

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
        for i, id in enumerate(search_db["npcs"]["ids"]):
            npc_name = search_db["npcs"]["names"][i]
            npc_level = search_db["npcs"]["levels"][i]
            npc_list += f"<li style='display:none'><a href='{self.npc_path}/{id}.html'>{npc_name} ({npc_level})</a></li>\n"
        npc_list += "\n</ul>"

        item_list = """
            <h3 id="itemHead" style='display:none'>Items</h3>
            <ul id='itemUL'>
        """
        img_path = self.img_path
        for i, id in enumerate(search_db["items"]["ids"]):
            item_list += f"<li style='display:none'><a href='{self.item_path}/{id}.html'><img src='{img_path}/item/5-{id}.jpg' style='position:relative; top:10px;'>{search_db['items']['names'][i]}</a></li>\n"
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
                  <td align="left"><img src="{img_path}/item/5-{drop[0]}.jpg" align="absmiddle" class="img_border" alt="{drop[4]}" title="{drop[4]}"> <a href="../{self.item_path}/{drop[0]}.html" title="{drop[4]}">{drop[4]}</a> ($DROP)</td>
                  <td>$CRYSTALS</td>
                  <td>{format_probability(drop[3])}</td>
                </tr>
        """

        drops = []
        chances = []
        for i, drop in enumerate(data["drop"]):
            crystal = self.item_data[drop[0]]["crystal"]
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
            crystal = self.item_data[drop[0]]["crystal"]
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
        <td valign="top" bgcolor="#1E4863"><table width="100%" border="0" cellpadding="5" cellspacing="0" class="show_list"><tbody><tr><td colspan="3"><img src="{img_path}/etc/blank.gif" height="8"><br><span class="txtbig"><b>{name}</b> ({stats["level"]})</span>&nbsp;&nbsp;&nbsp;<img src="{img_path}/etc/blank.gif" height="10"><br>
        """
        # Note: Removed location info for now from above:
        # <a href="/loc/21224/{name.lower().replace(" ", "-")}.html" title="{name} location on the map"><img src="{img_path}/etc/flag.gif" border="0" align="absmiddle" alt="{name} location on the map" title="{name} location on the map">Location</a><br>
        stats_template = '<br><img src="{img_path}/etc/blank.gif" height="12"><br>  {"Passive" if stats["agro"] is "No" else "Aggressive"} male, Exp: {stats["exp"]}, SP: {stats["sp"]}, HP: {stats["hp"]}, P.Atk: {stats["patk"]}, M.Atk: {stats["matk"]}, RunSpd: 000, Atk.Range: 000 </td></tr>'
        footer = "</tbody></table>\n</td>"

        for id, data in self.npc_data.items():
            name = data["name"]
            stats = data["stats"]

            title = f"<title>{name}</title>"
            header = eval(f'f"""{header_template}"""')
            # skills = Add skills here later
            stats = eval(f'f"""{stats_template}"""')

            drops = self.create_drops(data)

            css = self.css.format(f"../{self.css_path}")

            html = f"<html>\n{title}\n{css}\n{self.search}\n{self.table_head.format(img_path)}\n{header}\n{drops}\n{self.table_foot.format(img_path)}\n{footer}</html>"
            with open(os.path.join(self.site_path, self.npc_path, f"{id}.html"), "w") as f:
                f.write(html)

    def create_item_db(self):
        Drop = namedtuple("Drop", ["npc", "min", "max", "chance"])
        Npc = namedtuple("Npc", ["id", "name", "level", "agro"])
        item_data = {}

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

                    if id not in item_data:
                        item_data[id] = {}
                        item_data[id]["name"] = name
                        item_data[id]["type"] = self.parser.item_data[id].name
                        item_data[id]["crystal"] = self.parser.item_data[id].crystal
                        item_data[id]["info"] = []
                        item_data[id]["drop"] = []
                        item_data[id]["spoil"] = []

                    item_data[id][drop_type].append(Drop(npc_tuple, min_amt, max_amt, chance))

        return item_data

    def create_item_drops(self, data):
        img_path = f"../{self.img_path}"
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
                  <td class="npcName" align="left"><a href="../{self.npc_path}/{drop.npc.id}.html" title="View {drop.npc.name} drop and spoil">{drop.npc.name}</a></td>
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
        for i, drop in enumerate(data["drop"]):
            drops.append(
                eval(f'f"""{template}"""').replace(
                    "$DROP", f"{drop.min}-{drop.max}" if drop.min != drop.max else f"{drop.min}"
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
                eval(f'f"""{template}"""').replace(
                    "$DROP", f"{drop.min}-{drop.max}" if drop.min != drop.max else f"{drop.min}"
                )
            )
            levels.append(int(drop.npc.level))

        # Now sort the spoil list in order of chance:
        if len(spoils) > 0:
            _, spoils = (list(t) for t in zip(*sorted(zip(levels, spoils))))
            for i, spoil in enumerate(spoils):
                spoils[i] = spoil.replace(" $COLOR", " bgcolor=#1C425B" if i % 2 == 0 else "")

        spoils = header_2.format("Spoil") + "\n" + "\n".join(spoils)

        return f"{header.format(self.item_path, data['name'].lower().replace(' ', '-'))}\n{drops}<tr></tr>\n{spoils}"

    def create_item_pages(self):
        img_path = f"../{self.img_path}"
        header_template = """
        <td valign="top" bgcolor="#1E4863">
              <table width="100%" border="0" cellpadding="5" cellspacing="0" class="show_list">
                <tbody id="itemDataTable"><tr><td colspan="4"><img src="{img_path}/etc/blank.gif" height="8"><br><img src="{img_path}/item/5-{id}.jpg" align="absmiddle" class="img_border" alt="{name}" title="{name}">
        		<b class="txtbig">{name}</b>{crystals}<br><img src="{img_path}/etc/blank.gif" height="8"><br>
        """
        desc_template = 'Type: Blunt, P.Atk/Def: 175, M.Atk/Def: 91		<br><img src="{img_path}/etc/blank.gif" height="8"><br>Bestows either Anger, Health, or Rsk. Focus.</td></tr>'
        footer = "</tbody></table>\n</td>"

        for id, data in self.item_data.items():
            data = self.item_data[id]
            name = data["name"]
            title = f"<title>{name}</title>"
            crystals = (
                ""
                if data["crystal"].count == None
                else f" (crystals: {data['crystal'].count} {data['crystal'].type}) "
            )

            header = eval(f'f"""{header_template}"""')
            # Need to scrape descriptions from game files before enabling this:
            desc = ""  # eval(f'f"""{desc_template}"""')

            drops = self.create_item_drops(data)

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
    # pb.create_npc_pages()
    # pb.create_item_pages()
    pb.create_search_page()
