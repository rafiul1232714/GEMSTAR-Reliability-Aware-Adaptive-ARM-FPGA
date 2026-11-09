from pathlib import Path
import re
import shutil
import json

G = Path(r"E:\GEMSTAR_Project\gemstar")
B = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_20_Final_Research")

files = {
    "header": G / "Plugins/gemstar_interfaces/Source/GEMSTAR_Interfaces/Public/Interfaces/Sensor/SensorConfigurationData.h",
    "manager": G / "Plugins/GameFeatures/ue_radar_feature/Source/ue_radar_featureRuntime/Private/RadarSensorManager.cpp",
    "radar": G / "Plugins/GameFeatures/ue_radar_feature/Source/ue_radar_featureRuntime/Private/SimpleRadar.cpp",
    "ini": G / "Simulation/DefaultGemstar.ini"
}

backup_dir = B / "03_Configurations/Task20_45_Before_Range_Patch"
backup_dir.mkdir(parents=True, exist_ok=True)

def replace_one(text, old, new, name):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{name}: expected one matching location, found {count}"
        )
    return text.replace(old, new, 1)

def regex_one(text, pattern, replacement, name):
    result, n = re.subn(pattern, replacement, text, count=1)
    if n != 1:
        raise RuntimeError(f"{name}: patch anchor not found")
    return result

print("\n=== TASK 20.45 PATCH PREPARATION ===")

original = {}

for key, path in files.items():
    if not path.is_file():
        raise FileNotFoundError(path)
    original[key] = path.read_text(encoding="utf-8-sig")

updated = dict(original)

# 1. Add Range specifically to the radar structure.
header = updated["header"]
start = header.index("struct FRadarConfigurationData")
end = header.index("struct FCameraConfigurationData", start)
radar_struct = header[start:end]

if "float Range =" in radar_struct:
    raise RuntimeError("Radar Range field already exists; inspect manually")

radar_struct = replace_one(
    radar_struct,
    "float DistanceHalfFalloff = 2000.0;",
    """float DistanceHalfFalloff = 2000.0;
  UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SensorConfiguration")
  float Range = 10.0f;""",
    "Radar configuration struct"
)
updated["header"] = header[:start] + radar_struct + header[end:]

# 2. Connect parsed INI Range to radar configuration.
updated["manager"] = replace_one(
    updated["manager"],
    "config.Radar.DistanceHalfFalloff = distanceHalfFalloff * 100.0f;",
    """config.Radar.DistanceHalfFalloff = distanceHalfFalloff * 100.0f;
          config.Radar.Range = (Range > 0.0f) ? Range : 10.0f;""",
    "Radar manager range assignment"
)

# 3. Prevent BeginPlay from overwriting an existing configuration.
updated["radar"] = replace_one(
    updated["radar"],
    "CreateTestConfig();",
    """  if (Sensor.SensorViewConfig == nullptr)
  {
      CreateTestConfig();
  }""",
    "Radar BeginPlay initialization"
)

# Remove the old diagnostic (which reports the previous value).
old_log = r'\s*if \(Sensor\.SensorViewConfig != nullptr\)\s*\{\s*UE_LOG\(LogTemp, Warning,\s*TEXT\("TASK20_42_RADAR_RANGE: %.3f metres"\),\s*Sensor\.SensorViewConfig->range\(\)\);\s*\}'
updated["radar"], removed = re.subn(
    old_log, "", updated["radar"], count=1
)

if removed != 1:
    raise RuntimeError("Existing Task 20.42 diagnostic not found")

# Apply range after superclass initialization.
updated["radar"] = replace_one(
    updated["radar"],
    "Super::SetSensorConfiguration(NewSensorConfiguration);",
    """Super::SetSensorConfiguration(NewSensorConfiguration);
  if (Sensor.SensorViewConfig == nullptr)
  {
      CreateTestConfig();
  }
  Sensor.SensorViewConfig->set_range(SensorConfiguration.Radar.Range);
  UE_LOG(LogTemp, Warning,
      TEXT("TASK20_45_RADAR_RANGE: %.3f metres"),
      Sensor.SensorViewConfig->range());""",
    "Radar SetSensorConfiguration"
)

# 4. Set Range=50 inside radar's INI section only.
ini = updated["ini"]

match = re.search(
    r"(?m)^\[ue_radar_feature:sensor1\]\s*$",
    ini
)

if not match:
    raise RuntimeError("Radar INI section not found")

section_start = match.end()
next_section = re.search(r"(?m)^\[.*\]\s*$", ini[section_start:])
section_end = (
    section_start + next_section.start()
    if next_section else len(ini)
)

section = ini[section_start:section_end]

if re.search(r"(?m)^\s*Range\s*=", section):
    raise RuntimeError("Radar INI Range already exists")

section = section.rstrip() + "\nRange=50\n\n"
updated["ini"] = ini[:section_start] + section + ini[section_end:]

# All patch checks have passed: now preserve originals.
for key, path in files.items():
    backup = backup_dir / path.name
    if backup.exists():
        raise RuntimeError(
            f"Backup already exists: {backup}; no files modified"
        )

for key, path in files.items():
    shutil.copy2(path, backup_dir / path.name)

# Write the modified files.
for key, path in files.items():
    path.write_text(updated[key], encoding="utf-8")

summary = {
    "Task": "20.45",
    "ConfiguredRadarRangeM": 50,
    "PreviousRuntimeRangeM": 10,
    "ChangedFiles": [str(p) for p in files.values()],
    "Backups": str(backup_dir),
    "BuildCompleted": False,
    "RuntimeRangeVerified": False
}

report = B / "06_Research_Findings/task20_45_patch_summary.json"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(summary, indent=2), encoding="utf-8")

print("Header updated: True")
print("Radar manager updated: True")
print("Radar initialization updated: True")
print("INI radar range set to: 50 m")
print("Original files backed up: True")
print("Report saved:", report.is_file())
print("\n=== TASK 20.45 PATCH COMPLETE ===")
print("Build completed: False")
print("50 m runtime verified: False")
