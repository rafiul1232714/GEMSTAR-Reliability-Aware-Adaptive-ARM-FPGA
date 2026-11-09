import unreal
import os
import traceback

SOURCE = "/Game/Task24_C01/C01_DrivingPractiseAreaBrunswickMap"
DEST = "/Game/Task24_C02/C02_DrivingPractiseAreaBrunswickMap"

CONFIG = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_Gemstar_Launch.ini"

RESULT = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_Map_Configuration_Result.txt"

lines = []

def record(message):
    lines.append(str(message))
    unreal.log(str(message))

try:
    record("C02_AUTOMATION_STARTED=YES")

    if not os.path.isfile(CONFIG):
        raise RuntimeError("C02 launch configuration missing")

    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE):
        raise RuntimeError("C01 source map missing")

    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError("C02 destination map already exists")

    duplicated = unreal.EditorAssetLibrary.duplicate_asset(
        SOURCE, DEST
    )

    if not duplicated:
        raise RuntimeError("C02 map duplication failed")

    if not unreal.EditorAssetLibrary.save_asset(
        DEST, only_if_is_dirty=False
    ):
        raise RuntimeError("Could not save duplicated C02 map")

    record("C02_MAP_DUPLICATED=YES")

    subsystem = unreal.get_editor_subsystem(
        unreal.LevelEditorSubsystem
    )

    if subsystem is None:
        raise RuntimeError("LevelEditorSubsystem unavailable")

    subsystem.load_level(DEST)

    world = unreal.EditorLevelLibrary.get_editor_world()

    if world is None:
        raise RuntimeError("No editor world loaded")

    if world.get_name() != "C02_DrivingPractiseAreaBrunswickMap":
        raise RuntimeError("Wrong map loaded: " + world.get_name())

    settings = world.get_world_settings()

    if not isinstance(settings, unreal.GemstarWorldSettings):
        raise RuntimeError("Unexpected World Settings class")

    record("PREVIOUS_CONFIG=" + str(
        settings.get_editor_property("gemstar_configuration")
    ))

    settings.set_editor_property(
        "gemstar_configuration", CONFIG
    )

    selected = settings.get_editor_property(
        "gemstar_configuration"
    )

    if os.path.normcase(os.path.normpath(selected)) != \
       os.path.normcase(os.path.normpath(CONFIG)):
        raise RuntimeError("C02 configuration verification failed")

    record("C02_CONFIGURATION_ASSIGNED=YES")

    saved = subsystem.save_current_level()

    if not saved:
        raise RuntimeError("C02 map save failed")

    record("C02_MAP_SAVED=YES")
    record("TASK24_05_02_C02_MAP_CREATION_PASS")

except Exception:
    record("TASK24_05_02_C02_MAP_CREATION_FAILED")
    record(traceback.format_exc())

finally:
    with open(RESULT, "x", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
