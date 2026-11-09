import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Map could not be loaded")

config = world.get_world_settings().get_editor_property(
    "gemstar_configuration"
)

print("TASK23_10_CURRENT_MAP_CONFIG=" + str(config))
