
%% TASK 11.4C - COMMON LIDAR-RADAR COORDINATE FRAME
% GEMSTAR - Frame 101
% Convert both sensors to a consistent provisional
% OSI-style ego coordinate convention.

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

%% 2. Load LiDAR and Radar frame 101

L = readtable(fullfile(csvFolder, ...
    "task11_lidar_points_frame101.csv"));

R = readtable(fullfile(csvFolder, ...
    "task11_radar_points_frame101.csv"));

assert(all(L.frame == 101));
assert(all(R.frame == 101));

%% 3. Apply common coordinate convention

% LiDAR has already been transformed to OSI-style Y.
lidarX = L.x_ego_m;
lidarY = L.y_ego_m;
lidarZ = L.z_ego_m;

% Radar was originally reconstructed with Unreal-style Y.
% Reverse it to match the LiDAR convention.
radarX = R.x_ego_m;
radarY = -R.y_ego_m;
radarZ = R.z_ego_m;

%% 4. Create unified research dataset

lidarCount = height(L);
radarCount = height(R);

sensor = [
    repmat("LiDAR", lidarCount, 1);
    repmat("Radar", radarCount, 1)
];

frame = [
    L.frame;
    R.frame
];

time_s = [
    L.time_s;
    R.time_s
];

x_m = [
    lidarX;
    radarX
];

y_m = [
    lidarY;
    radarY
];

z_m = [
    lidarZ;
    radarZ
];

range_m = [
    L.range_m;
    R.range_m
];

signal_strength = [
    L.signal_strength;
    R.signal_strength
];

combined = table( ...
    frame, time_s, sensor, ...
    x_m, y_m, z_m, ...
    range_m, signal_strength);

outputFile = fullfile(csvFolder, ...
    "task11_common_lidar_radar_frame101.csv");

writetable(combined, outputFile);

%% 5. Top-down comparison

fig1 = figure("Color", "w", ...
    "Position", [100 100 1000 650]);

scatter(lidarX, lidarY, 8, ...
    [0.1 0.45 0.9], "filled");

hold on;

scatter(radarX, radarY, 60, ...
    [0.95 0.2 0.1], "filled");

plot(0, 0, "ks", ...
    "MarkerSize", 12, "LineWidth", 2);

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");

title("GEMSTAR LiDAR and Radar - Common Frame 101");

legend("LiDAR", "Radar", "Ego origin", ...
    "Location", "best");

axis equal;
grid on;

exportgraphics(fig1, fullfile(graphFolder, ...
    "task11_common_sensor_topview.png"), ...
    "Resolution", 300);

savefig(fig1, fullfile(graphFolder, ...
    "task11_common_sensor_topview.fig"));

%% 6. Three-dimensional comparison

fig2 = figure("Color", "w", ...
    "Position", [100 100 1100 750]);

scatter3(lidarX, lidarY, lidarZ, ...
    8, [0.1 0.45 0.9], "filled");

hold on;

scatter3(radarX, radarY, radarZ, ...
    55, [0.95 0.2 0.1], "filled");

plot3(0, 0, 0, "ks", ...
    "MarkerSize", 12, "LineWidth", 2);

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
zlabel("Height Z (m)");

title("LiDAR-Radar 3D Spatial Comparison");

legend("LiDAR", "Radar", "Ego origin", ...
    "Location", "best");

axis equal;
grid on;
view(45, 25);

exportgraphics(fig2, fullfile(graphFolder, ...
    "task11_common_sensor_3d.png"), ...
    "Resolution", 300);

savefig(fig2, fullfile(graphFolder, ...
    "task11_common_sensor_3d.fig"));

%% 7. Print results

fprintf("\nTASK 11.4C - COMMON COORDINATE FRAME\n");
fprintf("LiDAR points: %d\n", lidarCount);
fprintf("Radar points: %d\n", radarCount);
fprintf("Total points: %d\n", height(combined));

fprintf("\nSaved: %s\n", outputFile);

%% 8. Archive MATLAB source

sourceFile = fullfile(root, "matlab", ...
    "task11_common_sensor_frame.m");

if isfile(sourceFile)
    copyfile(sourceFile, codeFolder);
end

fprintf("\nTASK 11.4C COMPLETED\n");
