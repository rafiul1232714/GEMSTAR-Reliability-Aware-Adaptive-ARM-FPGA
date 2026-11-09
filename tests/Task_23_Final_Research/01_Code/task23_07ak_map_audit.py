import unreal

MAP = "/Game/ResearchValidation/SensorFusionValidationMap"
LABEL = "TASK23_CALIBRATION_TARGET_10M"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)

if not world:
    raise RuntimeError("Cannot load calibration map")

subsystem = unreal.get_editor_subsystem(
    unreal.EditorActorSubsystem
)

actors = subsystem.get_all_level_actors()

print("TASK23_AK_AUDIT_BEGIN")
print("ACTOR_COUNT:", len(actors))

targets = [
    actor for actor in actors
    if actor.get_actor_label() == LABEL
]

print("TARGET_COUNT:", len(targets))

if len(targets) != 1:
    raise RuntimeError(
        f"Expected exactly one calibration cube, found {len(targets)}"
    )

target = targets[0]

pos = target.get_actor_location()
rot = target.get_actor_rotation()
scale = target.get_actor_scale3d()
center, extent = target.get_actor_bounds(False)

print("TARGET_LABEL:", target.get_actor_label())
print("TARGET_CLASS:", target.get_class().get_name())
print("TARGET_LOCATION_CM:", pos.x, pos.y, pos.z)
print("TARGET_ROTATION:", rot.pitch, rot.yaw, rot.roll)
print("TARGET_SCALE:", scale.x, scale.y, scale.z)
print("TARGET_BOUNDS_CENTER_CM:", center.x, center.y, center.z)
print("TARGET_BOUNDS_EXTENT_CM:", extent.x, extent.y, extent.z)

print("TARGET_COMPONENTS:")

components = target.get_components_by_class(
    unreal.PrimitiveComponent
)

for component in components:
    print("COMPONENT:", component.get_name())
    try:
        print("COLLISION_ENABLED:", component.get_collision_enabled())
    except Exception as exc:
        print("COLLISION_QUERY_UNAVAILABLE:", exc)

print("NEARBY_ACTORS_ON_REFERENCE_AXIS:")

# Proposed Radar position: X=1940, Y=-2650, Z=250 cm.
# Print nearby actors whose bounding boxes overlap
# the approximate forward corridor X=1940..3140.
for actor in actors:
    if actor == target:
        continue

    try:
        c, e = actor.get_actor_bounds(False)

        overlaps_x = c.x + e.x >= 1940 and c.x - e.x <= 3140
        overlaps_y = c.y + e.y >= -2800 and c.y - e.y <= -2500
        overlaps_z = c.z + e.z >= 100 and c.z - e.z <= 400

        if overlaps_x and overlaps_y and overlaps_z:
            print(
                "CORRIDOR_ACTOR:",
                actor.get_actor_label(),
                "CENTER:", c.x, c.y, c.z,
                "EXTENT:", e.x, e.y, e.z
            )

    except Exception:
        pass

print("TASK23_AK_AUDIT_END")
