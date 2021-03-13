#!/usr/bin/env python3

# This script will install different versions of spack, and for each version,
# generate a concretized spec for a set of packages of interest.
#
# Usage:
# python generate_specs.py <package1> <package2>

from caliper.managers import GitHubManager
from caliper.metrics import MetricsExtractor

import subprocess
import shutil
import sys
import os


here = os.path.abspath(os.path.dirname(__file__))

## File Operations


def read_file(filename):
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def write_file(filename, content):
    with open(filename, "w") as filey:
        filey.writelines(content)
    return filename


def main():
    if len(sys.argv) < 2:
        sys.exit("Please provide at least one package to analyze, or a package file")

    # Sniff to see if we have a package file
    package_file = sys.argv[1]
    if os.path.exists(package_file):
        specs = read_file(package_file).split("\n")
    else:
        specs = sys.argv[1:]

    # Use caliper to create a GitHub manager, we'll have spack at every version
    manager = GitHubManager("spack/spack")
    extractor = MetricsExtractor(manager)
    git = extractor.prepare_repository()
    spack = os.path.join(git.folder, "bin", "spack")

    # Loop through installs, generate a spec for each package
    for release in manager.specs:

        # Not all versions of spack will be supported (e.g., Pythhon 2) and
        # not all packages exist for every version
        git.checkout(release["version"], dest=git.folder)

        for spec in specs:
            spec_folder = os.path.join(here, spec)
            if not os.path.exists(spec_folder):
                os.mkdir(spec_folder)
            filename = "%s-spack-%s.yaml" % (spec, release["version"])
            spec_output = os.path.join(spec_folder, filename)

            # Don't generate again
            if os.path.exists(spec_output):
                continue

            p = subprocess.Popen(
                [spack, "spec", "--yaml", spec], stdout=subprocess.PIPE
            )
            result = p.communicate()
            if p.returncode == 0:
                print("Writing result for %s" % filename)
                write_file(spec_output, result[0].decode("utf-8"))

    # Clean up git directory with spack
    if os.path.exists(git.folder):
        shutil.rmtree(git.folder)


if __name__ == "__main__":
    main()
