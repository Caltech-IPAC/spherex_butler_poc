import os
import logging
import shutil
import tempfile
import unittest

from astropy.io import fits

import lsst.utils.tests
from lsst.daf.butler import Butler, Config, DatasetRef, FileDataset, StorageClassFactory, Timespan
from lsst.daf.butler.tests import DatasetTestHelper, makeTestRepo, addDatasetType

from spherex.formatters.astropy_image import AstropyImageFormatter

TESTDIR = os.path.dirname(__file__)

# File-based db stays open at the end of the test,
# which would prevent running pytest with --open-files option
# File-based:
#   db: sqlite:///<butlerRoot>/mytest.sqlite3
# In-memory:
#   db: 'sqlite:///:memory:'
BUTLER_CONFIG = """
datastore:
  # Want to check disassembly so can't use InMemory
  cls: lsst.daf.butler.datastores.posixDatastore.PosixDatastore
  formatters:
    MyImage: spherex.formatters.astropy_image.AstropyImageFormatter
  templates:
    default: "{run:/}/{datasetType}.{component:?}/{label:?}/{detector:?}/{exposure.group_name:?}/{datasetType}_{component:?}_{label:?}_{calibration_label:?}_{exposure:?}_{detector:?}_{instrument:?}_{skypix:?}_{run}"

storageClasses:
  MyImage:
    pytype: astropy.io.fits.HDUList

registry:
  db: 'sqlite:///:memory:'

"""
INSTRUMENT_NAME = "MyCam"
DATASET_TYPE_NAME = "myDatasetType"

log = logging.getLogger(__name__)


class AstropyFitsTests(DatasetTestHelper, lsst.utils.tests.TestCase):
    root = None
    storageClassFactory = None

    @classmethod
    def setUpClass(cls):
        """Create a new butler once only."""

        cls.storageClassFactory = StorageClassFactory()

        cls.root = tempfile.mkdtemp(dir=TESTDIR)

        data_ids = {
            "instrument": [INSTRUMENT_NAME],
            "detector": [0, 1, 2, 3, 4, 5],
            "exposure": [11, 22],
        }

        cls.creatorButler = makeTestRepo(cls.root, data_ids, config=Config.fromYaml(BUTLER_CONFIG))
        datasetTypeName, storageClassName = (DATASET_TYPE_NAME, "MyImage")
        storageClass = cls.storageClassFactory.getStorageClass(storageClassName)
        addDatasetType(cls.creatorButler, datasetTypeName, set(data_ids), storageClass)
        # create test dataset type that does not have dimensions
        # addDatasetType(cls.creatorButler, datasetTypeName, {}, storageClass)

    @classmethod
    def tearDownClass(cls):
        if cls.root is not None:
            shutil.rmtree(cls.root, ignore_errors=True)

    def setUp(self):
        # make test collection
        # self.butler = makeTestCollection(self.creatorButler)
        self.collection = self._testMethodName
        self.butler = Butler(butler=self.creatorButler, run=self.collection)

    def test_putget(self):
        fitsPath = os.path.join(TESTDIR, "data", "small.fits")
        hdulist = fits.open(fitsPath)
        l1 = hdulist.info(False)  # list of tuples representing HDU info
        dataid = {"exposure": 11, "detector": 0, "instrument": INSTRUMENT_NAME}
        ref = self.butler.put(hdulist, DATASET_TYPE_NAME, dataid)

        # Get the full thing
        retrievedHDUList = self.butler.get(DATASET_TYPE_NAME, dataid)
        l2 = retrievedHDUList.info(False)  # list of tuples representing HDU info

        self.assertListEqual(l1, l2)

    def test_ingest(self):

        fitsPath = os.path.join(TESTDIR, "data", "small.fits")

        datasetType = self.butler.registry.getDatasetType(DATASET_TYPE_NAME)
        datasets = []
        for exposure in range(3, 5):
            for detector in range(6):
                # use the same fits to test ingest
                if not os.path.exists(fitsPath):
                    log.warning(f"No data found for detector {detector}, exposure {exposure} @ {fitsPath}.")
                    continue
                ref = DatasetRef(datasetType, dataId={"instrument": INSTRUMENT_NAME,
                                                      "detector": detector,
                                                      "exposure": exposure * 11})
                datasets.append(FileDataset(refs=ref, path=fitsPath, formatter=AstropyImageFormatter))

        # register new collection
        # run = "rawIngestedRun"
        # self.butler.registry.registerCollection(run, type=CollectionType.RUN)

        # collection is registered as a part of setUp
        run = self.collection

        with self.butler.transaction():
            for exposure in range(3, 5):
                expid = exposure*11
                self.butler.registry.insertDimensionData("exposure", {"instrument": INSTRUMENT_NAME,
                                                                      "id": expid,
                                                                      "name": f"{expid}",
                                                                      "group_name": "day1",
                                                                      "timespan": Timespan(begin=None, end=None)})
            # transfer can be 'auto', 'move', 'copy', 'hardlink', 'relsymlink' or 'symlink'
            self.butler.ingest(*datasets, transfer="symlink", run=run)

        # verify that 12 files were ingested (2 exposures for each detector)
        refsSet = set(self.butler.registry.queryDatasets(DATASET_TYPE_NAME, collections=[run]))
        self.assertEqual(len(refsSet), 12, f"Collection {run} should have 12 elements after ingest")

        # verify that data id is present
        dataid = {"exposure": 44, "detector": 5, "instrument": INSTRUMENT_NAME}
        refsList = list(self.butler.registry.queryDatasets(DATASET_TYPE_NAME, collections=[run],
                                                           dataId=dataid, deduplicate=True))
        self.assertEqual(len(refsList), 1, f"Collection {run} should have 1 element with {dataid}")

        # get the python representation of data id
        # retrievedHDUList = self.butler.get(DATASET_TYPE_NAME, dataid, collections=[run])


if __name__ == '__main__':
    unittest.main()

# Non-empty tables in butler repo, produced by this test_putget
# group_name is not set for this test case
#
# collection
# collection_id|name|type
# 1|test_putget|1
#
# dataset
# id|dataset_type_id|run_id
# 1|1|1
#
# dataset_collection_34
# dataset_type_id|dataset_id|collection_id|instrument|detector|exposure
# 1|1|1|MyCam|0|11
#
# dataset_location
# datastore_name|dataset_id
# PosixDatastore@<butlerRoot>|1
#
# dataset_type
# id|name|storage_class|dimensions_encoded
# 1|myDatasetType|MyImage|NA==
#
# detector
# instrument|id|full_name|lmin|lmax|r|desc
# MyCam|0|0||||
# MyCam|1|1||||
# MyCam|2|2||||
# MyCam|3|3||||
# MyCam|4|4||||
# MyCam|5|5||||
#
# instrument
# name|visit_max|exposure_max|detector_max|class_name
# MyCam||||
#
# opaque_meta;
# table_name
# posix_datastore_records
#
# posix_datastore_records
# dataset_id|path|formatter|storage_class|component|checksum|file_size
# 1|test_putget/myDatasetType/0/None/myDatasetType_11_0_MyCam_test_putget.fits|spherex.formatters.astropy_image.AstropyImageFormatter|MyImage|__NULL_STRING__||51840
#
# run
# collection_id|datetime_begin|datetime_end|host
# 1|||
