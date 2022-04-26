import datetime

import peewee

INDENT_SIZE = 2

DB = peewee.PostgresqlDatabase(
    # TODO
)

MAX_CACHE_LIFETIME = datetime.timedelta(days=7)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
)
