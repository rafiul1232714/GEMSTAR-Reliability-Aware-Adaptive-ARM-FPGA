%% Task 24.2.C.7.B - Nominal Common Vehicle-Frame Visualization
% Actual GEMSTAR SensorView frame 0.
% Transform: sensor-local UE -> nominal vehicle-relative OSI.
% IMPORTANT: Mount orientation and temporal alignment are not
% independently calibrated. These plots are diagnostic.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research';

csvDir = fullfile(root,'02_CSV_Data');
graphDir = fullfile(root,'03_Graphs');

lidarFile = fullfile(csvDir, ...
    'task24_02C_07_lidar_vehicle_frame000.csv');

radarFile = fullfile(csvDir, ...
    'task24_02C_07_radar_vehicle_frame000.csv');

assert(isfile(lidarFile),'LiDAR CSV missing');
assert(isfile(radarFile),'Radar CSV missing');

L = readtable(lidarFile,'TextType','string');
R = readtable(radarFile,'TextType','string');

assert(height(L)==5271,'LiDAR row count mismatch');
assert(height(R)==100,'Radar row count mismatch');

LC = L(L.Category=="CANDIDATE",:);
RC = R(R.Category=="CANDIDATE",:);

assert(height(LC)==1914,'LiDAR candidate count mismatch');
assert(height(RC)==32,'Radar candidate count mismatch');

mountCamera = [0.7 0 1.6];
mountLidar = [2.6 0 0.7];
mountRadar = [2.0 0 0.8];

%% CF-01: Common-frame 3D visualization

f1 = figure('Color','w','Position',[70 70 1200 800]);
hold on;

scatter3(LC.X_vehicle_OSI_m,LC.Y_vehicle_OSI_m, ...
    LC.Z_vehicle_OSI_m,10,[0.12 0.43 0.85], ...
    'filled','DisplayName','LiDAR candidates');

scatter3(RC.X_vehicle_OSI_m,RC.Y_vehicle_OSI_m, ...
    RC.Z_vehicle_OSI_m,65,[0.90 0.28 0.14], ...
    'filled','DisplayName','Radar candidates');

scatter3(mountCamera(1),mountCamera(2),mountCamera(3), ...
    130,'k','d','filled','DisplayName','Camera mount');

scatter3(mountLidar(1),mountLidar(2),mountLidar(3), ...
    130,[0 0.65 0.3],'^','filled','DisplayName','LiDAR mount');

scatter3(mountRadar(1),mountRadar(2),mountRadar(3), ...
    130,[0.75 0 0.75],'s','filled','DisplayName','Radar mount');

xlabel('Vehicle-relative OSI X (m)');
ylabel('Vehicle-relative OSI Y (m)');
zlabel('Vehicle-relative OSI Z (m)');

title({'CF-01 | Nominal common-frame LiDAR/Radar geometry', ...
       'Mount translations applied; extrinsics not independently calibrated'});

legend('Location','best');
axis equal;
grid on;
view(40,25);
hold off;

exportgraphics(f1,fullfile(graphDir, ...
    'task24_02C_07B_CF01_common_frame_3d.png'), ...
    'Resolution',200);

%% CF-02: Top-down X-Y comparison

f2 = figure('Color','w','Position',[110 100 1100 750]);
hold on;

scatter(LC.X_vehicle_OSI_m,LC.Y_vehicle_OSI_m, ...
    10,[0.12 0.43 0.85],'filled', ...
    'DisplayName','LiDAR candidates');

scatter(RC.X_vehicle_OSI_m,RC.Y_vehicle_OSI_m, ...
    55,[0.90 0.28 0.14],'filled', ...
    'DisplayName','Radar candidates');

scatter(mountLidar(1),mountLidar(2),110,'k','^','filled', ...
    'DisplayName','LiDAR origin');

scatter(mountRadar(1),mountRadar(2),110,'k','s','filled', ...
    'DisplayName','Radar origin');

xlabel('Vehicle-relative OSI X (m)');
ylabel('Vehicle-relative OSI Y (m)');
title('CF-02 | Nominal common-frame top-down view');

legend('Location','best');
axis equal;
grid on;
hold off;

exportgraphics(f2,fullfile(graphDir, ...
    'task24_02C_07B_CF02_common_frame_xy.png'), ...
    'Resolution',200);

%% CF-03: Side-view X-Z comparison

f3 = figure('Color','w','Position',[150 100 1100 750]);
hold on;

scatter(LC.X_vehicle_OSI_m,LC.Z_vehicle_OSI_m, ...
    10,[0.12 0.43 0.85],'filled', ...
    'DisplayName','LiDAR candidates');

scatter(RC.X_vehicle_OSI_m,RC.Z_vehicle_OSI_m, ...
    55,[0.90 0.28 0.14],'filled', ...
    'DisplayName','Radar candidates');

scatter(mountCamera(1),mountCamera(3),110,'k','d','filled', ...
    'DisplayName','Camera mount');

scatter(mountLidar(1),mountLidar(3),110,'k','^','filled', ...
    'DisplayName','LiDAR mount');

scatter(mountRadar(1),mountRadar(3),110,'k','s','filled', ...
    'DisplayName','Radar mount');

xlabel('Vehicle-relative OSI X (m)');
ylabel('Vehicle-relative OSI Z (m)');
title('CF-03 | Nominal common-frame side view');

legend('Location','best');
axis equal;
grid on;
hold off;

exportgraphics(f3,fullfile(graphDir, ...
    'task24_02C_07B_CF03_common_frame_xz.png'), ...
    'Resolution',200);

%% Verify generated files

names = {
    'task24_02C_07B_CF01_common_frame_3d.png'
    'task24_02C_07B_CF02_common_frame_xy.png'
    'task24_02C_07B_CF03_common_frame_xz.png'
};

for k = 1:numel(names)
    p = fullfile(graphDir,names{k});
    assert(isfile(p),'Missing output figure');
    info = dir(p);
    assert(info.bytes>0,'Empty figure file');
    fprintf('FIGURE_CREATED=%s\n',names{k});
end

fprintf('\n=== TASK 24.2.C.7.B COMMON-FRAME MATLAB ===\n');
fprintf('LIDAR_CANDIDATES=%d\n',height(LC));
fprintf('RADAR_CANDIDATES=%d\n',height(RC));
fprintf('TOTAL_CANDIDATES=%d\n',height(LC)+height(RC));
fprintf('FIGURES_CREATED=3\n');
fprintf('TRANSFORM_MODEL=NOMINAL_ZERO_ROTATION\n');
fprintf('TASK24_02C_07B_MATLAB_COMMON_FRAME_PASS\n');