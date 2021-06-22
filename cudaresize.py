#!/usr/bin/env python3

import argparse
import ctypes
from functools import partial
import numbers
import os
import shutil
import subprocess as subp
import sys

import numpy as np
import SimpleITK as sitk

def has_cuda():
    """Verify that the computer has CUDA."""
    ## FIXME: Something more robust that nvidia-smi?
    ## Find nvidia-smi
    paths = (
        "/usr/bin/nvidia-smi",
        "/bin/nvidia-smi",
        "/usr/local/bin/nvidia-smi",
    )

    for p in paths:
        if os.path.isfile(p):
            try:
                subp.check_call((p,), stderr=subp.DEVNULL, stdout=subp.DEVNULL)
            except:
                return False
            else:
                return True
    return False

## Load the library. The `libcudaresize.so` file must be somewhere in LD_LIBRARY_PATH, typically 
## in /usr/lib. Note that the current directory is not included: if you want this script to run 
## with the library in the current directory, run it with `LD_LIBRARY_PATH=. <the-script>`
cudaresize = ctypes.cdll.LoadLibrary("libcudaresize.so")
def fix_spacing(im, desired_spacing=0.15388000011444092, use_sitk=False, prefilter=True):
    """Fix the image spacing.

    :param im: the image, as loaded by SITK
    :param desired_spacing: either a float indicating the spacing in ITK units (0.154... = 154 um)
                            for isotropic spacing or a triple of the same for anisotropic
    :param use_sitk: use SITK's default CPU resampling instead
    :param prefilter: apply the prefilter
    """
    if isinstance(desired_spacing, numbers.Number):
        ## Convert it to a triple
        desired_spacing = (desired_spacing,)*3

    width, height, depth = im.GetSize()

    ws, hs, ds = im.GetSpacing()

    ## Compute the new dimensions
    new_width, new_height, new_depth = (round(i*(j/new_space)) for i,j,new_space in zip(im.GetSize(), im.GetSpacing(), desired_spacing))

    if (width, height, depth) == (new_width, new_height, new_depth):
        ## The current size is as close as we can get
        print("Nothing to do")
        return im

    #if not has_cuda() or use_sitk: ## Resize using SimpleITK instead
    ## If they're running this, they most likely have CUDA
    if use_sitk:
        print("Using SimpleITK for resizing, this may take a while...")
        new_size = (new_width, new_height, new_depth)
        output_spacing = tuple((i*(j/k) for i,j,k in zip(im.GetSpacing(), im.GetSize(), new_size)))
        rsf = sitk.ResampleImageFilter()
        rsf.SetDefaultPixelValue(-2000)
        rsf.SetOutputSpacing(output_spacing)
        rsf.SetInterpolator(sitk.sitkBSpline)
        rsf.SetOutputDirection(im.GetDirection())
        rsf.SetOutputOrigin(im.GetOrigin())
        rsf.SetSize(new_size)
        return rsf.Execute(im)

    print("Using CUDA for resizing")
    return resize(im, new_width, new_height, new_depth, prefilter)

def resize(im, new_width, new_height, new_depth, prefilter=True):
    """Resize an image to the given dimensions.

    :param im: the image, as loaded by SITK
    :param new_height: the new integer height for the image
    """
    width, height, depth = im.GetSize()
    ## Allocate the output array here
    output = np.zeros(new_width*new_height*new_depth, dtype=ctypes.c_float)
    output_ct = output.ctypes

    im_array = sitk.GetArrayFromImage(im)
    ## This cast is necessary
    dtype = im_array.dtype
    orig = im_array
    im_array = im_array.astype(ctypes.c_float).reshape(width*height*depth)

    im_array_ct = im_array.ctypes

    ## Run the actual interpolation
    cudaresize.interpolate(im_array_ct.data_as(ctypes.POINTER(ctypes.c_float)), output_ct.data_as(ctypes.POINTER(ctypes.c_float)), width, height, depth, new_width, new_height, new_depth, prefilter)
    print("Loading in numpy")
    ## Numpy indexing is reversed, we have to reshape it like this
    output = output.astype(dtype).reshape((new_depth, new_height, new_width))

    ## Finally, load it into the output image and copy over metadata
    print("Loading in SITK")
    output_im = sitk.GetImageFromArray(output)
    ## Don't set the desired spacing, set the actual spacing
    output_im.SetSpacing(tuple((i*(j/k) for i,j,k in zip(im.GetSpacing(), im.GetSize(), output_im.GetSize()))))
    output_im.SetDirection(im.GetDirection())
    output_im.SetOrigin(im.GetOrigin())

    return output_im

if __name__ == "__main__":
    ## Necessary for Docker containers to print in a timely fashion
    print = partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input volume to resample")
    parser.add_argument("output", help="Output volume")
    parser.add_argument("--cpu-resampling", action="store_true", help="Disable CUDA resampling and use the CPU instead (why?)")
    parser.add_argument("--no-prefilter", action="store_true", help="Disable the B-spline prefilter")
    parser.add_argument("spacing", help="Desired image spacing. Give either one (i.e. isotropic) or three (corresponding to RAS). Must be a float as in SimpleITK spacing, e.g. 0.154 corresponds to 154mu", type=float, nargs="+")

    args = parser.parse_args()

    if len(args.spacing) not in (1, 3):
        raise ValueError("Can only pass one or three spacing values")
    elif len(args.spacing) == 1:
        spacing = (args.spacing[0],)*3
    else:
        spacing = args.spacing

    print("Loading input file...")
    inp = sitk.ReadImage(args.input)
    print("Resampling...")
    inp = fix_spacing(inp, desired_spacing=spacing, use_sitk=args.cpu_resampling, prefilter=not args.no_prefilter)
    print("Writing resampled image...")
    sitk.WriteImage(inp, args.output)

    print("All done!")
