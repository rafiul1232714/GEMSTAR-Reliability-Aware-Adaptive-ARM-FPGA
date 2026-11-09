%% Task 24.2.C.4 - Recorded Sensor Mount Geometry
% Source: 372_GEMSTAR OSI recorded mounting_position metadata.
% This is nominal mounting geometry, not measured optical calibration.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research';

csvFile = fullfile(root, '02_CSV_Data', ...
    'task24_02C_03_cross_sensor_transform_validation.csv');

graphDir = fullfile(root, '03_Graphs');

assert(isfile(csvFile), 'Transformation CSV missing.');

T = readtable(csvFile, 'TextType', 'string');

assert(height(T) == 45, 'Expected 45 validation rows.');

errors = T.RoundTripError_m;

assert(all(isfinite(errors)), 'Nonfinite transformation error.');
assert(max(abs(errors)) <= 1e-9, ...
    'Unexpected round-trip error.');

%% Recorded vehicle-relative OSI mounting positions

names = {'Camera','LiDAR','Radar'};

mounts = [
    0.7  0.0  1.6
    2.6  0.0  0.7
    2.0  0.0  0.8
];

colors = lines(3);

%% Figure 1: Three-dimensional sensor mounting geometry

f1 = figure('Color','w','Position',[100 100 1050 720]);

hold on;

for k = 1:3
    scatter3(mounts(k,1),mounts(k,2),mounts(k,3), ...
        150,colors(k,:),'filled');

    text(mounts(k,1)+0.08, ...
        mounts(k,2)+0.03, ...
        mounts(k,3)+0.07, ...
        names{k},'FontSize',12);

    plot3([mounts(k,1) mounts(k,1)], ...
        [mounts(k,2) mounts(k,2)], ...
        [0 mounts(k,3)], ...
        ':','Color',colors(k,:));
end

plot3(mounts(:,1),mounts(:,2),mounts(:,3), ...
    '--k','LineWidth',1.2);

quiver3(0,0,0,0.7,0,0,0,'r','LineWidth',2);
quiver3(0,0,0,0,0.7,0,0,'g','LineWidth',2);
quiver3(0,0,0,0,0,0.7,0,'b','LineWidth',2);

xlabel('Vehicle-relative X (m)');
ylabel('Vehicle-relative Y (m)');
zlabel('Vehicle-relative Z (m)');

title('Recorded Camera, LiDAR and Radar mounting geometry');
legend(names,'Location','best');

grid on;
axis equal;
view(35,25);
hold off;

exportgraphics(f1,fullfile(graphDir, ...
    'task24_02C_04_sensor_mount_geometry_3d.png'), ...
    'Resolution',200);

%% Figure 2: Mounting positions in vehicle X-Z plane

f2 = figure('Color','w','Position',[150 100 1000 650]);

hold on;

for k = 1:3
    scatter(mounts(k,1),mounts(k,3), ...
        160,colors(k,:),'filled');

    text(mounts(k,1)+0.08,mounts(k,3)+0.05, ...
        sprintf('%s (%.2f, %.2f) m', ...
        names{k},mounts(k,1),mounts(k,3)));
end

xlabel('Vehicle-relative X (m)');
ylabel('Vehicle-relative Z (m)');
title('Sensor mounting offsets in the vehicle X-Z plane');

xlim([0 3.5]);
ylim([0 2.2]);
grid on;
axis equal;
hold off;

exportgraphics(f2,fullfile(graphDir, ...
    'task24_02C_04_sensor_mount_geometry_xz.png'), ...
    'Resolution',200);

%% Numerical evidence summary

fprintf('\n=== TASK 24.2.C.4 MATLAB GEOMETRY ===\n');
fprintf('VALIDATION_ROWS=%d\n',height(T));
fprintf('MAX_ROUNDTRIP_ERROR_M=%.12f\n',max(abs(errors)));

for k = 1:3
    fprintf('MOUNT_%s_XYZ_M=%.3f,%.3f,%.3f\n', ...
        upper(names{k}),mounts(k,:));
end

fprintf('FIGURES_CREATED=2\n');
fprintf('TASK24_02C_04_MATLAB_GEOMETRY_PASS\n');