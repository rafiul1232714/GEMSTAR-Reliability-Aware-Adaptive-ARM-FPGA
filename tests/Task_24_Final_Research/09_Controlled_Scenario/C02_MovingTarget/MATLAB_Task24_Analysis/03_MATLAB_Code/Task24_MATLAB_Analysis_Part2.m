%% TASK 24.10.5.2 - ADVANCED MATLAB EKF ANALYSIS
%
% Objective:
% Quantitatively compare LiDAR-only, LiDAR-Radar and
% LiDAR-Radar-Camera EKF estimators using saved Task 24 data.
%
% Ground Truth is evaluation-only.
% No EKF estimates are modified.
% This is a descriptive single-recording experiment.

clear; clc; close all;

%% PATHS

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';

data = fullfile(base, 'C02_V2_EKF_Input_53Frames_V1');
out = fullfile(base, 'MATLAB_Task24_Analysis');

figdir = fullfile(out, '01_Graphs');
csvdir = fullfile(out, '02_CSV_Data');
finddir = fullfile(out, '04_Research_Findings');

dirs = {figdir, csvdir, finddir};

for k = 1:numel(dirs)
    if ~exist(dirs{k}, 'dir')
        mkdir(dirs{k});
    end
end

%% REQUIRED INPUTS

required = {
    'gt_center_comparison_track2_v1.csv'
    'gt_surface_offset_diagnostic_v1.csv'
    'gt_robustness_per_frame_v1.csv'
};

for k = 1:numel(required)
    p = fullfile(data, required{k});
    assert(isfile(p), 'Missing CSV: %s', p);
end

%% PREVENT OVERWRITING OUTPUTS

for k = 7:12
    p = fullfile(figdir, sprintf('Task24_Figure_%02d.png', k));
    assert(~isfile(p), 'Figure already exists: %s', p);
end

summaryPath = fullfile(csvdir, ...
    'Task24_Three_Estimator_MATLAB_Metrics_V1.csv');

reportPath = fullfile(finddir, ...
    'Task24_MATLAB_Part2_Findings_V1.txt');

assert(~isfile(summaryPath), 'Summary already exists');
assert(~isfile(reportPath), 'Report already exists');

%% LOAD DATA

G = readtable(fullfile(data, ...
    'gt_center_comparison_track2_v1.csv'));

S = readtable(fullfile(data, ...
    'gt_surface_offset_diagnostic_v1.csv'));

R = readtable(fullfile(data, ...
    'gt_robustness_per_frame_v1.csv'));

assert(height(G) == 23, 'Expected 23 GT frames');
assert(height(S) == 23, 'Expected 23 geometry frames');
assert(height(R) == 23, 'Expected 23 robustness frames');

% Confirm that every comparison refers to the same frame.
assert(isequal(G.frame, S.frame, R.frame), ...
    'Frame alignment mismatch');

fprintf('\n=== TASK 24 MATLAB ANALYSIS PART 2 ===\n');
fprintf('Matched evaluation observations: %d\n', height(G));

%% DATA ARRAYS

t = G.time_s;

L = G.lidar_center_error_m;
D = G.radar_center_error_m;
C = G.camera_center_error_m;

improvementRadar = L - D;
improvementCamera = D - C;

%% FIGURE 07: GT AND ESTIMATOR TRAJECTORY

% Reconstruct positions from saved signed GT errors.
% These are the original EKF estimates, not GT-corrected states.

gtx = G.gt_center_x_ego_m;
gty = G.gt_center_y_ego_m;

lx = gtx + G.lidar_x_error_m;
ly = gty + G.lidar_y_error_m;

rx = gtx + G.radar_x_error_m;
ry = gty + G.radar_y_error_m;

cx = gtx + G.camera_x_error_m;
cy = gty + G.camera_y_error_m;

f = figure('Color','w','Position',[100 100 1050 670]);

plot(gtx, gty, '-k', 'LineWidth', 2.5);
hold on;

plot(lx, ly, '-o', ...
    'LineWidth',1.4,'MarkerSize',4);

plot(rx, ry, '-s', ...
    'LineWidth',1.4,'MarkerSize',4);

plot(cx, cy, '--', ...
    'LineWidth',1.5);

xlabel('Vehicle-relative X (m)');
ylabel('Vehicle-relative Y (m)');

title('Task 24: GT center and EKF trajectories');

legend('GT object center', ...
       'LiDAR-only EKF', ...
       'LiDAR-Radar EKF', ...
       'Three-sensor EKF', ...
       'Location','best');

axis equal;
grid on;

saveas(f, fullfile(figdir,'Task24_Figure_07.png'));
close(f);

%% FIGURE 08: SIGNED POSITION BIAS

f = figure('Color','w','Position',[100 100 1100 700]);

tiledlayout(2,1);

nexttile;

plot(t,G.lidar_x_error_m,'-o','LineWidth',1.5);
hold on;
plot(t,G.radar_x_error_m,'-s','LineWidth',1.5);
plot(t,G.camera_x_error_m,'--','LineWidth',1.5);

