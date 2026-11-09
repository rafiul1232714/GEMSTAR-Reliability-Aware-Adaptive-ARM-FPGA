import unreal
from pathlib import Path

output = Path(r"E:/GEMSTAR_Project/sensor-health-monitor/tests/Task_24_Final_Research/09_Controlled_Scenario/C01_Clear_Stationary10m/Validation/C01_Collision_Responses_V2.txt")
lines = []

def report(name, value):
    lines.append(str(name) + "=" + str(value))

asset_path = "/ue_vehicle_feature/Blueprints/Vehicles/BP_Small_Car"

report("BLUEPRINT", asset_path)

bp = unreal.EditorAssetLibrary.load_asset(asset_path)

if bp is None:
    raise RuntimeError("Blueprint not found")

cls = bp.generated_class()

if cls is None:
    raise RuntimeError("Blueprint generated class missing")

cdo = unreal.get_default_object(cls)

components = cdo.get_components_by_class(
    unreal.PrimitiveComponent
)

report("PRIMITIVE_COMPONENTS", len(components))

for component in components:
    report("COMPONENT", component.get_name())

    checks = {
        "COLLISION_ENABLED": "get_collision_enabled",
        "COLLISION_PROFILE": "get_collision_profile_name",
        "VISIBILITY_RESPONSE": "get_collision_response_to_channel",
        "OBJECT_TYPE": "get_collision_object_type"
    }

    for label, method_name in checks.items():
        try:
            method = getattr(component, method_name)

            if label == "VISIBILITY_RESPONSE":
                value = method(
                    unreal.CollisionChannel.ECC_VISIBILITY
                )
            else:
                value = method()

            report(label, value)

        except Exception as exc:
            report(label, "UNAVAILABLE: " + str(exc))

    try:
        report(
            "GENERATE_OVERLAP_EVENTS",
            component.get_editor_property(
                "generate_overlap_events"
            )
        )
    except Exception as exc:
        report("GENERATE_OVERLAP_EVENTS", str(exc))

output.write_text("\n".join(lines), encoding="utf-8")
