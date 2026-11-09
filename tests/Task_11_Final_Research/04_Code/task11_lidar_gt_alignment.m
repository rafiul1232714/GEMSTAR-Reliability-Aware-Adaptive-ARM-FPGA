
%% TASK 11.5R - LIDAR VS GROUND TRUTH ALIGNMENT
% GEMSTAR MOR100 - Frame 431
% Uses provisional world-to-ego coordinate conversion.
% Ground Truth is for validation only.

clc;
clear;
close all;

%% 1. Project folders

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

%% 2. Load existing data

L = readtable(fullfile(csvFolder, ...
    "task11_lidar_frame431_geometry.csv"));

G = readtable(fullfile(csvFolder, ...
    "task11_groundtruth_ego_frame431.csv"), ...
    'TextType', 'string');

%% 3. Select vehicles, excluding ego

isVehicle = contains(G.model_reference, ...
    ["Car", "Truck", "Bus"]);

isOther = G.object_id ~= 76895;

V = G(isVehicle & isOther, :);

distance = hypot(V.x_ego_m, V.y_ego_m);

nearby = V(distance <= 35, :);

fprintf('\nTASK 11.5R - SENSOR ALIGNMENT\n');
fprintf('LiDAR points: %d\n', height(L));
fprintf('Other vehicles within 35 m: %d\n', height(nearby));

disp(nearby);

%% 4. Top view overlay

fig1 = figure('Color', 'w', ...
    'Position', [100 100 1100 750]);

hold on;

% All LiDAR reflections - gray
scatter(L.x_ego_m, L.y_ego_m, ...
    7, [0.65 0.65 0.65], 'filled', ...
    'DisplayName', 'LiDAR reflections');

% Diagnostic candidate - orange
candidate = L.diagnostic_match == 1;

scatter(L.x_ego_m(candidate), ...
    L.y_ego_m(candidate), ...
    14, [0.95 0.35 0.1], 'filled', ...
    'DisplayName', 'Diagnostic surface 83391');

% Ground Truth vehicles - blue
scatter(nearby.x_ego_m, ...
    nearby.y_ego_m, ...
    110, [0.1 0.4 0.9], ...
    'filled', ...
    'DisplayName', 'Ground Truth vehicle centers');

% Label Ground Truth objects
for k = 1:height(nearby)

    text(nearby.x_ego_m(k) + 0.5, ...
        nearby.y_ego_m(k) + 0.5, ...
        string(nearby.object_id(k)), ...
        'FontSize', 10);

end

% Ego vehicle position
plot(0, 0, 'ks', ...
    'MarkerSize', 12, ...
    'LineWidth', 2, ...
    'DisplayName', 'Ego vehicle');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('GEMSTAR Frame 431: LiDAR and Ground Truth');

axis equal;
grid on;

xlim([-30 30]);
ylim([-15 15]);

legend('Location', 'bestoutside');

exportgraphics(fig1, fullfile(graphFolder, ...
    "task11_lidar_gt_overlay_frame431.png"), ...
    'Resolution', 300);

savefig(fig1, fullfile(graphFolder, ...
    "task11_lidar_gt_overlay_frame431.fig"));

%% 5. Forward-facing region only

fig2 = figure('Color', 'w', ...
    'Position', [100 100 1100 750]);

hold on;

scatter(L.x_ego_m, L.y_ego_m, ...
    8, [0.65 0.65 0.65], 'filled');

scatter(L.x_ego_m(candidate), ...
    L.y_ego_m(candidate), ...
    18, [0.95 0.35 0.1], 'filled');

front = nearby( ...
    nearby.x_ego_m >= 0 & ...
    nearby.x_ego_m <= 25 & ...
    abs(nearby.y_ego_m) <= 12, :);

scatter(front.x_ego_m, front.y_ego_m, ...
    110, [0.1 0.4 0.9], 'filled');

for k = 1:height(front)
    text(front.x_ego_m(k) + 0.3, ...
        front.y_ego_m(k) + 0.3, ...
        string(front.object_id(k)));
end

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('Frame 431 - Forward LiDAR Region');

axis equal;
grid on;

xlim([0 25]);
ylim([-12 12]);

%% 6. Save forward-view graph

exportgraphics(fig2, fullfile(graphFolder, ...
    "task11_lidar_gt_forward_frame431.png"), ...
    'Resolution', 300);

savefig(fig2, fullfile(graphFolder, ...
    "task11_lidar_gt_forward_frame431.fig"));

%% 7. Save validation summary

fid = fopen(fullfile(findingsFolder, ...
    "task11_frame431_alignment_notes.txt"), 'w');

assert(fid ~= -1, 'Unable to write findings.');

fprintf(fid, 'TASK 11.5R - LIDAR / GT ALIGNMENT\n');
fprintf(fid, 'Frame: 431\n');
fprintf(fid, 'Ego ID: 76895\n');
fprintf(fid, 'LiDAR points: %d\n', height(L));
fprintf(fid, 'GT vehicles within 35 m: %d\n', height(nearby));
fprintf(fid, 'GT vehicle centers in forward plot: %d\n', height(front));
fprintf(fid, 'Yaw/axis convention: provisional\n');
fprintf(fid, 'Sensor mounting and GT pose alignment: not yet validated\n');
fprintf(fid, 'Diagnostic surface label is not a vehicle classification\n');

fclose(fid);

%% 8. Archive MATLAB source

sourceFile = fullfile(root, ...
    "matlab", "task11_lidar_gt_alignment.m");

if isfile(sourceFile)
    copyfile(sourceFile, codeFolder);
end

fprintf('\nGT centers in forward region: %d\n', height(front));
fprintf('TASK 11.5R COMPLETED\n');
