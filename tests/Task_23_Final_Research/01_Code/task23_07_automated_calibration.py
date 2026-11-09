import unreal
from pathlib import Path
import csv
import traceback

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research"
)

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
TARGET_LABEL = "TASK23_CALIBRATION_TARGET_10M"

report_path = ROOT / "05_Raw_Data_References" / "task23_07_scene_report.txt"
csv_path = ROOT / "02_CSV_Data" / "task23_07_reference_target.csv"

report = []

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

    if not world:
        raise RuntimeError("Validation map failed to load")

    subsystem = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem
    )

    actors = list(subsystem.get_all_level_actors())

    report.append("TASK 23.7 - AUTOMATED CALIBRATION")
    report.append("Stage: SCENE_PREPARATION")
    report.append("Map: " + MAP)
    report.append("Actors before: " + str(len(actors)))
    report.append("")

    # ---------- Existing Radar inspection ----------

    radar = [
        a for a in actors
        if a.get_actor_label() ==
        "SimpleRadar_ConfiguredByBlueprint"
    ]

    if len(radar) != 1:
        raise RuntimeError(
            "Expected exactly one placed calibration Radar"
        )

    radar_actor = radar[0]
    radar_pos = radar_actor.get_actor_location()
    radar_rot = radar_actor.get_actor_rotation()

    report.append("RADAR_ACTOR_FOUND: YES")
    report.append(
        f"RADAR_POSITION_CM: {radar_pos.x:.2f},"
        f"{radar_pos.y:.2f},{radar_pos.z:.2f}"
    )
    report.append(
        f"RADAR_ROTATION_DEG: {radar_rot.pitch:.2f},"
        f"{radar_rot.yaw:.2f},{radar_rot.roll:.2f}"
    )

    # ---------- Manager and logger inventory ----------

    report.append("")
    report.append("RELEVANT_SCENE_ACTORS")

    for actor in actors:
        label = actor.get_actor_label()
        class_name = actor.get_class().get_name()

        combined = (label + " " + class_name).lower()

        if any(x in combined for x in [
            "radar", "lidar", "camera",
            "manager", "logger", "sensor"
        ]):
            report.append(f"{label} | {class_name}")

    # ---------- Known target geometry ----------

    # Target is placed 1000 cm along the Radar actor's
    # local forward vector, using its current orientation.

    forward = radar_rot.get_forward_vector()

    target_pos = unreal.Vector(
        radar_pos.x + forward.x * 1000.0,
        radar_pos.y + forward.y * 1000.0,
        radar_pos.z + forward.z * 1000.0
    )

    existing_targets = [
        a for a in actors
        if a.get_actor_label() == TARGET_LABEL
    ]

    if len(existing_targets) > 1:
        raise RuntimeError("Duplicate calibration targets detected")

    if existing_targets:
        target = existing_targets[0]
        report.append("TARGET_ACTION: UPDATED_EXISTING")
    else:
        target = subsystem.spawn_actor_from_class(
            unreal.StaticMeshActor,
            target_pos,
            unreal.Rotator(0, 0, 0)
        )
        if not target:
            raise RuntimeError("Target spawn failed")

        target.set_actor_label(TARGET_LABEL)
        report.append("TARGET_ACTION: CREATED_NEW")

    mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")

    if not mesh:
        raise RuntimeError("Basic Cube mesh unavailable")

    component = target.static_mesh_component
    component.set_static_mesh(mesh)

    target.set_actor_location(target_pos, False, False)
    target.set_actor_rotation(unreal.Rotator(0,0,0), False)

    # Unreal Basic Cube normally has 100 cm side length.
    # Scale 3 => nominal 300 cm sides.
    target.set_actor_scale3d(unreal.Vector(3,3,3))

    report.append("TARGET_LABEL: " + TARGET_LABEL)
    report.append(
        f"TARGET_POSITION_CM: {target_pos.x:.2f},"
        f"{target_pos.y:.2f},{target_pos.z:.2f}"
    )
    report.append("TARGET_SCALE: 3,3,3")
    report.append("TARGET_CENTER_DISTANCE_M: 10.0")
    report.append(
        "NOMINAL_FRONT_SURFACE_DISTANCE_M: 8.5"
    )

    # ---------- Reference manifest ----------

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "TargetLabel",
            "RadarXcm","RadarYcm","RadarZcm",
            "TargetXcm","TargetYcm","TargetZcm",
            "TargetScale",
            "CenterDistanceM",
            "ExpectedSurfaceRangeM",
            "ValidationStatus"
        ])

        writer.writerow([
            TARGET_LABEL,
            radar_pos.x, radar_pos.y, radar_pos.z,
            target_pos.x, target_pos.y, target_pos.z,
            3,
            10.0,
            8.5,
            "NOMINAL_GEOMETRY_ONLY"
        ])

    saved = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
        save_map_packages=True,
        save_content_packages=False
    )

    if saved is False:
        raise RuntimeError("Unreal reported that map save failed")

    report.append("")
    report.append("MAP_SAVE_RESULT: " + str(saved))
    report.append("STATUS: SCENE_PREPARED_NOT_RECORDED")
    report.append(
        "NOTE: Sensor publishing and target visibility "
        "have not been validated."
    )

except Exception:
    report.append("STATUS: FAILED")
    report.append(traceback.format_exc())
    raise

finally:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(report), encoding="utf-8"
    )

