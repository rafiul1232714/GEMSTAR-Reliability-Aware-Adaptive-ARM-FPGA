# Task 25 — Reliability and failure-injection replay (local only)

Based on the Task 24 C02 code (LiDAR-only, LiDAR–Radar, experimental Camera bearing EKF) and the 24 matched provisional Track 2 observations.

## Setup on Windows

1. Copy `task25_replay.py` into `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_25_Final_Research\01_Code`.
2. Install dependencies in your chosen Python environment: `python -m pip install numpy matplotlib`.
3. Run PowerShell:

```powershell
$root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests'
python "$root\Task_25_Final_Research\01_Code\task25_replay.py" `
  --task24 "$root\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_V2_EKF_Input_53Frames_V1" `
  --task25 "$root\Task_25_Final_Research"
```

## Outputs

* `02_CSV_Data/task25_replay_samples.csv` — per-frame injected and baseline EKF estimates
* `02_CSV_Data/task25_fault_summary.csv` — scenario summary
* `04_Plots/task25_trajectory_x.png` — state comparison
* `04_Plots/task25_fault_sensitivity.png` — mean GT-center error
* `04_Plots/task25_bev_diagnostic.png` — lightweight geometric BEV (offline)
* `05_Raw_Data_References/task25_sha256_manifest.csv` — input hashes
* `06_Research_Findings/Task25_preliminary_findings.md` — provenance, numbers and limitations

## Important

This script **does not** modify Task 24 sources. It reconstructs the baseline EKF and halts if the replay diverges by more than 1e-5 m from the Task 24 exported trajectories. Do **not** interpret the single-sequence results as sensor-reliability calibration, independent validation, or evidence of power savings.

Fault cases: Radar dropout, Camera dropout, periodic LiDAR dropout, Radar Doppler bias, Camera-bearing bias, and joint dropout. The cases are intentionally deterministic and exploratory. GroundTruth is evaluation-only.

If the replay assertion fails, stop and investigate; do not disable it.
