import datetime

import peewee

INDENT_SIZE = 2

DB = peewee.PostgresqlDatabase(
    # TODO
)

MAX_CACHE_LIFETIME = datetime.timedelta(days=1)
