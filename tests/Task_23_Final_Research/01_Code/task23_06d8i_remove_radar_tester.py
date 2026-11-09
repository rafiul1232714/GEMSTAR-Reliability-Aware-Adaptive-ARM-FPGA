import unreal

map_path = "/Game/ResearchValidation/SensorFusionValidationMap"

if not unreal.EditorAssetLibrary.load_asset(map_path):
    raise RuntimeError("Validation map asset not found")

world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)

if not world:
    raise RuntimeError("Failed to load validation map")

actors = unreal.EditorLevelLibrary.get_all_level_actors()

matches = [
    actor for actor in actors
    if actor.get_actor_label() == "RadarSensorTester"
]

print("RADAR_TESTER_MATCHES_BEFORE:", len(matches))

if len(matches) != 1:
    raise RuntimeError(
        "Expected exactly one RadarSensorTester actor"
    )

removed = unreal.EditorLevelLibrary.destroy_actor(matches[0])

if not removed:
    raise RuntimeError("Failed to remove RadarSensorTester")

remaining = [
    actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()
    if actor.get_actor_label() == "RadarSensorTester"
]

print("RADAR_TESTER_MATCHES_AFTER:", len(remaining))

if remaining:
    raise RuntimeError("RadarSensorTester is still present")

saved = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
    save_map_packages=True,
    save_content_packages=False
)

print("SAVE_RESULT:", saved)
print("TASK_23_6D_8I_COMPLETE")
