import unreal
MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23WeatherClear.ini"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Map reload failed")
actual = world.get_world_settings().get_editor_property("gemstar_configuration")
if actual.replace("\\", "/") != EXPECTED:
    raise RuntimeError("Persisted weather configuration mismatch: " + actual)
print("TASK23_WEATHER_MAP_VERIFIED")
