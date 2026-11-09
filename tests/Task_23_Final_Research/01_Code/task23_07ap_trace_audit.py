import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Map loading failed")

actors = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
).get_all_level_actors()

targets = [a for a in actors if a.get_actor_label() == LABEL]

if len(targets) != 1:
    raise RuntimeError(f"Expected 1 target, found {len(targets)}")

cube = targets[0]
mesh = cube.get_components_by_class(unreal.StaticMeshComponent)[0]

print("TASK23_AP_BEGIN")
print("TARGET_LOCATION:", cube.get_actor_location())
print("COLLISION_ENABLED:", mesh.get_collision_enabled())

start = unreal.Vector(1940, -2650, 250)
end = unreal.Vector(7000, -2650, 250)

# TRACE_TYPE_QUERY1 conventionally maps to Visibility
# under Unreal's default trace-channel configuration.
result = unreal.SystemLibrary.line_trace_multi(
    world,
    start,
    end,
    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
    False,
    [],
    unreal.DrawDebugTrace.NONE,
    True
)

hit_success, hits = result

print("TRACE_SUCCESS:", hit_success)
print("TRACE_HIT_COUNT:", len(hits))

for hit in hits:
    actor = hit.get_editor_property("hit_actor")
    distance = hit.get_editor_property("distance")

    print(
        "HIT_ACTOR:",
        actor.get_actor_label() if actor else "NONE",
        "DISTANCE_CM:",
        distance
    )

print("TASK23_AP_END")
