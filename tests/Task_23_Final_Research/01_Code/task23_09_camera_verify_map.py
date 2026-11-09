import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23CameraBaseline.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Independent map reload failed")

actual = world.get_world_settings().get_editor_property(
    "gemstar_configuration"
)

print("TASK23_09_ACTUAL_CONFIG:", actual)

if actual.replace("\\", "/") != EXPECTED:
    raise RuntimeError("Wrong persisted camera configuration")

print("TASK23_09_CAMERA_MAP_VERIFIED")
