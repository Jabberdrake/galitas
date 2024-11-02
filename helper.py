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
from helper_utils import plain, brass, blue, teal, purple, red                  # Text formatting
from helper_utils import print_info, print_verbose, print_error                 # Logging functions
from helper_utils import print_art, print_help, print_intro, print_data         # Menus and Displays
from helper_utils import is_seatile
from helper_utils import Area, Region, Superregion, Continent
from helper_utils import get_area, get_region, get_superregion, get_continent
from helper_utils import InternalHelperException, UnknownAreaException, UnknownRegionException, UnknownSuperregionException, UnknownContinentException
import helper_data

def load_almanac():
    url = f'https://docs.google.com/spreadsheets/d/{helper_data.ALMANAC_ID}/gviz/tq?tqx=out:csv&sheet={helper_data.PROVS_SHEET}'
    dataframe = pd.read_csv(url)
    dataframe = dataframe.drop(dataframe.columns[30:41], axis = 1)
    dataframe.columns = ["name", "id", "type", "rgb", "area", "region", "superregion", "continent", "winters", "monsoons", "terrain", "climate", "is_colonized", "is_owned_by", "is_core_of", "is_city", "religion", "culture", "tradenode", "tradegood", "latentgood", "cot_rank", "base_tax", "base_production", "base_manpower", "total_development", "has_lv2_fort", "discovered_by", "prov_modifiers", "notes"]
    dataframe = dataframe.dropna(axis=0, subset=['type'])
    return dataframe

def find_last_province(dataframe):
    for i in range(helper_data.MAX_PROVINCES):
        try:
            dataframe.loc[i, 'name']
        except KeyError as error:
            return error.args[0]

