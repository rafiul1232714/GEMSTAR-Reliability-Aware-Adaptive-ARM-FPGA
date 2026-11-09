import unreal
from pathlib import Path

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23_12_Camera_FogMOR20.ini"

EVIDENCE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
    r"\06_Research_Findings"
    r"\task23_12D_02B_before_restore.txt"
)

if EVIDENCE.exists():
    raise RuntimeError("Evidence already exists")

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if world is None:
    raise RuntimeError("Cannot load map")

actual = str(
    world.get_world_settings().get_editor_property(
        "gemstar_configuration"
    )
).replace("\\", "/")

if actual != EXPECTED:
    raise RuntimeError(
        "Unexpected active configuration: " + actual
    )

EVIDENCE.write_text(
    "MAP=" + MAP + "\n"
    + "EXPECTED=" + EXPECTED + "\n"
    + "ACTUAL=" + actual + "\n"
    + "STATUS=PASS\n",
    encoding="utf-8"
)

unreal.log("TASK23_12D_02B_CURRENT_MAP_VERIFIED")
