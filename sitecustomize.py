"""
Process-wide Python startup tweaks for local development.

This repo mixes packages such as PyTorch and OpenCV that can each ship an
OpenMP runtime on Windows. In some environments that triggers the
`libiomp5md.dll already initialized` crash during import. Setting
KMP_DUPLICATE_LIB_OK allows the process to continue so local verification and
training scripts can start.
"""
import os
import platform


if platform.system() == "Windows":
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
