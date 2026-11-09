
%% TASK 11.5U - FRAME 150 VEHICLE INSPECTION
% GEMSTAR MOR100
% LiDAR points versus provisional Ground Truth vehicle position
% No Statistics and Machine Learning Toolbox required.

clc;
clear;
close all;

%% 1. DEFINE FOLDERS

root = "E:\GEMSTAR_Project\sensor-health-monitor";

archive = fullfile(root, ...
    "tests", "Task_11_Final_Research");

csvFolder = fullfile(archive, "02_CSV_Data");
graphFolder = fullfile(archive, "01_Graphs");
codeFolder = fullfile(archive, "04_Code");
findingsFolder = fullfile(archive, "06_Research_Findings");

if ~isfolder(graphFolder), mkdir(graphFolder); end
if ~isfolder(codeFolder), mkdir(codeFolder); end
if ~isfolder(findingsFolder), mkdir(findingsFolder); end

%% 2. LOAD LIDAR POINTS

L = readtable(fullfile(csvFolder, ...
    "task11_lidar_frame150_geometry.csv"));

assert(height(L) > 0, "No LiDAR points available.");

%% 3. GROUND TRUTH CANDIDATE

gtX = 5.48;
gtY = 2.18;

% Provisional search window, not a vehicle bounding box
windowX = 2.5;
windowY = 2.0;

nearPositive = ...
    abs(L.x_ego_m - gtX) <= windowX & ...
    abs(L.y_ego_m - gtY) <= windowY;

nearNegative = ...
    abs(L.x_ego_m - gtX) <= windowX & ...
    abs(L.y_ego_m + gtY) <= windowY;

fprintf('\nTASK 11.5U - FRAME 150\n');
fprintf('Total LiDAR points: %d\n', height(L));
fprintf('Points near +Y candidate: %d\n', sum(nearPositive));
fprintf('Points near mirrored -Y: %d\n', sum(nearNegative));

%% 4. GRAPH 1 - TOP VIEW

fig1 = figure('Color', 'w', ...
    'Position', [100 100 1100 750]);

hold on;

scatter(L.x_ego_m, L.y_ego_m, ...
    8, [0.65 0.65 0.65], 'filled', ...
    'DisplayName', 'LiDAR points');

scatter(L.x_ego_m(nearPositive), ...
    L.y_ego_m(nearPositive), ...
    12, [0.95 0.45 0.10], 'filled', ...
    'DisplayName', 'Points in +Y search window');

plot(gtX, gtY, 'bp', ...
    'MarkerSize', 15, 'LineWidth', 2, ...
    'DisplayName', 'Provisional GT vehicle center');

plot(gtX, -gtY, 'mp', ...
    'MarkerSize', 15, 'LineWidth', 2, ...
    'DisplayName', 'Mirrored Y test position');

plot(0, 0, 'ks', ...
    'MarkerSize', 10, 'LineWidth', 2, ...
    'DisplayName', 'Ego origin');

plot(2.6, 0, 'kd', ...
    'MarkerSize', 9, 'LineWidth', 2, ...
    'DisplayName', 'LiDAR mount');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');
title('Frame 150 - LiDAR and Provisional Vehicle Location');

axis equal;
grid on;
legend('Location', 'bestoutside');

exportgraphics(fig1, fullfile(graphFolder, ...
    "task11_frame150_vehicle_topview.png"), ...
    'Resolution', 300);

savefig(fig1, fullfile(graphFolder, ...
    "task11_frame150_vehicle_topview.fig"));

%% 5. GRAPH 2 - 3D POINT CLOUD

fig2 = figure('Color', 'w', ...
    'Position', [100 100 1100 750]);

scatter3(L.x_ego_m, ...
    L.y_ego_m, ...
    L.z_ego_m, ...
    9, L.z_ego_m, 'filled');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');
zlabel('Height Z (m)');

title('Frame 150 - LiDAR Point Cloud 3D');

axis equal;
grid on;
view(45,25);
colorbar;

exportgraphics(fig2, fullfile(graphFolder, ...
    "task11_frame150_lidar_3d.png"), ...
    'Resolution', 300);

savefig(fig2, fullfile(graphFolder, ...
    "task11_frame150_lidar_3d.fig"));

%% 6. GRAPH 3 - CLOSE-UP COMPARISON

fig3 = figure('Color', 'w', ...
    'Position', [100 100 1000 700]);

hold on;

scatter(L.x_ego_m, L.y_ego_m, ...
    10, [0.65 0.65 0.65], 'filled', ...
    'DisplayName', 'LiDAR points');

scatter(L.x_ego_m(nearPositive), ...
    L.y_ego_m(nearPositive), ...
    16, [0.95 0.45 0.10], 'filled', ...
    'DisplayName', '+Y search window');

scatter(L.x_ego_m(nearNegative), ...
    L.y_ego_m(nearNegative), ...
    16, [0.15 0.65 0.8], 'filled', ...
    'DisplayName', '-Y search window');

plot(gtX, gtY, 'bp', ...
    'MarkerSize', 15, 'LineWidth', 2, ...
    'DisplayName', 'GT +Y');

plot(gtX, -gtY, 'mp', ...
    'MarkerSize', 15, 'LineWidth', 2, ...
    'DisplayName', 'GT mirrored -Y');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('Frame 150 - Vehicle Candidate Close-Up');

xlim([2 11]);
ylim([-6 6]);

axis equal;
grid on;
legend('Location', 'bestoutside');

exportgraphics(fig3, fullfile(graphFolder, ...
    "task11_frame150_vehicle_closeup.png"), ...
    'Resolution', 300);

savefig(fig3, fullfile(graphFolder, ...
    "task11_frame150_vehicle_closeup.fig"));

%% 7. SAVE SEARCH-WINDOW DATA

P = L(nearPositive, :);
N = L(nearNegative, :);

writetable(P, fullfile(csvFolder, ...
    "task11_frame150_positive_y_window.csv"));

writetable(N, fullfile(csvFolder, ...
    "task11_frame150_negative_y_window.csv"));

%% 8. ARCHIVE SCRIPT

sourceFile = fullfile(root, ...
    "matlab", "task11_frame150_vehicle_inspection.m");

if isfile(sourceFile)
    copyfile(sourceFile, codeFolder);
end

%% 9. SAVE RESEARCH FINDINGS

fid = fopen(fullfile(findingsFolder, ...
    "task11_frame150_visual_inspection.txt"), 'w');

assert(fid ~= -1, "Unable to save research findings.");

fprintf(fid, 'TASK 11.5U - FRAME 150\n');
fprintf(fid, 'Total LiDAR points: %d\n', height(L));
fprintf(fid, 'Positive Y window points: %d\n', sum(nearPositive));
fprintf(fid, 'Negative Y window points: %d\n', sum(nearNegative));
fprintf(fid, 'GT object ID: 76865\n');
fprintf(fid, 'GT coordinates: provisional\n');
fprintf(fid, 'Vehicle detection: NOT CONFIRMED\n');
fprintf(fid, 'Ground filtering: not applied to frame 150\n');
fprintf(fid, 'No simulator object IDs used for classification\n');

fclose(fid);

fprintf('\nTASK 11.5U COMPLETED\n');
