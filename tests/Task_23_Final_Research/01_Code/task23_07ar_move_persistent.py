import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map loading failed")

actors = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
).get_all_level_actors()

targets = [a for a in actors if a.get_actor_label() == LABEL]

if len(targets) != 1:
    raise RuntimeError(f"Expected one target, found {len(targets)}")

target = targets[0]

print("TARGET_BEFORE:", target.get_actor_location())

target.set_actor_location(
    unreal.Vector(3140, -2650, 250),
    False,
    False
)

print("TARGET_AFTER:", target.get_actor_location())

saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)

print("EXPLICIT_MAP_SAVE_RESULT:", saved)

if not saved:
    raise RuntimeError("Explicit map save failed")

print("TASK23_AR_MAP_SAVE_COMPLETED")
