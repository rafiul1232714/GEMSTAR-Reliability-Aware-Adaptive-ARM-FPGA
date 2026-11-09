import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Cannot load calibration map")

actors = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
).get_all_level_actors()

targets = [
    a for a in actors
    if a.get_actor_label() == LABEL
]

if len(targets) != 1:
    raise RuntimeError(
        f"Expected exactly one cube, found {len(targets)}"
    )

cube = targets[0]

print("TASK23_AR_ACTOR_NAME:", cube.get_name())
print("TASK23_AR_BEFORE:", cube.get_actor_location())

cube.set_actor_location(
    unreal.Vector(3140, -2650, 250),
    False,
    False
)

position = cube.get_actor_location()

if abs(position.x - 3140) > 0.01:
    raise RuntimeError("Target movement failed")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
    save_map_packages=True,
    save_content_packages=False
)

print("TASK23_AR_AFTER:", position)
print("TASK23_AR_MOVE_SCRIPT_COMPLETE")
