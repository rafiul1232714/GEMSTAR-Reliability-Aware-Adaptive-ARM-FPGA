import unreal
import hashlib
import os
import traceback

SOURCE = "/ue_driving_practise_area_brunswick_map_feature/DrivingPractiseAreaBrunswickMap"
DEST = "/Game/Task24_C01/C01_DrivingPractiseAreaBrunswickMap"

CONFIG = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C01_Clear_Stationary10m\C01_Gemstar_Launch.ini"

SOURCE_FILE = r"E:\GEMSTAR_Project\gemstar\Plugins\GameFeatures\ue_driving_area_brunswick_map_feature\Content\DrivingPractiseAreaBrunswickMap.umap"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== TASK 24.4.3.R UNREAL MAP AUTOMATION ===")

    if not os.path.isfile(CONFIG):
        raise RuntimeError("C01 configuration file missing")

    if not os.path.isfile(SOURCE_FILE):
        raise RuntimeError("Original map missing")

    original_hash = sha256_file(SOURCE_FILE)

    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE):
        raise RuntimeError("Original Unreal map asset not found")

    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError("C01 map asset already exists; refusing overwrite")

    print("ORIGINAL_MAP_SHA256_BEFORE=" + original_hash)

    success = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST)

    if not success:
        raise RuntimeError("Map duplication failed")

    print("C01_MAP_DUPLICATED=YES")

    unreal.EditorLevelLibrary.load_level(DEST)

    world = unreal.EditorLevelLibrary.get_editor_world()

    if world is None:
        raise RuntimeError("Could not access duplicated map world")

    settings = world.get_world_settings()

    if settings is None:
        raise RuntimeError("Duplicated map World Settings unavailable")

    if not isinstance(settings, unreal.GemstarWorldSettings):
        raise RuntimeError(
            "Map World Settings is not GemstarWorldSettings: "
            + str(type(settings))
        )

    settings.set_editor_property("gemstar_configuration", CONFIG)

    selected = settings.get_editor_property("gemstar_configuration")

    if os.path.normcase(os.path.normpath(selected)) != os.path.normcase(os.path.normpath(CONFIG)):
        raise RuntimeError("GemstarConfiguration property mismatch")

    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Could not save duplicated map")

    if sha256_file(SOURCE_FILE) != original_hash:
        raise RuntimeError("Original map hash changed unexpectedly")

    print("C01_MAP_ASSET=" + DEST)
    print("C01_GEMSTAR_CONFIGURATION=" + selected)
    print("ORIGINAL_MAP_MODIFIED=NO")
    print("SIMULATION_EXECUTED=NO")
    print("TASK24_04_03R_MAP_AUTOMATION_PASS")

try:
    main()
except Exception:
    traceback.print_exc()
    print("TASK24_04_03R_MAP_AUTOMATION_FAILED")
    raise