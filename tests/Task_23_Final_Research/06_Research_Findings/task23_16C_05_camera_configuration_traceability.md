# Task 23.16.C.5 - Camera Configuration Traceability

## Purpose

Resolve two historical configuration filenames referenced in
task23_12D_04_final_camera_research_report.md.

## Historical filenames and archived candidates

| Historical report reference | Archived candidate |
|---|---|
| Task23_12_Camera_FogMOR100.ini | 04_Configurations/task23_12_camera_fog100.ini |
| Task23_12_Camera_FogMOR20.ini | 04_Configurations/task23_12_camera_fog20.ini |

These mappings are supported by the weather configuration settings,
but filename and parameter agreement alone do not establish that
the archived files are byte-identical to the runtime-loaded originals.

## Archived weather settings

| Configuration | WeatherEffectEnabled | ActiveWeatherType | MOR (m) | PrecipitationIntensity |
|---|---|---|---|---|
| task23_12_camera_clear.ini | true | Clear | 100.0 | 0.0 |
| task23_12_camera_fog100.ini | true | Fog | 100.0 | 0.0 |
| task23_12_camera_fog20.ini | true | Fog | 20.0 | 0.0 |

External weather input is commented out in these configurations.

## Sensor configuration consistency

Camera sensor1:
- Mount: SensorPlatform_1
- Mounting position: (70, 0, 160) cm
- Horizontal field of view: 90 degrees

## Evidence interpretation

The three archived files provide configuration-level evidence
for the intended Clear, Fog MOR100 and Fog MOR20 scenarios.

The original Camera research report also records runtime weather
observations. Those observations must remain distinguished from
configuration-file contents.

No independent byte-for-byte comparison against the historical
runtime-loaded files was performed in Task 23.16.C.5.

## Archive preservation

Original INI configurations and original research reports remain
unchanged. This note resolves the naming discrepancy for archive
navigation and documentation purposes.