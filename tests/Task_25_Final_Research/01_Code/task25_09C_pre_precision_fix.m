%% TASK 25.9C - INDEPENDENT MATLAB NUMERICAL CROSS-CHECK
% Recompute research statistics directly from source CSV files.
% Compare against the Python reference from Task 25.9B.
% Numerical agreement does not prove physical perception accuracy.

clearvars; close all; clc;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_25_Final_Research';
dataDir = fullfile(root, '02_CSV_Data');
findDir = fullfile(root, '06_Research_Findings');

P = readtable(fullfile(dataDir, ...
    'task25_80_python_numerical_reference.csv'), ...
    'TextType', 'string');

D = readtable(fullfile(dataDir, ...
    'task25_65_fallback_decisions.csv'), ...
    'TextType', 'string');

A = readtable(fullfile(dataDir, ...
    'task25_33_association_distance_analysis.csv'), ...
    'TextType', 'string');

E = readtable(fullfile(dataDir, ...
    'task25_40_ekf_consistency_audit.csv'), ...
    'TextType', 'string');

N = readtable(fullfile(dataDir, ...
    'task25_43_validated_radar_nis.csv'), ...
    'TextType', 'string');

G = readtable(fullfile(dataDir, ...
    'task25_73_quality_gate_specification.csv'), ...
    'TextType', 'string');

assert(height(P) == 18, 'Expected 18 Python metrics');
assert(height(D) == 168, 'Expected 168 decisions');
assert(height(A) == 162, 'Expected 162 associations');
assert(height(E) == 23, 'Expected 23 EKF residual rows');
assert(height(N) == 24, 'Expected 24 Radar NIS rows');
assert(height(G) == 6, 'Expected six quality gates');

%% 1. Fallback counts

modes = strtrim(string(D.controller_mode));

validModes = [
    "NORMAL_CANDIDATE"
    "DEGRADED_CANDIDATE"
    "HOLD_OR_ALERT"
];

assert(all(ismember(modes, validModes)), ...
    'Unknown fallback controller mode');

assert(all(strtrim(string(D.quality_authorization)) == ...
    "UNVERIFIED"), 'Unexpected quality authorization');

fallbackTotal = height(D);
fallbackNormal = nnz(modes == "NORMAL_CANDIDATE");
fallbackDegraded = nnz(modes == "DEGRADED_CANDIDATE");
fallbackHold = nnz(modes == "HOLD_OR_ALERT");

assert(fallbackNormal + fallbackDegraded + ...
    fallbackHold == fallbackTotal, 'Fallback counts mismatch');

%% 2. LiDAR and Radar association distances

sensor = strtrim(string(A.Sensor));
status = strtrim(string(A.Status));

assert(all(ismember(sensor, ["LiDAR", "Radar"])), ...
    'Unexpected sensor in association table');

lidarMask = sensor == "LiDAR" & status == "MATCHED";
radarMask = sensor == "Radar" & ...
    status == "PROVISIONAL_RADAR_SPATIAL_MATCH";

associationLidarCount = nnz(lidarMask);
associationRadarCount = nnz(radarMask);

lidarDistances = str2double(string(A.Distance_m(lidarMask)));
radarDistances = str2double(string(A.Distance_m(radarMask)));

assert(~isempty(lidarDistances) && ~isempty(radarDistances), ...
    'Missing association distance observations');

assert(all(isfinite(lidarDistances)) && ...
    all(isfinite(radarDistances)), ...
    'Nonfinite association distance');

assert(all(lidarDistances >= 0) && ...
    all(radarDistances >= 0), ...
    'Negative association distance');

lidarMeanDistance = mean(lidarDistances);
radarMeanGap = mean(radarDistances);

%% 3. EKF residual and sigma calculations

lidarResidual = str2double(string(E.LiDAR_ResidualX_m));
radarResidual = str2double(string(E.Radar_ResidualX_m));

lidarSigma = str2double(string(E.LiDAR_SigmaX_m));
radarSigma = str2double(string(E.Radar_SigmaX_m));

assert(all(isfinite(lidarResidual)) && ...
    all(isfinite(radarResidual)), 'Nonfinite residual');

