import unreal
from pathlib import Path

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Validation map could not be loaded")

subsystem = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
)

actors = list(subsystem.get_all_level_actors())

# Remove only the known redundant Blueprint Radar
redundant = [
    a for a in actors
    if a.get_actor_label() ==
    "SimpleRadar_ConfiguredByBlueprint"
]

if len(redundant) != 1:
    raise RuntimeError(
        f"Expected one redundant Radar, found {len(redundant)}"
    )

for actor in redundant:
    subsystem.destroy_actor(actor)

# Update the existing calibration cube
targets = [
    a for a in actors
    if a.get_actor_label() ==
    "TASK23_CALIBRATION_TARGET_10M"
]

if len(targets) != 1:
    raise RuntimeError(
        f"Expected one calibration cube, found {len(targets)}"
    )

target = targets[0]

target.set_actor_location(
    unreal.Vector(2940, -2650, 250),
    False,
    False
)

target.set_actor_rotation(
    unreal.Rotator(0, 0, 0),
    False
)

target.set_actor_scale3d(
    unreal.Vector(3, 3, 3)
)

saved = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
    save_map_packages=True,
    save_content_packages=False
)

if saved is False:
    raise RuntimeError("Map save failed")

report = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research"
    r"\05_Raw_Data_References\task23_07y_alignment.txt"
)

report.write_text(
    "TASK 23.7Y - RADAR TARGET ALIGNMENT\n"
    "Redundant placed Radar removed: YES\n"
    "Target label: TASK23_CALIBRATION_TARGET_10M\n"
    "Target position (cm): 2940,-2650,250\n"
    "Target scale: 3,3,3\n"
    "Configured Radar position (cm): 1940,-2650,250\n"
    "Nominal center distance (m): 10\n"
    "Nominal front surface distance (m): 8.5\n"
    "Configuration activated: NOT YET\n"
    "Map saved: YES\n",
    encoding="utf-8"
)

print("TASK23_07Y_ALIGNMENT_COMPLETE")
