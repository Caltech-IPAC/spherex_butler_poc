import re
import datetime
import logging

from lsst.daf.butler.core.utils import findFileResources

from lsst.daf.butler import (
    Butler,
    CollectionType,
    DataCoordinate,
    DatasetRef,
    DatasetType,
    FileDataset,
    Timespan
)

from ..formatters.astropy_image import AstropyImageFormatter


def ingestSimulated(repo, locations, regex, output_run, transfer="auto", ingest_type="rawexp"):
    """Ingests raw frames into the butler registry

    Parameters
    ----------
    repo : `str`
        URI to the repository.
    locations : `list` [`str`]
        Files to ingest and directories to search for files that match
        ``regex`` to ingest.
    regex : `str`
        Regex string used to find files in directories listed in locations.
    output_run : `str`
        The path to the location, the run, where datasets should be put.
    transfer : `str` or None
        The external data transfer type, by default "auto".
    ingest_type : `str`
        ingest product data type.

    Raises
    ------
    Exception
        Raised if operations on configuration object fail.

    Notes
    -----
    This method inserts all datasets for an exposure within a transaction,
    guaranteeing that partial exposures are never ingested.  The exposure
    dimension record is inserted with `Registry.syncDimensionData` first
    (in its own transaction), which inserts only if a record with the same
    primary key does not already exist.  This allows different files within
    the same exposure to be incremented in different runs.
    """

    butler = Butler(repo, writeable=True)

    # make sure instrument and detector dimensions are populated
    with butler.registry.transaction():
        instrument_record = {
            "name": "simulator",
            "exposure_max": 600000,
            "detector_max": 6,
            "class_name": "spherex.instrument.SimulatorInstrument"
        }
        butler.registry.syncDimensionData("instrument", instrument_record)
        for idx in range(1, 7):
            detector_record = {
                "instrument": "simulator",
                "id": idx,
                "full_name": f"array{idx}"
            }
            butler.registry.syncDimensionData("detector", detector_record)

    dimension_universe = butler.registry.dimensions
    datasetType = DatasetType(ingest_type,
                              dimension_universe.extract(("instrument", "detector", "exposure")),
                              "SPHERExImage",
                              universe=dimension_universe)
    # idempotent dataset type registration
    butler.registry.registerDatasetType(datasetType)

    # idempotent collection registration
    run = f"{ingest_type}r" if (output_run is None) else output_run
    butler.registry.registerCollection(run, type=CollectionType.RUN)

    n_failed = 0
    files = findFileResources(locations, regex)

    # example: sim_exposure_000000_array_1.fits or
    #   sim_exposure_000000_array_2_dark_current.fits
    pattern = re.compile(r"sim_exposure_(\d+)_array_(\d)[_,.]")

    # do we want to group observations?
    grp = datetime.date.today().strftime("%Y%m%d")

    datasets = []
    for file in files:
        # parse exposure and detector ids from file name
        m = pattern.search(file)
        if m is None:
            n_failed += 1
            logging.error(f"{file} does not match simulator file pattern")
            continue
        else:
            g = m.groups()
            if len(g) != 2:
                n_failed += 1
                logging.error(f"Unable to get exposure and detector from file name: {file}")
                continue
            else:
                [exposure_id, detector_id] = list(map(int, g))

        try:
            exposure_record = {"instrument": "simulator",
                               "id": exposure_id,
                               "name": f"{exposure_id:06d}",
                               "group_name": f"{grp}",
                               "timespan": Timespan(begin=None, end=None)}
            # idempotent insertion of individual dimension rows
            butler.registry.syncDimensionData("exposure", exposure_record)
        except Exception as e:
            n_failed += 1
            logging.error(f"Unable to insert exposure record for file {file}: {e}")
            continue

        dataId = DataCoordinate.standardize(instrument="simulator",
                                            detector=detector_id,
                                            exposure=exposure_id,
                                            universe=butler.registry.dimensions)
        ref = DatasetRef(datasetType, dataId=dataId)
        datasets.append(FileDataset(refs=ref, path=file, formatter=AstropyImageFormatter))

    with butler.transaction():
        butler.ingest(*datasets, transfer=transfer, run=run)
