%% TASK 24.10.5.1 - MATLAB RESEARCH ANALYSIS
% All inputs originate from the clean V2 GEMSTAR recording.
% Ground Truth is used for evaluation only.
% The script does not modify existing research files.

clear; clc; close all;

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';
data = fullfile(base, 'C02_V2_EKF_Input_53Frames_V1');
out = fullfile(base, 'MATLAB_Task24_Analysis');
figdir = fullfile(out, '01_Graphs');

if ~exist(figdir, 'dir')
    mkdir(figdir);
end

% Check all required files before generating outputs.
files = {
    'selected_frames.csv'
    'lidar_clustering_summary_v1.csv'
    'lidar_temporal_tracks_v1.csv'
    'radar_track_association_summary_v1.csv'
    'radar_lidar_velocity_consistency_v1.csv'
    'gt_center_comparison_track2_v1.csv'
};

for i = 1:numel(files)
    p = fullfile(data, files{i});
    assert(isfile(p), 'Missing required CSV: %s', p);
end

% Prevent accidental overwrite of previously generated graphs.
for i = 1:6
    p = fullfile(figdir, sprintf('Task24_Figure_%02d.png', i));
    assert(~isfile(p), 'Existing plot will not be overwritten: %s', p);
end

% Load research datasets.
S = readtable(fullfile(data, 'selected_frames.csv'));
L = readtable(fullfile(data, 'lidar_clustering_summary_v1.csv'));
T = readtable(fullfile(data, 'lidar_temporal_tracks_v1.csv'));
R = readtable(fullfile(data, 'radar_track_association_summary_v1.csv'));
V = readtable(fullfile(data, 'radar_lidar_velocity_consistency_v1.csv'));
G = readtable(fullfile(data, 'gt_center_comparison_track2_v1.csv'));

assert(height(S) == 53, 'Unexpected selected frame count');
assert(height(G) == 23, 'Unexpected GT evaluation count');

fprintf('\n=== TASK 24 MATLAB ANALYSIS PART 1 ===\n');
fprintf('Selected frames: %d\n', height(S));
fprintf('Tracked LiDAR observations: %d\n', height(T));
fprintf('Radar association records: %d\n', height(R));
fprintf('GT evaluation frames: %d\n', height(G));

%% FIGURE 01 - SENSOR AVAILABILITY

f = figure('Color', 'w', 'Position', [100 100 1000 460]);

plot(S.time_s, S.lidar_valid_points, '-o', ...
    'LineWidth', 1.5, 'MarkerSize', 3);
hold on;

yyaxis right;
plot(S.time_s, S.radar_valid_returns, '-s', ...
    'LineWidth', 1.5, 'MarkerSize', 3);

ylabel('Valid Radar returns');
yyaxis left;
ylabel('Valid LiDAR points');

xlabel('Recording time (s)');
title('Task 24: Sensor measurement availability');
legend('LiDAR points', 'Radar returns', 'Location', 'best');
grid on;

saveas(f, fullfile(figdir, 'Task24_Figure_01.png'));
close(f);

%% FIGURE 02 - LIDAR CLUSTERING

f = figure('Color', 'w', 'Position', [100 100 1000 460]);

yyaxis left;
plot(L.time_s, L.filtered_points, '-o', 'LineWidth', 1.5);
ylabel('Filtered LiDAR points');

yyaxis right;
stairs(L.time_s, L.clusters_found, 'LineWidth', 1.5);
ylabel('Geometric cluster count');

xlabel('Recording time (s)');
title('Task 24: LiDAR filtering and clustering');
grid on;

saveas(f, fullfile(figdir, 'Task24_Figure_02.png'));
close(f);

%% FIGURE 03 - TEMPORAL TRACKS IN VEHICLE COORDINATES

f = figure('Color', 'w', 'Position', [100 100 900 650]);

ids = unique(T.track_id);

