# spherex_butler_poc

Proof-of-concept code for using [dax_butler](https://github.com/lsst/daf_butler) – Rubin/LSST Gen3 Butler framework 
for storage, retrieval, and querying of datasets – in SPHEREx pipelines.

### Resources

- [07/2020 Gen3 Middleware Update & Tutorial](https://docs.google.com/presentation/d/1GHAcuulgeLuJUrzDejczYhj2Fx0kBuFhxEf3T97HT80)
- [07/2020 Tutorial notebooks](https://github.com/lsst-dm/dm-demo-notebooks/tree/u/jbosch/desc-2020-07/workshops/desc-2020-07/gen3-butler)
    - https://pipelines.lsst.io/v/weekly/modules/lsst.daf.butler/organizing.html
    - https://pipelines.lsst.io/v/weekly/modules/lsst.daf.butler/queries.html
    - https://pipelines.lsst.io/v/weekly/modules/lsst.daf.butler/dimensions.html

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

- in  container: 
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