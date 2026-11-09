
%% TASK 11.3F - GEMSTAR LIDAR POINT CLOUD
% Reconstruct LiDAR reflections from verified C++ ray ordering
% Frame 101, MOR 100 recording

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

if ~isfolder(graphFolder), mkdir(graphFolder); end
if ~isfolder(codeFolder), mkdir(codeFolder); end

%% 2. Read LiDAR measurements

file = fullfile(csvFolder, ...
    "task11_lidar_measurements.csv");

assert(isfile(file), "LiDAR CSV not found.");

% Read only frame 101 to reduce memory usage.
opts = detectImportOptions(file);
T = readtable(file, opts);

frameID = 101;

F = T(T.frame == frameID, :);

% Exclude near-zero and invalid range measurements.
F = F(isfinite(F.range_m) & ...
      F.range_m >= 0.1 & ...
      isfinite(F.signal_strength), :);

fprintf("\nTASK 11.3F - LIDAR RECONSTRUCTION\n");
fprintf("Frame: %d\n", frameID);
fprintf("Valid LiDAR points: %d\n", height(F));

assert(~isempty(F), ...
    "No valid LiDAR points in frame 101.");

%% 3. Verified LiDAR angular grid

horizontalRays = 251;
verticalRays = 21;

horizontalFOV = deg2rad(90);
verticalFOV = deg2rad(20);

% Indices from the recorded ray_index column
% C++ uses zero-based indices.
index = double(F.ray_index);

h = mod(index, horizontalRays);
v = floor(index ./ horizontalRays);

assert(all(h >= 0 & h < horizontalRays));
assert(all(v >= 0 & v < verticalRays));

theta = -horizontalFOV / 2 + ...
    horizontalFOV .* h ./ (horizontalRays - 1);

phi = -verticalFOV / 2 + ...
    verticalFOV .* v ./ (verticalRays - 1);

%% 4. Reconstruct sensor-relative points
% Unreal forward vector for pitch/yaw:
% X = cos(pitch)*cos(yaw)
% Y = cos(pitch)*sin(yaw)
% Z = sin(pitch)
%
% In the OSI-style convention used for this initial
% reconstruction, the lateral Y direction is reversed.

r = double(F.range_m);

xSensor = r .* cos(phi) .* cos(theta);
ySensor = -r .* cos(phi) .* sin(theta);
zSensor = r .* sin(phi);

%% 5. Apply LiDAR mounting offset
% From GEMSTAR OSI configuration:
% X=2.6 m, Y=0 m, Z=0.7 m
% Mount rotation approximately zero.

xEgo = xSensor + F.mount_x;
yEgo = ySensor + F.mount_y;
zEgo = zSensor + F.mount_z;

%% 6. Save the reconstructed coordinates

P = table( ...
    F.frame, ...
    F.time_s, ...
    F.ray_index, ...
    F.range_m, ...
    F.signal_strength, ...
    xEgo, ...
    yEgo, ...
    zEgo, ...
    'VariableNames', { ...
    'frame', 'time_s', 'ray_index', ...
    'range_m', 'signal_strength', ...
    'x_ego_m', 'y_ego_m', 'z_ego_m'});

outputFile = fullfile(csvFolder, ...
    "task11_lidar_points_frame101.csv");

writetable(P, outputFile);

%% 7. Plot top-down LiDAR point cloud

fig1 = figure("Color", "w");

scatter(xEgo, yEgo, 8, r, "filled");
hold on;

plot(0, 0, "ks", ...
    "MarkerSize", 12, ...
    "LineWidth", 2);

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title("GEMSTAR LiDAR Top View - Frame 101");

axis equal;
grid on;
colorbar;

exportgraphics(fig1, fullfile(graphFolder, ...
    "task11_lidar_topview_frame101.png"), ...
    "Resolution", 300);

savefig(fig1, fullfile(graphFolder, ...
    "task11_lidar_topview_frame101.fig"));

%% 8. Plot 3D LiDAR point cloud

fig2 = figure("Color", "w", ...
    "Position", [100 100 1050 750]);

scatter3(xEgo, yEgo, zEgo, ...
    8, F.signal_strength, "filled");

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
zlabel("Height Z (m)");

title("GEMSTAR LiDAR 3D Point Cloud - Frame 101");

axis equal;
grid on;
colorbar;
view(45, 25);

exportgraphics(fig2, fullfile(graphFolder, ...
    "task11_lidar_3d_frame101.png"), ...
    "Resolution", 300);

savefig(fig2, fullfile(graphFolder, ...
    "task11_lidar_3d_frame101.fig"));

%% 9. Print reconstruction summary

fprintf("\nX range: %.3f to %.3f m\n", ...
    min(xEgo), max(xEgo));

fprintf("Y range: %.3f to %.3f m\n", ...
    min(yEgo), max(yEgo));

fprintf("Z range: %.3f to %.3f m\n", ...
    min(zEgo), max(zEgo));

fprintf("\nSaved: %s\n", outputFile);

%% 10. Archive MATLAB source

sourceFile = fullfile(root, "matlab", ...
    "task11_lidar_pointcloud.m");

if isfile(sourceFile)
    copyfile(sourceFile, codeFolder);
end

fprintf("\nTASK 11.3F COMPLETED\n");
