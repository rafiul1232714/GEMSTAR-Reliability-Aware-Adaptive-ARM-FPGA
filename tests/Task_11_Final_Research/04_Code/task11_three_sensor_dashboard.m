
%% TASK 11.8D - THREE-SENSOR DASHBOARD
% GEMSTAR MOR100 - Frame 150
% Camera + LiDAR + Radar
% No additional toolbox required.
% Synchronized visualization, NOT confirmed object fusion.

clc;
clear;
close all;

%% 1. PROJECT PATHS

root = "E:\GEMSTAR_Project\sensor-health-monitor";

archive = fullfile(root, ...
    "tests", "Task_11_Final_Research");

csvDir = fullfile(archive, "02_CSV_Data");
graphDir = fullfile(archive, "01_Graphs");
codeDir = fullfile(archive, "04_Code");
findDir = fullfile(archive, "06_Research_Findings");

if ~isfolder(graphDir), mkdir(graphDir); end
if ~isfolder(codeDir), mkdir(codeDir); end
if ~isfolder(findDir), mkdir(findDir); end

%% 2. INPUT FILES

cameraFile = fullfile(graphDir, ...
    "task11_mor100_frame0150_camera_0.ppm");

lidarFile = fullfile(csvDir, ...
    "task11_lidar_frame150_geometry.csv");

clusterFile = fullfile(csvDir, ...
    "task11_frame150_independent_cluster_labels.csv");

radarFile = fullfile(csvDir, ...
    "task11_frame150_radar_cluster_association.csv");

metadataFile = fullfile(csvDir, ...
    "task11_camera_frame150_metadata.csv");

assert(isfile(cameraFile), "Camera file missing.");
assert(isfile(lidarFile), "LiDAR file missing.");
assert(isfile(clusterFile), "Cluster file missing.");
assert(isfile(radarFile), "Radar file missing.");
assert(isfile(metadataFile), "Camera metadata missing.");

%% 3. LOAD DATA

I = imread(cameraFile);

L = readtable(lidarFile);
C = readtable(clusterFile);
R = readtable(radarFile);
M = readtable(metadataFile);

assert(all(L.frame == 150), "LiDAR frame mismatch.");
assert(all(C.frame == 150), "Cluster frame mismatch.");
assert(all(R.frame == 150), "Radar frame mismatch.");
assert(all(M.frame == 150), "Camera frame mismatch.");

cameraTime = M.timestamp_s(1);

%% 4. PRINT SENSOR COUNTS

fprintf('\n====================================\n');
fprintf('TASK 11.8D - THREE-SENSOR DASHBOARD\n');
fprintf('====================================\n');

fprintf('Frame: 150\n');
fprintf('Camera timestamp: %.6f s\n', cameraTime);
fprintf('Camera size: %d x %d\n', size(I,2), size(I,1));

fprintf('Total LiDAR points: %d\n', height(L));
fprintf('LiDAR candidate points: %d\n', height(C));

clustered = C.cluster_id > 0;

fprintf('LiDAR clustered points: %d\n', sum(clustered));
fprintf('Radar reflections: %d\n', height(R));

nearRadar = R.nearest_cluster_xy_m <= 1.0;

fprintf('Radar returns within 1 m: %d\n', sum(nearRadar));

% Compare recorded timestamps where available.
if ismember('time_s', L.Properties.VariableNames)
    fprintf('LiDAR timestamp: %.6f s\n', L.time_s(1));
    fprintf('Camera-LiDAR delta: %.6f s\n', ...
        cameraTime - L.time_s(1));
end

if ismember('time_s', R.Properties.VariableNames)
    fprintf('Radar timestamp: %.6f s\n', R.time_s(1));
    fprintf('Camera-Radar delta: %.6f s\n', ...
        cameraTime - R.time_s(1));
end

%% 5. CREATE COMBINED DASHBOARD

fig = figure( ...
    'Color', 'w', ...
    'Position', [50 50 1500 850]);

t = tiledlayout(2,2, ...
    'TileSpacing','compact', ...
    'Padding','compact');

%% PANEL 1 - CAMERA IMAGE

nexttile(t,1);

image(I);
axis image off;

title('Camera - Frame 150');

%% PANEL 2 - ALL LIDAR POINTS

