# spherex_butler_poc

Proof-of-concept code for using [dax_butler](https://github.com/lsst/daf_butler) – Rubin/LSST Gen3 Butler framework 
for storage, retrieval, and querying of datasets – in SPHEREx pipelines.

#### Why using Butler?

LSST Butler is a Python 3 only package, which provides data access framework for LSST Data Management team.
The main function of such a framework is to organize the discrete entities of stored data to facilitate its search and retrieval.

LSST Butler abstracts:
- **where data live on the storage**   
The data can live in a POSIX datastore, on Amazon S3, or elsewhere.
The framework users deal with Python rather than stored representations of data entities.
- **data format and how to deal with it**  
Formatters are used to to move between stored and Python representations of data entities. 
As a result users deal with Python objects, such as astropy Table or CCDData instead of 
the stored formats, such as VOTable, FITS or HDF5.
- **calibrations**   
You ask for a calibration for an image, and it returns you the right file. (Use case: bias reference image - 
it is averaged over a few days. The algorithmic code does not need to be aware of how the bias reference is obtained.)

#### Butler concepts

- **Dataset** is a discrete entity of stored data, uniquely identified by a _Collection_ and _DatasetRef_.  
- **Collection** is an entity that contains _Datasets_.  
- **DatasetRef** is an identifier for a _Dataset_.  
- **Registry** is a database that holds metadata and provenance for _Datasets_.  
- **Dimension** is a concept used to organize and label _Datasets_. _Dimension_ is analogous to a coordinate axis 
in coordinate space. _Dataset_ can be viewed as a point in this space with the position is defined by 
_DataCoordinate_ or _data id_. For example, SPHEREx raw image might be identified by the observation 
(pointing of the telescope at a particular time) and the detector array that took this image. For this reason, 
_observation_ and and _detector_ might be good _Dimensions_ to describe raw image _Datasets_. 
- **DatasetType** is a named category of _Datasets_ (ex. raw image)  
Together, _DatasetType_ and _DataCoordinate_ 
make a unique _Dataset_ identifier, see [DatasetRef](https://pipelines.lsst.io/v/weekly/py-api/lsst.daf.butler.DatasetRef.html#lsst.daf.butler.DatasetRef).   

#### Resources

- [07/2020 Gen3 Middleware Update & Tutorial](https://docs.google.com/presentation/d/1GHAcuulgeLuJUrzDejczYhj2Fx0kBuFhxEf3T97HT80)
- [07/2020 Tutorial notebooks](https://github.com/lsst-dm/dm-demo-notebooks/tree/u/jbosch/desc-2020-07/workshops/desc-2020-07/gen3-butler)
    - https://pipelines.lsst.io/v/weekly/modules/lsst.daf.butler/organizing.html
    - https://pipelines.lsst.io/v/weekly/modules/lsst.daf.butler/queries.html
    - https://pipelines.lsst.io/v/weekly/modules/lsst.daf.butler/dimensions.html

#### Proof-of-concept directions

- Custom python representations of stored _Datasets_  
Verified that we can create a custom _Formatter_, that maps stored representation of a particular dataset type 
into its Python representation. (Using `butler.put()` to store Python object into file system datastore and 
`butler.get()` to retrieve Python object from the stored file.)
- Custom set of _Dimensions_  
Verified that we can organize our _Datasets_ around custom set of _Dimensions_, see Caveats below.
- File ingest (using `butler.ingest()`)   
Butler allows to configure file templates (`datastore.templates`), which allows to use _Collection_ name,
_DatasetType_, and any of the field in _Dimensions_ tables to create directory structure and file name 
of _Dataset_ stored representation.  
Verified that the data can be ingested into datastore according to the defined template and 
the transfer type (ex. copy, symlink).

Proof-of-concept is designed around Python unit tests that run in a container
on GitHub-hosted machines as a part of GitHub's built-in continuous integration service,
see `.github/workflows/unit_test.yaml`

#### Caveats

Butler allows to override parts of its configuration. The overwritten configuration is merged 
with the default configuration. However, as of August 2020, there is no option in Butler to override the default dimensions.yaml
For the proof-of-concept purposes, we just replace `daf_butler/python/lsst/daf/butler/configs/dimensions.yaml`
with `sperex_butler_poc/python/spherex/configs/dimensions.yaml`

Other known issues:
- Butler relies on `lsst.sphgeom` lower level C++ library, which does not support HEALPix pixelization at the moment



### Testing Gen3 Butler

#### Running daf_butler tests

- lsst_scipipe conda environment:
```
> git clone https://github.com/lsst/scipipe_conda_env.git
> cd scipipe_conda_env/etc
> conda create --name lsst_scipipe --file conda-osx-64.lock
> conda activate lsst_scipipe
> conda install ipykernel (to be able to use lsst_scipipe in jupyter lab running in another environment)
```

- source code repos:
```
> git clone https://github.com/lsst/daf_butler
> git clone https://github.com/lsst/obs_base
```

- setup for running butler tests:
```
> pip install -r https://raw.githubusercontent.com/lsst/sphgeom/master/requirements.txt
> pip install pytest-xdist pytest-openfiles
> cd daf_butler
> pip install -r requirements.txt
> pip install -v .
```
(the info about pip packages installed in `lsst_scipipe` conda environment can be found in `<CONDA_ROOT_DIR>/envs/lsst_scipipe/lib/python3.7/site-packages`)

- run butler tests:
```
> pytest -r a -v -n 3 --open-files
```

#### Testing in a container (using weekly image):

- make sure you have test data (Git LFS repo) and test scripts:
```
> git clone https://github.com/lsst/testdata_ci_hsc
> git clone https://github.com/lsst/ci_hsc_gen3
```

- start up container:
```
> docker run -it -v `pwd`:/home/lsst/mnt docker.io/lsstsqre/centos:7-stack-lsst_distrib-w_latest
```

- in container: 
```
$ source /opt/lsst/software/stack/loadLSST.bash
$ setup lsst_distrib
$ cd /home/lsst/mnt
$ setup -j -r testdata_ci_hsc
$ setup -j -r ci_hsc_gen3
$ echo $TESTDATA_CI_HSC_DIR; echo $CI_HSC_GEN3_DIR
$ cd ci_hsc_gen3/$ scons
$ sqlite3_analyzer /home/lsst/mnt/ci_hsc_gen3/DATA/gen3.sqlite3  
```