hold on;
for i = 1:numel(ids)
    idx = T.track_id == ids(i);

    if sum(idx) >= 3
        plot(T.x_m(idx), T.y_m(idx), '-o', ...
            'LineWidth', 1.5, 'MarkerSize', 4, ...
            'DisplayName', sprintf('Track %d', ids(i)));
    end
end

xlabel('Vehicle-relative X (m)');
ylabel('Vehicle-relative Y (m)');
title('Task 24: LiDAR temporal track trajectories');
axis equal;
grid on;
legend('Location', 'best');

saveas(f, fullfile(figdir, 'Task24_Figure_03.png'));
close(f);

%% FIGURE 04 - RADAR MATCHED RETURNS BY TRACK

f = figure('Color', 'w', 'Position', [100 100 1000 460]);

r2 = R(R.track_id == 2, :);
r7 = R(R.track_id == 7, :);

plot(r2.time_s, r2.radar_matched_returns, '-o', ...
    'LineWidth', 1.5);
hold on;
plot(r7.time_s, r7.radar_matched_returns, '-s', ...
    'LineWidth', 1.5);

xlabel('Recording time (s)');
ylabel('Spatially matched Radar returns');
title('Task 24: Provisional Radar association coverage');
legend('Track 2', 'Track 7', 'Location', 'best');
grid on;

saveas(f, fullfile(figdir, 'Task24_Figure_04.png'));
close(f);

%% FIGURE 05 - RADAR VS LIDAR RADIAL VELOCITY

f = figure('Color', 'w', 'Position', [100 100 1000 460]);

plot(V.frame, V.radar_radial_velocity_mps, '-o', ...
    'LineWidth', 1.8);
hold on;

plot(V.frame, V.lidar_radial_velocity_mps, '-s', ...
    'LineWidth', 1.8);

xlabel('Frame index');
ylabel('Radial velocity (m/s)');
title('Task 24: Radar-LiDAR velocity consistency');
legend('Radar Doppler', 'LiDAR finite difference', ...
    'Location', 'best');
grid on;

saveas(f, fullfile(figdir, 'Task24_Figure_05.png'));
close(f);

%% FIGURE 06 - GROUND TRUTH CENTER ERROR

f = figure('Color', 'w', 'Position', [100 100 1100 500]);

plot(G.time_s, G.lidar_center_error_m, '-o', ...
    'LineWidth', 1.5);
hold on;

plot(G.time_s, G.radar_center_error_m, '-s', ...
    'LineWidth', 1.5);

plot(G.time_s, G.camera_center_error_m, '--', ...
    'LineWidth', 1.8);

xlabel('Recording time (s)');
ylabel('2D GT center-reference error (m)');
title('Task 24: Matched three-estimator position errors');

legend('LiDAR-only', 'LiDAR-Radar', ...
    'LiDAR-Radar-Camera', 'Location', 'best');

grid on;

saveas(f, fullfile(figdir, 'Task24_Figure_06.png'));
close(f);

%% NUMERICAL SUMMARY

fprintf('\n=== NUMERICAL FINDINGS ===\n');

fprintf('LiDAR-only mean GT center error: %.6f m\n', ...
    mean(G.lidar_center_error_m));

fprintf('LiDAR-Radar mean GT center error: %.6f m\n', ...
    mean(G.radar_center_error_m));

fprintf('Three-sensor mean GT center error: %.6f m\n', ...
    mean(G.camera_center_error_m));

fprintf('Median absolute Doppler disagreement: %.6f m/s\n', ...
    median(V.absolute_residual_mps));

fprintf('Total Track 2 Radar matches: %d\n', ...
    sum(r2.radar_matched_returns));

fprintf('Total Track 7 Radar matches: %d\n', ...
    sum(r7.radar_matched_returns));

fprintf('\nSAVED_FIGURES=6\n');
fprintf('GROUND_TRUTH_USED_FOR_TRACKING=NO\n');
fprintf('MATLAB_ANALYSIS_STATUS=DESCRIPTIVE\n');
fprintf('TASK24_MATLAB_PART1_COMPLETE\n');