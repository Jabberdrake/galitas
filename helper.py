"""This module contains the bulk of the logic for the Helper script."""

# External imports
import pandas as pd
import csv
import re
import numpy as np
import os
import argparse
from InquirerPy import inquirer

# Local imports
from helper_utils import plain, bold, brass, blue, teal, purple             # Text formatting
from helper_utils import print_info, print_verbose                          # Logging functions
from helper_utils import print_art, print_help, print_intro, print_data     # Menus and Displays

### SCRIPT DATA
data = {
    "ALMANAC_NAME": "Almanac of Galitas",
    "ALMANAC_ID": "1SjlQj7fh65_2u0yAp32Sc-J8injhJ0zUvlC27soAzSs",
    "PROVS_SHEET": "Provinces",
    "FIRST_TEMP_WASTELAND": 4971,
    "MAX_PROVINCES": 5000 
}
###

def load_almanac():
    url = f'https://docs.google.com/spreadsheets/d/{data["ALMANAC_ID"]}/gviz/tq?tqx=out:csv&sheet={data["PROVS_SHEET"]}'
    dataframe = pd.read_csv(url)
    dataframe = dataframe.drop(dataframe.columns[30:41], axis = 1)
    dataframe.columns = ["name", "id", "type", "rgb", "area", "region", "superregion", "continent", "winters", "monsoons", "terrain", "climate", "is_colonized", "is_owned_by", "is_core_of", "is_city", "religion", "culture", "tradenode", "tradegood", "latentgood", "cot_rank", "base_tax", "base_production", "base_manpower", "total_development", "has_lv2_fort", "discovered_by", "prov_modifiers", "notes"]
    dataframe = dataframe.dropna(axis=0, subset=['type'])
    return dataframe

def find_last_province(dataframe):
    for i in range(data["MAX_PROVINCES"]):
        try:
            dataframe.loc[i, 'name']
        except KeyError as error:
            return error.args[0]

def update_definition_file(dataframe, last_province):
    with open('map/definition.csv', 'w', encoding='UTF-8', newline='') as definition_file:
        writer = csv.writer(definition_file)
        writer.writerow(["province", "red", "green", "blue", "x", "x"])
        i = 0
        for i in range(data["MAX_PROVINCES"] - 1):
            if i+1 > last_province and i+1 < data["FIRST_TEMP_WASTELAND"]:
                continue
            id = str(dataframe.at[i, 'id'])
            rgb = str(dataframe.at[i, 'rgb'])
            x = str(dataframe.at[i, 'name']).strip()
            row = [id, rgb, x, "x"]
            writer.writerow(row)

    definition = open("map/definition.csv", encoding='UTF-8')
    newtext = definition.read().replace(",", ";")
    definition.close()

    definition = open("map/definition.csv", "w", encoding='UTF-8')
    definition.write(newtext)
    definition.close()

