import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Saved map could not be loaded")

actors = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
).get_all_level_actors()

targets = [
    a for a in actors
    if a.get_actor_label() == LABEL
]

if len(targets) != 1:
    raise RuntimeError("Calibration target not found")

target = targets[0]
position = target.get_actor_location()

print("TASK23_AR_DISK_POSITION:", position)

if abs(position.x - 3140) > 0.01:
    raise RuntimeError(
        f"Saved map incorrect: X={position.x}, expected 3140"
    )

print("TASK23_AR_SAVED_MAP_VERIFIED")
