import pandas as pd
import re
import csv

# [Options] may be useful for debugging
pd.options.display.max_rows = 9999
#pd.options.display.max_columns = 30
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', 800)

# [Setup] leave as is, please
SHEET_ID = "1SjlQj7fh65_2u0yAp32Sc-J8injhJ0zUvlC27soAzSs"
SHEET_NAME = "Provinces"
url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'
df = pd.read_csv(url)
df = df.drop(df.columns[30:41], axis = 1)
df.columns = ["name", "id", "type", "rgb", "area", "region", "superregion", "continent", "winters", "monsoons", "terrain", "climate", "is_colonized", "is_owned_by", "is_core_of", "is_city", "religion", "culture", "tradenode", "tradegood", "latentgood", "cot_rank", "base_tax", "base_production", "base_manpower", "total_development", "has_lv2_fort", "discovered_by", "prov_modifiers", "notes"]
df = df.dropna(axis=0, subset=['type'])

# [Config] please add all recognizable tradenodes to this!!
tradenode_map = {
    "Debug Node": "debug",
    "Pavedda": "pavedda",
    "Tsekkan Channel": "tsekkan-channel",
    "Lehmunjikom": "lehmunjikom",
    "Meljikom": "meljikom",
    "Cominol": "cominol",
    "Arjagana": "arjagana",
    "Rastago": "rastago",
    "Telon Tchegur": "telon-tchegur",
    "Katiichi": "katiichi",
    "Upper Travnann": "upper-travnann",
    "Toshvann": "toshvann",
    "Kara": "kara",
    "Xi'yàrä": "xiyara",
    "Allolic Gate": "allolic-gate",
    "Luiin": "luiin",
    "Hewe Kahmang": "hewekahmang",
    "Konoko": "konoko",
    "Oñanin Sea": "onanin-sea",
    "Kolettchi": "kolettchi",
    "Ulé": "ule",
    "Ven": "ven",
    "Tula": "tula",
    "Cheppa": "cheppa",
    "Mirma": "mirma",
    "Upper Oom": "upper-oom",
    "Lower Oom": "lower-oom",
    "Harjann": "harjann",
    "Etchedalm": "etchedalm",
    "Tuka": "tuka",
    "Doshintcha": "doshintcha",
    "Hauyuxalaam": "hauyuxalaam",
    "Nomong": "nomong",
    "Sokathii": "sokathii"
}

# Note: Unlike most other scripts, simply running this script won't cut it.
#       This script will create a new file called "tradenode_helper_result.txt",
#       which contains the *mold* for the "members" section of the common/tradenodes file.
#       After running this script, you should copy the results onto the corresponding "members" section
#       of the tradenode you're editing.
#       Also, please delete the result textfile once you're done with it. Thanks!

# [Logic] aux function to format names
def f_remove_accents(old):
    """
    Removes common accent characters, lower form.
    Uses: regex.
    """
    new = old.lower()
    new = re.sub(r'[àáâãäå]', 'a', new)
    new = re.sub(r'[èéêë]', 'e', new)
    new = re.sub(r'[ìíîï]', 'i', new)
    new = re.sub(r'[òóôõö]', 'o', new)
    new = re.sub(r'[ùúûü]', 'u', new)
    new = re.sub('ñ', 'n', new)
    new = re.sub(' ','-', new)
    return new

# [Logic] where the magic happens
provnode_mapping = {}
for tradenode in tradenode_map.values():
    provnode_mapping.update({tradenode: [[],[]]}) # [[land tiles], [sea tiles]]

print(provnode_mapping)

i = -1
last_province = 0
with open('map/definition.csv', 'r', encoding='UTF-8') as definition:
    for line in definition.readlines():
        i = i + 1
        line_arr = line.split(";")
        if not line_arr[0].isnumeric():
            print(line)
            continue
        else:
            provID = int(line_arr[0])
            if last_province == 0 and i != provID:
                last_province = i-1
            type_str = str(df.at[provID-1, 'type'])
            if not type_str in ["Open Sea Tile", "Coastal Sea Tile", "Inland Sea Tile", "Land"]:
                continue
            print("debug: we are in " + line_arr[4])
            tradenode_str = str(df.at[provID-1, 'tradenode'])
            if tradenode_str in tradenode_map.keys():
                tradenode = tradenode_map[tradenode_str]
            else:
                tradenode = f_remove_accents(tradenode_str).lower().replace(" ", "_")
            tradenode_tiles = provnode_mapping[tradenode]
            if type_str == "Land":
                tradenode_tiles[0].append(provID)
            else:
                tradenode_tiles[1].append(provID)


with open('tradenode_helper_result.txt', 'w', encoding='ISO-8859-1') as result:
    statement = ""
    for tradenode in provnode_mapping:
        statement = statement + '\n' + tradenode + " = {\n"
        landtiles_list = provnode_mapping[tradenode][0]
        landtiles_string = ' '.join([str(tile) for tile in landtiles_list])
        seatiles_list = provnode_mapping[tradenode][1]
        seatiles_string = ' '.join([str(tile) for tile in seatiles_list])
        statement = statement + "\t#Land Tiles" + "\n\t" + landtiles_string + "\n\n"
        statement = statement + "\t#Sea Tiles" + "\n\t" + seatiles_string + "\n"
        statement = statement + "}" + "\n\n"
    result.write(statement)