def update_province_history(dataframe, args):

    # Note: for the purposes of running this script, you do NOT need to worry about filling out the following columns in the almanac:
    #        - Area
    #        - Region
    #        - Superregion
    #        - Continent
    #        - Winters
    #        - Monsoons
    #        - Terrain
    #        - Climate
    #        - Trade Node
    #        - Latent Good
    #        - Province Modifiers
    #        - Notes

    # Note: a few common crash causes when running this script:
    #        - a land tile does not have a set religion in the almanac
    #        - a land tile does not have a set culture in the almanac
    #        - a land tile does not have "Yes" or "No" in the "Has Lv. 2 Fort" column (this doesn't crash while running the script, but can fuck up the game)
    #        - a land tile does not have "Yes" or "No" in the "Colonized" column (this doesn't crash while running the script, but can fuck up the game)
    #        - a land tile does not have a recognizable religion (either is not in religion_map or cannot be directly translated)
    #        - a land tile does not have a recognizable culture (either is not in culture_map or cannot be directly translated)
    #        - a land tile does not have a set center of trade rank (if the province isn't supposed to have a center of trade, write 0 in the almanac)

    # Will be reworked later
    tech_groups = ["western", "eastern"]

    # Used in cases where localized-to-internal name assignment isn't straightforward.
    religion_map = {
        "Catholic": "catholic",
        "Orthodox": "orthodox"
    }
    culture_map = {
        "Francien": "cosmopolitan_french", #like this
        "Portuguese": "portuguese"
    }

    with open('map/definition.csv', 'r', encoding='UTF-8') as definition:
        for line in definition.readlines():
            line_arr = line.split(";")
            if not line_arr[0].isnumeric():
                continue
            else:
                provID = int(line_arr[0])
                if args.verbose and provID % 50 == 0:
                    print_verbose(args.verbose, "Processing province no. " + str(provID) + "...")

                provNAME = str(line_arr[4])
                filename = str(provID) + " - " + provNAME.replace("?", "").replace("/", "-")
                filename = filename.translate(str.maketrans({'\u2018': "'", '\u2019': "'"}))
                filename = filename.replace("Š", "S")
                
                histpath = str(os.getcwd()) + '\history\provinces'
                for file in os.listdir(histpath):
                    if file.startswith(str(provID)):
                        os.remove(histpath + '\\' + file)

                # treats "Type" cell
                if not dataframe.at[provID-1, 'type'] == "Land":
                    with open('history/provinces/' + filename + ".txt", "w+", encoding='ISO-8859-1') as history:
                        history.write("# " + filename + '\n')
                        history.write('\n')
                        if provID < 4000:
                            for tech_group in tech_groups:
                                history.write("discovered_by = " + tech_group + "\n")
                else:
                    # handles the "Is Owned By" cell
                    owner = str(dataframe.at[provID-1, 'is_owned_by'])

                    # handles the "Is Core Of" cell
                    if str(dataframe.at[provID-1, 'is_core_of']) == "nan":
                        core_of = [owner]
                    else:
                        core_of = str(dataframe.at[provID-1, 'is_core_of']).split(";")
                    
                    # handles the "Culture" cell
                    culture_str = str(dataframe.at[provID-1, 'culture'])
                    if culture_str in culture_map.keys():
                        culture = culture_map[culture_str]
                    else:
                        culture = plain(culture_str).lower().replace(" ", "_")
                    
                    # handles the "Religion" cell
                    religion_str = str(dataframe.at[provID-1, 'religion'])
                    if religion_str in religion_map.keys():
                        religion = religion_map[religion_str]
                    else:
                        religion = plain(religion_str).lower().replace(" ", "_")

                    # handles the "Base Tax" cell
                    base_tax = dataframe.at[provID-1, 'base_tax']
                    if np.isnan(base_tax):
                        base_tax = 1
                    else:
                        base_tax = int(base_tax)
                    
                    # handles the "Base Production" cell
                    base_production = dataframe.at[provID-1, 'base_production']
                    if np.isnan(base_production):
                        base_production = 1
                    else:
                        base_production = int(base_production)
                    
                    # handles the "Base Manpower" cell
                    base_manpower = dataframe.at[provID-1, 'base_manpower']
                    if np.isnan(base_manpower):
                        base_manpower = 1
                    else:
                        base_manpower = int(base_manpower)

                    # handles the "Trade Good" cell
                    goods = str(dataframe.at[provID-1, 'tradegood']).lower().strip().replace(" ", "_")

                    # handles the "Center of Trade Rank" cell
                    cot = int(dataframe.at[provID-1, 'cot_rank'])
                    
                    # handles the "Colonized" cell
                    is_city = str(dataframe.at[provID-1, 'is_colonized']).lower()

                    # handles the "Has Lv. 2 Fort" cell
                    fort = str(dataframe.at[provID-1, 'has_lv2_fort']).lower()

                    # writes to file
                    with open('history/provinces/' + filename + ".txt", "w+", encoding='ISO-8859-1') as history:
                        history.write("# " + filename + '\n')
                        history.write('\n')
                        if is_city == "yes":
                            history.write("owner = " + owner + '\n')
                            history.write("controller = " + owner + '\n')
                            for cored in core_of:
                                history.write("add_core = " + cored + '\n')
                            history.write('\n')
                        history.write("culture = " + culture + '\n')
                        history.write("religion = " + religion + '\n')
                        history.write("capital = \"\"\n")
                        history.write('\n')
                        history.write("hre = no\n")
                        history.write('\n')
                        history.write("base_tax = " + str(base_tax) + '\n')
                        history.write("base_production = " + str(base_production) + '\n')
                        history.write("base_manpower = " + str(base_manpower) + '\n')
                        history.write('\n')
                        history.write("trade_goods = " + goods + '\n')
                        if not cot == 0:
                            history.write("center_of_trade = " + str(cot) + '\n')
                        history.write('\n')
                        history.write("is_city = " + is_city + '\n')
                        history.write("fort_15th = " + fort + '\n')
                        history.write('\n')
                        for tech_group in tech_groups:
                            history.write("discovered_by = " + tech_group + "\n")

