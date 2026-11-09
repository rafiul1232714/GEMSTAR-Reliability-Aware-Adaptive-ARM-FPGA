import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map reload failed")

actors = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
).get_all_level_actors()

targets = [a for a in actors if a.get_actor_label() == LABEL]

if len(targets) != 1:
    raise RuntimeError("Target missing after reload")

position = targets[0].get_actor_location()

print("VERIFIED_TARGET_POSITION:", position)

if abs(position.x - 3140) > 0.01:
    raise RuntimeError(
        f"Persistence failed: X={position.x}"
    )

print("TASK23_AR_PERSISTENCE_PASS")
