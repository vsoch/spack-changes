# Source Code

This data extraction will include changes to source code, namely the number
of changed lines and total changes. We will do the extractions easily using
[caliper](https://caliper-python.readthedocs.io/en/latest/getting_started/user-guide.html#metrics-extractor).
We are going to do them for spack as well, since changes to spack might be important
to know.

## Extraction

To do the extraction, you will need to install caliper, version 0.0.23 or greater:

```bash
$ pip install caliper
```

We can run the extraction as follows:

```bash
$ caliper extract github:LLNL/axom
$ caliper extract github:Alpine-DAV/ascent
$ caliper extract github:spack/spack
```

A [requirements.txt](requirements.txt) file is provided to install caliper,
and then [extract.sh](extract.sh) is provided to perform the extraction.
The extract script also has `caliper view` functions to generate a change
plot for each package.

You can [read the documentation](https://caliper-python.readthedocs.io/en/latest/getting_started/user-guide.html#metrics-extractor)
if you want to modify this to be run from within Python.

## Results

You can view results at the following urls:

 - [LLNL/axom](https://vsoch.github.io/spack-changes/data/sourcecode/github/LLNL-axom/)
 - [Alpine-DAV/ascent](https://vsoch.github.io/spack-changes/data/sourcecode/github/Alpine-DAV-ascent/)
 - [spack/spack](https://vsoch.github.io/spack-changes/data/sourcecode/github/spack-spack/)
