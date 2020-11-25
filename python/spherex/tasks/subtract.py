from astropy.io import fits

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT


class SubtractTaskConnections(pipeBase.PipelineTaskConnections,
                              dimensions={"instrument", "exposure", "detector"},
                              defaultTemplates={}):
    inputImage = cT.Input(
        name="rawexp",
        doc="Input image.",
        storageClass="SPHERExImage",
        dimensions=["instrument", "exposure", "detector"],
    )
    subtractImage = cT.Input(
        name="dark",
        doc="Image that will be subtracted from the input image.",
        storageClass="SPHERExImage",
        dimensions=["instrument", "exposure", "detector"],
    )
    outputImage = cT.Output(
        name='postDark',
        doc="Output image after subtraction.",
        storageClass="SPHERExImage",
        dimensions=["instrument", "exposure", "detector"],
    )

    def __init__(self, *, config=None):
        super().__init__(config=config)
        # if config.inputDatasetType is not None:
        #     self.inputImage["name"] = config.inputDatasetType
        # if config.subtractDatasetType is not None:
        #     self.subtractImage["name"] = config.subtractDatasetType
        # if config.outputDatasetType is not None:
        #     self.outputImage["name"] = config.outputDatasetType


class SubtractTaskConfig(pipeBase.PipelineTaskConfig,
                         pipelineConnections=SubtractTaskConnections):
    """Configuration parameters for SubtractDark

    """
    inputDatasetType = pexConfig.Field(
        dtype=str,
        doc="Dataset type for input image",
        default="rawexp",
    )
    subtractDatasetType = pexConfig.Field(
        dtype=str,
        doc="Dataset type for image to be subtracted",
        default="dark",
    )
    outputDatasetType = pexConfig.Field(
        dtype=str,
        doc="Dataset type for output image",
        default="postDark",
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

        # basic validation
        if inputImage[0].data.shape != subtractImage[0].data.shape:
            raise RuntimeError("input and subtract image shapes do not match")

        hdu = inputImage[0].copy()
        hdu.data = inputImage[0].data - subtractImage[0].data
        itype = self.config.inputDatasetType
        otype = self.config.subtractDatasetType
        hdu.header.add_comment(f"{itype} with subtracted {otype}")
        outputImage = fits.HDUList()
        outputImage.append(hdu)

        return pipeBase.Struct(
            outputImage=outputImage
        )
