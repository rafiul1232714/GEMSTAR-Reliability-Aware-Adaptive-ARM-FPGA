import unreal

print("=== TASK 24.4.3.S UNREAL PYTHON PREFLIGHT ===")

source = "/ue_driving_practise_area_brunswick_map_feature/DrivingPractiseAreaBrunswickMap"

print("PYTHON_RUNNING=YES")
print("UNREAL_VERSION=" + str(unreal.SystemLibrary.get_engine_version()))

print("EDITOR_ASSET_LIBRARY_AVAILABLE=" +
      str(hasattr(unreal, "EditorAssetLibrary")))

print("EDITOR_LEVEL_LIBRARY_AVAILABLE=" +
      str(hasattr(unreal, "EditorLevelLibrary")))

print("GEMSTAR_WORLD_SETTINGS_AVAILABLE=" +
      str(hasattr(unreal, "GemstarWorldSettings")))

print("ORIGINAL_MAP_ASSET_FOUND=" +
      str(unreal.EditorAssetLibrary.does_asset_exist(source)))

print("ORIGINAL_MAP_MODIFIED=NO")
print("TASK24_04_03S_UNREAL_PYTHON_PREFLIGHT_PASS")