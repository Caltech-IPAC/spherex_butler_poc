from astropy.io import fits

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT


class SubtractTaskConnections(pipeBase.PipelineTaskConnections,
                              dimensions={"instrument", "exposure", "detector"},
                              defaultTemplates={}):
    inputImage = cT.Input(
        name="intype",  # default dataset type for input image
        doc="Input image.",
        storageClass="SPHERExImage",
        dimensions=["instrument", "exposure", "detector"],
    )
    subtractImage = cT.Input(
        name="subtracttype",  # default dataset type for subtract image
        doc="Image that will be subtracted from the input image.",
        storageClass="SPHERExImage",
        dimensions=["instrument", "exposure", "detector"],
    )
    outputImage = cT.Output(
        name='postsubtracttype',  # default dataset type for output image
        doc="Output image after subtraction.",
        storageClass="SPHERExImage",
        dimensions=["instrument", "exposure", "detector"],
    )

    def __init__(self, *, config=None):
        super().__init__(config=config)


class SubtractTaskConfig(pipeBase.PipelineTaskConfig,
                         pipelineConnections=SubtractTaskConnections):
    """Configuration parameters for SubtractDark

    """
    inputHDUNum = pexConfig.Field(
        dtype=int,
        doc="HDU number for input image",
        default=0,
    )
    subtractHDUNum = pexConfig.Field(
        dtype=int,
        doc="HDU number for image to be subtracted",
        default=0,
    )


class SubtractTask(pipeBase.PipelineTask):
    """Subtract images

    """
    ConfigClass = SubtractTaskConfig
    _DefaultName = "subtract"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, inputImage, subtractImage):
        """Subtract image pixels

        Parameters
        ----------
        inputImage : `astropy.io.fits.HDUList`
            Input image
        subtractImage : `astropy.io.fits.HDUList`
            Image to be subtracted

        Returns
        -------
        result : `lsst.pipe.base.Struct`
            Result struct with component:
            - ``outputImage`` : `astropy.io.fits.HDUList`
                Image after subtraction.
        """

        inputHDUIdx = self.config.inputHDUNum
        subtractHDUIdx = self.config.subtractHDUNum

        # basic validation
        if inputImage[inputHDUIdx].data.shape != subtractImage[subtractHDUIdx].data.shape:
            raise RuntimeError("input and subtract image shapes do not match")

        hdu = inputImage[inputHDUIdx].copy()
        hdu.data = inputImage[inputHDUIdx].data - subtractImage[subtractHDUIdx].data
        hdu.header.add_comment("Dark current subtracted")
        outputImage = fits.HDUList()
        outputImage.append(hdu)

        return pipeBase.Struct(
            outputImage=outputImage
        )
