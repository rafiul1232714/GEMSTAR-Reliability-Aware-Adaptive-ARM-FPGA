import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
CONFIG = "Simulation/Task23LidarDisplaced.ini"
LABEL = "TASK23_CALIBRATION_TARGET_10M"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Cannot load research map")

actors = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
).get_all_level_actors()

targets = [
    actor for actor in actors
    if actor.get_actor_label() == LABEL
]

if len(targets) != 1:
    raise RuntimeError(
        f"Expected one calibration cube; found {len(targets)}"
    )

target = targets[0]
before = target.get_actor_location()

print("TASK23_LIDAR_TARGET_BEFORE:", before)

if abs(before.x - 2940) > 0.01:
    raise RuntimeError(
        f"Unexpected original cube X: {before.x}"
    )

target.set_actor_location(
    unreal.Vector(3140, -2650, 250),
    False,
    False
)

after = target.get_actor_location()

if abs(after.x - 3140) > 0.01:
    raise RuntimeError("Cube movement failed")

settings = world.get_world_settings()
settings.set_editor_property(
    "gemstar_configuration", CONFIG
)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Map saving failed")

print("TASK23_LIDAR_TARGET_AFTER:", after)
print("TASK23_LIDAR_DISPLACED_MAP_SAVED")
