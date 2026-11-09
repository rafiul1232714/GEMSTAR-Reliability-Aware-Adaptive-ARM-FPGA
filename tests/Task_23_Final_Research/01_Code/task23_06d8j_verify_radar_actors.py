import unreal
from pathlib import Path

map_path = "/Game/ResearchValidation/SensorFusionValidationMap"

result_path = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\05_Raw_Data_References\task23_06d8j_actor_verification.txt"
)

world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)

if not world:
    raise RuntimeError("Validation map failed to load")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
labels = [a.get_actor_label() for a in actors]

tester_count = labels.count("RadarSensorTester")
radar_count = labels.count("SimpleRadar_ConfiguredByBlueprint")

report = [
    "TASK 23.6D-8J ACTOR VERIFICATION",
    "Map: " + map_path,
    "Total actors: " + str(len(actors)),
    "RadarSensorTester count: " + str(tester_count),
    "SimpleRadar_ConfiguredByBlueprint count: " + str(radar_count),
    "",
    "RADAR-RELATED ACTORS"
]

for actor in actors:
    label = actor.get_actor_label()
    if "radar" in label.lower():
        pos = actor.get_actor_location()
        report.append(
            f"{label} | X={pos.x:.2f}, "
            f"Y={pos.y:.2f}, Z={pos.z:.2f} cm"
        )

if tester_count == 0 and radar_count == 1:
    report.append("STATUS: PASS")
else:
    report.append("STATUS: NEEDS_INSPECTION")

result_path.parent.mkdir(parents=True, exist_ok=True)
result_path.write_text("\n".join(report), encoding="utf-8")

print("Actor verification report written")
