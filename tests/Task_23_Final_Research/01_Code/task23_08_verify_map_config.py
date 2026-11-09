import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23LidarCalibration.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Cannot reload map")

settings = world.get_world_settings()
actual = settings.get_editor_property("gemstar_configuration")

print("TASK23_08_VERIFIED_CONFIG:", actual)

if actual.replace("\\", "/") != EXPECTED:
    raise RuntimeError("LiDAR configuration override was not saved")

print("TASK23_08_MAP_CONFIG_PASS")
