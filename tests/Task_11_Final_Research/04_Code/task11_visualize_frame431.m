
%% TASK 11.5J - VISUALIZE FRAME 431
% Diagnostic geometry investigation
% Object IDs are used for visualization only.

clc;
clear;
close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor";

archive = fullfile(root, ...
    "tests", "Task_11_Final_Research");

csvFolder = fullfile(archive, "02_CSV_Data");
graphFolder = fullfile(archive, "01_Graphs");
codeFolder = fullfile(archive, "04_Code");

T = readtable(fullfile(csvFolder, ...
    "task11_lidar_frame431_geometry.csv"));

candidate = T.diagnostic_match == 1;

fprintf("\nTASK 11.5J - FRAME 431\n");
fprintf("Total points: %d\n", height(T));
fprintf("Diagnostic candidate: %d\n", sum(candidate));

%% 1. Top-down view

fig1 = figure('Color', 'w');

scatter(T.x_ego_m(~candidate), ...
    T.y_ego_m(~candidate), ...
    7, [0.7 0.7 0.7], 'filled');

hold on;

scatter(T.x_ego_m(candidate), ...
    T.y_ego_m(candidate), ...
    18, [0.9 0.2 0.1], 'filled');

plot(0, 0, 'ks', 'MarkerSize', 10);

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('LiDAR Frame 431 - Diagnostic Candidate');

legend('Other reflections', ...
    'Simulator object 83391', 'Ego origin');

axis equal;
grid on;

exportgraphics(fig1, fullfile(graphFolder, ...
    'task11_frame431_topview.png'), ...
    'Resolution', 300);

savefig(fig1, fullfile(graphFolder, ...
    'task11_frame431_topview.fig'));

%% 2. Three-dimensional view

fig2 = figure('Color', 'w');

scatter3(T.x_ego_m(~candidate), ...
    T.y_ego_m(~candidate), ...
    T.z_ego_m(~candidate), ...
    7, [0.7 0.7 0.7], 'filled');

hold on;

scatter3(T.x_ego_m(candidate), ...
    T.y_ego_m(candidate), ...
    T.z_ego_m(candidate), ...
    18, [0.9 0.2 0.1], 'filled');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');
zlabel('Height Z (m)');

title('LiDAR Frame 431 - 3D Geometry');

legend('Other reflections', ...
    'Simulator object 83391');

axis equal;
grid on;
view(45,25);

exportgraphics(fig2, fullfile(graphFolder, ...
    'task11_frame431_3d.png'), ...
    'Resolution', 300);

savefig(fig2, fullfile(graphFolder, ...
    'task11_frame431_3d.fig'));

%% 3. Archive source

source = fullfile(root, ...
    'matlab', 'task11_visualize_frame431.m');

if isfile(source)
    copyfile(source, codeFolder);
end

fprintf("\nTASK 11.5J MATLAB COMPLETED\n");
