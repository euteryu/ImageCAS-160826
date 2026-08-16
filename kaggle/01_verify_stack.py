from __future__ import annotations

import importlib.metadata

import nibabel
import numpy
import scipy
import torch
import nnunetv2  # noqa: F401 - the import itself is part of the check


def main() -> None:
    cuda_available = torch.cuda.is_available()
    print(f"nnU-Net: {importlib.metadata.version('nnunetv2')}")
    print(f"PyTorch: {torch.__version__}")
    print(f"NumPy: {numpy.__version__}")
    print(f"SciPy: {scipy.__version__}")
    print(f"NiBabel: {nibabel.__version__}")
    print(f"CUDA available: {cuda_available}")
    print(f"GPU: {torch.cuda.get_device_name(0) if cuda_available else None}")
    if not cuda_available:
        raise RuntimeError("CUDA is unavailable")
    try:
        value = (torch.ones(1, device="cuda") + 1).item()
        torch.cuda.synchronize()
    except Exception as error:
        raise RuntimeError("CUDA is visible but cannot execute a PyTorch kernel") from error
    if value != 2:
        raise RuntimeError(f"Unexpected CUDA smoke-test result: {value}")
    print("CUDA kernel test: PASS")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
