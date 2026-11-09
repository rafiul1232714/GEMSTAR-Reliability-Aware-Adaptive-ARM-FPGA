import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"

EXPECTED = "Simulation/Task23_11E_FogMOR100.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map load failed")

actual = str(
    world.get_world_settings().get_editor_property(
        "gemstar_configuration"
    )
).replace("\\", "/")

if actual != EXPECTED:
    raise RuntimeError(
        "Fog MOR 100 configuration mismatch: " + actual
    )

print("TASK23_11E_FOG100_MAP_VERIFIED")
