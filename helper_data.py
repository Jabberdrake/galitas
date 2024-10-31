"""This module contains script configuration and map data."""

### Constants used in script configuration
ALMANAC_NAME = "Almanac of Galitas"
ALMANAC_ID = "1SjlQj7fh65_2u0yAp32Sc-J8injhJ0zUvlC27soAzSs"
PROVS_SHEET = "Provinces"
FIRST_TEMP_WASTELAND = 4971
MAX_PROVINCES = 5000

### Simple maps used for non-trivial name assignment
RELIGION_MAP = { # Used in cases where localized-to-internal name assignment isn't straightforward.
    "Catholic": "catholic",
    "Orthodox": "orthodox"
}
CULTURE_MAP = { # Used in cases where localized-to-internal name assignment isn't straightforward.
    "Francien": "cosmopolitan_french", #like this
    "Portuguese": "portugese"
}

CONTINENTS = ["galitas",]

TECHGROUP_MAP = ["western", "eastern"]