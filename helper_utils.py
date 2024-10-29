"""This module contains some shared utility functions."""

import re
import helper_data

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

def red(string):
    return colored(string, "#cc5c46")

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
    new = re.sub(r'[\'\"]', '', new)
    new = re.sub(r'[ \t]', "_", new)
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

# Formats and prints a given string to denote it as ERROR logging.
def print_error(string):
    print(red(bold('>>')) + " " + string)

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

def print_data(args):
    print()
    print_info("Global flags:")
    print("\t" + brass("★ ") + "Verbose mode: " + purple("Enabled" if args.verbose else "Disabled"))
    print()

    print_info("Almanac info:")
    print("\t" + brass("★ ") + "Document name: " + purple(helper_data.ALMANAC_NAME))
    print("\t" + brass("★ ") + "Document id: " + purple(helper_data.ALMANAC_ID))
    print("\t" + brass("★ ") + "Target sheet: " + purple(helper_data.PROVS_SHEET))
    print()

    print_info("Map processing settings:")
    print("\t" + brass("★ ") + "Lowest ID for temporary wasteland: " + purple(helper_data.FIRST_TEMP_WASTELAND))
    print("\t" + brass("★ ") + "Max provinces: " + purple(helper_data.MAX_PROVINCES))
    print()

###

### CLASSES ###

class Area:
    def __init__(self, internal_name, localized_name, region):
        self.iname = internal_name
        self.lname = localized_name
        self.region = region
        self.visible_by = []
        self.provinces = []

    def __str__(self):
        aux = ",".join([str(id) for id in self.provinces])
        return f"{self.iname}<{self.region.iname}>({aux})"
    
    def __eq__(self, other):
        if isinstance(other, Area):
            return self.iname == other.iname and self.region == other.region
        return False
    
    def add_province(self, province):
        self.provinces.append(province)
    
    def add_visible_by(self, techgroup):
        self.visible_by.append(techgroup)

class Region:
    def __init__(self, internal_name, localized_name, superregion):
        self.iname = internal_name
        self.lname = localized_name
        self.superregion = superregion
        self.areas = []

    def __str__(self):
        aux = ",".join([area.iname for area in self.areas])
        return f"{self.iname}<{self.superregion.iname}>({aux})"
    
    def __eq__(self, other):
        if isinstance(other, Region):
            return self.iname == other.iname and self.superregion == other.superregion
        return False

    def add_area(self, area):
        self.areas.append(area)

class Superregion:
    def __init__(self, internal_name, localized_name, continent):
        self.iname = internal_name
        self.lname = localized_name
        self.continent = continent
        self.regions = []
    
    def __str__(self):
        aux = ",".join([region.iname for region in self.regions])
        return f"{self.iname}<{self.continent.iname}>({aux})"
    
    def __eq__(self, other):
        if isinstance(other, Superregion):
            return self.iname == other.iname and self.continent == other.continent
        return False

    def add_region(self, region):
        self.regions.append(region)

class Continent:
    def __init__(self, internal_name, localized_name):
        self.iname = internal_name
        self.lname = localized_name
        self.superregions = []

    def __str__(self):
        aux = ",".join([sregion.iname for sregion in self.superregions])
        return f"{self.iname}({aux})"
    
    def __eq__(self, other):
        if isinstance(other, Continent):
            return self.iname == other.iname
        return False

    def add_superregion(self, superregion):
        self.superregions.append(superregion)

class InternalHelperException(Exception):
    """Raised (and hopefully caught) within the Helper script whenever a fatal error occurs during execution."""

    def __init__(self, message):
        super().__init__(message)

class UnknownAreaException(Exception):
    """Raised if nothing is returned in a 'get_area()' call."""

    def __init__(self, message):
        super().__init__(message)

class UnknownRegionException(Exception):
    """Raised if nothing is returned in a 'get_region()' call."""

    def __init__(self, message):
        super().__init__(message)

class UnknownSuperregionException(Exception):
    """Raised if nothing is returned in a 'get_superregion()' call."""

    def __init__(self, message):
        super().__init__(message)

class UnknownContinentException(Exception):
    """Raised if nothing is returned in a 'get_continent()' call."""

    def __init__(self, message):
        super().__init__(message)

def get_continent(continent_name):
    continent_name = plain(continent_name)

    for continent in helper_data.CONTINENTS:
        if continent_name == continent.iname:
            return continent
    raise UnknownContinentException(f"'{continent_name}' does not match a known continent!")
        
def get_superregion(superregion_name, continent_name):
    continent = get_continent(continent_name)
    superregion_name = plain(superregion_name)

    for superregion in continent.superregions:
        if superregion_name == superregion.iname:
            return superregion
    raise UnknownSuperregionException(f"'{superregion_name}' does not match a known superregion!")
        
def get_region(region_name, superregion_name, continent_name):
    superregion = get_superregion(superregion_name, continent_name)
    region_name = plain(region_name)

    for region in superregion.regions:
        if region_name == region.iname:
            return region
    raise UnknownRegionException(f"'{region_name}' does not match a known region!")
        
def get_area(area_name, region_name, superregion_name, continent_name):
    region = get_region(region_name, superregion_name, continent_name)
    area_name = plain(area_name)

    for area in region.areas:
        if area_name == area.iname:
            return area
    raise UnknownAreaException(f"'{area_name}' does not match a known area!")
    
###