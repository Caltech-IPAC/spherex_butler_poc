# spherex_butler_poc

Proof-of-concept code for using [dax_butler](https://github.com/lsst/daf_butler) – Rubin/LSST Gen3 Butler and 
PipelineTask framework in SPHEREx pipelines.

_Butler_ organizes _datasets_ (units of stored data) in data repositories, identifying them by a combination of 
_dataset type_, _data id_, and _collection_. It encapsulates all I/O done by pipeline code. 

_PipelineTask_ is a framework for writing and packaging algorithmic code that enables generating a pipeline execution 
plan, in the form of a directed acyclic graph (DAG). PipelineTask is built on top of Butler.


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

- [10/2020 Gen3 Middleware Tutorial](https://github.com/lsst-dm/obs-bootcamp-2020-bosch-tutorial/)
- [07/2020 Gen3 Middleware Tutorial](https://github.com/lsst-dm/dm-demo-notebooks/tree/u/jbosch/desc-2020-07/workshops/desc-2020-07/gen3-butler)
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
- Custom butler command   
It is possible to use butler framework to create butler [subcommands](https://pipelines.lsst.io/v/weekly/modules/lsst.daf.butler/writing-subcommands.html#adding-butler-subcommands). 
Verified this capability by adding `ingest-simulated` subcommand.
- Simple task and example pipeline  
Created SubtractTask pipeline task, which accepts two images and subtracts the second from the first.
Created an example pipeline that runs this task, see `pipelines/ExamplePipeline.yaml`.

Proof-of-concept is designed around Python unit tests that run in a container
on GitHub-hosted machines as a part of GitHub's built-in continuous integration service,
see `.github/workflows/unit_test.yaml`  
Unfortunately, pipeline tasks can not be validated with GitHub actions, because they rely on
[pipe_base](https://github.com/lsst/pipe_base) and [ctrl_mpexec](https://github.com/lsst/ctrl_mpexec) packages with 
deeper rooted dependencies. Running example pipeline requires installing Rubin/LSST environment, where packages 
are managed with [EUPS](https://developer.lsst.io/stack/eups-tutorial.html).

Dependency management is one of the main concerns when using Rubin/LSST pipeline framework.

#### Caveats

Butler allows to override parts of its configuration. The overwritten configuration is merged 
with the default configuration. As of November 2020, it's possible to completely overrode dimensions, 
but not possible to completely replace formatters and storage classes.

There is an implied requirement in `ctrl_mpexec` package that `instrument` dimension table must have 
a reference to instrument class. 

Other known issues:
- Butler relies on `lsst.sphgeom` lower level C++ library, which does not support HEALPix pixelization at the moment


### Testing Gen3 Butler and Pipeline Task framework

#### Testing locally

##### Install latest weekly

To install the latest pipeline distribution `lsst_distrib` built by Rubin/LSST project, follow [newinstall](https://pipelines.lsst.io/install/newinstall.html#run-newinstall-sh) recipe:

```
# from an empty directory - 
curl -OL https://raw.githubusercontent.com/lsst/lsst/master/scripts/newinstall.sh
# continue a previous failed install, if any, in batch mode, and prefer tarballs
bash newinstall.sh -cbt 
source loadLSST.bash
# install weekly 46 for 2020
eups distrib install -t w_2020_46 lsst_distrib  
# fix shebangs - tarballs have shebangs encoded at build time that need to be fixed at install time
curl -sSL https://raw.githubusercontent.com/lsst/shebangtron/master/shebangtron | python
# use with tag option if other versions installed: setup -t w_2020_46 lsst_distrib
setup lsst_distrib
```
[What newinstall does](https://pipelines.lsst.io/install/newinstall.html#newinstall-background)

You only need to do newinstall when conda base environment changes.
Check the last modified date of [conda-system](https://eups.lsst.codes/stack/osx/10.9/conda-system/).

If newest weekly is installed without running newinstall.sh, the previous versions can be removed
with [this script](https://github.com/lsst/lsstsw/blob/u/jbosch/bin/pruneTags). The script will remove 
all packages except locally set up and those with the given tag. Use `--dry-run`
option to avoid surprises:
```
pruneTags w_2020_44 --delete-untagged --dry-run
```

##### Running example pipeline

To run the example pipeline defined in these repository follow these steps:

- Install the latest `lsst_distrib` (see above)

- Set up spherex_butler_poc repository with EUPS package manager:
```
git checkout https://github.com/Caltech-IPAC/spherex_butler_poc.git
cd spherex_butler_poc
# set up the package in the eups stack
setup -r . -t $USER
# review set up packages (optional)
eups list -s
```
- Create a directory where the buttler repository will live:
```
mkdir ../test_spherex
cd ../test_spherex
```
- Run SPHEREx simulator to produce simulated files. 
The simulated files have exposure and detector id embedded in the file names.

- Create empty butler repository (DATA):
```
butler create --override --seed-config ../spherex_butler_poc/python/spherex/configs/butler.yaml --dimension-config ../spherex_butler_poc/python/spherex/configs/dimensions.yaml DATA
```
- Ingest simulated images:
```
butler ingest-simulated DATA /<abspath>/simulator_files
```
- Ingest simulated dark current images (the group is set to the ingest date, hence ingesting raw and dark images should be done on the same date):
```
butler ingest-simulated --regex dark_current.fits --ingest-type dark DATA /<abspath>/simulator_files
```
- Examine butler database
```
sqlite3 DATA/spherex.sqlite3
> .header on
> .tables
> select * from file_datastore_records;
> .exit
```
- Create pipeline execution plan as a qgraph.dot file
```
pipetask qgraph -p ../spherex_butler_poc/pipelines/ExamplePipeline.yaml --qgraph-dot qgraph.dot -b DATA -i rawexpr,darkr -o subtractr
```
- Convert `qgraph.dot` into `pdf` (`graphvis` required):
```
dot -Tpdf qgraph.dot -o qgraph.pdf
```
- Run example pipeline:
```
pipetask run -p ../spherex_butler_poc/pipelines/ExamplePipeline.yaml -b DATA --register-dataset-types -i rawexpr,darkr -o subtractr
```
- Optionally: rerun replacing (`--replace-run`) and removing (`--prune-replaced=purge`) the previous run:
```
pipetask run -p ../spherex_butler_poc/pipelines/ExamplePipeline.yaml -b DATA -o subtractr --replace-run --prune-replaced=purge
```
- Examine butler repository in `DATA` directory

- Explore the contents of butler repository using command line tools:
```
> butler query-collections DATA
> butler query-collections DATA --collection-type CHAINED
> butler query-collections DATA --flatten-chains subtractr
```

### Testing in a container (using weekly image):

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
