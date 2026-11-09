from pathlib import Path
import numpy as np

root = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research\08_Processed_Data"
)

for folder in ["LiDAR_Range", "LiDAR_Source_Matched"]:
    print(f"\n=== {folder} ===")

    files = sorted((root / folder).glob("*.npz"))
    print("Number of datasets:", len(files))

    for path in files[:3]:
        print("\nFile:", path.name)

        with np.load(path, allow_pickle=False) as data:
            for key in data.files:
                value = data[key]
                print(
                    f"  {key}: "
                    f"shape={value.shape}, "
                    f"dtype={value.dtype}"
                )
