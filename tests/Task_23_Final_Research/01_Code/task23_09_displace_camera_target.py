import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"
CONFIG = "Simulation/Task23CameraDisplaced.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Map could not be loaded")

actors = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
).get_all_level_actors()

targets = [
    actor for actor in actors
    if actor.get_actor_label() == LABEL
]

if len(targets) != 1:
    raise RuntimeError(f"Expected one cube, found {len(targets)}")

cube = targets[0]
pos = cube.get_actor_location()

print("ORIGINAL_TARGET:", pos)

if (abs(pos.x - 2940) > 0.01 or
    abs(pos.y + 2650) > 0.01 or
    abs(pos.z - 250) > 0.01):
    raise RuntimeError("Unexpected baseline cube position")

cube.set_actor_location(
    unreal.Vector(3140, -2650, 250),
    False,
    False
)

world.get_world_settings().set_editor_property(
    "gemstar_configuration", CONFIG
)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Could not save displaced map")

print("CAMERA_TARGET_DISPLACEMENT_SAVED")
