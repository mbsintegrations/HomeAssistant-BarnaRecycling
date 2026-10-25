"""Constants for the Barna Recycling integration."""
DOMAIN = "barna_recycling"
VERSION = "0.1.0"
BASE_URL = "https://cportal.barnarecycling.com/"
UPDATE_HOURS = 6
STREAMS = ("waste", "recycling", "compost")
CARD_PATH = "/barna_recycling/frontend"
CARD_URL = CARD_PATH + "/barna-recycling-card.js?v=" + VERSION + "-release1"
