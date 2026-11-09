import unreal
from pathlib import Path

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23_12_Camera_Clear.ini"

EVIDENCE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
    r"\06_Research_Findings"
    r"\task23_12A_clear_map_verification.txt"
)

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if world is None:
    raise RuntimeError("Map reload failed")

actual = str(
    world.get_world_settings().get_editor_property(
        "gemstar_configuration"
    )
).replace("\\", "/")

if actual != EXPECTED:
    raise RuntimeError(
        "Wrong saved map configuration: " + actual
    )

EVIDENCE.write_text(
    "MAP=" + MAP + "\n"
    + "EXPECTED=" + EXPECTED + "\n"
    + "ACTUAL=" + actual + "\n"
    + "STATUS=PASS\n",
    encoding="utf-8"
)

unreal.log("TASK23_12A_CLEAR_MAP_INDEPENDENT_PASS")
