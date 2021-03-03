__all__ = ["CCDDataFormatter"]

from astropy import units as u
from astropy.nddata import CCDData, fits_ccddata_reader, fits_ccddata_writer

from typing import (
    Any,
    Optional,
    Type,
)

from lsst.daf.butler.formatters.file import FileFormatter


class CCDDataFormatter(FileFormatter):
    """Interface for reading and writing astropy
    image objects to and from FITS files.
    """

    extension = ".fits"

    unsupportedParameters = None
    """This formatter does not support any parameters (`frozenset`)"""

    def _readFile(self, path: str, pytype: Optional[Type[Any]] = None) -> Any:
        """Read a file from the path in multi-extension FITS format into CCDData.

        Parameters
        ----------
        path : `str`
            Path to use to open JSON format file.
        pytype : `class`, optional
            Not used by this implementation.

        Returns
        -------
        data : `~astropy.nddata.CCDData`
            Either data as Python object or None
            if the file could not be opened.
        """
        # todo check pytype?
        try:
            data = fits_ccddata_reader(path, unit=(u.electron/u.s))
        except FileNotFoundError:
            data = None

        return data

    def _writeFile(self, inMemoryDataset: Any) -> None:
        """Write in memory dataset to file on disk.

        Parameters
        ----------
        inMemoryDataset : `object`
            Object to serialize.

        Raises
        ------
        Exception
            The file could not be written.
        """
        if not isinstance(inMemoryDataset, CCDData):
            raise NotImplementedError("Unable to write this representation of FITS into a file.")
        fits_ccddata_writer(inMemoryDataset, self.fileDescriptor.location.path)
