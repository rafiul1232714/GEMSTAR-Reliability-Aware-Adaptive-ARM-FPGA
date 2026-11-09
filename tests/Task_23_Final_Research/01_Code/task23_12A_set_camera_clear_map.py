import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
CONFIG = "Simulation/Task23_12_Camera_Clear.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Cannot load validation map")

settings = world.get_world_settings()

original = settings.get_editor_property(
    "gemstar_configuration"
)

print("ORIGINAL_CONFIG:", original)

settings.set_editor_property(
    "gemstar_configuration", CONFIG
)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Map save failed")

print("TASK23_12A_CLEAR_MAP_SAVED")
