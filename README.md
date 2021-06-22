# CUDA Resampling Script

This script resamples volumes in SimpleITK-readable formats using the CUDA-based B-Spline interpolation algorithm from [this repository](https://github.com/DannyRuijters/CubicInterpolationCUDA/).

## Requirements
- Python 3
- SimpleITK
- CUDA (tested on 10 and 11)

## Building
- Set the `CUDA_PATH` environment variable to point to CUDA (e.g. `/usr/local/cuda-11.0.3` or `/opt/cuda/`)
- Open a terminal in the git directory and run `./build.sh`
- Alternatively, manually run the commands in `build.sh`
- You should end up with the `libcudaresize.so` library in the current directory

## Installation
- Copy the `libcudaresize.so` file to `/usr/lib` or another path on `LD_LIBRARY_PATH`
- Copy the `cudaresize.py` file somewhere convenient

## A Note on CUDA
Compiling against CUDA 11 gives a number of deprecation warnings; these are in the underlying [CubicInterpolationCUDA](https://github.com/DannyRuijters/CubicInterpolationCUDA/) repository (written for CUDA 3 and last updated for CUDA 5).
