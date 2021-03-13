#!/usr/bin/env spack-python

# This script will take a package directory and calculate pairwise diffs for
# the packages installed. We take two approaches:
# 1. calculating basic similarity metrics based on the loaded specs
# 2. using the spack asp solver to generate sets of facts (and them compare them)
#
# You must have the spack bin with spack python on your PATH for this to work!
# See https://gist.github.com/tgamblin/83eba3c6d27f90d9fa3afebfc049ceaf for
# the dummy example of using spack.solve to calculate the diff.
# Usage:
# spack python calculate_diff.py <package-dir>


from distutils.version import StrictVersion
import subprocess
import yaml
import shutil
from glob import glob
import sys
import json
import os

try:
    import spack.spec
    from spack.solver.asp import SpackSolverSetup
except ImportError:
    sys.exit("You must have the spack bin on your path to import spack modules.")

# spack python does not support __file__
here = os.getcwd()

# Prepare a solver setup to parse differences
setup = spack.solver.asp.SpackSolverSetup()

## File Operations


def read_file(filename):
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def write_json(filename, content):
    write_file(filename, json.dumps(content, indent=4))


def write_file(filename, content):
    with open(filename, "w") as filey:
        filey.writelines(content)
    return filename


def is_semvar(version):
    try:
        StrictVersion(version)
        return True
    except ValueError:
        return False


def read_yaml(filename):
    stream = read_file(filename)
    return yaml.load(stream, Loader=yaml.FullLoader)


def to_tuple(asp_function):
    return tuple([asp_function.name, *asp_function.args])


def load_spack_spec(spec_file):
    with open(spec_file, "r") as stream:
        spec = spack.spec.Spec.from_yaml(stream)
    spec.concretize()
    return spec


def diff(a, b):
    # See https://gist.github.com/tgamblin/83eba3c6d27f90d9fa3afebfc049ceaf for
    a_facts = set(to_tuple(t) for t in setup.spec_clauses(a))
    b_facts = set(to_tuple(t) for t in setup.spec_clauses(b))
    print(a_facts.difference(b_facts))
    print(b_facts.difference(a_facts))


def create_package_lookup(spec):
    """Create a lookup with package names as keys. We basically unwrap the spec
    from it's list under spec['spec']. This will only work assuming unique
    package names (which might not be the case for later versions of spack. We
    also are going to treat the compiler as a package, since it eventually will
    be anyway!
    """
    lookup = {}
    for package in spec["spec"]:
        name = list(package.keys())[0]
        lookup.update(package)
        lookup[package[name]["compiler"]["name"]] = {
            "version": package[name]["compiler"]["version"]
        }
    return lookup


