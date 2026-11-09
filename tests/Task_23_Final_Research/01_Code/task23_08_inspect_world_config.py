import unreal

map_path = "/Game/ResearchValidation/SensorFusionValidationMap"

world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)

if not world:
    raise RuntimeError("Cannot load research validation map")

settings = world.get_world_settings()

print("TASK23_LIDAR_WORLD_SETTINGS_CLASS:", settings.get_class().get_name())

try:
    value = settings.get_editor_property("gemstar_configuration")
    print("TASK23_LIDAR_MAP_CONFIG:", repr(value))
except Exception as exc:
    print("TASK23_LIDAR_MAP_CONFIG_READ_ERROR:", str(exc))

print("TASK23_LIDAR_INSPECTION_COMPLETE")
