# Spack Spec Changes

For this change analysis, we want to be able to generate concretized specs
for the same packages across versions of spack, and then see how those specs
change over time. This will require installing spack at different versions,
and then concretizing (and saving) the resulting spec. You can see a list of early
results [here](https://vsoch.github.io/spack-changes/data/specs/). 

## What to think about

The results let you explore each package based on a similarity matrix of differences
(across different metrics) along with a side by side comparison of a single package,
and different features like versions or nodes. As you do this, keep in mind:

- You should take notice of what you *don't* see - if a package doesn't have output for a version, this can mean a few things:
  - 1. Running `spack spec <package>` for that version of spack was not successful. 
  - 2. Since we are running with Python 3, the version of Spack had Python 2.x code and it dind't work.
  - 3. The package was not added to spack at the time.


## Usage

### 1. Generate Specs

To run the script, you want to provide one or more spack packages as arguments:

```bash
$ python generate_specs.py axom ascent
```

This will write output to [packages](packages). Note that you can also generate a list of packages:

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

### 2. Calculate Diffs

Next, we can use the script [calculate_diffs.py](calculate_diffs.py) to generate
a similarity score between specs. Spack python needs to be on your path - we are
setting this up to use the asp solver to generate diffs (although it doesn't work yet
because it's trying to validate them). We can provide one or more package folders to calculate:

```bash
$ export PATH=/path/to/spack/bin:$PATH
$ spack python calculate_diff.py packages/ascent
```

The algorithms to discuss data structures (separate from the solver diff approach)
are discussed next. We will be running this more at scale in the following sections,
but before that, let's discuss the comparison metrics.

### Level 1 Comparison: List of Packages

The simplest comparison we can do (a baseline) is to compare the list of packages
in a spec, verbatim. Given spec A and spec B, each with a set of packages and versions,
we can say:

```
sim(A, B) = intersection of common packages / size of union of packages
```

**Note** For this metric and the following, since a compiler is just a name and 
a version, we include it in this metric as a package. This makes the assumption that
the compiler is equally important to a package. If it's more important, we might want
to separate them (or eventually change the weights). But I think this is a reasonable 
thing to try first.

### Level 2 Comparison: List of Packages with Versions

This next metric does the same thing, but only considered packages the same
if they have the exact same version.

### Level 3 Comparison: List of Packages with Weighted Versions

But if spec A has version 1.0.0 and spec B has version 2.0.0, these aren't really
the same thing. We'd want to be able to include in this metric how similar they are,
and this is the goal of this second level comparison. Given a set of versions for
a package, this gives us a list:

```
v1.0.0, v2.0.0, v.3.0.0, ... v.18.0.0
```

We can calculate a range of versions (e.g., in the above we'd go from 1 to 18)
and then be able to calculate a distance between any two actual versions. If the versions
are branch names (e.g., develop vs. master) we can only give a boolean yes/no (1/0) answer. Once we know
that difference, we can use it to come up with a more fine grained number to represent
the difference, e.g., given package AA in spec A, and package AB in B (the same
package with different versions):

```
sim(AA, AB) = 1 - (distance between AA and AB / total distance)
```

The result of the above should be a value between 0 and 1 that represents how
close the version strings are. Let's call these values generally sim(X1, X2), where
X is a common package, and 1 and 2 are different versions between specs.
We can then use this value in the same equation (where we were using 1/0 before
to represent overlap or not):

```
sim(A, B) = sums of sim(X1, X2) / size of union of packages
```

This gives us a similarity metric that has a weighted score that accounts for
versions.

### Level 4 Comparison

Now that we have comparisons for packages, we need to consider other metadata in the spec!
We want to treat the parameters and arch as separate comparisons, which we can
do in the same way (intersection / union). And then if we want to combine them we will
need to weight them based on importance.

> Question: how important is a parameter vs. package for stability?

We will calculate them as different metrics for now.


### Detailed Comparisons

For the detailed view, we will want to know exactly what is different (and overlapping)
between packages. For this strategy, we use the spack asp solver to generate a list
of facts for each spec, and then we output the differences between each one, along
with the intersection. Since these visualizations are separate, they are output
as one file per pair of packages. The main visualization (to show similarity scores)
will link to these views. The plotting is dicusssed next.

### 3. Plot Results

The data output by the previous spec, which is located in each package folder,
works with the [index.html](index.html) and [compare.html](compare.html)
to generate a similarity matrix (half) and column-like Venn diagram to compare
packages. We just need to:

1. generate results for many packages
2. add the result names to an index.html to link them all together

Discussed next.

### 4. Run Scaled

Note that some older versions of spack produce specs that are sort of empty
like this (and we cannot use):

```yaml
spec:
- octave-io:
    versions:
    - ':'
    hash: c3mls5rk6ohxlkflxx65kdh3byudfg35
```

So the script is modified to not include these. We now would want to run this
at scale, generating data for each package. Remember we need to have spack
on our path:

```bash
$ export PATH=/path/to/spack/bin:$PATH
```

And then a simple for loop can work to run the script, ensuring that we don't
run it for directories with the result already existing.

```bash
for package in $(ls packages/); do
   outfile="packages/${package}/spec-diffs.json"
   if [ ! -f "${outfile}" ]; then
       echo "Parsing $package"
       spack python calculate_diff.py "packages/${package}"
   fi
done
```

Finally, we want to generate an entry for each package we find.

```bash
for package in $(ls packages/); do
   outfile="packages/${package}/spec-diffs.json"
   if [ -f "${outfile}" ]; then
       echo "      <div onclick=\"document.location='spec.html?name=packages/${package}'\" class=\"card\"> ${package}</div>"
   fi
done
```

I just copy pasted this into the [index.html](index.html). Then we can also automatically
use this same method to add the right folders to git!

```bash
for package in $(ls packages/); do
   outfile="packages/${package}/spec-diffs.json"
   if [ -f "${outfile}" ]; then
       git add packages/$package/
   fi
done
```
