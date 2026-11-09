import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
CONFIG = "Simulation/Task23_11E_Clear.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map load failed")

settings = world.get_world_settings()

old_config = str(
    settings.get_editor_property("gemstar_configuration")
)

print("PREVIOUS_CONFIG=" + old_config)

settings.set_editor_property(
    "gemstar_configuration",
    CONFIG
)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Map save failed")

print("TASK23_11E_CLEAR_MAP_SAVED")
