import os
import unittest
import tempfile
import shutil

import lsst.utils.tests

from lsst.daf.butler import Config
from lsst.daf.butler import StorageClassFactory
from lsst.daf.butler.tests import DatasetTestHelper, makeTestRepo, addDatasetType, makeTestCollection

from astropy.io import fits

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
    default: "{run:/}/{datasetType}.{component:?}/{label:?}/{detector:?}/{exposure:?}/{datasetType}_{component:?}_{label:?}_{calibration_label:?}_{exposure:?}_{detector:?}_{instrument:?}_{skypix:?}_{run}"

storageClasses:
  MyImage:
    pytype: astropy.io.fits.HDUList

registry:
  db: 'sqlite:///:memory:'

"""

DATASET_TYPE_NAME = "myDatasetType"


class AstropyFitsTests(DatasetTestHelper, lsst.utils.tests.TestCase):
    root = None
    storageClassFactory = None

    @classmethod
    def setUpClass(cls):
        """Create a new butler once only."""

        cls.storageClassFactory = StorageClassFactory()

        cls.root = tempfile.mkdtemp(dir=TESTDIR)

        data_ids = {
            "instrument": ["MyCam"],
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
        self.butler = makeTestCollection(self.creatorButler)
        # collection = "myTestCollection"
        # self.butler = Butler(butler=self.creatorButler, run=collection)

    def test_putget(self):
        fitsPath = os.path.join(TESTDIR, "data", "small.fits")
        hdulist = fits.open(fitsPath)
        l1 = hdulist.info(False)  # list of tuples representing HDU info
        dataid = {"exposure": 11, "detector": 0, "instrument": "MyCam"}
        ref = self.butler.put(hdulist, DATASET_TYPE_NAME, dataid)

        # Get the full thing
        retrievedHDUList = self.butler.get(DATASET_TYPE_NAME, dataid)
        l2 = retrievedHDUList.info(False)  # list of tuples representing HDU info

        self.assertListEqual(l1, l2)


if __name__ == '__main__':
    unittest.main()

# Non-empty tables in butler repo, produced by this test
#
# collection
# collection_id|name|type
# 1|test228001913|1
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
# 1|test228001913/myDatasetType/0/11/myDatasetType_11_0_MyCam_test228001913.fits|spherex.formatters.astropy_image.AstropyImageFormatter|MyImage|__NULL_STRING__||51840
#
# run
# collection_id|datetime_begin|datetime_end|host
# 1|||
