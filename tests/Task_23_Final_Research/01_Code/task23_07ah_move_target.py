import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Map load failed")

subsystem = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
)

targets = [
    a for a in subsystem.get_all_level_actors()
    if a.get_actor_label() == LABEL
]

if len(targets) != 1:
    raise RuntimeError(
        f"Expected one target; found {len(targets)}"
    )

target = targets[0]

target.set_actor_location(
    unreal.Vector(3140, -2650, 250),
    False,
    False
)

position = target.get_actor_location()

if abs(position.x - 3140) > 0.01:
    raise RuntimeError("Target position verification failed")

saved = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
    save_map_packages=True,
    save_content_packages=False
)

if saved is False:
    raise RuntimeError("Map save failed")

print("TASK23_07AH_TARGET_MOVED")
print(f"Target position: {position.x}, {position.y}, {position.z}")
