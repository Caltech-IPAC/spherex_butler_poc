import os
import logging
import shutil
import tempfile
import unittest

import lsst.utils.tests
from lsst.daf.butler import Butler, ButlerURI, Config, DatasetRef, FileDataset, StorageClassFactory, Timespan
from lsst.daf.butler.tests import DatasetTestHelper, makeTestRepo, addDatasetType

from astropy.io import fits
from astropy.nddata import CCDData
from spherex.core import SPHERExImage

from spherex.formatters import AstropyImageFormatter, CCDDataFormatter, SPHERExImageFormatter

TESTDIR = os.path.dirname(__file__)

log = logging.getLogger(__name__)


def read_astropy_image(fitsPath: str) -> fits.hdu.HDUList:
    return fits.open(fitsPath)


def read_ccddata(fitsPath: str) -> CCDData:
    # unit must be specified
    return CCDData.read(fitsPath, unit="adu")


def read_spherex_image(fitsPath: str) -> SPHERExImage:
    # unit must be specified
    return SPHERExImage.read(fitsPath, unit="adu")


FORMATTERS = [
    {"formatter_cls": SPHERExImageFormatter,
     "dataset_type": "spherex_image",
     "storage_class": "SPHERExImage",
     "inmem_cls": SPHERExImage,
     "reader": read_spherex_image
     },
    {"formatter_cls": CCDDataFormatter,
     "dataset_type": "ccddata_image",
     "storage_class": "CCDData",
     "inmem_cls": CCDData,
     "reader": read_ccddata
     },
    {"formatter_cls": AstropyImageFormatter,
     "dataset_type": "astropy_image",
     "storage_class": "MyImage",
     "inmem_cls": fits.hdu.HDUList,
     "reader": read_astropy_image
     }
]

INSTRUMENT_NAME = "MyCam"


class FormattersTests(DatasetTestHelper, lsst.utils.tests.TestCase):
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

        configURI = ButlerURI("resource://spherex/configs", forceDirectory=True)
        butlerConfig = Config(configURI.join("butler.yaml"))
        # in-memory db is being phased out
        # butlerConfig["registry", "db"] = 'sqlite:///:memory:'
        cls.creatorButler = makeTestRepo(cls.root, data_ids, config=butlerConfig,
                                         dimensionConfig=configURI.join("dimensions.yaml"))
        for formatter in FORMATTERS:
            datasetTypeName, storageClassName = (formatter["dataset_type"], formatter["storage_class"])
            storageClass = cls.storageClassFactory.getStorageClass(storageClassName)
            addDatasetType(cls.creatorButler, datasetTypeName, set(data_ids), storageClass)

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
        dataid = {"exposure": 11, "detector": 0, "instrument": INSTRUMENT_NAME}
        for formatter in FORMATTERS:
            # in-memory object, representing fits
            inmemobj = formatter["reader"](fitsPath)

            # save in-memory object into butler dataset
            datasetTypeName = formatter["dataset_type"]
            self.butler.put(inmemobj, datasetTypeName, dataid)

            # get butler dataset
            retrievedobj = self.butler.get(datasetTypeName, dataid)
            self.assertTrue(isinstance(retrievedobj, formatter["inmem_cls"]))
            self.assertTrue(retrievedobj.__class__.__name__, inmemobj.__class__.__name__)

    def test_ingest(self):

        fitsPath = os.path.join(TESTDIR, "data", "small.fits")

        formatter = FORMATTERS[0]
        datasetTypeName, formatterCls = (formatter["dataset_type"], formatter["formatter_cls"])

        datasetType = self.butler.registry.getDatasetType(datasetTypeName)
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
                datasets.append(FileDataset(refs=ref, path=fitsPath, formatter=formatterCls))

        # register new collection
        # run = "rawIngestedRun"
        # self.butler.registry.registerCollection(run, type=CollectionType.RUN)

        # collection is registered as a part of setUp
        run = self.collection

        with self.butler.transaction():
            for exposure in range(3, 5):
                expid = exposure*11
                self.butler.registry.insertDimensionData("exposure",
                                                         {"instrument": INSTRUMENT_NAME,
                                                          "id": expid,
                                                          "name": f"{expid}",
                                                          "group_name": "day1",
                                                          "timespan": Timespan(begin=None, end=None)})
            # transfer can be 'auto', 'move', 'copy', 'hardlink', 'relsymlink'
            # or 'symlink'
            self.butler.ingest(*datasets, transfer="symlink", run=run)

        # verify that 12 files were ingested (2 exposures for each detector)
        refsSet = set(self.butler.registry.queryDatasets(datasetTypeName, collections=[run]))
        self.assertEqual(len(refsSet), 12, f"Collection {run} should have 12 elements after ingest")

        # verify that data id is present
        dataid = {"exposure": 44, "detector": 5, "instrument": INSTRUMENT_NAME}
        refsList = list(self.butler.registry.queryDatasets(datasetTypeName,
                                                           collections=[run],
                                                           dataId=dataid))
        self.assertEqual(len(refsList), 1, f"Collection {run} should have 1 element with {dataid}")

        # get the python representation of data id
        # self.butler.get(DATASET_TYPE_NAME, dataid, collections=[run])


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
