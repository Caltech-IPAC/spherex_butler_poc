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

BUTLER_CONFIG = """
datastore:
  # Want to check disassembly so can't use InMemory
  cls: lsst.daf.butler.datastores.posixDatastore.PosixDatastore
  formatters:
    MyImage: spherex.astropy_image.AstropyImageFormatter
storageClasses:
  MyImage:
    pytype: astropy.io.fits.HDUList
registry:
  db: sqlite:///<butlerRoot>/mytest.sqlite3
"""

DATASET_TYPE_NAME = "myDatasetType"

class AstropyFitsTests(DatasetTestHelper, lsst.utils.tests.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a new butler once only."""

        cls.storageClassFactory = StorageClassFactory()

        cls.root = tempfile.mkdtemp(dir=TESTDIR)

        dataIds = {
            "instrument": ["MyCam"],
            "physical_filter": ["myFilter"],
            "visit": [11,22],
        }

        cls.creatorButler = makeTestRepo(cls.root, dataIds, config=Config.fromYaml(BUTLER_CONFIG))
        datasetTypeName, storageClassName = (DATASET_TYPE_NAME, "MyImage")
        storageClass = cls.storageClassFactory.getStorageClass(storageClassName)
        addDatasetType(cls.creatorButler, datasetTypeName, set(dataIds), storageClass)
        # create test dataset type that does not have dimensions
        #addDatasetType(cls.creatorButler, datasetTypeName, {}, storageClass)

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
        l1 = hdulist.info(False) # list of tuples representing HDU info
        dataId = {"visit": 11, "physical_filter": "myFilter", "instrument": "MyCam"}
        ref = self.butler.put(hdulist, DATASET_TYPE_NAME, dataId)

        # Get the full thing
        retrievedHDUList = self.butler.get(DATASET_TYPE_NAME, dataId)
        l2 = retrievedHDUList.info(False) # list of tuples representing HDU info

        self.assertListEqual(l1, l2)


if __name__ == '__main__':
    unittest.main()

# Non-empty tables in butler repo, produced by this test
#
# collection
# collection_id|name|type
# 1|test980668348|1
#
# dataset;
# id|dataset_type_id|run_id
# 1|1|1
#
# dataset_collection_248c;
# dataset_type_id|dataset_id|collection_id|instrument|visit
# 1|1|1|MyCam|11
#
# dataset_location
# datastore_name|dataset_id
# PosixDatastore@<butlerRoot>|1
#
# dataset_type
# id|name|storage_class|dimensions_encoded
# 1|myDatasetType|MyImage|JIw=
#
# instrument
# name|visit_max|exposure_max|detector_max|class_name
# MyCam||||
#
# opaque_meta;
# table_name
# posix_datastore_records
#
# physical_filter
# instrument|name|abstract_filter
# MyCam|myFilter|
#
# posix_datastore_records
# dataset_id|path|formatter|storage_class|component|checksum|file_size
# 1|test980668348/myDatasetType/myFilter/11/myDatasetType_myFilter_11_MyCam_test980668348.fits|spherex.astropy_image.AstropyImageFormatter|MyImage|__NULL_STRING__||51840
#
# run
# collection_id|datetime_begin|datetime_end|host
# 1|||
#
# visit
# instrument|id|physical_filter|visit_system|name|exposure_time|seeing|region|datetime_begin|datetime_end
# MyCam|11|myFilter||11|||||
# MyCam|22|myFilter||22|||||