import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
CONFIG = "Simulation/Task23LidarCalibration.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Cannot load validation map")

settings = world.get_world_settings()

print("TASK23_08_ORIGINAL_CONFIG:",
      settings.get_editor_property("gemstar_configuration"))

settings.set_editor_property("gemstar_configuration", CONFIG)

saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)

if not saved:
    raise RuntimeError("Map configuration could not be saved")

print("TASK23_08_MAP_CONFIG_SAVED")
