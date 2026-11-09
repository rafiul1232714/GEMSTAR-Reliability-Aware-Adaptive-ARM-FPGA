import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"
CONFIG = "Simulation/Task23LidarDisplaced.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map reload failed")

actors = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
).get_all_level_actors()

targets = [
    actor for actor in actors
    if actor.get_actor_label() == LABEL
]

if len(targets) != 1:
    raise RuntimeError("Calibration cube missing")

position = targets[0].get_actor_location()
config = world.get_world_settings().get_editor_property(
    "gemstar_configuration"
)

print("TASK23_LIDAR_VERIFIED_POSITION:", position)
print("TASK23_LIDAR_VERIFIED_CONFIG:", config)

if abs(position.x - 3140) > 0.01:
    raise RuntimeError("Displacement did not persist")

if config.replace("\\", "/") != CONFIG:
    raise RuntimeError("LiDAR configuration override incorrect")

print("TASK23_LIDAR_DISPLACEMENT_VERIFIED")
