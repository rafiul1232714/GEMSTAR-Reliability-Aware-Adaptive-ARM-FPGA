import unreal
import traceback

MAP = "/Game/Task24_C02_CleanCamera/C02_CleanCamera_TestMap"

lines = []

def record(value):
    lines.append(str(value))
    unreal.log(str(value))

try:
    record("TASK24_06_04Z_RUNTIME_AUDIT_STARTED")

    subsystem = unreal.get_editor_subsystem(
        unreal.LevelEditorSubsystem
    )

    subsystem.load_level(MAP)

    world = unreal.EditorLevelLibrary.get_editor_world()

    if world is None:
        raise RuntimeError("Editor world unavailable")

    settings = world.get_world_settings()

    record("MAP=" + world.get_name())
    record("CONFIG=" + str(
        settings.get_editor_property("gemstar_configuration")
    ))

    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    record("EDITOR_ACTOR_COUNT=" + str(len(actors)))

    for actor in actors:
        name = actor.get_name()
        class_name = actor.get_class().get_name()

        if any(key in (name + " " + class_name).lower()
               for key in ("visualizer", "lidar", "radar", "camera")):
            record("ACTOR=" + name + " CLASS=" + class_name)

    record("EDITOR_WORLD_INSPECTION_COMPLETE")
    record("NOTE=Runtime-spawned actors require a separate Play-session inspection")
    record("TASK24_06_04Z_RUNTIME_AUDIT_PASS")

except Exception:
    record("TASK24_06_04Z_RUNTIME_AUDIT_FAILED")
    record(traceback.format_exc())

with open(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_Visualizer_Audit_Result.txt", "x", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

for line in lines:
    print(line)