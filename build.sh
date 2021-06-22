#!/bin/sh

## Update all submodules
git submodule update

## Fix up the cubic interpolation repository
cd CubicInterpolationCUDA
git checkout d52d23cf4ad152d011101b19d305d64540b665fd
git apply ../moderncuda.patch

## Compile the library
cd ..
make
