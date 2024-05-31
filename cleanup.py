# workaround for https://github.com/joshua-auchincloss/hatch-cython/issues/53

import glob
import os

for ext in ["c", "so", "pyd"]:
    for file in glob.glob(f"src/**/*.{ext}", recursive=True):
        os.unlink(file)
