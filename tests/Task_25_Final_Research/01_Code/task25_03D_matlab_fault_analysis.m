%% TASK 25.3D - MATLAB Fault Analysis (Corrected Version)
% GEMSTAR Reliability-Aware Adaptive ARM-FPGA Research
% Reads validated CSV data and automatically saves figures.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_25_Final_Research';

dataDir = fullfile(root, '02_CSV_Data');
plotDir = fullfile(root, '04_Plots');
findingsDir = fullfile(root, '06_Research_Findings');

if ~exist(plotDir, 'dir')
    mkdir(plotDir);
end

if ~exist(findingsDir, 'dir')
    mkdir(findingsDir);
end

%% STEP 1 - Read datasets

S = readtable( ...
    fullfile(dataDir, 'task25_fault_summary.csv'), ...
    'TextType', 'string');

A = readtable( ...
    fullfile(dataDir, 'task25_26_fault_consistency_validation.csv'), ...
    'TextType', 'string');

names = [
    "baseline"
    "radar_dropout"
    "camera_dropout"
    "lidar_every4_dropout"
    "radar_bias_6mps"
    "camera_bias_0p20rad"
    "joint_dropout"
];

labels = {
    'Baseline'
    'Radar dropout'
    'Camera dropout'
    'LiDAR periodic dropout'
    'Radar +6 m/s'
    'Camera +0.20 rad'
    'Joint dropout'
};

assert(height(S) == 7, 'Expected 7 summary scenarios');
assert(height(A) == 7, 'Expected 7 audit scenarios');

%% STEP 2 - Match scenario order

[okS, idxS] = ismember(names, string(S.scenario));
[okA, idxA] = ismember(names, string(A.Scenario));

assert(all(okS) && numel(unique(idxS)) == 7, ...
    'Summary scenario names do not match');

assert(all(okA) && numel(unique(idxA)) == 7, ...
    'Audit scenario names do not match');

S = S(idxS, :);
A = A(idxA, :);

%% STEP 3 - Correct CSV data types

% Convert CSV numeric columns safely.
S.samples = str2double(string(S.samples));
S.gt_evaluation_samples = ...
    str2double(string(S.gt_evaluation_samples));

S.mean_gt_center_error_m = ...
    str2double(string(S.mean_gt_center_error_m));

S.rmse_gt_center_m = ...
    str2double(string(S.rmse_gt_center_m));

S.max_gt_center_error_m = ...
    str2double(string(S.max_gt_center_error_m));

numericAuditColumns = {
    'LiDAR_Dropped'
    'Radar_Accepted'
    'Radar_Rejected'
    'Camera_Accepted'
    'Camera_Rejected'
};

for k = 1:numel(numericAuditColumns)
    column = numericAuditColumns{k};
    A.(column) = str2double(string(A.(column)));
end

% Correct True/False interpretation.
matchedFrames = strcmpi( ...
    strtrim(string(A.MatchedFrames)), 'true');

auditMatches = strcmpi( ...
    strtrim(string(A.AuditMatches)), 'true');

assert(all(matchedFrames), ...
    'Frame alignment verification failed');

assert(all(auditMatches), ...
    'Fault consistency verification failed');

assert(all(S.samples == 24), ...
    'Expected 24 replay observations per scenario');

assert(all(S.gt_evaluation_samples > 0), ...
    'Missing GT evaluation samples');

assert(all(S.gt_evaluation_samples <= S.samples), ...
    'GT evaluation count exceeds replay observations');

disp('MATLAB_BOOLEAN_VALIDATION_PASS');

%% STEP 4 - Extract numerical results

meanError = S.mean_gt_center_error_m;
rmseError = S.rmse_gt_center_m;
maxError = S.max_gt_center_error_m;

errors = [meanError, rmseError, maxError];

assert(all(isfinite(errors(:))) && all(errors(:) >= 0), ...
    'Invalid tracking-error values');

responses = [
    A.Radar_Accepted, ...
    A.Radar_Rejected, ...
    A.Camera_Accepted, ...
    A.Camera_Rejected, ...
    A.LiDAR_Dropped
];

assert(all(isfinite(responses(:))) && ...
    all(responses(:) >= 0), ...
    'Invalid sensor response counts');

%% STEP 5 - Figure 1: Tracking error comparison

fig1 = figure( ...
    'Color', 'w', ...
    'Position', [100 100 1250 650]);

bar(errors, 'grouped');

