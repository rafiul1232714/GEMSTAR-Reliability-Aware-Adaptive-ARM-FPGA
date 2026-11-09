import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
CONFIG = "Simulation/Task23CameraBaseline.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Cannot load validation map")

settings = world.get_world_settings()

print(
    "TASK23_09_ORIGINAL_CONFIG:",
    settings.get_editor_property("gemstar_configuration")
)

settings.set_editor_property("gemstar_configuration", CONFIG)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Cannot save camera configuration")

print("TASK23_09_CAMERA_MAP_SAVED")
