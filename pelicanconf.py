import alchemy

AUTHOR = 'Mark Snidal'
SITENAME = "Mark's Yellhorn"
SITEURL = ''

PATH = 'content'

TIMEZONE = 'America/New_York'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (("GitHub", "https://github.com/msnidal"),("LinkedIn", "https://www.linkedin.com/in/msnidal/"))
SOCIAL = ()

DEFAULT_PAGINATION = 10

THEME = alchemy.path()

STATIC_PATHS = ["static"]
EXTRA_PATH_METADATA = {
    "static/favicon.ico": {"path": "favicon.ico"},
}


# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True