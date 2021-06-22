# CUDA Resampling Script

This script resamples volumes in SimpleITK-readable formats using the CUDA-based B-Spline interpolation algorithm from [this repository](https://github.com/DannyRuijters/CubicInterpolationCUDA/).

## Requirements
- Python 3
- SimpleITK
- CUDA (tested on 10 and 11)

## Building
- Open a terminal in the git directory and run `./build.sh`
- Alternatively, manually run the commands in `build.sh`

## Installation
- Copy the `libcudaresize.so` file to `/usr/lib` or another path on `LD_LIBRARY_PATH`
- Copy the `cudaresize.py` file somewhere convenient

## A Note on CUDA
Compiling against CUDA 11 gives a number of deprecation warnings; these are in the underlying [CubicInterpolationCUDA](https://github.com/DannyRuijters/CubicInterpolationCUDA/) repository (written for CUDA 3 and last updated for CUDA 5).
