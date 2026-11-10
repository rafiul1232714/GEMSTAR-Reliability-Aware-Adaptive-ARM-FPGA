$ErrorActionPreference = "Stop"

$root = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_25_Final_Research"

$sourcePath = Join-Path $root "02_CSV_Data\task25_42_nis_source_comparison.csv"
$outputPath = Join-Path $root "02_CSV_Data\task25_43_validated_radar_nis.csv"

$rows = @(Import-Csv -LiteralPath $sourcePath)

if ($rows.Count -ne 24) {
    throw "ERROR: Expected 24 source observations; found $($rows.Count)"
}

$requiredColumns = @(
    "Frame",
    "Source_Radar_Status",
    "Source_Radar_NIS",
    "Audit_Radar_Status",
    "Audit_Radar_NIS",
    "Audit_Within_Gate"
)

foreach ($column in $requiredColumns) {
    if ($rows[0].PSObject.Properties.Name -notcontains $column) {
        throw "ERROR: Missing column $column"
    }
}

$culture = [System.Globalization.CultureInfo]::InvariantCulture
$style = [System.Globalization.NumberStyles]::Float

$validated = @(
    foreach ($row in $rows) {

        $frameNumber = [int]$row.Frame
        $statusText = [string]$row.Source_Radar_Status
        $rawNIS = ([string]$row.Source_Radar_NIS).Trim()

        $parsedValue = 0.0

        $parsedOK = [double]::TryParse(
            $rawNIS,
            $style,
            $culture,
            [ref]$parsedValue
        )

        $finite = $parsedOK -and
            -not [double]::IsNaN($parsedValue) -and
            -not [double]::IsInfinity($parsedValue)

        if ($finite -and $parsedValue -lt 0) {
            throw "ERROR: Negative NIS at frame $frameNumber"
        }

        if ($finite -and $statusText -ne "ACCEPTED") {
            throw "ERROR: Finite NIS without ACCEPTED status at frame $frameNumber"
        }

        if (-not $finite -and $statusText -eq "ACCEPTED") {
            throw "ERROR: ACCEPTED update without finite NIS at frame $frameNumber"
        }

        if ($statusText -ne [string]$row.Audit_Radar_Status) {
            throw "ERROR: Status mismatch at frame $frameNumber"
        }

        if ($finite) {

            $auditNIS = 0.0

            $auditOK = [double]::TryParse(
                [string]$row.Audit_Radar_NIS,
                $style,
                $culture,
                [ref]$auditNIS
            )

            if (-not $auditOK -or
                [double]::IsNaN($auditNIS) -or
                [double]::IsInfinity($auditNIS)) {
                throw "ERROR: Invalid audit NIS at frame $frameNumber"
            }

            if ([math]::Abs($parsedValue - $auditNIS) -gt 0.000001) {
                throw "ERROR: NIS disagreement at frame $frameNumber"
            }

            if ([string]$row.Audit_Within_Gate -ne "True") {
                throw "ERROR: Accepted update not marked within gate"
            }
        }

        [PSCustomObject]@{
            Frame = $frameNumber
            Radar_Status = $statusText
            NIS_Valid = $finite
            Radar_NIS = if ($finite) {
                $parsedValue.ToString("G17", $culture)
            } else {
                ""
            }
            Within_Recorded_Gate = if ($finite) {
                "True"
            } else {
                "NotEvaluated"
            }
        }
    }
)

$validRows = @($validated | Where-Object { $_.NIS_Valid -eq $true })
$invalidRows = @($validated | Where-Object { $_.NIS_Valid -eq $false })

$acceptedFrames = @($validRows | ForEach-Object { [int]$_.Frame } | Sort-Object)
$expectedFrames = @(245,286,326,816)

if ($validated.Count -ne 24) {
    throw "ERROR: Validated row count is $($validated.Count), expected 24"
}

if ($validRows.Count -ne 4 -or $invalidRows.Count -ne 20) {
    throw "ERROR: Expected 4 finite NIS and 20 unavailable NIS"
}

if (($acceptedFrames -join ",") -ne ($expectedFrames -join ",")) {
    throw "ERROR: Unexpected accepted Radar frames"
}

$groups = @($validated | Group-Object Radar_Status)

$counts = @{}
foreach ($g in $groups) {
    $counts[$g.Name] = $g.Count
}

if ($counts["ACCEPTED"] -ne 4 -or
    $counts["NOT_AVAILABLE"] -ne 19 -or
    $counts["INSUFFICIENT_RETURNS"] -ne 1) {
    throw "ERROR: Unexpected Radar status distribution"
}

# Write only after all checks have passed.
$validated | Export-Csv -LiteralPath $outputPath `
    -NoTypeInformation -Encoding UTF8

$check = @(Import-Csv -LiteralPath $outputPath)

if ($check.Count -ne 24) {
    throw "ERROR: Saved CSV row-count verification failed"
}

Write-Host ""
Write-Host "=== TASK 25.5G CORRECTED VALIDATION ==="
Write-Host ""

$validRows |
    Format-Table Frame, Radar_Status, Radar_NIS, Within_Recorded_Gate -AutoSize

Write-Host "TOTAL_OBSERVATIONS:" $validated.Count
Write-Host "VALID_NIS:" $validRows.Count
Write-Host "UNAVAILABLE_NIS:" $invalidRows.Count

Write-Host ""
Write-Host "RADAR STATUS DISTRIBUTION:"
$groups | Select-Object Name, Count | Format-Table -AutoSize

Write-Host "SAVED_CSV_ROWS:" $check.Count
Write-Host "TASK25_05G_NIS_VALIDATION_PASS"
Write-Host "Saved:" $outputPath
