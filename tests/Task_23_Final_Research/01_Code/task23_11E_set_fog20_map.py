import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
CONFIG = "Simulation/Task23_11E_FogMOR20.ini"
EXPECTED_PREVIOUS = "Simulation/Task23_11E_Clear.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map load failed")

settings = world.get_world_settings()

previous = str(
    settings.get_editor_property("gemstar_configuration")
).replace("\\", "/")

print("PREVIOUS_CONFIG=" + previous)

if previous != EXPECTED_PREVIOUS:
    raise RuntimeError(
        "Unexpected previous map configuration: " + previous
    )

settings.set_editor_property(
    "gemstar_configuration",
    CONFIG
)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Map save failed")

print("TASK23_11E_FOG20_MAP_SAVED")
