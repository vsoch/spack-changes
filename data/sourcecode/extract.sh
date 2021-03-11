#!/bin/bash

caliper extract github:LLNL/axom
caliper extract github:Alpine-DAV/ascent
caliper view github/LLNL-axom/changedlines/changedlines-results.json --title "LLNL axom Changed Lines" --outdir github/LLNL-axom/
caliper view github/Alpine-DAV-ascent/changedlines/changedlines-results.json --title "Alpine-DAV ascent Changed Lines" --outdir github/Alpine-DAV-ascent/
caliper view github/spack-spack/changedlines/changedlines-results.json --title "Spack Changed Lines" --outdir github/spack-spack
