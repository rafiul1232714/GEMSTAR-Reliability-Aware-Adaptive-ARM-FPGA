import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
CONFIG = "Simulation/Task23WeatherFog.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map load failed")

settings = world.get_world_settings()
settings.set_editor_property("gemstar_configuration", CONFIG)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Map save failed")

print("TASK23_10_FOG_MAP_SAVED")
