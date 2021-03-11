# Spack Spec Changes

For this change analysis, we want to be able to generate concretized specs
for the same packages across versions of spack, and then see how those specs
change over time. This will require installing spack at different versions,
and then concretizing (and saving) the resulting spec.

## Usage

To run the script, you want to provide one or more spack packages as arguments:

```bash
$ python generate_specs.py axom ascent
```

Note that you can also generate a list of packages:

```bash
$ spack list > packages.txt
```

And then provide that file instead:

```bash
$ python generate_specs.py packages.txt
```

You shouldn't worry about re-running - if a package result already exists it
will be skipped. The resulting output will be organized in folders by package name, and for each 
package, a spec file is saved for each version of spack that we were able to
extract for. This means that we aren't going to have it work for the oldest
versions of spack that might use Python 2.x, or if the package of interest 
did not exist for a particular version.

For kicks and giggles, I decided to also parse all packages that were present
in the very first version of spack!

```bash
$ python generate_specs.py zlib vim tmux tau stat spindle scr SAMRAI pmgr_collective parmetis openmpi ncurses mvapich2 mrnet mpileaks mpich libunwind libevent libelf libdwarf launchmon hdf5 graphlib dyninst cmake callpath boost
```

This generated the folder structure that you see here, with yaml for each package.
We next want to try comparing these structures.