def build_tiletrees(dataframe, last_province, args):
    root = helper_data.CONTINENTS

    areas = []
    regions = []
    superregions = []

    illegal_namelist = ["nan", "?", "-", "debug", "test", "freaky", "freakistan"]

    with open('map/definition.csv', 'r', encoding='UTF-8') as definition:
        for line in definition.readlines():
            line_arr = line.split(";")
            if not line_arr[0].isnumeric():
                continue
            else:
                provID = int(line_arr[0])
                if provID > last_province:
                    return
                
                tiletype = dataframe.at[provID-1, 'type']
                if tiletype == "Indev" or tiletype == "Lake":
                    pass
                if args.verbose and provID % 50 == 0:
                    print_verbose(args.verbose, "Processing province no. " + str(provID) + "...")
                
                # Processing area name
                area_lname = str(dataframe.at[provID-1, 'area'])
                area_iname = plain(area_lname)
                if area_iname in illegal_namelist:
                    print_error(f"Invalid area name ({red(area_lname)}) found for province no. {purple(str(provID))}. Quitting!\n")
                    raise InternalHelperException("FATAL")
                
                # Processing region name
                region_lname = str(dataframe.at[provID-1, 'region'])
                region_iname = plain(region_lname)
                if region_iname in illegal_namelist:
                    print_error(f"Invalid region name ({red(region_lname)}) found for province no. {purple(str(provID))}. Quitting!\n")
                    raise InternalHelperException("FATAL")
                
                # Processing superregion name
                superregion_lname = str(dataframe.at[provID-1, 'superregion'])
                superregion_iname = plain(superregion_lname)
                if superregion_iname in illegal_namelist:
                    print_error(f"Invalid superregion name ({red(superregion_lname)}) found for province no. {purple(str(provID))}. Quitting!\n")
                    raise InternalHelperException("FATAL")

                # Processing continent name
                if is_seatile(tiletype): # In EU4, sea tiles do not have an associated continent. To cope with that, we're going to make a dummy continent, 'seatiles', and keep an eye out for it whenever we write the continent.txt file.
                    continent_lname = "seatiles"
                else:
                    continent_lname = str(dataframe.at[provID-1, 'continent'])
                continent_iname = plain(continent_lname)
                if continent_iname in illegal_namelist:
                    print_error(f"Invalid continent name ({red(continent_lname)}) found for province no. {purple(str(provID))}. Quitting!\n")
                    raise InternalHelperException("FATAL")
                
                # handle the 'Continent' field
                try:
                    continent = get_continent(continent_lname) # if this continent exists and is already registered, we good
                except UnknownContinentException as c_error:
                    print_verbose(args.verbose, f"Registering new continent: '{continent_iname}' ({continent_lname})!")
                    continent = Continent(continent_iname, continent_lname)
                    root.append(continent) # add to tree root
                
                # handle the 'Superregion' field
                try:
                    superregion = get_superregion(superregion_iname, continent_lname)
                except UnknownSuperregionException as s_error:
                    # either the superregion doesn't exist at all, or it exists under the wrong path
                    for known_superregion in superregions:
                        if known_superregion.iname == superregion_iname and known_superregion.continent != continent:
                            print_error(f"Tried to register superregion '{superregion_lname}' under two different continents ({known_superregion.continent.iname} ≠ {continent_iname}) while processing province no. {purple(str(provID))}! Quitting!\n")
                            raise InternalHelperException("FATAL")
                    print_verbose(args.verbose, f"Registering new superregion: '{superregion_iname}' ({superregion_lname}) under {continent_iname}!")
                    superregion = Superregion(superregion_iname, superregion_lname, continent)
                    continent.add_superregion(superregion) # add to parent continent
                    superregions.append(superregion) # add to global list
                
                # handle the 'Region' field
                try:
                    region = get_region(region_lname, superregion_lname, continent_lname)
                except UnknownRegionException as r_error:
                    # either the region doesn't exist at all, or it exists under the wrong path
                    for known_region in regions:
                        if known_region.iname == region_iname and known_region.superregion != superregion:
                            print_error(f"Tried to register region '{region_lname}' under two different superregions ({known_region.superregion.iname} ≠ {superregion_iname}) while processing province no. {purple(str(provID))}! Quitting!\n")
                            raise InternalHelperException("FATAL")
                    print_verbose(args.verbose, f"Registering new region: '{region_iname}' ({region_lname}) under {superregion_iname}!")
                    region = Region(region_iname, region_lname, superregion)
                    superregion.add_region(region) # add to parent superregion
                    regions.append(region) # add to global list

                # handle the 'Area' field
                try:
                    area = get_area(area_lname, region_lname, superregion_lname, continent_lname)
                except UnknownAreaException as a_error:
                    # either the area doesn't exist at all, or it exists under the wrong path
                    for known_area in areas:
                        if known_area.iname == area_iname and known_area.region != region:
                            print_error(f"Tried to register area '{area_lname}' under two different regions ({known_area.region.iname} ≠ {region_iname}) while processing province no. {purple(str(provID))}! Quitting!\n")
                            raise InternalHelperException("FATAL")
                    print_verbose(args.verbose, f"Registering new area: '{area_iname}' ({area_lname}) under {region_iname}!")
                    area = Area(area_iname, area_lname, region)
                    region.add_area(area) # add to parent region
                    areas.append(area) # add to global list

                area.add_province(provID)
    return root
                
def write_areas(treeroot, args):
    pass

def write_regions(treeroot, args):
    pass

def write_superregions(treeroot, args):
    pass

def rebuild_definition_file(dataframe, last_province):
    with open('map/definition.csv', 'w', encoding='UTF-8', newline='') as definition_file:
        writer = csv.writer(definition_file)
        writer.writerow(["province", "red", "green", "blue", "x", "x"])
        i = 0
        for i in range(helper_data.MAX_PROVINCES - 1):
            if i+1 > last_province and i+1 < helper_data.FIRST_TEMP_WASTELAND:
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

def reload_province_history(dataframe, args):
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

    religion_map = helper_data.RELIGION_MAP
    culture_map = helper_data.CULTURE_MAP
    tech_groups = helper_data.TECHGROUP_MAP

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

def reload_province_loca():
    with open('localisation/replace/prov_names_l_english.yml', 'w', encoding='UTF-8-sig') as loca:
        with open('map/definition.csv', 'r', encoding='UTF-8') as definition:
            loca.write('l_english:\n')
            for line in definition.readlines():
                line_arr = line.split(";")
                if line_arr[0].isnumeric():
                    loca.write(' PROV' + str(line_arr[0]) + ": \"" + line_arr[4] + '\"\n')

