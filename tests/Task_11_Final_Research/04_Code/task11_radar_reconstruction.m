
%% TASK 11.3B - RADAR SPATIAL RECONSTRUCTION
% GEMSTAR Radar - Fog MOR 100
% First visualization in ego-relative coordinates

clc;
clear;
close all;

%% 1. Define paths

root = "E:\GEMSTAR_Project\sensor-health-monitor";

archive = fullfile(root, ...
    "tests", "Task_11_Final_Research");

csvFolder = fullfile(archive, "02_CSV_Data");
graphFolder = fullfile(archive, "01_Graphs");
codeFolder = fullfile(archive, "04_Code");

if ~isfolder(graphFolder), mkdir(graphFolder); end
if ~isfolder(codeFolder), mkdir(codeFolder); end

%% 2. Load Radar measurements

inputFile = fullfile(csvFolder, ...
    "task11_radar_measurements.csv");

assert(isfile(inputFile), "Radar CSV not found.");

T = readtable(inputFile);

fprintf("TASK 11.3B - RADAR RECONSTRUCTION\n");
fprintf("Total Radar measurements: %d\n", height(T));

%% 3. Select one representative frame

frameID = 101;

F = T(T.frame == frameID, :);

% Exclude near-zero reflections
F = F(F.range_m >= 0.1 & ...
      isfinite(F.range_m) & ...
      isfinite(F.horizontal_angle_rad) & ...
      isfinite(F.vertical_angle_rad), :);

fprintf("Frame: %d\n", frameID);
fprintf("Valid Radar points: %d\n", height(F));

assert(~isempty(F), ...
    "No valid Radar reflections in selected frame.");

%% 4. Reconstruct sensor-relative coordinates

r = F.range_m;
theta = F.horizontal_angle_rad;
phi = F.vertical_angle_rad;

xSensor = r .* cos(phi) .* cos(theta);
ySensor = r .* cos(phi) .* sin(theta);
zSensor = r .* sin(phi);

%% 5. Apply Radar mounting position
% Verified from the OSI configuration:
% x = 2.0, y = 0, z = 0.8
% Rotation is approximately zero.

xEgo = xSensor + F.mount_x;
yEgo = ySensor + F.mount_y;
zEgo = zSensor + F.mount_z;

%% 6. Save reconstructed points

P = table( ...
    F.frame, ...
    F.time_s, ...
    F.ray_index, ...
    F.range_m, ...
    F.signal_strength, ...
    F.doppler_hz, ...
    xEgo, yEgo, zEgo, ...
    'VariableNames', { ...
    'frame', 'time_s', 'ray_index', ...
    'range_m', 'signal_strength', 'doppler_hz', ...
    'x_ego_m', 'y_ego_m', 'z_ego_m'});

outputFile = fullfile(csvFolder, ...
    "task11_radar_points_frame101.csv");

writetable(P, outputFile);

%% 7. Plot top-down Radar measurements

fig1 = figure("Color", "w");

scatter(xEgo, yEgo, 65, F.range_m, "filled");
hold on;

plot(0, 0, "ks", ...
    "MarkerSize", 12, ...
    "LineWidth", 2);

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title("GEMSTAR Radar Reflections - Frame 101");

axis equal;
grid on;
colorbar;

legend("Radar reflections", "Ego origin", ...
    "Location", "best");

exportgraphics(fig1, fullfile(graphFolder, ...
    "task11_radar_topview_frame101.png"), ...
    "Resolution", 300);

savefig(fig1, fullfile(graphFolder, ...
    "task11_radar_topview_frame101.fig"));

%% 8. Plot 3D Radar measurements

fig2 = figure("Color", "w");

scatter3(xEgo, yEgo, zEgo, ...
    65, F.signal_strength, "filled");

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
zlabel("Height Z (m)");

title("GEMSTAR Radar 3D Reflections - Frame 101");

axis equal;
grid on;
colorbar;
view(45, 25);

exportgraphics(fig2, fullfile(graphFolder, ...
    "task11_radar_3d_frame101.png"), ...
    "Resolution", 300);

savefig(fig2, fullfile(graphFolder, ...
    "task11_radar_3d_frame101.fig"));

%% 9. Print summary

fprintf("\nRadar reconstruction completed.\n");
fprintf("X range: %.3f to %.3f m\n", ...
    min(xEgo), max(xEgo));

fprintf("Y range: %.3f to %.3f m\n", ...
    min(yEgo), max(yEgo));

fprintf("Z range: %.3f to %.3f m\n", ...
    min(zEgo), max(zEgo));

fprintf("Saved: %s\n", outputFile);

%% 10. Archive MATLAB source

source = fullfile(root, "matlab", ...
    "task11_radar_reconstruction.m");

if isfile(source)
    copyfile(source, codeFolder);
end

fprintf("\nTASK 11.3B COMPLETED\n");
