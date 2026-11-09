
%% ============================================================
% TASK 13.3C - LIDAR / RADAR VS GROUND TRUTH BOX
% GEMSTAR MOR100 - Frame 150
%
% Uses Task 13.2A sensor reconstructions and
% Task 11 Ground Truth data.
%
% IMPORTANT:
% Task 13.2A sensor Y is Unreal-style positive Y.
% Ground Truth uses OSI-style positive Y.
% Therefore sensor ego Y is reversed here.
%
% The GT dimensions are interpreted as half-extents
% of world-axis-aligned actor bounds.
%
% INSIDE BOX DOES NOT PROVE OBJECT IDENTITY.
%% ============================================================

clc;
clear;
close all;

%% 1. PATHS

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

task11 = fullfile(root, ...
    'tests','Task_11_Final_Research');

task13 = fullfile(root, ...
    'tests','Task_13_Final_Research');

csvDir = fullfile(task13,'02_CSV_Data');
graphDir = fullfile(task13,'01_Graphs');
findDir = fullfile(task13,'06_Research_Findings');
codeDir = fullfile(task13,'04_Code');

folders = {csvDir,graphDir,findDir,codeDir};

for k = 1:numel(folders)
    if ~isfolder(folders{k})
        mkdir(folders{k});
    end
end

%% 2. LOAD RECORDED DATA

gtFile = fullfile(task11,'02_CSV_Data', ...
    'task11_groundtruth_objects.csv');

lidarFile = fullfile(csvDir, ...
    'task13_2a_lidar_common_frame.csv');

radarFile = fullfile(csvDir, ...
    'task13_2a_radar_common_frame.csv');

assert(isfile(gtFile),'Missing Ground Truth CSV');
assert(isfile(lidarFile),'Missing LiDAR CSV');
assert(isfile(radarFile),'Missing Radar CSV');

GT = readtable(gtFile);
L = readtable(lidarFile);
R = readtable(radarFile);

frameID = 150;
egoID = 76895;
targetID = 76865;

egoRows = GT(GT.frame == frameID & ...
    GT.object_id == egoID,:);

targetRows = GT(GT.frame == frameID & ...
    GT.object_id == targetID,:);

assert(height(egoRows)==1,'Ego GT row missing or duplicate');
assert(height(targetRows)==1,'Target GT row missing or duplicate');

assert(all(L.frame==frameID), ...
    'LiDAR CSV includes unexpected frames');

assert(all(R.frame==frameID), ...
    'Radar CSV includes unexpected frames');

ego = egoRows(1,:);
target = targetRows(1,:);

%% 3. GROUND TRUTH GEOMETRY

egoCenter = [ego.x_m,ego.y_m,ego.z_m];

targetCenter = [ ...
    target.x_m,target.y_m,target.z_m];

egoYaw = ego.yaw_rad;

% The exporter writes Unreal actor world-AABB half-extents
% directly into OSI dimension fields.
extent = [ ...
    target.length_m, ...
    target.width_m, ...
    target.height_m];

boxMin = targetCenter - extent;
boxMax = targetCenter + extent;

%% 4. SENSOR EGO COORDINATES INTO OSI CONVENTION

% Task 13.2A has X/Y/Z following local Unreal ray convention.
% Conversion Y -> -Y is supported by ToOSI.cpp.

lidarEgo = [ ...
    double(L.x_ego_m), ...
    -double(L.y_ego_m), ...
    double(L.z_ego_m)];

radarEgo = [ ...
    double(R.x_ego_m), ...
    -double(R.y_ego_m), ...
    double(R.z_ego_m)];

%% 5. TRANSFORM EGO COORDINATES INTO OSI WORLD

c = cos(egoYaw);
s = sin(egoYaw);

RegoToWorld = [ ...
    c,-s,0;
    s, c,0;
    0, 0,1];

