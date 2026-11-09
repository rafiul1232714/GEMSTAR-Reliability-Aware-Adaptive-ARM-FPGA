import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"

PREVIOUS = "Simulation/Task23_11E_FogMOR20.ini"
TARGET = "Simulation/Task23_11E_FogMOR100.ini"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map load failed")

settings = world.get_world_settings()

actual = str(
    settings.get_editor_property("gemstar_configuration")
).replace("\\", "/")

if actual != PREVIOUS:
    raise RuntimeError(
        "Unexpected previous configuration: " + actual
    )

settings.set_editor_property(
    "gemstar_configuration",
    TARGET
)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Map save failed")

print("TASK23_11E_FOG100_MAP_SAVED")
