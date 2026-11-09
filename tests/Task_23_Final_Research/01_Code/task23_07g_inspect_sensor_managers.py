import unreal
from pathlib import Path

map_path = "/Game/ResearchValidation/SensorFusionValidationMap"

out = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\05_Raw_Data_References\task23_07g_sensor_manager_inventory.txt")

world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)

if not world:
    raise RuntimeError("Could not load validation map")

subsystem = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
)

actors = subsystem.get_all_level_actors()

report = [
    "TASK 23.7G — SENSOR MANAGER INVENTORY",
    "Map: " + map_path,
    "Total actors: " + str(len(actors)),
    "",
    "=== RELEVANT ACTORS ==="
]

for actor in actors:
    name = actor.get_actor_label()
    cls = actor.get_class().get_name()

    if any(
        term in (name + " " + cls).lower()
        for term in ["radar", "lidar", "camera", "sensor", "logger", "manager"]
    ):
        pos = actor.get_actor_location()

        report.append(
            f"{name} | Class={cls} | "
            f"X={pos.x:.2f}, "
            f"Y={pos.y:.2f}, "
            f"Z={pos.z:.2f}"
        )

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(report), encoding="utf-8")

print("TASK23_07G_INVENTORY_COMPLETE")
