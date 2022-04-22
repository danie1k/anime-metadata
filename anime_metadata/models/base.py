import peewee

from anime_metadata import constants


class BaseModel(peewee.Model):
    class Meta:
        database = constants.DB
