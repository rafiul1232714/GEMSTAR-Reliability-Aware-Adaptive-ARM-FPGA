import os
import traceback

RESULT = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C01_Clear_Stationary10m\task24_04_03S3_direct_preflight_result.txt"

lines = ["PYTHON_SCRIPT_STARTED=YES"]

try:
    import unreal

    source = "/ue_driving_practise_area_brunswick_map_feature/DrivingPractiseAreaBrunswickMap"

    lines.append("UNREAL_VERSION=" + str(unreal.SystemLibrary.get_engine_version()))

    lines.append(
        "EDITOR_ASSET_LIBRARY_AVAILABLE=" +
        str(hasattr(unreal, "EditorAssetLibrary"))
    )

    lines.append(
        "EDITOR_LEVEL_LIBRARY_AVAILABLE=" +
        str(hasattr(unreal, "EditorLevelLibrary"))
    )

    lines.append(
        "GEMSTAR_WORLD_SETTINGS_AVAILABLE=" +
        str(hasattr(unreal, "GemstarWorldSettings"))
    )

    if hasattr(unreal, "EditorAssetLibrary"):
        found = unreal.EditorAssetLibrary.does_asset_exist(source)
        lines.append("ORIGINAL_MAP_ASSET_FOUND=" + str(found))

    lines.append("PYTHON_EXECUTION_RESULT=PASS")

except Exception:
    lines.append("PYTHON_EXECUTION_RESULT=FAIL")
    lines.append(traceback.format_exc())

with open(RESULT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("\n".join(lines))