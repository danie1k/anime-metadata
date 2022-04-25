import click

from anime_metadata import constants, models


@click.command()
def main():
    constants.DB.connect()
    constants.DB.create_tables(
        [
            models.ProviderCache,
        ]
    )

    # TODO