yline(0,'k:');

ylabel('Signed X error (m)');
title('Longitudinal position bias');
legend('LiDAR','LiDAR-Radar','Three-sensor', ...
    'Location','best');
grid on;

nexttile;

plot(t,G.lidar_y_error_m,'-o','LineWidth',1.5);
hold on;
plot(t,G.radar_y_error_m,'-s','LineWidth',1.5);
plot(t,G.camera_y_error_m,'--','LineWidth',1.5);

yline(0,'k:');

xlabel('Recording time (s)');
ylabel('Signed Y error (m)');
title('Lateral position bias');
grid on;

saveas(f, fullfile(figdir,'Task24_Figure_08.png'));
close(f);

%% FIGURE 09: RADAR CONTRIBUTION BY FRAME

f = figure('Color','w','Position',[100 100 1100 520]);

stem(t, 100*improvementRadar, ...
    'filled','LineWidth',1.5);

hold on;

yline(0,'k-','LineWidth',1.2);
xline(G.time_s(G.frame==530),'--', ...
    'Camera update frame');

xlabel('Recording time (s)');
ylabel('Radar improvement in center error (cm)');

title('Task 24: Positive = Radar improves GT-center error');
grid on;

saveas(f, fullfile(figdir,'Task24_Figure_09.png'));
close(f);

%% FIGURE 10: CAMERA EFFECT IN MILLIMETRES

f = figure('Color','w','Position',[100 100 1050 500]);

plot(t, 1000*improvementCamera, '-o', ...
    'LineWidth',1.7,'MarkerSize',5);

hold on;

yline(0,'k-');
xline(G.time_s(G.frame==530),'--', ...
    'Camera update');

xlabel('Recording time (s)');
ylabel('Camera improvement (mm)');

title(['Task 24: Camera contribution relative ', ...
       'to LiDAR-Radar']);

grid on;

saveas(f, fullfile(figdir,'Task24_Figure_10.png'));
close(f);

%% FIGURE 11: EMPIRICAL ERROR DISTRIBUTION

f = figure('Color','w','Position',[100 100 1100 580]);

sortedL = sort(L);
sortedD = sort(D);
sortedC = sort(C);

n = numel(L);
cdfY = (1:n)'/n;

plot(sortedL,cdfY,'-o','LineWidth',1.5);
hold on;

plot(sortedD,cdfY,'-s','LineWidth',1.5);
plot(sortedC,cdfY,'--','LineWidth',1.5);

xlabel('GT-center error (m)');
ylabel('Empirical cumulative fraction');

title('Task 24: Matched position-error distributions');

legend('LiDAR-only', ...
       'LiDAR-Radar', ...
       'Three-sensor', ...
       'Location','best');

grid on;

saveas(f, fullfile(figdir,'Task24_Figure_11.png'));
close(f);

%% FIGURE 12: GEOMETRY AND REFERENCE-POINT EFFECT

f = figure('Color','w','Position',[100 100 1100 650]);

tiledlayout(2,1);

nexttile;

plot(t,S.gt_length_m,'-o','LineWidth',1.5);
hold on;

plot(t,S.gt_width_m,'-s','LineWidth',1.5);

ylabel('Reported dimension (m)');
title('Ground Truth target bounding-box dimensions');
legend('Length','Width','Location','best');
grid on;

nexttile;

scatter(S.relative_yaw_deg, ...
    S.radar_center_error_m,70,'filled');

hold on;

scatter(S.relative_yaw_deg, ...
    S.radar_rear_face_error_m,70);

xlabel('Target-to-ego relative yaw (degrees)');
ylabel('Reference-point discrepancy (m)');

title('Center vs. approximate rear-face discrepancy');
legend('GT center','Approximate rear face', ...
    'Location','best');

grid on;

saveas(f, fullfile(figdir,'Task24_Figure_12.png'));
close(f);

%% QUANTITATIVE ESTIMATOR METRICS

names = [
    "LiDAR-only"
    "LiDAR-Radar"
    "Three-sensor"
];

errors = {L,D,C};

N = zeros(3,1);
MAE = zeros(3,1);
RMSE = zeros(3,1);
MedianError = zeros(3,1);
P95 = zeros(3,1);
MaxError = zeros(3,1);
MeanSignedX = zeros(3,1);
MeanSignedY = zeros(3,1);

xerrors = {
    G.lidar_x_error_m
    G.radar_x_error_m
    G.camera_x_error_m
};

yerrors = {
    G.lidar_y_error_m
    G.radar_y_error_m
    G.camera_y_error_m
};

for k = 1:3

    e = errors{k};

    N(k) = numel(e);
    MAE(k) = mean(e);
    RMSE(k) = sqrt(mean(e.^2));
    MedianError(k) = median(e);
    MaxError(k) = max(e);

    ordered = sort(e);
    pos = 1 + (numel(e)-1)*0.95;

    low = floor(pos);
    high = ceil(pos);

    P95(k) = ordered(low) + ...
        (pos-low)*(ordered(high)-ordered(low));

    MeanSignedX(k) = mean(xerrors{k});
    MeanSignedY(k) = mean(yerrors{k});

