%% Task 24.2.C.6.B - Actual GEMSTAR Sensor Point Clouds
% Source: 372_GEMSTAR SensorView frame 0.
% Sensor-local Unreal axes. NOT vehicle-frame calibrated.
% CANDIDATE = positive TOF/signal and range > 0.01 m.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research';

csvDir = fullfile(root,'02_CSV_Data');
graphDir = fullfile(root,'03_Graphs');

lidarFile = fullfile(csvDir, ...
    'task24_02C_06A_lidar_points_frame000.csv');

radarFile = fullfile(csvDir, ...
    'task24_02C_06A_radar_points_frame000.csv');

assert(isfile(lidarFile),'LiDAR CSV missing');
assert(isfile(radarFile),'Radar CSV missing');

L = readtable(lidarFile,'TextType','string');
R = readtable(radarFile,'TextType','string');

assert(height(L)==5271,'Unexpected LiDAR row count');
assert(height(R)==100,'Unexpected Radar row count');

LC = L(L.Category=="CANDIDATE",:);
RC = R(R.Category=="CANDIDATE",:);

assert(height(LC)==1914,'Unexpected LiDAR candidate count');
assert(height(RC)==32,'Unexpected Radar candidate count');

fprintf('\n=== TASK 24.2.C.6.B MATLAB POINT CLOUDS ===\n');
fprintf('LIDAR_CANDIDATES=%d\n',height(LC));
fprintf('RADAR_CANDIDATES=%d\n',height(RC));
fprintf('LIDAR_NEAR_ZERO=%d\n',sum(L.Category=="NEAR_ZERO"));
fprintf('RADAR_NEAR_ZERO=%d\n',sum(R.Category=="NEAR_ZERO"));

%% PC-01: LiDAR reconstructed 3D points

f1 = figure('Color','w','Position',[80 80 1100 760]);

scatter3(LC.X_UE_local_m,LC.Y_UE_local_m, ...
    LC.Z_UE_local_m,12,LC.Range_m,'filled');

xlabel('LiDAR-local Unreal X (m)');
ylabel('LiDAR-local Unreal Y (m)');
zlabel('LiDAR-local Unreal Z (m)');

title('PC-01 | GEMSTAR LiDAR reconstructed points, frame 0');
cb = colorbar;
cb.Label.String = 'Range (m)';
axis equal;
grid on;
view(40,25);

exportgraphics(f1,fullfile(graphDir, ...
    'task24_02C_06B_PC01_lidar_3d.png'), ...
    'Resolution',200);

%% PC-02: Radar reconstructed 3D points

f2 = figure('Color','w','Position',[120 100 1100 760]);

scatter3(RC.X_UE_local_m,RC.Y_UE_local_m, ...
    RC.Z_UE_local_m,65,RC.Range_m,'filled');

xlabel('Radar-local Unreal X (m)');
ylabel('Radar-local Unreal Y (m)');
zlabel('Radar-local Unreal Z (m)');

title('PC-02 | GEMSTAR Radar reconstructed points, frame 0');
cb = colorbar;
cb.Label.String = 'Range (m)';
axis equal;
grid on;
view(40,25);

exportgraphics(f2,fullfile(graphDir, ...
    'task24_02C_06B_PC02_radar_3d.png'), ...
    'Resolution',200);

%% PC-03: Comparison in separate sensor-local coordinates
% Overlay is illustrative ONLY.
% Sensor origins are independently located at (0,0,0).
% Points are NOT yet expressed in a common vehicle frame.

f3 = figure('Color','w','Position',[160 100 1150 760]);

hold on;

scatter3(LC.X_UE_local_m,LC.Y_UE_local_m, ...
    LC.Z_UE_local_m,12,[0.15 0.45 0.85], ...
    'filled','DisplayName','LiDAR-local candidates');

scatter3(RC.X_UE_local_m,RC.Y_UE_local_m, ...
    RC.Z_UE_local_m,65,[0.85 0.25 0.15], ...
    'filled','DisplayName','Radar-local candidates');

xlabel('Sensor-local Unreal X (m)');
ylabel('Sensor-local Unreal Y (m)');
zlabel('Sensor-local Unreal Z (m)');

title({'PC-03 | LiDAR / Radar local-frame comparison', ...
       'NOT registered to a common vehicle coordinate frame'});

legend('Location','best');
axis equal;
grid on;
view(40,25);
hold off;

exportgraphics(f3,fullfile(graphDir, ...
    'task24_02C_06B_PC03_local_frame_comparison.png'), ...
    'Resolution',200);

%% Verification

names = {
    'task24_02C_06B_PC01_lidar_3d.png'
    'task24_02C_06B_PC02_radar_3d.png'
    'task24_02C_06B_PC03_local_frame_comparison.png'
};

for k = 1:numel(names)
    path = fullfile(graphDir,names{k});
    assert(isfile(path),'Missing exported figure');
    info = dir(path);
    assert(info.bytes>0,'Empty exported figure');
    fprintf('FIGURE_CREATED=%s\n',names{k});
end

fprintf('FIGURES_CREATED=3\n');
fprintf('TASK24_02C_06B_MATLAB_POINT_CLOUD_PASS\n');