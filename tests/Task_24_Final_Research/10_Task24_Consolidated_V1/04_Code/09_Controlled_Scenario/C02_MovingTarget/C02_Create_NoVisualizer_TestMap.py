import unreal
import os
import traceback

SOURCE = "/Game/Task24_C02/C02_DrivingPractiseAreaBrunswickMap"
DEST = "/Game/Task24_C02_NoVisualizer/C02_NoVisualizer_TestMap"

CONFIG = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_NoVisualizer_Test_V2.ini"

RESULT = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_NoVisualizer_Map_Result.txt"

lines = []

def record(value):
    lines.append(str(value))
    unreal.log(str(value))

try:
    record("V2_MAP_AUTOMATION_STARTED=YES")

    if not os.path.isfile(CONFIG):
        raise RuntimeError("V2 configuration missing")

    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE):
        raise RuntimeError("Original C02 map missing")

    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError("V2 map already exists")

    duplicated = unreal.EditorAssetLibrary.duplicate_asset(
        SOURCE, DEST
    )

    if not duplicated:
        raise RuntimeError("V2 map duplication failed")

    subsystem = unreal.get_editor_subsystem(
        unreal.LevelEditorSubsystem
    )

    if subsystem is None:
        raise RuntimeError("LevelEditorSubsystem unavailable")

    subsystem.load_level(DEST)

    world = unreal.EditorLevelLibrary.get_editor_world()

    if world is None:
        raise RuntimeError("Editor world unavailable")

    if world.get_name() != "C02_NoVisualizer_TestMap":
        raise RuntimeError("Unexpected map loaded")

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
        raise RuntimeError("V2 configuration assignment failed")

    record("V2_CONFIGURATION_ASSIGNED=YES")

    saved = subsystem.save_current_level()

    if not saved:
        raise RuntimeError("V2 map save failed")

    record("V2_MAP_SAVED=YES")
    record("ORIGINAL_C02_MAP_PRESERVED=YES")
    record("TASK24_06_04AL_V2_MAP_PASS")

except Exception:
    record("TASK24_06_04AL_V2_MAP_FAILED")
    record(traceback.format_exc())

finally:
    with open(RESULT, "x", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")