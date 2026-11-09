import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"
CONFIG = "Simulation/Task23CameraDisplaced.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Independent map reload failed")

actors = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
).get_all_level_actors()

matches = [
    a for a in actors
    if a.get_actor_label() == LABEL
]

if len(matches) != 1:
    raise RuntimeError("Cube not found")

pos = matches[0].get_actor_location()

actual = world.get_world_settings().get_editor_property(
    "gemstar_configuration"
)

print("SAVED_CUBE_POSITION:", pos)
print("SAVED_CAMERA_CONFIG:", actual)

if (abs(pos.x - 3140) > 0.01 or
    abs(pos.y + 2650) > 0.01 or
    abs(pos.z - 250) > 0.01):
    raise RuntimeError("Cube displacement not persisted")

if actual.replace("\\", "/") != CONFIG:
    raise RuntimeError("Camera configuration not persisted")

print("CAMERA_TARGET_DISPLACEMENT_VERIFIED")
