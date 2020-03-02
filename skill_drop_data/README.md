# Skill Drop Data tool

This is a tool that allows you to modify the Lineage II client files in order to display the mob stats, drops, and spoils as passive skills for easy reference.

Note that this is currently build for Interlude, however with minor changes to the `.ddf` file path accessed by `l2asmdisasm` in `/utils/`, it should be possible to make this work for other chronicles without too much difficulty, however you may need to replace the `/npcs/`, `/items/`, and `/original_data/` folders with chronicle-specific files.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install numpy and BeautifulSoup.

```bash
pip install numpy bs4
```

## Usage

This can be used from the command line as follows:

```bash
python create_skill_data.py <--no-info | --no-drops | --no-spoils | --vip>
```

where the options in the triangular brackets are optional, and perform as follows:

* `--no-info` : Disables adding NPC stats as a passive skill (default is enabled)
* `--no-drops` : Disables adding NPC drops as a passive skill (default is enabled)
* `--no-spoils` : Disables adding NPC spoils as a passive skill (default is enabled)
* `--vip` : Enables VIP mode, which multiplies XP, SP, and adena drop amounts by 1.5x, and increases drop rates of items other than adena by 1.5x (default is disabled)

The output of this execution will be put into the `/new_data/` folder, and should consist of `skillname-e.dat` & `skillgrp.dat` which can directly be put into the Lineage II system folder.

## Details

This script works by taking the NPC and drop data from the `/npcs/` and `/items/` folder and parsing the contained XMLs into a python dictionary containing the information for each mob (the `/items/` folder is needed to map the item IDs in the drop lists in `/npcs/` to their names).

Once the XMLs are processed, the default `skillname-e.dat` and `skillgrp.dat` files (contained in `/original_data/`) are converted to a readable format, and the NPC info from the previous step is added to them.

Finally, the updated `.dat` files are re-encoded and put into `/new_data/` with the same file names.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