nexttile(t,2);

hold on;

scatter(L.x_ego_m, L.y_ego_m, ...
    5, [0.75 0.75 0.75], 'filled', ...
    'DisplayName','LiDAR points');

scatter(C.x_ego_m(clustered), ...
    C.y_ego_m(clustered), ...
    15, [0.1 0.45 0.9], 'filled', ...
    'DisplayName','LiDAR Cluster');

plot(0,0,'ks', ...
    'MarkerSize',8, ...
    'LineWidth',1.5, ...
    'DisplayName','Ego origin');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('LiDAR - Geometry-only Cluster');

axis equal;
grid on;
legend('Location','best');

%% PANEL 3 - RADAR REFLECTIONS

nexttile(t,3);

hold on;

scatter(R.x_ego_m, R.y_ego_m, ...
    40, [0.85 0.2 0.2], 'filled', ...
    'DisplayName','Radar returns');

scatter(R.x_ego_m(nearRadar), ...
    R.y_ego_m(nearRadar), ...
    75, [0.1 0.65 0.2], 'filled', ...
    'DisplayName','Within 1 m of LiDAR cluster');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('Radar - Spatial Observations');

axis equal;
grid on;
legend('Location','best');

%% PANEL 4 - LIDAR AND RADAR OVERLAY

nexttile(t,4);

hold on;

scatter(C.x_ego_m(clustered), ...
    C.y_ego_m(clustered), ...
    18, [0.1 0.45 0.9], 'filled', ...
    'DisplayName','LiDAR Cluster');

scatter(R.x_ego_m(~nearRadar), ...
    R.y_ego_m(~nearRadar), ...
    35, [0.6 0.6 0.6], 'filled', ...
    'DisplayName','Other Radar');

scatter(R.x_ego_m(nearRadar), ...
    R.y_ego_m(nearRadar), ...
    65, [0.9 0.2 0.1], 'filled', ...
    'DisplayName','Nearby Radar');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('LiDAR-Radar Proximity');

axis equal;
grid on;
legend('Location','best');

sgtitle('GEMSTAR MOR100 - Three-Sensor Inspection, Frame 150');

%% 6. SAVE DASHBOARD

pngFile = fullfile(graphDir, ...
    "task11_frame150_three_sensor_dashboard.png");

figFile = fullfile(graphDir, ...
    "task11_frame150_three_sensor_dashboard.fig");

exportgraphics(fig,pngFile,'Resolution',300);
savefig(fig,figFile);

%% 7. SAVE RESEARCH FINDINGS

reportFile = fullfile(findDir, ...
    "task11_three_sensor_dashboard_findings.txt");

fid = fopen(reportFile,'w');

assert(fid ~= -1, "Unable to write research report.");

fprintf(fid,'TASK 11.8D - THREE-SENSOR DASHBOARD\n');
fprintf(fid,'Frame: 150\n');
fprintf(fid,'Camera timestamp: %.6f s\n',cameraTime);
fprintf(fid,'LiDAR total points: %d\n',height(L));
fprintf(fid,'LiDAR candidate points: %d\n',height(C));
fprintf(fid,'LiDAR clustered points: %d\n',sum(clustered));
fprintf(fid,'Radar reflections: %d\n',height(R));
fprintf(fid,'Radar within 1 m: %d\n',sum(nearRadar));

fprintf(fid,'\nResearch limitations:\n');
fprintf(fid,'Frame numbers matched across three sensors.\n');
fprintf(fid,'Timestamp agreement must be checked.\n');
fprintf(fid,'Sensor coordinate convention remains provisional.\n');
fprintf(fid,'LiDAR cluster is an elongated structure.\n');
fprintf(fid,'Camera object detection not yet implemented.\n');
fprintf(fid,'Object-level three-sensor fusion not yet confirmed.\n');

fclose(fid);

%% 8. ARCHIVE MATLAB CODE

sourceFile = fullfile(root, ...
    "matlab", "task11_three_sensor_dashboard.m");

if isfile(sourceFile)
    copyfile(sourceFile,codeDir,'f');
end

%% 9. FINAL RESULT

fprintf('\nDashboard saved:\n%s\n',pngFile);

fprintf('\nTASK 11.8D COMPLETED SUCCESSFULLY\n');