end

Metrics = table(names,N,MAE,RMSE, ...
    MedianError,P95,MaxError, ...
    MeanSignedX,MeanSignedY, ...
    'VariableNames',{ ...
    'Estimator','Frames','Mean2DError_m', ...
    'RMSE2D_m','Median2DError_m', ...
    'P95_2DError_m','Max2DError_m', ...
    'MeanSignedX_m','MeanSignedY_m'});

writetable(Metrics,summaryPath);

%% RADAR AND CAMERA IMPROVEMENT ANALYSIS

tol = 1e-6;

radarBetter = sum(improvementRadar > tol);
radarWorse = sum(improvementRadar < -tol);
radarSame = sum(abs(improvementRadar) <= tol);

cameraMean = mean(improvementCamera);
radarMean = mean(improvementRadar);

radarPercent = 100*radarMean/mean(L);

cameraFrame = find(G.frame==530);

assert(numel(cameraFrame)==1, ...
    'Expected exactly one Camera update frame');

cameraFrameChange = improvementCamera(cameraFrame);

%% SAVE RESEARCH FINDINGS

fid = fopen(reportPath,'w');

assert(fid >= 0, 'Cannot open research report');

fprintf(fid,'TASK 24 - MATLAB ADVANCED ANALYSIS\n');
fprintf(fid,'===================================\n\n');

fprintf(fid,'Evaluated frames: %d\n',height(G));
fprintf(fid,'All estimators use the same GT frames.\n\n');

for k = 1:3

    fprintf(fid,'%s\n',names(k));
    fprintf(fid,'Mean center error: %.6f m\n',MAE(k));
    fprintf(fid,'2D RMSE: %.6f m\n',RMSE(k));
    fprintf(fid,'P95 center error: %.6f m\n',P95(k));
    fprintf(fid,'Maximum error: %.6f m\n\n',MaxError(k));

end

fprintf(fid,'RADAR CONTRIBUTION\n');

fprintf(fid,'Mean improvement: %.6f m\n',radarMean);
fprintf(fid,'Relative mean improvement: %.3f %%\n',radarPercent);
fprintf(fid,'Improved frames: %d\n',radarBetter);
fprintf(fid,'Worsened frames: %d\n',radarWorse);
fprintf(fid,'Approximately unchanged frames: %d\n\n',radarSame);

fprintf(fid,'CAMERA CONTRIBUTION\n');

fprintf(fid,'Mean improvement: %.9f m\n',cameraMean);

fprintf(fid,'Frame 530 improvement: %.9f m\n\n', ...
    cameraFrameChange);

fprintf(fid,'GEOMETRIC LIMITATIONS\n');

fprintf(fid,['Center-reference errors include potential ', ...
    'surface-to-center mismatch.\n']);

fprintf(fid,['Approximate rear-face reference is ', ...
    'not a validated physical reference.\n']);

fprintf(fid,['Ground Truth target dimensions vary ', ...
    'during the recording.\n\n']);

fprintf(fid,'STATISTICAL LIMITATIONS\n');

fprintf(fid,'One recording, one tracked target.\n');
fprintf(fid,'Only 23 valid reference-aligned samples.\n');
fprintf(fid,'Measurements are temporally correlated.\n');
fprintf(fid,'No statistical generalization is claimed.\n');
fprintf(fid,'No GT measurements were used to update the EKF.\n');

fclose(fid);

%% CONSOLE RESULTS

disp(' ');
disp('=== TASK 24.10.5.2 RESULTS ===');

disp(Metrics);

fprintf('RADAR_MEAN_IMPROVEMENT_M=%.7f\n',radarMean);
fprintf('RADAR_RELATIVE_IMPROVEMENT_PERCENT=%.4f\n',radarPercent);

fprintf('RADAR_IMPROVED_FRAMES=%d\n',radarBetter);
fprintf('RADAR_WORSENED_FRAMES=%d\n',radarWorse);
fprintf('RADAR_UNCHANGED_FRAMES=%d\n',radarSame);

fprintf('CAMERA_MEAN_IMPROVEMENT_M=%.9f\n',cameraMean);

fprintf('FRAME530_CAMERA_IMPROVEMENT_M=%.9f\n', ...
    cameraFrameChange);

fprintf('SAVED_NEW_FIGURES=6\n');

fprintf('METRICS_CSV=%s\n',summaryPath);
fprintf('RESEARCH_REPORT=%s\n',reportPath);

fprintf('GROUND_TRUTH_USED_FOR_FILTER_UPDATE=NO\n');
fprintf('ORIGINAL_INPUTS_MODIFIED=NO\n');
fprintf('TASK24_MATLAB_PART2_COMPLETE\n');