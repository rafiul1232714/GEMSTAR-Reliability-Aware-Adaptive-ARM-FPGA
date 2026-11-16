import sys
import importlib

print("Python version:", sys.version.split()[0])

for package in ["torch", "ultralytics", "cv2", "osi3"]:
    try:
        module = importlib.import_module(package)
        version = getattr(module, "__version__", "installed")
        print(f"{package}: YES ({version})")
    except Exception as error:
        print(
            f"{package}: NO "
            f"({type(error).__name__}: {error})"
        )
