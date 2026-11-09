import unreal
from pathlib import Path

result = Path(r"E:/GEMSTAR_Project/sensor-health-monitor/tests/Task_24_Final_Research/09_Controlled_Scenario/C01_Clear_Stationary10m/Validation/C01_Vehicle_Collision_Result.txt")

lines = []

def report(text):
    lines.append(str(text))

report("=== C01 VEHICLE COLLISION INSPECTION ===")

registry = unreal.AssetRegistryHelpers.get_asset_registry()

assets = registry.get_assets_by_class(
    unreal.TopLevelAssetPath("/Script/Engine", "Blueprint"),
    True
)

matches = [
    asset for asset in assets
    if str(asset.asset_name) == "BP_Small_Car"
]

report("MATCHING_BLUEPRINTS=" + str(len(matches)))

for asset in matches:
    path = str(asset.package_name)

    report("BLUEPRINT_PATH=" + path)

    bp = unreal.EditorAssetLibrary.load_asset(path)

    if not bp:
        report("LOAD_FAILED=" + path)
        continue

    cls = bp.generated_class()

    if not cls:
        report("GENERATED_CLASS_MISSING=" + path)
        continue

    cdo = unreal.get_default_object(cls)

    components = cdo.get_components_by_class(
        unreal.PrimitiveComponent
    )

    report("PRIMITIVE_COMPONENTS=" + str(len(components)))

    for component in components:
        report("COMPONENT=" + component.get_name())

        for name in (
            "collision_enabled",
            "collision_profile_name",
            "collision_trace_flag",
            "generate_overlap_events"
        ):
            try:
                value = component.get_editor_property(name)
                report(name.upper() + "=" + str(value))
            except Exception:
                report(name.upper() + "=NOT_EXPOSED")

result.parent.mkdir(parents=True, exist_ok=True)
result.write_text("\n".join(lines), encoding="utf-8")
