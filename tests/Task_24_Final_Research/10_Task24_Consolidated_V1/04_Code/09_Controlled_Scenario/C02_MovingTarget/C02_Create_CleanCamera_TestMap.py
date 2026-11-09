import unreal
import os
import traceback

SOURCE = "/Game/Task24_C02/C02_DrivingPractiseAreaBrunswickMap"
DEST = "/Game/Task24_C02_CleanCamera/C02_CleanCamera_TestMap"

CONFIG = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_CleanCamera_Test_V1.ini"

RESULT = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_CleanCamera_Map_Result.txt"

lines = []

def record(message):
    lines.append(str(message))
    unreal.log(str(message))

try:
    record("C02_CLEAN_CAMERA_AUTOMATION_STARTED=YES")

    if not os.path.isfile(CONFIG):
        raise RuntimeError("Clean-Camera INI missing")

    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE):
        raise RuntimeError("Original C02 map missing")

    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError("Clean-Camera test map already exists")

    duplicated = unreal.EditorAssetLibrary.duplicate_asset(
        SOURCE, DEST
    )

    if not duplicated:
        raise RuntimeError("Could not duplicate C02 map")

    record("C02_ORIGINAL_MAP_PRESERVED=YES")
    record("C02_TEST_MAP_DUPLICATED=YES")

    subsystem = unreal.get_editor_subsystem(
        unreal.LevelEditorSubsystem
    )

    if subsystem is None:
        raise RuntimeError("LevelEditorSubsystem unavailable")

    subsystem.load_level(DEST)

    world = unreal.EditorLevelLibrary.get_editor_world()

    if world is None:
        raise RuntimeError("No editor world available")

    if world.get_name() != "C02_CleanCamera_TestMap":
        raise RuntimeError("Unexpected loaded map")

    settings = world.get_world_settings()

    if not isinstance(settings, unreal.GemstarWorldSettings):
        raise RuntimeError("Unexpected World Settings class")

    settings.set_editor_property(
        "gemstar_configuration",
        CONFIG
    )

    selected = settings.get_editor_property(
        "gemstar_configuration"
    )

    if os.path.normcase(os.path.normpath(selected)) != \
       os.path.normcase(os.path.normpath(CONFIG)):
        raise RuntimeError("Clean-Camera configuration assignment failed")

    record("C02_CLEAN_CONFIGURATION_ASSIGNED=YES")

    saved = subsystem.save_current_level()

    if not saved:
        raise RuntimeError("Clean-Camera test map save failed")

    record("C02_CLEAN_TEST_MAP_SAVED=YES")
    record("TASK24_06_04O_CLEAN_CAMERA_MAP_PASS")

except Exception:
    record("TASK24_06_04O_CLEAN_CAMERA_MAP_FAILED")
    record(traceback.format_exc())

finally:
    with open(RESULT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")