% Row-vector representation.
lidarWorld = ...
    (RegoToWorld * lidarEgo')' + egoCenter;

radarWorld = ...
    (RegoToWorld * radarEgo')' + egoCenter;

% ASSUMPTION:
% Sensor ego-frame origin coincides with the recorded
% ego GT origin. This has not been independently verified.

%% 6. CALCULATE POINT-TO-BOX DISTANCES

% For each axis:
% distance is zero when the point lies inside its bounds.
%
% Outside distance:
% sqrt(dx^2 + dy^2 + dz^2)
%
% This is distance to the closed AABB volume, not
% necessarily to a visible physical car surface.

lidarAxisDistance = max( ...
    max(boxMin-lidarWorld, lidarWorld-boxMax),0);

radarAxisDistance = max( ...
    max(boxMin-radarWorld,radarWorld-boxMax),0);

lidarDistance = sqrt(sum(lidarAxisDistance.^2,2));

radarDistance = sqrt(sum(radarAxisDistance.^2,2));

insideL = all( ...
    lidarWorld >= boxMin & lidarWorld <= boxMax,2);

insideR = all( ...
    radarWorld >= boxMin & radarWorld <= boxMax,2);

nearL25 = lidarDistance <= 0.25;
nearL50 = lidarDistance <= 0.50;
nearL100 = lidarDistance <= 1.00;

nearR25 = radarDistance <= 0.25;
nearR50 = radarDistance <= 0.50;
nearR100 = radarDistance <= 1.00;

%% 7. PRINT COUNTS

fprintf('\n========================================\n');
fprintf('TASK 13.3C - BOX ASSOCIATION RESULTS\n');
fprintf('========================================\n');

fprintf('GT target: %d\n',targetID);
fprintf('LiDAR measurements: %d\n',height(L));
fprintf('Radar measurements: %d\n',height(R));

fprintf('\n--- LIDAR ---\n');
fprintf('Inside GT AABB: %d\n',sum(insideL));
fprintf('Within 0.25 m: %d\n',sum(nearL25));
fprintf('Within 0.50 m: %d\n',sum(nearL50));
fprintf('Within 1.00 m: %d\n',sum(nearL100));

fprintf('\n--- RADAR ---\n');
fprintf('Inside GT AABB: %d\n',sum(insideR));
fprintf('Within 0.25 m: %d\n',sum(nearR25));
fprintf('Within 0.50 m: %d\n',sum(nearR50));
fprintf('Within 1.00 m: %d\n',sum(nearR100));

fprintf('\nNOTE: Near counts include inside points.\n');

%% 8. SAVE POINT-LEVEL CSV FILES

% All table columns are numeric.
% array2table avoids the table-name assignment problem.

lidarMatrix = [ ...
    double(L.frame), ...
    double(L.ray_index), ...
    lidarWorld, ...
    lidarDistance, ...
    double(insideL), ...
    double(nearL25), ...
    double(nearL50), ...
    double(nearL100)];

lidarNames = { ...
    'frame','ray_index', ...
    'world_x_m','world_y_m','world_z_m', ...
    'distance_to_box_m', ...
    'inside_gt_box', ...
    'within_025m', ...
    'within_050m', ...
    'within_100m'};

lidarTable = array2table( ...
    lidarMatrix,'VariableNames',lidarNames);

radarMatrix = [ ...
    double(R.frame), ...
    radarWorld, ...
    radarDistance, ...
    double(insideR), ...
    double(nearR25), ...
    double(nearR50), ...
    double(nearR100)];

radarNames = { ...
    'frame', ...
    'world_x_m','world_y_m','world_z_m', ...
    'distance_to_box_m', ...
    'inside_gt_box', ...
    'within_025m', ...
    'within_050m', ...
    'within_100m'};

radarTable = array2table( ...
    radarMatrix,'VariableNames',radarNames);

lidarOut = fullfile(csvDir, ...
    'task13_3c_lidar_box_candidates.csv');

radarOut = fullfile(csvDir, ...
    'task13_3c_radar_box_candidates.csv');

writetable(lidarTable,lidarOut);
writetable(radarTable,radarOut);

%% 9. FIGURE 1 - WORLD XY TOP VIEW

fig1 = figure('Color','w', ...
    'Position',[80 80 1250 800]);

hold on;

% All measured points
scatter(lidarWorld(:,1),lidarWorld(:,2), ...
    9,[0.45 0.60 0.85],'filled');

scatter(radarWorld(:,1),radarWorld(:,2), ...
    50,[0.95 0.55 0.12],'filled');

% Candidate near-box points
scatter(lidarWorld(nearL50,1), ...
    lidarWorld(nearL50,2), ...
    28,[0.10 0.65 0.25],'filled');

scatter(radarWorld(nearR50,1), ...
    radarWorld(nearR50,2), ...
    95,[0.80 0.15 0.65],'filled');

% GT target world-AABB footprint
rectangle( ...
    'Position',[boxMin(1),boxMin(2), ...
    2*extent(1),2*extent(2)], ...
    'EdgeColor',[0.85 0.20 0.15], ...
    'LineWidth',2.5);

scatter(egoCenter(1),egoCenter(2), ...
    130,'k','filled');

scatter(targetCenter(1),targetCenter(2), ...
    120,[0.85 0.20 0.15],'filled');

xlabel('OSI world X (m)');
ylabel('OSI world Y (m)');

title('Task 13.3C - Sensor Measurements vs GT AABB');

axis equal;
grid on;

legend( ...
    {'All LiDAR','All Radar', ...
    'LiDAR within 0.5 m', ...
    'Radar within 0.5 m', ...
    'Target GT AABB', ...
    'Ego GT center','Target GT center'}, ...
    'Location','bestoutside');

topPNG = fullfile(graphDir, ...
    'task13_3c_sensor_gt_box_top_view.png');

topFIG = fullfile(graphDir, ...
    'task13_3c_sensor_gt_box_top_view.fig');

exportgraphics(fig1,topPNG,'Resolution',250);
savefig(fig1,topFIG);

%% 10. FIGURE 2 - DISTANCE TO GT BOX

fig2 = figure('Color','w', ...
    'Position',[110 110 1200 700]);

tiledlayout(1,2);

nexttile;

histogram(lidarDistance,40);
xlabel('Distance to GT AABB (m)');
ylabel('LiDAR point count');
title('LiDAR Point-to-Box Distance');
grid on;

nexttile;

histogram(radarDistance,20);
xlabel('Distance to GT AABB (m)');
ylabel('Radar return count');
title('Radar Point-to-Box Distance');
grid on;

distPNG = fullfile(graphDir, ...
    'task13_3c_box_distance_distribution.png');

distFIG = fullfile(graphDir, ...
    'task13_3c_box_distance_distribution.fig');

exportgraphics(fig2,distPNG,'Resolution',250);
savefig(fig2,distFIG);

%% 11. FIGURE 3 - VERTICAL POSITION OF CANDIDATES

fig3 = figure('Color','w', ...
    'Position',[130 130 1150 700]);

hold on;

scatter(lidarWorld(:,1),lidarWorld(:,3), ...
    8,[0.55 0.65 0.85],'filled');

scatter(lidarWorld(nearL50,1), ...
    lidarWorld(nearL50,3), ...
    35,[0.10 0.65 0.25],'filled');

scatter(radarWorld(nearR50,1), ...
    radarWorld(nearR50,3), ...
    75,[0.85 0.25 0.60],'filled');

% GT AABB vertical bounds
plot([boxMin(1) boxMax(1)], ...
    [boxMin(3) boxMin(3)], ...
    'r-','LineWidth',2);

plot([boxMin(1) boxMax(1)], ...
    [boxMax(3) boxMax(3)], ...
    'r-','LineWidth',2);

xlabel('OSI world X (m)');
ylabel('OSI world Z (m)');

title('Vertical Geometry of Near-Box Measurements');

grid on;

verticalPNG = fullfile(graphDir, ...
    'task13_3c_vertical_candidate_geometry.png');

verticalFIG = fullfile(graphDir, ...
    'task13_3c_vertical_candidate_geometry.fig');

exportgraphics(fig3,verticalPNG,'Resolution',250);
savefig(fig3,verticalFIG);

%% 12. SAVE NUMERICAL SUMMARY

summaryValues = [ ...
    frameID, ...
    targetID, ...
    height(L), ...
    height(R), ...
    sum(insideL), ...
    sum(insideR), ...
    sum(nearL25), ...
    sum(nearR25), ...
    sum(nearL50), ...
    sum(nearR50), ...
    sum(nearL100), ...
    sum(nearR100)];

summaryNames = { ...
    'frame','target_gt_id', ...
    'lidar_count','radar_count', ...
    'lidar_inside_box','radar_inside_box', ...
    'lidar_within_025m','radar_within_025m', ...
    'lidar_within_050m','radar_within_050m', ...
    'lidar_within_100m','radar_within_100m'};

summaryTable = array2table( ...
    summaryValues,'VariableNames',summaryNames);

summaryFile = fullfile(csvDir, ...
    'task13_3c_box_association_summary.csv');

writetable(summaryTable,summaryFile);

%% 13. SAVE RESEARCH FINDINGS

findFile = fullfile(findDir, ...
    'task13_3c_sensor_box_association_findings.txt');

fid = fopen(findFile,'w');

assert(fid~=-1,'Unable to save findings');

fprintf(fid,'TASK 13.3C - SENSOR BOX ASSOCIATION\n\n');

fprintf(fid,'Scenario: GEMSTAR MOR100\n');
fprintf(fid,'Frame: %d\n',frameID);
fprintf(fid,'Target GT ID: %d\n\n',targetID);

fprintf(fid,'LiDAR inside box: %d / %d\n', ...
    sum(insideL),height(L));

fprintf(fid,'Radar inside box: %d / %d\n', ...
    sum(insideR),height(R));

fprintf(fid,'LiDAR within 0.5m: %d\n',sum(nearL50));
fprintf(fid,'Radar within 0.5m: %d\n',sum(nearR50));

fprintf(fid,'\nLIMITATIONS\n');

fprintf(fid, ...
    'GT box uses world-axis bounding extents.\n');

fprintf(fid, ...
    'It is not a validated vehicle-aligned box.\n');

fprintf(fid, ...
    'Sensor and GT ego origins are assumed coincident.\n');

fprintf(fid, ...
    'Sensor points follow Task 13.2A reconstruction.\n');

fprintf(fid, ...
    'A point inside the box does not prove target identity.\n');

fprintf(fid, ...
    'No confirmed tri-sensor fusion is established.\n');

fclose(fid);

%% 14. ARCHIVE MATLAB CODE

sourceFile = fullfile(root,'matlab', ...
    'task13_gt_box_sensor_association.m');

if isfile(sourceFile)
    copyfile(sourceFile,codeDir,'f');
end

%% 15. FINAL SUMMARY

disp('===== TASK 13.3C NUMERICAL SUMMARY =====');
disp(summaryTable);

fprintf('\nSaved CSVs:\n');
fprintf('%s\n',lidarOut);
fprintf('%s\n',radarOut);
fprintf('%s\n',summaryFile);

fprintf('\nSaved figures:\n');
fprintf('%s\n',topPNG);
fprintf('%s\n',distPNG);
fprintf('%s\n',verticalPNG);

fprintf('\nTASK 13.3C COMPLETED SUCCESSFULLY\n');
