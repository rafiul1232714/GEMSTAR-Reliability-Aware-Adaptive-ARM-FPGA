from pathlib import Path
p = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_29_Final_Research\04_Code\task29_python_execution_probe.txt")
p.write_text("PYTHON_EXECUTED", encoding="utf-8")
print("PYTHON_EXECUTED", flush=True)
