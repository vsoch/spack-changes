# Spack Changes

> How do we represent a change set in spack?

We want to develop a metric for change, or more specifically, a way to model change
for a spack package. I should be able to understand:

 - differences in specs themselves
 - differences in build environments
 - differences in source code of packages
 - abi differences

## Goals

We would want to be able to:

1. measure stability of a spack configuration. E.g., if center A is running configuration CA, and center B is running configuration CB, which one is more stable over time, meaning the changes in packages (specs) are fewer?
2. understand how concretization changes over time with respect to spack versions.
3. Be able to associated some level or kind of difference/change to builds failing.

## Measuring 

Each of these changes can be measured in different ways:

### Differences in Specs

If we convert a spec into a set of facts, we could diff them to see differences. We'd need a way to turn that into a metric (likely we would have a set of packages in one spec and not the other, one for each spec, a set of packages that overlap with exact versions, and a set of packages that overlap with different versions. In the case of a different version, we'd need to have a metric that says "a change from 1.0.0 to 2.0.0 is larger than a change from 0.1.0 to 0.2.0. This assumes that packages use semver.

### Differences in Build Environments

Current spack doesn't include the build environment in the metadata folder, but if/when we add
this, it should be fairly easy to compare these.

### Differences in Source Code

If each package is assocaited with a git repository (at least to start we will
focus on git packages) we can easily use a tool like [caliper](https://github.com/vsoch/caliper)
to extract changes and generate a plot. This would mean the number of changes
per release version of the package.

## Packages

We will start out with two packages, [axom](https://github.com/LLNL/axom) and [ascent](https://github.com/Alpine-DAV/ascent).


## Organization

The raw data will be organized in [data](data), and in subfolders by the type.

 - [sourcecode](data/sourcecode): will use caliper to assess high level changes in the code base.
 - [specs](data/specs): We want to look at changes in spack specs, over time.
