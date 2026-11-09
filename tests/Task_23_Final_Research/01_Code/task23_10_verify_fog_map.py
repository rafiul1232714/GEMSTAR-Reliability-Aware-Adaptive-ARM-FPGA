import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23WeatherFog.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map load failed")

actual = world.get_world_settings().get_editor_property(
    "gemstar_configuration"
)

actual = str(actual).replace("\\", "/")

if actual != EXPECTED:
    raise RuntimeError(
        "Fog configuration mismatch: " + actual
    )

print("TASK23_10_FOG_MAP_VERIFIED")
