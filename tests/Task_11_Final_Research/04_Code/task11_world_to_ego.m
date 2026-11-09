
%% TASK 11.5Q - WORLD TO EGO TRANSFORMATION
% GEMSTAR MOR100
% Ground Truth ego object ID: 76895
% Verified using vehicle mapping CSV
%
% Uses XY rotation under an assumed yaw convention.
% Axis conventions must be validated before fusion.

clc;
clear;
close all;

%% 1. FOLDERS

root = "E:\GEMSTAR_Project\sensor-health-monitor";

archive = fullfile(root, ...
    "tests", "Task_11_Final_Research");

csvFolder = fullfile(archive, "02_CSV_Data");
graphFolder = fullfile(archive, "01_Graphs");
codeFolder = fullfile(archive, "04_Code");

%% 2. LOAD GROUND TRUTH

GT = readtable(fullfile(csvFolder, ...
    "task11_groundtruth_objects.csv"), ...
    'TextType', 'string');

%% 3. SELECT FRAME AND EGO VEHICLE

frameNumber = 431;
egoID = 76895;

F = GT(GT.frame == frameNumber, :);

ego = F(F.object_id == egoID, :);

assert(height(ego) == 1, ...
    "Expected exactly one ego vehicle.");

fprintf('\nTASK 11.5Q - WORLD TO EGO\n');

fprintf('Ego object ID: %d\n', egoID);

fprintf('Ego world X: %.3f m\n', ego.x_m);
fprintf('Ego world Y: %.3f m\n', ego.y_m);
fprintf('Ego yaw: %.4f rad\n', ego.yaw_rad);

%% 4. CALCULATE POSITION DIFFERENCES

dx = F.x_m - ego.x_m;
dy = F.y_m - ego.y_m;
dz = F.z_m - ego.z_m;

%% 5. ROTATE INTO EGO FRAME
% Assumes world and ego XY coordinates follow
% a conventional rotation by ego yaw.
% Requires validation against recorded sensor data.

yaw = ego.yaw_rad;

x_ego = cos(yaw).*dx + sin(yaw).*dy;

y_ego = -sin(yaw).*dx + cos(yaw).*dy;

z_ego = dz;

%% 6. CREATE OUTPUT TABLE

R = table( ...
    F.frame, ...
    F.object_id, ...
    F.model_reference, ...
    x_ego, ...
    y_ego, ...
    z_ego, ...
    'VariableNames', { ...
    'frame', ...
    'object_id', ...
    'model_reference', ...
    'x_ego_m', ...
    'y_ego_m', ...
    'z_ego_m'});

%% 7. DISPLAY VEHICLE POSITIONS

vehicles = contains(R.model_reference, ...
    ["Car", "Truck", "Bus"]);

V = R(vehicles, :);

fprintf('\n===== VEHICLES IN EGO COORDINATES =====\n');

disp(V);

%% 8. SELECT NEARBY VEHICLES

distance = hypot(V.x_ego_m, V.y_ego_m);

nearby = V(distance <= 30 & ...
    V.object_id ~= egoID, :);

fprintf('\n===== VEHICLES WITHIN 30 METERS =====\n');

disp(nearby);

%% 9. PLOT EGO-RELATIVE VEHICLE POSITIONS

fig = figure('Color', 'w', ...
    'Position', [100 100 1000 700]);

hold on;

scatter(V.x_ego_m, V.y_ego_m, ...
    60, 'filled');

plot(0, 0, 'rs', ...
    'MarkerSize', 12, ...
    'LineWidth', 2);

for k = 1:height(V)

    text(V.x_ego_m(k) + 1, ...
        V.y_ego_m(k) + 1, ...
        string(V.object_id(k)), ...
        'FontSize', 9);

end

xlabel('Ego Forward X (m)');
ylabel('Ego Lateral Y (m)');

title('GEMSTAR Ground Truth - Ego Frame 431');

grid on;
axis equal;

xlim([-40 40]);
ylim([-40 40]);

exportgraphics(fig, fullfile(graphFolder, ...
    "task11_groundtruth_ego_frame431.png"), ...
    'Resolution', 300);

savefig(fig, fullfile(graphFolder, ...
    "task11_groundtruth_ego_frame431.fig"));

%% 10. SAVE RESEARCH DATA

writetable(R, fullfile(csvFolder, ...
    "task11_groundtruth_ego_frame431.csv"));

writetable(nearby, fullfile(csvFolder, ...
    "task11_nearby_vehicles_frame431.csv"));

%% 11. ARCHIVE CODE

sourceFile = fullfile(root, ...
    "matlab", "task11_world_to_ego.m");

if isfile(sourceFile)
    copyfile(sourceFile, codeFolder);
end

fprintf('\nTASK 11.5Q COMPLETED\n');
fprintf('Nearby vehicles: %d\n', height(nearby));
