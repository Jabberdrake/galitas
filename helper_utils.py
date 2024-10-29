"""This module contains some shared utility functions."""

import re

### TEXT FORMATTING ###
def bold(string):
    return '\033[1m' + string + '\033[0m'

def colored(string, hexcolor):
    r = int(hexcolor[1:3], 16)
    g = int(hexcolor[3:5], 16)
    b = int(hexcolor[5:7], 16)
    return f"\033[38;2;{r};{g};{b}m{string}\033[0m"

def brass(string):
    return colored(string, "#e5c07b")

def blue(string):
    return colored(string, "#61afef")

def teal(string):
    return colored(string, "#008080")

def purple(string):
    return colored(string, "#d8bbfa")

def plain(old):
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
    return new

###

### INFORMATION LOGGING ###

# Formats and prints a given string to denote it as DEBUG logging.
def print_verbose(verbose, string):
    if verbose:
        print(teal(bold('>>')) + " " + string)

# Formats and prints a given string to denote it as INFO logging.
def print_info(string):
    print(brass(bold('>>')) + " " + string)

### MENUS AND DISPLAYS ###

# Displays some cool ASCII art on startup. Only visible whenever the script isn't started with a help flag.
def print_art():
    art = r"""
    ┓┏  ┓      
    ┣┫┏┓┃┏┓┏┓┏┓
    ┛┗┗ ┗┣┛┗ ┛ 
         ┛
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━     
    """

    desc = 'a EU4 busywork automation script, by Jabberdrake\n'

    print(brass(art) + brass(bold(desc)))

# Displays the help menu. Is executed whenever the script is started with a help flag.
def print_help(parser):

    print(brass(bold('Usage:')) + " python3 helper.py [" + blue("options") + "]\n\n" + brass(bold('Options:')))
    for action in parser._actions:
        flags = blue(", ".join(action.option_strings))
        print(f"\t{flags}\t\t{action.help}")
    
    print(f"\n{parser.epilog}\n")

# Displays the intro text. Is executed whenever the script is started with an intro flag.
def print_intro():
    print(brass(bold("What is this thing?")))
    print("\tIn short, Helper is a tool that aims to help EU4 modders by automating away some of the busier, most boring and often brainless tasks. Prime examples include adding new provinces, editing province data or implementing trade flow networks.\n\tIt used to be the case that, for each of these tasks, you'd have to pour over dozens of files, input the same (ish) data over and over again ad nauseum, only to certainly make some mistakes here and there and then spend an hour or two trying to whack them out. Very unpleasant stuff. By using Helper, you can set up all the data you need in a Google Spreadsheet, run a single command and have the script do it all for you!")
    print("\n\n" + brass(bold("Common use cases:")))
    print("\tWIP!")

    print()

def print_data(data, args):
    print()
    print_info("Global flags:")
    print("\t" + brass("★ ") + "Verbose mode: " + purple("Enabled" if args.verbose else "Disabled"))
    print()

    print_info("Almanac info:")
    print("\t" + brass("★ ") + "Document name: " + purple(data["ALMANAC_NAME"]))
    print("\t" + brass("★ ") + "Document id: " + purple(data["ALMANAC_ID"]))
    print("\t" + brass("★ ") + "Target sheet: " + purple(data["PROVS_SHEET"]))
    print()

    print_info("Map processing settings:")
    print("\t" + brass("★ ") + "Lowest ID for temporary wasteland: " + purple(data["FIRST_TEMP_WASTELAND"]))
    print("\t" + brass("★ ") + "Max provinces: " + purple(data["MAX_PROVINCES"]))
    print()

###