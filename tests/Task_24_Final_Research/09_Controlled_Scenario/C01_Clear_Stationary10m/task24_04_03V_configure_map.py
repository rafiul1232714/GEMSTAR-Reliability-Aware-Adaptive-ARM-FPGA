import unreal
import os
import traceback

RESULT = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C01_Clear_Stationary10m\task24_04_03V_result.txt"

CONFIG = r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C01_Clear_Stationary10m\C01_Gemstar_Launch.ini"

EXPECTED = "C01_DrivingPractiseAreaBrunswickMap"
lines = []

def record(message):
    lines.append(message)
    unreal.log(message)

try:
    record("PYTHON_STARTED=YES")

    world = unreal.EditorLevelLibrary.get_editor_world()

    if world is None:
        raise RuntimeError("No editor world available")

    name = world.get_name()
    record("LOADED_WORLD=" + name)

    if name != EXPECTED:
        raise RuntimeError(
            "Incorrect map loaded; refusing changes: " + name
        )

    settings = world.get_world_settings()

    if not isinstance(settings, unreal.GemstarWorldSettings):
        raise RuntimeError(
            "Unexpected World Settings class: " + str(type(settings))
        )

    record("WORLD_SETTINGS_CLASS_VERIFIED=YES")

    current = settings.get_editor_property("gemstar_configuration")
    record("PREVIOUS_CONFIGURATION=" + str(current))

    settings.set_editor_property("gemstar_configuration", CONFIG)

    selected = settings.get_editor_property("gemstar_configuration")

    if os.path.normcase(os.path.normpath(selected)) != os.path.normcase(os.path.normpath(CONFIG)):
        raise RuntimeError("C01 configuration property mismatch")

    record("C01_CONFIGURATION_ASSIGNED=YES")

    subsystem = unreal.get_editor_subsystem(
        unreal.LevelEditorSubsystem
    )

    if subsystem is None:
        raise RuntimeError("LevelEditorSubsystem unavailable")

    saved = subsystem.save_current_level()
    record("SAVE_RETURN=" + str(bool(saved)))

    if not saved:
        raise RuntimeError("Copied map save failed")

    record("C01_MAP_CONFIGURATION_SAVED=YES")
    record("TASK24_04_03V_MAP_CONFIGURATION_PASS")

except Exception:
    record("TASK24_04_03V_MAP_CONFIGURATION_FAILED")
    record(traceback.format_exc())

finally:
    with open(RESULT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")