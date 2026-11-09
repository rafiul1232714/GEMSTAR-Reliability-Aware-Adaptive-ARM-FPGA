import unreal
from pathlib import Path

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
EXPECTED = "Simulation/Task23_12_Camera_FogMOR100.ini"

EVIDENCE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
    r"\06_Research_Findings"
    r"\task23_12B_fog100_map_set_evidence.txt"
)

if EVIDENCE.exists():
    raise RuntimeError("Evidence file already exists")

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if world is None:
    raise RuntimeError("Validation map not found")

settings = world.get_world_settings()

original = str(
    settings.get_editor_property("gemstar_configuration")
)

settings.set_editor_property(
    "gemstar_configuration",
    EXPECTED
)

if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
    raise RuntimeError("Map save failed")

EVIDENCE.write_text(
    "MAP=" + MAP + "\n"
    + "PREVIOUS=" + original + "\n"
    + "EXPECTED=" + EXPECTED + "\n"
    + "SAVE_STATUS=PASS\n",
    encoding="utf-8"
)

unreal.log("TASK23_12B_FOG100_MAP_SET_PASS")
