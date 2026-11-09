import unreal
import os
import traceback

CONFIG = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_Gemstar_Launch.ini"

RESULT = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_Configure_Existing_Map_Result.txt"

EXPECTED = "C02_DrivingPractiseAreaBrunswickMap"

lines = []

def record(message):
    lines.append(str(message))
    unreal.log(str(message))

try:
    record("C02_CONFIGURATION_SCRIPT_STARTED=YES")

    if not os.path.isfile(CONFIG):
        raise RuntimeError("C02 launch configuration missing")

    # The map must already be loaded when Unreal starts.
    # Do not call load_level() in this script.
    world = unreal.EditorLevelLibrary.get_editor_world()

    if world is None:
        raise RuntimeError("No editor world available")

    record("LOADED_WORLD=" + world.get_name())

    if world.get_name() != EXPECTED:
        raise RuntimeError(
            "Wrong map loaded; refusing modification"
        )

    settings = world.get_world_settings()

    if not isinstance(settings, unreal.GemstarWorldSettings):
        raise RuntimeError(
            "Unexpected World Settings class: " + str(type(settings))
        )

    record("WORLD_SETTINGS_VERIFIED=YES")

    previous = settings.get_editor_property(
        "gemstar_configuration"
    )

    record("PREVIOUS_CONFIGURATION=" + str(previous))

    settings.set_editor_property(
        "gemstar_configuration",
        CONFIG
    )

    selected = settings.get_editor_property(
        "gemstar_configuration"
    )

    if os.path.normcase(os.path.normpath(selected)) != \
       os.path.normcase(os.path.normpath(CONFIG)):
        raise RuntimeError("Configuration assignment failed")

    record("C02_CONFIGURATION_ASSIGNED=YES")

    subsystem = unreal.get_editor_subsystem(
        unreal.LevelEditorSubsystem
    )

    if subsystem is None:
        raise RuntimeError("LevelEditorSubsystem unavailable")

    saved = subsystem.save_current_level()

    record("SAVE_RETURN=" + str(bool(saved)))

    if not saved:
        raise RuntimeError("C02 map save failed")

    record("C02_MAP_CONFIGURATION_SAVED=YES")
    record("TASK24_05_02_C02_CONFIGURATION_PASS")

except Exception:
    record("TASK24_05_02_C02_CONFIGURATION_FAILED")
    record(traceback.format_exc())

finally:
    with open(RESULT, "x", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