def rebuild_continent_file(dataframe, last_province, args):
    continent_list = helper_data.CONTINENTS

    cmapping = {}
    for continent in continent_list:
        cmapping.update({continent: []})

    with open('map/definition.csv', 'r', encoding='UTF-8') as definition:
        for line in definition.readlines():
            line_arr = line.split(";")
            if not line_arr[0].isnumeric() or int(line_arr[0]) >= helper_data.FIRST_TEMP_WASTELAND:
                continue
            else:
                provID = int(line_arr[0])
                if not dataframe.at[provID-1, 'type'] == "Land" and not dataframe.at[provID-1, 'type'] == "Wasteland":
                    continue
                if args.verbose and provID % 50 == 0:
                    print_verbose(args.verbose, "Processing province no. " + str(provID) + "...")
                continent_iname = plain(str(dataframe.at[provID-1, 'continent']))

                provinces_of_continent = cmapping[continent_iname]
                provinces_of_continent.append(provID)

    with open('map/continent.txt', 'w', encoding='ISO-8859-1') as result:
        for continent in cmapping:
            statement = continent + " = {\n"

            provinces_of_continent = cmapping[continent]

            provinces_as_string = ' '.join([str(prov) for prov in provinces_of_continent])
            statement = statement + "\t" + provinces_as_string + "\n"
            statement = statement + "}" + "\n\n"

        base_game_section = "### Base Game\neurope = {\n\n}\n\nasia = {\n\n}\n\nafrica = {\n\n}\n\nnorth_america = {\n\n}\n\nsouth_america = {\n\n}\n\noceania = {\n\n}\n\n"
        
        debug_continent_section = "debug_continent = { #unused province ids go here to prevent errors. if an id is present in 2 continents, it will create an error, so they're easy to find\n"
        debug_string = ' '.join([str(id) for id in range(last_province+1, helper_data.MAX_PROVINCES)])
        debug_continent_section = debug_continent_section + '\t' + debug_string + '\n'
        debug_continent_section = debug_continent_section + "}\n\n"

        last_section = "island_check_provinces = {\n\n}\n\n# Used for RNW\nnew_world = {\n\n}\n"

        statement = statement + base_game_section + debug_continent_section + last_section
        result.write(statement)


