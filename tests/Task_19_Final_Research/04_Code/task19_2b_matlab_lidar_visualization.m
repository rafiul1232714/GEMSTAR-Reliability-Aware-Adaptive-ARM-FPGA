%% TASK 19.2B
% GEMSTAR LiDAR - 3D Point Cloud Visualization
% Frame 150
% Reconstructed sensor-local coordinates

clear;
clc;
close all;

%% 1. Define project paths

base = ...
"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

csvFile = fullfile(base, ...
    "08_Extracted_PointClouds", ...
    "task19_2a_frame150_candidate_xyz.csv");

graphDir = fullfile(base, "01_Graphs");
dataDir  = fullfile(base, "02_CSV_Data");

assert(isfile(csvFile), ...
    "CSV file not found: %s", csvFile);

%% 2. Import reconstructed LiDAR points

T = readtable(csvFile);

x = T.X;
y = T.Y;
z = T.Z;

range = T.RangeM;
strength = T.SignalStrength;

fprintf("\n=== TASK 19.2B MATLAB LIDAR ===\n");
fprintf("Frame: 150\n");
fprintf("Imported candidate points: %d\n", height(T));

%% 3. Create 3D point cloud

fig1 = figure("Color", "w", ...
    "Name", "GEMSTAR LiDAR 3D Point Cloud");

scatter3(x, y, z, 12, range, "filled");

xlabel("X - Forward (m)");
ylabel("Y - Lateral, OSI sign (m)");
zlabel("Z - Up (m)");

title("GEMSTAR LiDAR - Frame 150 - Reconstructed Point Cloud");

axis equal;
grid on;
view(40, 25);

cb = colorbar;
cb.Label.String = "Range (m)";

exportgraphics(fig1, ...
    fullfile(graphDir, ...
    "task19_2b_matlab_lidar_3d.png"), ...
    "Resolution", 200);

%% 4. Create top-view point cloud

fig2 = figure("Color", "w", ...
    "Name", "GEMSTAR LiDAR Top View");

scatter(x, y, 12, range, "filled");

xlabel("X - Forward (m)");
ylabel("Y - Lateral (m)");

title("GEMSTAR LiDAR - Frame 150 - Top View");

axis equal;
grid on;

cb = colorbar;
cb.Label.String = "Range (m)";

exportgraphics(fig2, ...
    fullfile(graphDir, ...
    "task19_2b_matlab_lidar_top_view.png"), ...
    "Resolution", 200);

%% 5. Plot signal strength versus range

fig3 = figure("Color", "w", ...
    "Name", "LiDAR Signal Strength");

scatter(range, strength, 12, "filled");

xlabel("Range (m)");
ylabel("Signal strength");
title("GEMSTAR LiDAR - Signal Strength vs Range");

grid on;

exportgraphics(fig3, ...
    fullfile(graphDir, ...
    "task19_2b_matlab_signal_strength.png"), ...
    "Resolution", 200);

%% 6. Calculate statistics

minRange = min(range);
maxRange = max(range);
medianRange = median(range);

minX = min(x);
maxX = max(x);

minY = min(y);
maxY = max(y);

minZ = min(z);
maxZ = max(z);

fprintf("\n=== POINT CLOUD STATISTICS ===\n");

fprintf("Candidate points: %d\n", numel(x));
fprintf("Minimum range: %.3f m\n", minRange);
fprintf("Maximum range: %.3f m\n", maxRange);
fprintf("Median range: %.3f m\n", medianRange);

fprintf("X extent: %.3f to %.3f m\n", minX, maxX);
fprintf("Y extent: %.3f to %.3f m\n", minY, maxY);
fprintf("Z extent: %.3f to %.3f m\n", minZ, maxZ);

%% 7. Export summary statistics

summary = table( ...
    150, ...
    numel(x), ...
    minRange, ...
    medianRange, ...
    maxRange, ...
    minX, maxX, ...
    minY, maxY, ...
    minZ, maxZ, ...
    'VariableNames', { ...
    'Frame', ...
    'CandidatePoints', ...
    'MinRangeM', ...
    'MedianRangeM', ...
    'MaxRangeM', ...
    'MinX', 'MaxX', ...
    'MinY', 'MaxY', ...
    'MinZ', 'MaxZ' ...
    });

writetable(summary, ...
    fullfile(dataDir, ...
    "task19_2b_matlab_pointcloud_statistics.csv"));

%% 8. Final verification

fprintf("\n=== TASK 19.2B COMPLETE ===\n");

fprintf("3D graph saved: %d\n", ...
    isfile(fullfile(graphDir, ...
    "task19_2b_matlab_lidar_3d.png")));

fprintf("Top-view graph saved: %d\n", ...
    isfile(fullfile(graphDir, ...
    "task19_2b_matlab_lidar_top_view.png")));

fprintf("Signal graph saved: %d\n", ...
    isfile(fullfile(graphDir, ...
    "task19_2b_matlab_signal_strength.png")));

fprintf("Statistics CSV saved: %d\n", ...
    isfile(fullfile(dataDir, ...
    "task19_2b_matlab_pointcloud_statistics.csv")));