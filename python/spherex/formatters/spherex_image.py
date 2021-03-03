__all__ = ["SPHERExImageFormatter"]

from typing import (
    Any,
    Optional,
    Type,
)

from astropy import units as u
from lsst.daf.butler.formatters.file import FileFormatter

from ..core import SPHERExImage, spherex_image_reader, spherex_image_writer


class SPHERExImageFormatter(FileFormatter):
    """Interface for reading and writing astropy
    image objects to and from FITS files.
    """

    extension = ".fits"

    unsupportedParameters = None
    """This formatter does not support any parameters (`frozenset`)"""

    def _readFile(self, path: str, pytype: Optional[Type[Any]] = None) -> Any:
        """Read a file from the path in FITS format.

        Parameters
        ----------
        path : `str`
            Path to use to open JSON format file.
        pytype : `class`, optional
            Not used by this implementation.

        Returns
        -------
        data : `object`
            Either data as Python object read from JSON file, or None
            if the file could not be opened.
        """
        # todo check pytype?
        try:
            data = spherex_image_reader(path, unit=(u.electron / u.s))
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
        if not isinstance(inMemoryDataset, SPHERExImage):
            raise NotImplementedError("Unable to write this representation of FITS into a file.")
        spherex_image_writer(inMemoryDataset, self.fileDescriptor.location.path)
