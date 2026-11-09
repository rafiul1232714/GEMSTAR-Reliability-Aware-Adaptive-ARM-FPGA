
%% TASK 11.5C - SURFACE NORMAL GROUND FILTER
% GEMSTAR LiDAR - Frame 101
% Compare ground-like and non-ground-like surfaces

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

%% 2. Load reconstructed points and normals

P = readtable(fullfile(csvFolder, ...
    "task11_lidar_points_frame101.csv"));

N = readtable(fullfile(csvFolder, ...
    "task11_lidar_normals_frame101.csv"));

fprintf("\nTASK 11.5C - NORMAL-BASED GROUND FILTER\n");

%% 3. Match points by original ray index

%% 3. Match points by frame and ray index

T = innerjoin(P, N, ...
    'Keys', {'frame', 'ray_index'});

fprintf("Matched LiDAR points: %d\n", height(T));

assert(height(T) == height(P), ...
    "Missing surface normals for some points.");

%% 4. Normalize surface normals

nx = T.normal_x;
ny = T.normal_y;
nz = T.normal_z;

magnitude = sqrt(nx.^2 + ny.^2 + nz.^2);

validNormals = isfinite(magnitude) & magnitude > 0.5;

normalZ = zeros(height(T), 1);
normalZ(validNormals) = nz(validNormals) ./ magnitude(validNormals);

%% 5. Classify ground-like surfaces

groundCandidate = validNormals & normalZ >= 0.9;

otherCandidate = ~groundCandidate;

fprintf("Ground-like points: %d\n", sum(groundCandidate));
fprintf("Other points: %d\n", sum(otherCandidate));

%% 6. Plot 3D surface classification

fig1 = figure("Color", "w", ...
    "Position", [100 100 1100 750]);

scatter3( ...
    T.x_ego_m(groundCandidate), ...
    T.y_ego_m(groundCandidate), ...
    T.z_ego_m(groundCandidate), ...
    10, [0.5 0.5 0.5], "filled");

hold on;

scatter3( ...
    T.x_ego_m(otherCandidate), ...
    T.y_ego_m(otherCandidate), ...
    T.z_ego_m(otherCandidate), ...
    20, [0.9 0.2 0.1], "filled");

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
zlabel("Height Z (m)");

title("LiDAR Surface-Normal Classification - Frame 101");

legend("Horizontal upward-facing", ...
    "Other or invalid normals", ...
    "Location", "best");

axis equal;
grid on;
view(45, 25);

exportgraphics(fig1, fullfile(graphFolder, ...
    "task11_normal_surface_classification_3d.png"), ...
    "Resolution", 300);

savefig(fig1, fullfile(graphFolder, ...
    "task11_normal_surface_classification_3d.fig"));

%% 7. Plot top-down classification

fig2 = figure("Color", "w");

scatter( ...
    T.x_ego_m(groundCandidate), ...
    T.y_ego_m(groundCandidate), ...
    8, [0.6 0.6 0.6], "filled");

hold on;

scatter( ...
    T.x_ego_m(otherCandidate), ...
    T.y_ego_m(otherCandidate), ...
    20, [0.9 0.2 0.1], "filled");

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title("LiDAR Surface Classification - Top View");

legend("Ground-like orientation", ...
    "Other surfaces", ...
    "Location", "best");

axis equal;
grid on;

exportgraphics(fig2, fullfile(graphFolder, ...
    "task11_normal_surface_classification_topview.png"), ...
    "Resolution", 300);

savefig(fig2, fullfile(graphFolder, ...
    "task11_normal_surface_classification_topview.fig"));

%% 8. Save classification CSV

T.groundCandidate = groundCandidate;
T.otherCandidate = otherCandidate;
T.normalZ_normalized = normalZ;

output = fullfile(csvFolder, ...
    "task11_lidar_normal_classification_frame101.csv");

writetable(T, output);

%% 9. Archive MATLAB code

source = fullfile(root, "matlab", ...
    "task11_normal_ground_filter.m");

if isfile(source)
    copyfile(source, codeFolder);
end

fprintf("\nSaved: %s\n", output);
fprintf("TASK 11.5C COMPLETED\n");