def update_provinces(args):

    print_verbose(args.verbose, "Loading almanac...")
    almanac = load_almanac()
    print_verbose(args.verbose, "Loaded almanac '" + helper_data.ALMANAC_NAME + "'!")

    print_verbose(args.verbose, "Calculating highest ID province in loaded almanac...")
    last_province = find_last_province(almanac)
    print_verbose(args.verbose, "Highest province ID in loaded almanac is " + str(last_province) + "!")

    print_verbose(args.verbose, "Rebuilding 'definition.csv' file...")
    rebuild_definition_file(almanac, last_province)
    print_verbose(args.verbose, "Successfully rebuilt 'definition.csv'!")

    print_verbose(args.verbose, "Reloading province history files...")
    reload_province_history(almanac, args)
    print_verbose(args.verbose, "Successfully reloaded all province history files!")

    print_verbose(args.verbose, "Reloaded localization files for provinces...")
    reload_province_loca() #Currently draws province names from 'definition.csv', not the almanac.
    print_verbose(args.verbose, "Successfully reloaded all localization files for provinces!")

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
    parser.add_argument("-v", "--verbose", action="store_true", help="Enables 'verbose' mode, which prints more information throughout operations. Very useful for debugging!")
    parser.add_argument("-i", "--intro", action="store_true", help="Lists some introductory information, along with some common use cases. Consider using this flag if you're a bit lost!")
    parser.add_argument("-m",  "--multi", action="store_true", help="Enables 'multi' mode, which prevents the program from exiting after doing an operation.")

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
            print_verbose(args.verbose, "Verbose mode is now enabled!")
        if args.multi:
            print_verbose(args.verbose, "Multi mode is now enabled!")
        print('\n')

    repeat_flag = True
    while repeat_flag:
        # If multi mode is not enabled, quit after one operation
        if args.multi == False:
            repeat_flag = False

        # Allow user to select operation
        mode = inquirer.select(
            message="Select one of the following operations:",
            choices=[
                "Check script data",
                "Update provinces",
                "Reload province history",
                "Reload province localization",
                "Rebuild continent file",
                "Rewrite tile hierarchy",
                "Exit"
            ]
        ).execute()

        # Do operation
        try:
            match mode:
                case "Check script data":
                    print_data(args)
                case "Update provinces":
                    update_provinces(args)
                case "Reload province history":
                    # Load the almanac
                    print_verbose(args.verbose, "Loading almanac...")
                    almanac = load_almanac()
                    print_verbose(args.verbose, "Loaded almanac '" + helper_data.ALMANAC_NAME + "'!")

                    # Update province history files
                    print_verbose(args.verbose, "Reloading province history files...")
                    reload_province_history(almanac, args)

                    # Print success message
                    print_info("Successfully reloaded all province history files!\n")
                case "Reload province localization":
                    # Update province loca file
                    print_verbose(args.verbose, "Reloading localization files for provinces...")
                    reload_province_loca() #Currently draws province names from 'definition.csv', not the almanac.

                    # Print success message
                    print_info("Successfully reloading all localization files for provinces!\n")
                case "Rebuild continent file":
                    # Load the almanac
                    print_verbose(args.verbose, "Loading almanac...")
                    almanac = load_almanac()
                    print_verbose(args.verbose, "Loaded almanac '" + helper_data.ALMANAC_NAME + "'!")

                    # Find the last province
                    print_verbose(args.verbose, "Calculating highest ID province in loaded almanac...")
                    last_province = find_last_province(almanac)
                    print_verbose(args.verbose, "Highest province ID in loaded almanac is " + str(last_province) + "!")

                    print_info("Remember to manually edit the 'continent_map' field in the script coding if you add any new continents!")

                    print_verbose(args.verbose, "Rebuilding 'map/continent.txt' file...")
                    rebuild_continent_file(almanac, last_province, args)

                    # Print success message
                    print_info("Successfully rebuilt the 'map/continent.txt' file!\n")
                case "Rewrite tile hierarchy":
                    # Load the almanac
                    print_verbose(args.verbose, "Loading almanac...")
                    almanac = load_almanac()
                    print_verbose(args.verbose, "Loaded almanac '" + helper_data.ALMANAC_NAME + "'!")

                    # Find the last province
                    print_verbose(args.verbose, "Calculating highest ID province in loaded almanac...")
                    last_province = find_last_province(almanac)
                    print_verbose(args.verbose, "Highest province ID in loaded almanac is " + str(last_province) + "!")

                    # Build abstract tile trees
                    print_verbose(args.verbose, "Building abstract tile tree...")
                    root = build_tiletrees(almanac, last_province, args)
                    print_verbose(args.verbose, "Successfully built abstract tile tree!")

                    # Write area file
                    print_verbose(args.verbose, "Writing area info on 'map/area.txt' file...")
                    write_areas(root, args)
                    print_verbose(args.verbose, "Successfully wrote area info!")

                    # Write region file
                    print_verbose(args.verbose, "Writing region info on 'map/region.txt' file...")
                    write_regions(root, args)
                    print_verbose(args.verbose, "Successfully wrote region info!")

                    # Write superregions file
                    print_verbose(args.verbose, "Writing superregion info on 'map/superregion.txt' file...")
                    write_superregions(root, args)
                    print_verbose(args.verbose, "Successfully wrote superregion info!")

                    # Write continent file
                    print_verbose(args.verbose, "Writing continent info on 'map/continent.txt'...")
                    rebuild_continent_file(almanac, last_province, args)

                    # Print success message
                    print_info("Successfully rewrote the tile hierarchy!\n")
                case "Exit":
                    print_info("See you next time!\n")
                    return
                case _:
                    print_error("Uh oh... This wasn't supposed to happen. Quitting!\n")
                    return
        except InternalHelperException as ierror:
            pass


if __name__ == "__main__":
    main()