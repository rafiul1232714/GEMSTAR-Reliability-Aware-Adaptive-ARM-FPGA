import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23_12_Camera_Clear.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Cannot reload validation map")

actual = world.get_world_settings().get_editor_property(
    "gemstar_configuration"
)

print("ACTUAL_CONFIG:", actual)

if actual.replace("\\", "/") != EXPECTED:
    raise RuntimeError(
        "Saved map configuration mismatch: " + actual
    )

print("TASK23_12A_CLEAR_MAP_VERIFIED")