def update_province_loca():
    with open('localisation/replace/prov_names_l_english.yml', 'w', encoding='UTF-8-sig') as loca:
        with open('map/definition.csv', 'r', encoding='UTF-8') as definition:
            loca.write('l_english:\n')
            for line in definition.readlines():
                line_arr = line.split(";")
                if line_arr[0].isnumeric():
                    loca.write(' PROV' + str(line_arr[0]) + ": \"" + line_arr[4] + '\"\n')

def update_provinces(args):

    print_verbose(args.verbose, "Loading almanac...")
    almanac = load_almanac()
    print_verbose(args.verbose, "Loaded almanac '" + data["ALMANAC_NAME"] + "'!")

    print_verbose(args.verbose, "Calculating highest ID province in loaded almanac...")
    last_province = find_last_province(almanac)
    print_verbose(args.verbose, "Highest province ID in loaded almanac is " + str(last_province) + "!")

    print_verbose(args.verbose, "Updating 'definition.csv' file...")
    update_definition_file(almanac, last_province)
    print_verbose(args.verbose, "Successfully updated 'definition.csv'!")

    print_verbose(args.verbose, "Updating province history files...")
    update_province_history(almanac, args)
    print_verbose(args.verbose, "Successfully updated all province history files!")

    print_verbose(args.verbose, "Updating localization files for provinces...")
    update_province_loca() #Currently draws province names from 'definition.csv', not the almanac.
    print_verbose(args.verbose, "Successfully updated all localization files for provinces!")

    print_info("Successfully updated all provinces!\n")

def main():
    parser = argparse.ArgumentParser(
        prog='Helper',
        description='A EU4 busywork automation script.',
        usage='%(prog)s [options]',
        add_help=False,
        epilog='If you need anything, contact Jabberdrake!'
    )

    parser.add_argument("-h", "--help", action="store_true", help="Displays the help menu. The one you're reading right now.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enables verbose mode. Very useful for debugging!")
    parser.add_argument("-i", "--intro", action="store_true", help="Lists some introductory information, along with some common use cases. Consider using this flag if you're a bit lost!")

    args = parser.parse_args()

    if args.help:
        print_help(parser)
        return
    
    # Start the actual program.
    print_art()
    
    if not any(vars(args).values()):
        print_info("For some information on how to use the script, consider running: 'python3 helper.py --help'!\n")
    else:
        if args.intro:
            print_intro()
        if args.verbose:
            print_verbose(args.verbose, "Verbose mode is now enabled!\n")

    while True:
        mode = inquirer.select(
            message="Select one of the following operations:",
            choices=[
                "Update provinces",
                "Check script data", 
                "Exit"
            ]
        ).execute()

        match mode:
            case "Update provinces":
                update_provinces(args)
            case "Check script data":
                print_data(data, args)
            case "Exit":
                print_info("See you next time!\n")
                return
            case _:
                print_info("Uh oh... This wasn't supposed to happen. Quitting!\n")
                return


if __name__ == "__main__":
    main()