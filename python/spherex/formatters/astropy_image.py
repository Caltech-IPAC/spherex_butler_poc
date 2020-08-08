__all__ = ("AstropyImageFormatter",)

from astropy.io import fits

from typing import (
    Any,
    Optional,
    Type,
)

from lsst.daf.butler.formatters.file import FileFormatter


class AstropyImageFormatter(FileFormatter):
    """Interface for reading and writing astropy image objects to and from FITS files.
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
            data = fits.open(path)
        except FileNotFoundError:
            data = None

        return data

    def _writeFile(self, inMemoryDataset: Any) -> None:
        """Write the in memory dataset to file on disk.

        Parameters
        ----------
        inMemoryDataset : `object`
            Object to serialize.

        Raises
        ------
        Exception
            The file could not be written.
        """
        if not isinstance(inMemoryDataset, fits.HDUList):
            raise NotImplementedError("Unable to write this representation of FITS into a file.")
        inMemoryDataset.writeto(self.fileDescriptor.location.path)

    # todo: do we need to implement _fromBytes, _toBytes, and _coerceType? When are they used?
    # import builtins
    # import pickle
    # if TYPE_CHECKING:
    #     from lsst.daf.butler import StorageClass
    #
    # def _fromBytes(self, serializedDataset: bytes, pytype: Optional[Type[Any]] = None) -> Any:
    #     """Read the bytes object as a python object.
    #
    #     Parameters
    #     ----------
    #     serializedDataset : `bytes`
    #         Bytes object to unserialize.
    #     pytype : `class`, optional
    #         Not used by this implementation.
    #
    #     Returns
    #     -------
    #     inMemoryDataset : `object`
    #         The requested data as a Python object or None if the string could
    #         not be read.
    #     """
    #     try:
    #         data = pickle.loads(serializedDataset)
    #     except pickle.PicklingError:
    #         data = None
    #
    #     return data
    #
    # def _toBytes(self, inMemoryDataset: Any) -> bytes:
    #     """Write the in memory dataset to a bytestring.
    #
    #     Parameters
    #     ----------
    #     inMemoryDataset : `object`
    #         Object to serialize
    #
    #     Returns
    #     -------
    #     serializedDataset : `bytes`
    #         bytes representing the serialized dataset.
    #
    #     Raises
    #     ------
    #     Exception
    #         The object could not be serialized.
    #     """
    #     return pickle.dumps(inMemoryDataset, protocol=-1)
    #
    # def _coerceType(self, inMemoryDataset: Any, storageClass: StorageClass,
    #                 pytype: Optional[Type[Any]] = None) -> Any:
    #     """Coerce the supplied inMemoryDataset to type `pytype`.
    #
    #     Parameters
    #     ----------
    #     inMemoryDataset : `object`
    #         Object to coerce to expected type.
    #     storageClass : `StorageClass`
    #         StorageClass associated with `inMemoryDataset`.
    #     pytype : `type`, optional
    #         Override type to use for conversion.
    #
    #     Returns
    #     -------
    #     inMemoryDataset : `object`
    #         Object of expected type `pytype`.
    #     """
    #     if pytype is not None and not hasattr(builtins, pytype.__name__):
    #         if storageClass.isComposite():
    #             inMemoryDataset = storageClass.assembler().assemble(inMemoryDataset, pytype=pytype)
    #         elif not isinstance(inMemoryDataset, pytype):
    #             # Hope that we can pass the arguments in directly
    #             inMemoryDataset = pytype(inMemoryDataset)
    #     return inMemoryDataset
