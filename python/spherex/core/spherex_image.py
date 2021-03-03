# SPHEREx Image will be stored in a FITS file with
#    header-only primary hdu (to allow compressed images)
# and the following extensions:
#    image extension
#    flags extension
#    variance extension

__all__ = ['SPHERExImage', 'spherex_image_reader', 'spherex_image_writer']

from astropy.io import fits, registry
from astropy.nddata import CCDData, fits_ccddata_reader, FlagCollection

FLAG_DEFS = {
    'NONFUNC': 2,
    'COSMICRAY': 1,
    'SATURATED': 0,
    'HOT': 3,
    'OUTLIER': 4,
    'DARKREF': 5,
    'PERSISTENT': 6
}


class SPHERExImage(CCDData):
    """Container class for SPHEREx image components

    It contains SPHEREx image components, such as ccd data, flags, etc.
    and provides support for reading and writing SPHERExImage from/to FITS.

    Parameters
    ----------
    data : `~astropy.nddata.NDData`-like or `numpy.ndarray`-like
        CCD data contained in this object.
        Note that the data will always be saved by *reference*, so you should
        make a copy of the ``data`` before passing it in if that's the desired
        behavior.

    flags : `numpy.ndarray` or None, optional
        Flags giving information about each pixel. These can be specified
        as a Numpy array of any type with a shape matching that of the
        data.
        Default is ``None``.

    flag_defs " dict-like object or None, optional
        Flag definitions, which map flag name to a bit in the flags array.

    wcs : `~astropy.wcs.WCS` or None, optional
        WCS-object containing the world coordinate system for the data.
        Default is ``None``.

    meta : dict-like object or None, optional
        Metadata for this object. "Metadata" here means all information that
        is included with this object but not part of any other attribute
        of this particular object, e.g. creation date, unique identifier,
        simulation parameters, exposure time, telescope name, etc.

    unit : `~astropy.units.Unit` or str, optional
        The units of the data.
        Default is ``None``.

        .. warning::

            If the unit is ``None`` or not otherwise specified it will raise a
            ``ValueError``

    Methods
    -------
    read(\\*args, \\**kwargs)
        ``Classmethod`` to create an SPHERExImage instance based on a ``FITS`` file.
        This method uses :func:`spherex_fits_reader` with the provided
        parameters.
    write(\\*args, \\**kwargs)
        Writes the contents of the SPHERExImage instance into a new ``FITS`` file.
        This method uses :func:`spherex_fits_writer` with the provided
        parameters.
    """

    def __init__(self, *args, **kwargs):
        if 'flags' in kwargs and isinstance(kwargs['flags'], FlagCollection):
            raise NotImplementedError('Flag collection is not supported')
        if 'flag_defs' in kwargs:
            self._flag_defs = kwargs.pop('flag_defs')
        super().__init__(*args, **kwargs)

    @property
    def flag_defs(self):
        return self._flag_defs

    @flag_defs.setter
    def flag_defs(self, value):
        self._flag_defs = value


def _get_flag_defs(header: fits.Header):
    """Get flag definition dictionary from the the header

    Parameters
    ----------
    header : dict-like object

    Returns
    -------
    flag_defs : dict-like object

    """
    flag_defs = {}
    for key, val in header.items():
        if key.startswith('MP_'):
            try:
                intval = int(val)
                if intval > 31:
                    raise ValueError(f'bit value {intval} for flag {key}'
                                     ' is too large')
                flagkey = key[3:]
                flag_defs[flagkey] = intval
            except ValueError:
                pass
    if len(flag_defs) > 0:
        return flag_defs


def _add_flag_defs(spherex_image: SPHERExImage, header: fits.Header) -> None:
    """Add image flag definitions to the header

    Parameters
    ----------
    spherex_image : `~spherex.data.SPHERExImage`
    header : dict-like object

    """

    # check for None or empty dictionary
    if not spherex_image.flag_defs:
        return

    # convention understood by Firefly:
    # EXTTYPE=MASK and flag bit values in keywords starting with "MP_"
    header['EXTTYPE'] = 'MASK'
    for key, val in spherex_image.flag_defs.items():
        prefix = 'MP_' if len(key) < 6 else 'HIERARCH MP_'
        header[f'{prefix}{key.upper()}'] = val