def main():
    if len(sys.argv) < 2:
        sys.exit("Please provide at least one package directory.")

    # Sniff to see if we have a package file
    package_dirs = sys.argv[1:]

    for package_dir in package_dirs:

        print("Parsing package directory %s" % package_dir)

        # Keep a lookup of diffs, by version1-version2 (sorted)
        diffs = {}

        spec_files = glob("%s/*.yaml" % package_dir)

        # We need the entire list of versions, for every dependency, in advance
        # We are treating compilers as packages
        _versions = {}
        for spec_file in spec_files:
            spec = read_yaml(spec_file)
            for package in spec["spec"]:
                name = list(package.keys())[0]
                if name not in _versions:
                    _versions[name] = set()
                if package[name]["compiler"]["name"] not in _versions:
                    _versions[package[name]["compiler"]["name"]] = set()

                _versions[name].add(package[name]["version"])
                _versions[package[name]["compiler"]["name"]].add(
                    package[name]["compiler"]["version"]
                )

        # Create a range for each version between 0 and N, scale each one to it.
        versions = {}
        for name, version_list in _versions.items():
            # We have to support semantic versioning for all
            if any([not is_semvar(x) for x in version_list]):
                versions[name] = {"semvar": False, "list": sorted(version_list)}
            else:
                versions[name] = {"semvar": True, "list": sorted(version_list)}
                versions[name]["numbers"] = [
                    float(x.replace(".", "", 1)) for x in versions[name]["list"]
                ]
                versions[name]["range"] = abs(
                    versions[name]["numbers"][-1] - versions[name]["numbers"][0]
                )

        # For each spec file, generate the raw asp
        for spec_file1 in spec_files:
            spec1 = read_yaml(spec_file1)
            spack_spec1 = load_spack_spec(spec_file1)
            spec1_name = os.path.basename(spec_file1).replace(".yaml", "")

            for spec_file2 in spec_files:
                spec2 = read_yaml(spec_file2)
                spec2_name = os.path.basename(spec_file2).replace(".yaml", "")
                spack_spec2 = load_spack_spec(spec_file2)

                # The unique key for the result is the sorted spec names
                key = "-".join(sorted([spec1_name, spec2_name]))
                result = {}

                # Calculate the diff via the solver setup! TODO
                # diff(spack_spec1, spack_spec2)
                # checks needs to be optional https://github.com/spack/spack/blob/develop/lib/spack/spack/solver/asp.py#L969

                ## Comparison 1: just the overlap of packages
                # Cut out early and call them perfectly equal if we are comparing the same spec
                if spec_file1 == spec_file2:
                    result = {
                        "1_package_name_overlap": 1,
                        "2_package_name_version_exact": 1,
                        "3_package_weighted_versions": 1,
                        "4_parameter_overlap": 1,
                        "5_arch_overlap": 1,
                    }
                    diffs[key] = result
                    continue

                # Create a lookup of packages for each
                # Note that here we are treating the compiler like a package
                lookup1 = create_package_lookup(spec1)
                lookup2 = create_package_lookup(spec2)

                # 1. Comparison 1: Just compare list of packages
                packages1 = set(lookup1.keys())
                packages2 = set(lookup2.keys())

                # sim(A, B) = intersection of common packages / size of union of packages
                result["1_package_name_overlap"] = len(
                    packages1.intersection(packages2)
                ) / len(packages1.union(packages2))

                # 2. Comparison 2: Include exact versions
                version1 = set(
                    ["%s-%s" % (name, x["version"]) for name, x in lookup1.items()]
                )
                version2 = set(
                    ["%s-%s" % (name, x["version"]) for name, x in lookup2.items()]
                )
                result["2_package_name_version_exact"] = len(
                    version1.intersection(version2)
                ) / len(version1.union(version2))

                # 3. Comparison 3: Package and weighted version
                # The intersection score will be the sum of the weighted distances
                intersection = 0

                # The parameter overlap will be done in a similar fashion
                parameter_intersection = 0
                arch_intersection = 0

                for package in packages1.intersection(packages2):

                    # If we don't have semantic versions, we compare them verbatim
                    if not versions[package]["semvar"]:
                        if lookup1[package]["version"] == lookup2[package]["version"]:
                            intersection += 1
                        continue

                    # Get version indices for the numbers to calculate distance
                    v1_idx = versions[package]["list"].index(
                        lookup1[package]["version"]
                    )
                    v2_idx = versions[package]["list"].index(
                        lookup2[package]["version"]
                    )
                    distance = abs(
                        versions[package]["numbers"][v2_idx]
                        - versions[package]["numbers"][v1_idx]
                    )

                    # If we only have one version, it's perfectly the same
                    if len(versions[package]["list"]) == 1:
                        intersection += 1

                    else:
                        # A result of 1 here means exactly the same, 0 is the most difference (the packages
                        # at either end of the range)
                        intersection += 1 - (distance / versions[package]["range"])

                    # 4. Comparison of parameter overlap - we don't count undefined in the list
                    defined1_params = set(
                        [
                            "%s-%s" % (k, v)
                            for k, v in lookup1[package].get("parameters", {}).items()
                            if v
                        ]
                    )
                    defined2_params = set(
                        [
                            "%s-%s" % (k, v)
                            for k, v in lookup2[package].get("parameters", {}).items()
                            if v
                        ]
                    )

                    # We can't divide by 0
                    if defined1_params or defined2_params:
                        parameter_intersection += len(
                            defined1_params.intersection(defined2_params)
                        ) / len(defined1_params.union(defined2_params))

                    # 5. Comparison of arch values (platform, platform os, and
                    arch1 = set(
                        [
                            "%s-%s" % (k, v)
                            for k, v in lookup1[package].get("arch", {}).items()
                        ]
                    )
                    arch2 = set(
                        [
                            "%s-%s" % (k, v)
                            for k, v in lookup2[package].get("arch", {}).items()
                        ]
                    )
                    if arch1 or arch2:
                        arch_intersection += len(arch1.intersection(arch2)) / len(
                            arch1.union(arch2)
                        )

                result["3_package_weighted_versions"] = intersection / len(
                    packages1.union(packages2)
                )
                result["4_parameter_overlap"] = parameter_intersection / len(
                    packages1.union(packages2)
                )
                result["5_arch_overlap"] = arch_intersection / len(
                    packages1.union(packages2)
                )
                diffs[key] = result

        # Save the result to the package folder
        result_file = os.path.join(package_dir, "spec-diffs.json")
        write_json(result_file, diffs)


if __name__ == "__main__":
    main()
