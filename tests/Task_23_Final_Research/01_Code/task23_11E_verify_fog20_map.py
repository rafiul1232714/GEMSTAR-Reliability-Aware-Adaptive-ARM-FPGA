import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23_11E_FogMOR20.ini"

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
        "Fog configuration mismatch: " + actual
    )

print("TASK23_11E_FOG20_MAP_VERIFIED")
