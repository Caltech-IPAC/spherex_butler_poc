import os
import shutil
import tempfile
import unittest

from astropy import units as u
from astropy.io import fits
from astropy.nddata import CCDData
from spherex.core import SPHERExImage, spherex_image_reader, spherex_image_writer

TESTDIR = os.path.dirname(__file__)


class TestSPHERExImage(unittest.TestCase):
    root = None

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(dir=TESTDIR)

    @classmethod
    def tearDownClass(cls):
        if cls.root is not None:
            shutil.rmtree(cls.root, ignore_errors=True)

    def test_read_write(self):
        file_path = os.path.join(TESTDIR, "data", "small.fits")

        # read multi-extension FITS file with
        # data in the first extension
        # flags - in the second
        # uncertainty - in the third
        spherex_image = spherex_image_reader(file_path, unit=(u.electron/u.s),
                                             hdu_uncertainty=3,
                                             hdu_flags=2)

        self.assertTrue(isinstance(spherex_image, SPHERExImage))
        self.assertTrue(isinstance(spherex_image, CCDData))
        self.assertTrue(spherex_image.data is not None)
        self.assertTrue(spherex_image.flags is not None)
        self.assertEqual(len(spherex_image.flag_defs), 9)

        # convert SPHEREx image object into multi-extension FITS file
        out_path = os.path.join(self.root, "small.fits")
        spherex_image_writer(spherex_image, out_path, hdu_uncertainty='VARIANCE',
                             hdu_flags='FLAGS', wcs_relax=True, key_uncertainty_type='UTYPE')

        with fits.open(out_path) as hdulist:
            # Primary extension - header only
            # first extension - data
            # second extension - variance
            # third extension - flags
            self.assertEqual(len(hdulist), 4)


if __name__ == '__main__':
    unittest.main()
