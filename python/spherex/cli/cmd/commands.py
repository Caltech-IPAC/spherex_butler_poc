import click

from lsst.daf.butler.cli.opt import (repo_argument,
                                     locations_argument,
                                     regex_option,
                                     run_option,
                                     transfer_option
                                     )
from lsst.daf.butler.cli.utils import (cli_handle_exception)
from ... import script

from lsst.daf.butler.cli.utils import MWArgumentDecorator
instrument_argument = MWArgumentDecorator("instrument",
                                          help="The name or fully-qualified class name of an instrument.")

# default regular expression to find sumulated files
rawexp_re = r"sim_exposure_(\d+)_array_(\d).fits"


@click.command(short_help="Ingest simulated images.")
@repo_argument(required=True)
@locations_argument(help="LOCATIONS specifies files to ingest and/or locations to search for files.",
                    required=True)
@regex_option(default=rawexp_re,
              help="Regex string used to find files in directories listed in LOCATIONS. "
                   "Searches for fits files by default.")
@run_option(required=False)
@transfer_option()
@click.option("--ingest-type", default="rawexp", help="Raw exposure images")
def ingest_simulated(*args, **kwargs):
    """Ingest raw frames into from a directory into the butler registry"""
    cli_handle_exception(script.ingestSimulated, *args, **kwargs)
