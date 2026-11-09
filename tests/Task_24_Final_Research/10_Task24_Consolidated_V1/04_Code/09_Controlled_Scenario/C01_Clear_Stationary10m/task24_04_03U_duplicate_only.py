import unreal
import os
import traceback

SOURCE = "/ue_driving_practise_area_brunswick_map_feature/DrivingPractiseAreaBrunswickMap"
DEST = "/Game/Task24_C01/C01_DrivingPractiseAreaBrunswickMap"

RESULT = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C01_Clear_Stationary10m\task24_04_03U_result.txt"

lines = []

def record(message):
    lines.append(message)
    print(message, flush=True)

try:
    record("PYTHON_STARTED=YES")

    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE):
        raise RuntimeError("Original map asset unavailable")

    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError("Destination asset already exists")

    duplicated = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST)
    record("DUPLICATION_RETURN=" + str(bool(duplicated)))

    if not duplicated:
        raise RuntimeError("Asset duplication returned failure")

    saved = unreal.EditorAssetLibrary.save_asset(
        DEST, only_if_is_dirty=False
    )

    record("SAVE_RETURN=" + str(bool(saved)))

    if not saved:
        raise RuntimeError("Duplicated map could not be saved")

    record("C01_ASSET_EXISTS=" + str(
        unreal.EditorAssetLibrary.does_asset_exist(DEST)
    ))

    record("MAP_LOADED_BY_SCRIPT=NO")
    record("TASK24_04_03U_DUPLICATION_SCRIPT_PASS")

except Exception:
    record("TASK24_04_03U_DUPLICATION_SCRIPT_FAILED")
    record(traceback.format_exc())

finally:
    with open(RESULT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")