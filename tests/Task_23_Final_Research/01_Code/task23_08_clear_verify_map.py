import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23LidarClearCalibration.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Map reload failed")

actual = world.get_world_settings().get_editor_property(
    "gemstar_configuration"
)

print("ACTUAL_CLEAR_CONFIG:", actual)

if actual.replace("\\", "/") != EXPECTED:
    raise RuntimeError("Wrong persisted map configuration")

print("TASK23_CLEAR_MAP_VERIFIED")
