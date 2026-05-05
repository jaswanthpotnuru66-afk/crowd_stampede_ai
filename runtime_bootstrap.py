import os
import platform


if platform.system() == "Windows":
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