assert(all(isfinite(lidarSigma)) && ...
    all(isfinite(radarSigma)), 'Nonfinite sigma');

assert(all(lidarSigma > 0) && all(radarSigma > 0), ...
    'Nonpositive reported sigma');

lidarMeanResidual = mean(lidarResidual);
radarMeanResidual = mean(radarResidual);

lidarMeanSigma = mean(lidarSigma);
radarMeanSigma = mean(radarSigma);

%% 4. Radar NIS validation

nisValidText = lower(strtrim(string(N.NIS_Valid)));

assert(all(ismember(nisValidText, ...
    ["true", "false", "1", "0"])), ...
    'Unexpected Radar NIS validity flag');

validNIS = nisValidText == "true" | nisValidText == "1";
nisValues = str2double(string(N.Radar_NIS));

assert(all(isfinite(nisValues(validNIS))), ...
    'Valid Radar NIS contains nonfinite values');

assert(all(~isfinite(nisValues(~validNIS))), ...
    'Unavailable Radar NIS contains finite values');

nisStatuses = strtrim(string(N.Radar_Status));
assert(all(nisStatuses(validNIS) == "ACCEPTED"), ...
    'Valid Radar NIS is not accepted');

acceptedNIS = nisValues(validNIS);

assert(~isempty(acceptedNIS), ...
    'No accepted finite Radar NIS');

radarNISMean = mean(acceptedNIS);

%% 5. Quality gate counts

gateIDs = strtrim(string(G.GateID));
assert(numel(unique(gateIDs)) == 6, ...
    'Duplicate quality gate ID');

qualityAuthorization = strtrim(string(G.Authorization));

qualityGateTotal = height(G);
qualityGateAuthorized = nnz(qualityAuthorization == "PASS");

%% 6. Independently calculated metric table

metricNames = [
    "fallback_total"
    "fallback_normal"
    "fallback_degraded"
    "fallback_hold"
    "association_lidar_matched"
    "association_radar_provisional"
    "association_lidar_mean_distance_m"
    "association_radar_mean_gap_m"
    "ekf_gt_rows"
    "ekf_lidar_mean_signed_residual_x_m"
    "ekf_radar_mean_signed_residual_x_m"
    "ekf_lidar_mean_sigma_x_m"
    "ekf_radar_mean_sigma_x_m"
    "radar_nis_rows"
    "radar_nis_finite_accepted"
    "radar_nis_mean_accepted"
    "quality_gate_total"
    "quality_gate_authorized"
];

matlabValues = [
    fallbackTotal
    fallbackNormal
    fallbackDegraded
    fallbackHold
    associationLidarCount
    associationRadarCount
    lidarMeanDistance
    radarMeanGap
    height(E)
    lidarMeanResidual
    radarMeanResidual
    lidarMeanSigma
    radarMeanSigma
    height(N)
    numel(acceptedNIS)
    radarNISMean
    qualityGateTotal
    qualityGateAuthorized
];

assert(numel(metricNames) == 18);
assert(numel(matlabValues) == 18);
assert(all(isfinite(matlabValues)), ...
    'MATLAB produced a nonfinite metric');

%% 7. Compare independent MATLAB and Python results

pythonNames = strtrim(string(P.Metric));
pythonValues = str2double(string(P.PythonValue));

assert(numel(unique(pythonNames)) == 18, ...
    'Duplicate Python metric names');

assert(all(isfinite(pythonValues)), ...
    'Invalid Python numerical reference');

[found, locations] = ismember(metricNames, pythonNames);

assert(all(found), 'Python reference is missing a metric');
assert(numel(unique(locations)) == 18, ...
    'Python metric mapping is ambiguous');

pythonOrdered = pythonValues(locations);

absoluteDifference = abs(matlabValues - pythonOrdered);

absoluteTolerance = 1e-10;
relativeTolerance = 1e-9;

allowedTolerance = max( ...
    absoluteTolerance * ones(size(matlabValues)), ...
    relativeTolerance * max(abs(matlabValues), abs(pythonOrdered)) ...
);

