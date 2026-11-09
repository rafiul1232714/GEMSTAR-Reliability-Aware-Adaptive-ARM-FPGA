
%% TASK 11.4 - LIDAR AND RADAR SPATIAL ALIGNMENT
% Compare the same recorded frame
% Check Radar lateral sign convention

clc;
clear;
close all;

%% 1. Paths

root = "E:\GEMSTAR_Project\sensor-health-monitor";

archive = fullfile(root, ...
    "tests", "Task_11_Final_Research");

csvFolder = fullfile(archive, "02_CSV_Data");
graphFolder = fullfile(archive, "01_Graphs");
codeFolder = fullfile(archive, "04_Code");

%% 2. Load reconstructed measurements

L = readtable(fullfile(csvFolder, ...
    "task11_lidar_points_frame101.csv"));

R = readtable(fullfile(csvFolder, ...
    "task11_radar_points_frame101.csv"));

fprintf("\nTASK 11.4 - SPATIAL ALIGNMENT\n");
fprintf("LiDAR points: %d\n", height(L));
fprintf("Radar points: %d\n", height(R));

assert(all(L.frame == 101));
assert(all(R.frame == 101));

%% 3. Compare two lateral-axis conventions
% Original Radar reconstruction uses positive Y.
% LiDAR reconstruction negates Unreal lateral Y.
%
% Both alternatives are plotted for inspection.

fig = figure("Color", "w", ...
    "Position", [100 100 1250 550]);

tiledlayout(1, 2);

nexttile;

scatter(L.x_ego_m, L.y_ego_m, ...
    7, [0.1 0.45 0.9], "filled");

hold on;

scatter(R.x_ego_m, R.y_ego_m, ...
    55, [0.95 0.2 0.1], "filled");

plot(0, 0, "ks", "MarkerSize", 10);

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title("A: Original Radar Y");
legend("LiDAR", "Radar", "Ego origin");
axis equal;
grid on;

nexttile;

scatter(L.x_ego_m, L.y_ego_m, ...
    7, [0.1 0.45 0.9], "filled");

hold on;

scatter(R.x_ego_m, -R.y_ego_m, ...
    55, [0.95 0.2 0.1], "filled");

plot(0, 0, "ks", "MarkerSize", 10);

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title("B: Radar Y Sign Reversed");
legend("LiDAR", "Radar", "Ego origin");
axis equal;
grid on;

sgtitle("GEMSTAR LiDAR-Radar Coordinate Convention Check");

%% 4. Save comparison graph

exportgraphics(fig, fullfile(graphFolder, ...
    "task11_lidar_radar_alignment_check.png"), ...
    "Resolution", 300);

savefig(fig, fullfile(graphFolder, ...
    "task11_lidar_radar_alignment_check.fig"));

%% 5. Save both Radar candidates
% These are candidate transformations, not final
% validated coordinates.

comparison = table( ...
    R.frame, ...
    R.ray_index, ...
    R.x_ego_m, ...
    R.y_ego_m, ...
    -R.y_ego_m, ...
    R.z_ego_m, ...
    'VariableNames', { ...
    'frame', 'ray_index', ...
    'x_ego_m', ...
    'radar_y_original_m', ...
    'radar_y_flipped_m', ...
    'z_ego_m'});

writetable(comparison, fullfile(csvFolder, ...
    "task11_radar_coordinate_candidates.csv"));

%% 6. Archive source

sourceFile = fullfile(root, "matlab", ...
    "task11_lidar_radar_alignment.m");

if isfile(sourceFile)
    copyfile(sourceFile, codeFolder);
end

fprintf("\nAlignment comparison saved.\n");
fprintf("TASK 11.4 INITIAL CHECK COMPLETED\n");
