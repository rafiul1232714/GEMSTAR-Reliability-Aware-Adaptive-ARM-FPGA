import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23_11E_Clear.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map load failed")

actual = str(
    world.get_world_settings().get_editor_property(
        "gemstar_configuration"
    )
).replace("\\", "/")

print("ACTUAL_CONFIG=" + actual)

if actual != EXPECTED:
    raise RuntimeError(
        "Configuration mismatch: " + actual
    )

print("TASK23_11E_CLEAR_MAP_VERIFIED")