def spherex_image_reader(filename, hdu=0, unit=None, hdu_uncertainty=3,
                         hdu_mask='MASK', hdu_flags=2,
                         key_uncertainty_type='UTYPE', **kwd) -> SPHERExImage:
    """
    Generate a SPHERExImage object from a FITS file.
    When flags and variance are present, they are expected to be in
    the second and the third extensions.

    Parameters
    ----------
    filename : str
        Name of fits file.

    hdu : str or int, optional
        FITS extension from which the data should be initialized. If zero and
        and no data in the primary extension, it will search for the first
        extension with data. The header will be added to the primary header.
        Default is ``0``.

    unit : `~astropy.units.Unit`, optional
        Units of the image data. If this argument is provided and there is a
        unit for the image in the FITS header (the keyword ``BUNIT`` is used
        as the unit, if present), this argument is used for the unit.
        Default is ``None``.

    hdu_uncertainty : str or int or None, optional
        FITS extension from which the uncertainty should be initialized. If the
        extension does not exist the uncertainty of the SPHERExImage is ``None``.
        Default is ``3``.

    hdu_mask : str or int or None, optional
        FITS extension from which the mask should be initialized. If the
        extension does not exist the mask of the SPHERExImage is ``None``.
        Default is ``'MASK'``.

    hdu_flags : str or int or None, optional
        FITS extension from which the flags should be initialized. If the
        extension does not exist the flags of the SPHERExImage is ``None``.
        Default is ``2``.

    key_uncertainty_type : str, optional
        The header key name where the class name of the uncertainty  is stored
        in the hdu of the uncertainty (if any).
        Default is ``'UTYPE'``.

    kwd :
        Any additional keyword parameters are passed through to the FITS reader
        in :mod:`astropy.io.fits`; see Notes for additional discussion.

    Returns
    -------
    spherex_image : `~spherex.data.SPHERExImage`

    Notes
    -----
    FITS files that contained scaled data (e.g. unsigned integer images) will
    be scaled and the keywords used to manage scaled data in
    :mod:`astropy.io.fits` are disabled.
    """

    ccddata = fits_ccddata_reader(filename, hdu=hdu, unit=unit,
                                  hdu_uncertainty=hdu_uncertainty,
                                  hdu_mask=hdu_mask,
                                  key_uncertainty_type=key_uncertainty_type, **kwd)

    flags = None
    flag_defs = None
    with fits.open(filename, **kwd) as hdus:
        if hdu_flags is not None and hdu_flags in hdus:
            flags_hdu = hdus[hdu_flags]
            flags = flags_hdu.data
            hdr = hdus[hdu_flags].header
            flag_defs = _get_flag_defs(hdr)

        spherex_image = SPHERExImage(ccddata.data, meta=ccddata.header,
                                     unit=ccddata.unit, mask=ccddata.mask,
                                     uncertainty=ccddata.uncertainty,
                                     wcs=ccddata.wcs, flags=flags,
                                     flag_defs=flag_defs)
    return spherex_image


def spherex_image_writer(spherex_image: SPHERExImage, fileobj, hdu_mask='MASK', hdu_uncertainty='VARIANCE',
                         hdu_flags='FLAGS', wcs_relax=True, key_uncertainty_type='UTYPE', **kwd):
    """Write `~spherex.core.SPHERExImage` to a file

    Parameters
    ----------
    spherex_image : `~spherex.core.SPHERExImage`

    fileobj : file-like object or filename

    hdu_mask, hdu_uncertainty, hdu_flags : str or None, optional
        If it is a string append this attribute to the HDUList as
        `~astropy.io.fits.ImageHDU` with the string as extension name.
        Default is ``'MASK'`` for mask, ``'VARIANCE'`` for uncertainty and
        ``'FLAGS'`` for flags

    wcs_relax : bool
        Value of the ``relax`` parameter to use in converting the WCS to a
        FITS header using `~astropy.wcs.WCS.to_header`. The common
        ``CTYPE`` ``RA---TAN-SIP`` and ``DEC--TAN-SIP`` requires
        ``relax=True`` for the ``-SIP`` part of the ``CTYPE`` to be
        preserved.

    key_uncertainty_type : str, optional
        The header key name for the class name of the uncertainty (if any)
        that is used to store the uncertainty type in the uncertainty hdu.
        Default is ``'UTYPE'``.

    kwd : dict

    Returns
    -------

    """

    # to_hdu does not support flags at the moment
    # to_hdu puts image data into PrimaryHDU
    hdulist = spherex_image.to_hdu(hdu_mask=hdu_mask, hdu_uncertainty=hdu_uncertainty,
                                   wcs_relax=wcs_relax, key_uncertainty_type=key_uncertainty_type)

    # add primary hdu - critical to support compressed images later
    # minimum header with EXTEND will be provided if header is None
    primary_hdu = fits.PrimaryHDU(data=None, header=None)
    hdulist.insert(0, primary_hdu)

    # add flags hdu - 2nd extension after the image data
    if hdu_flags and spherex_image.flags is not None:
        hdr_flags = fits.Header()
        _add_flag_defs(spherex_image, hdr_flags)

        hdu = fits.ImageHDU(spherex_image.flags.data, hdr_flags, name=hdu_flags)
        hdulist.insert(2, hdu)

    hdulist.writeto(fileobj, **kwd)


# Register read/write methods for SPHERExImage
with registry.delay_doc_updates(SPHERExImage):
    registry.register_reader(data_format='fits', data_class=SPHERExImage, function=spherex_image_reader)
    registry.register_writer(data_format='fits', data_class=SPHERExImage, function=spherex_image_writer)
    registry.register_identifier(data_format='fits', data_class=SPHERExImage, identifier=fits.connect.is_fits)