grid on;
ylabel('GT-center position error (m)');
xlabel('Controlled fault scenario');

title('Task 25.3 - Tracking Error Under Controlled Faults');

set(gca, ...
    'XTick', 1:7, ...
    'XTickLabel', labels, ...
    'FontSize', 11);

xtickangle(30);

legend( ...
    {'Mean error', 'RMSE', 'Maximum error'}, ...
    'Location', 'northwest');

exportgraphics(fig1, ...
    fullfile(plotDir, ...
    'task25_27_matlab_fault_tracking_error.png'), ...
    'Resolution', 300);

exportgraphics(fig1, ...
    fullfile(plotDir, ...
    'task25_27_matlab_fault_tracking_error.pdf'), ...
    'ContentType', 'vector');

disp('FIGURE_1_SAVED');

%% STEP 6 - Figure 2: Sensor fault response

fig2 = figure( ...
    'Color', 'w', ...
    'Position', [150 150 1250 650]);

bar(responses, 'grouped');

grid on;
ylabel('Number of observations');
xlabel('Controlled fault scenario');

title('Task 25.3 - Sensor Fault Injection Response');

set(gca, ...
    'XTick', 1:7, ...
    'XTickLabel', labels, ...
    'FontSize', 11);

xtickangle(30);

legend({ ...
    'Radar accepted', ...
    'Radar rejected', ...
    'Camera accepted', ...
    'Camera rejected', ...
    'LiDAR dropped'}, ...
    'Location', 'northwest');

exportgraphics(fig2, ...
    fullfile(plotDir, ...
    'task25_28_matlab_fault_responses.png'), ...
    'Resolution', 300);

exportgraphics(fig2, ...
    fullfile(plotDir, ...
    'task25_28_matlab_fault_responses.pdf'), ...
    'ContentType', 'vector');

disp('FIGURE_2_SAVED');

%% STEP 7 - Compare all scenarios with baseline

baselineMean = meanError(1);
deltaMean = meanError - baselineMean;

fprintf('\n=== TASK 25.3D MATLAB RESULTS ===\n');

fprintf('Baseline mean error: %.6f m\n\n', baselineMean);

for i = 1:7
    fprintf( ...
        '%-24s Mean=%.6f RMSE=%.6f Delta=%.6f m\n', ...
        char(names(i)), ...
        meanError(i), ...
        rmseError(i), ...
        deltaMean(i));
end

%% STEP 8 - Save research findings

reportPath = fullfile( ...
    findingsDir, ...
    'task25_29_matlab_fault_analysis.txt');

fid = fopen(reportPath, 'w');

assert(fid > 0, 'Unable to create findings report');

fprintf(fid, 'TASK 25.3D - MATLAB FAULT ANALYSIS\n');
fprintf(fid, 'Seven controlled fault scenarios\n\n');

for i = 1:7
    fprintf(fid, ...
        '%s: GT_N=%d, Mean=%.6f, RMSE=%.6f, Max=%.6f\n', ...
        char(names(i)), ...
        S.gt_evaluation_samples(i), ...
        meanError(i), ...
        rmseError(i), ...
        maxError(i));
end

fprintf(fid, '\nRESEARCH LIMITATIONS:\n');
fprintf(fid, ...
    'Matched frames are not independent trials.\n');
fprintf(fid, ...
    'Small error differences do not prove improvement.\n');
fprintf(fid, ...
    'GT-center reference geometry has known limitations.\n');
fprintf(fid, ...
    'Sensor association remains partly provisional.\n');
fprintf(fid, ...
    'No measured ARM-FPGA energy results exist yet.\n');
fprintf(fid, ...
    'TASK25_03D_MATLAB_PASS\n');

fclose(fid);

%% STEP 9 - Verify saved outputs

files = {
    'task25_27_matlab_fault_tracking_error.png'
    'task25_27_matlab_fault_tracking_error.pdf'
    'task25_28_matlab_fault_responses.png'
    'task25_28_matlab_fault_responses.pdf'
};

for i = 1:numel(files)
    filePath = fullfile(plotDir, files{i});
    info = dir(filePath);

    assert(~isempty(info) && info.bytes > 0, ...
        ['Missing or empty figure: ', files{i}]);
end

assert(isfile(reportPath), ...
    'Missing research findings report');

fprintf('\nALL_FIGURES_SAVED_SUCCESSFULLY\n');
fprintf('TASK25_03D_MATLAB_PASS\n');
fprintf('Output folder: %s\n', plotDir);