countMetrics = [
    "fallback_total"
    "fallback_normal"
    "fallback_degraded"
    "fallback_hold"
    "association_lidar_matched"
    "association_radar_provisional"
    "ekf_gt_rows"
    "radar_nis_rows"
    "radar_nis_finite_accepted"
    "quality_gate_total"
    "quality_gate_authorized"
];

countMask = ismember(metricNames, countMetrics);

% Counts must match exactly, even when floating-point
% metrics are allowed small numerical differences.
allowedTolerance(countMask) = 0;

passed = absoluteDifference <= allowedTolerance;

status = strings(numel(metricNames), 1);
status(passed) = "PASS";
status(~passed) = "FAIL";

results = table( ...
    metricNames, ...
    pythonOrdered, ...
    matlabValues, ...
    absoluteDifference, ...
    allowedTolerance, ...
    status, ...
    'VariableNames', { ...
        'Metric', ...
        'PythonValue', ...
        'MATLABValue', ...
        'AbsoluteDifference', ...
        'AllowedTolerance', ...
        'Agreement' ...
    } ...
);

outputCSV = fullfile(dataDir, ...
    'task25_81_matlab_numerical_crosscheck.csv');

writetable(results, outputCSV);

assert(isfile(outputCSV), ...
    'Cross-check CSV was not saved');

saved = readtable(outputCSV, 'TextType', 'string');

assert(height(saved) == 18, ...
    'Saved cross-check has wrong row count');

%% 8. Save findings

reportPath = fullfile(findDir, ...
    'task25_82_matlab_crosscheck_findings.txt');

fid = fopen(reportPath, 'w');
assert(fid > 0, 'Cannot create MATLAB findings report');

fprintf(fid, 'TASK 25.9C - PYTHON MATLAB CROSS-CHECK\n');
fprintf(fid, 'METRICS_COMPARED: %d\n', numel(metricNames));
fprintf(fid, 'COUNT_METRICS_EXACT: %d\n', nnz(countMask));
fprintf(fid, 'NUMERICAL_METRICS: %d\n', nnz(~countMask));
fprintf(fid, 'ABSOLUTE_TOLERANCE: %.12g\n', absoluteTolerance);
fprintf(fid, 'RELATIVE_TOLERANCE: %.12g\n', relativeTolerance);
fprintf(fid, 'METRICS_PASSED: %d\n', nnz(passed));
fprintf(fid, 'METRICS_FAILED: %d\n', nnz(~passed));
fprintf(fid, 'MAX_ABSOLUTE_DIFFERENCE: %.17g\n', ...
    max(absoluteDifference));
fprintf(fid, 'QUALITY_AUTHORIZATION: UNVERIFIED\n');
fprintf(fid, 'ENERGY_SAVINGS_CLAIMED: NO\n');

if all(passed)
    fprintf(fid, 'CROSS_LANGUAGE_NUMERICAL_AGREEMENT: PASS\n');
else
    fprintf(fid, 'CROSS_LANGUAGE_NUMERICAL_AGREEMENT: FAIL\n');
end

fclose(fid);

%% 9. Display the results

fprintf('\n=== TASK 25.9C MATLAB NUMERICAL CROSS-CHECK ===\n');

disp(results);

fprintf('METRICS_COMPARED: %d\n', numel(metricNames));
fprintf('METRICS_PASSED: %d\n', nnz(passed));
fprintf('METRICS_FAILED: %d\n', nnz(~passed));
fprintf('COUNT_METRICS_EXACT: %d\n', nnz(countMask));
fprintf('MAX_ABSOLUTE_DIFFERENCE: %.17g\n', ...
    max(absoluteDifference));

if ~all(passed)
    error('TASK25_09C_CROSS_LANGUAGE_COMPARISON_FAILED');
end

fprintf('CROSS_LANGUAGE_NUMERICAL_AGREEMENT: PASS\n');
fprintf('QUALITY_AUTHORIZATION: UNVERIFIED\n');
fprintf('TASK25_09C_MATLAB_CROSSCHECK_PASS\n');
fprintf('CSV: %s\n', outputCSV);
fprintf('REPORT: %s\n', reportPath);
