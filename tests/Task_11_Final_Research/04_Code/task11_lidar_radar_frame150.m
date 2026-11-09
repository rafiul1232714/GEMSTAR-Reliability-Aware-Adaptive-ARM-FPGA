
%% TASK 11.7A - LIDAR RADAR SPATIAL COMPARISON
% GEMSTAR MOR100 - Frame 150
% No Statistics Toolbox required.
% No Ground Truth used for association.

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
findingsDir = fullfile(archive, "06_Research_Findings");

if ~isfolder(graphDir), mkdir(graphDir); end
if ~isfolder(codeDir), mkdir(codeDir); end
if ~isfolder(findingsDir), mkdir(findingsDir); end

%% 2. LOAD LIDAR CLUSTERS AND RADAR

L = readtable(fullfile(csvDir, ...
    "task11_frame150_independent_cluster_labels.csv"));

Rall = readtable(fullfile(csvDir, ...
    "task11_radar_measurements.csv"));

R = Rall(Rall.frame == 150 & ...
    Rall.range_m >= 0.1 & ...
    isfinite(Rall.range_m), :);

fprintf('\nTASK 11.7A - LIDAR RADAR COMPARISON\n');
fprintf('LiDAR candidate points: %d\n', height(L));
fprintf('Radar reflections: %d\n', height(R));

%% 3. RECONSTRUCT RADAR COORDINATES

% Confirmed Radar mount in meters
mountX = 2.0;
mountY = 0.0;
mountZ = 0.8;

r = R.range_m;
az = R.horizontal_angle_rad;
el = R.vertical_angle_rad;

% Provisional lateral sign convention.
% Matches our reconstructed LiDAR coordinate system.
radarX = mountX + r .* cos(el) .* cos(az);
radarY = mountY - r .* cos(el) .* sin(az);
radarZ = mountZ + r .* sin(el);

R.x_ego_m = radarX;
R.y_ego_m = radarY;
R.z_ego_m = radarZ;

%% 4. EXTRACT VALID LIDAR CLUSTERS

ids = unique(L.cluster_id(L.cluster_id > 0));

fprintf('LiDAR clusters: %d\n', numel(ids));

%% 5. TOP VIEW OVERLAY

fig1 = figure('Color','w', ...
    'Position',[100 100 1100 750]);

hold on;

colors = lines(max(1, numel(ids)));

for k = 1:numel(ids)

    idx = L.cluster_id == ids(k);

    scatter(L.x_ego_m(idx), ...
        L.y_ego_m(idx), ...
        22, colors(k,:), 'filled', ...
        'DisplayName', ...
        sprintf('LiDAR Cluster %d', ids(k)));

end

scatter(radarX, radarY, ...
    55, [0.9 0.15 0.15], 'filled', ...
    'DisplayName','Radar reflections');

plot(0,0,'ks', ...
    'MarkerSize',11,'LineWidth',2, ...
    'DisplayName','Ego origin');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('Frame 150 - LiDAR and Radar Spatial Overlay');

axis equal;
grid on;
legend('Location','bestoutside');

exportgraphics(fig1,fullfile(graphDir, ...
    'task11_frame150_lidar_radar_overlay.png'), ...
    'Resolution',300);

savefig(fig1,fullfile(graphDir, ...
    'task11_frame150_lidar_radar_overlay.fig'));

%% 6. 3D OVERLAY

fig2 = figure('Color','w', ...
    'Position',[100 100 1100 750]);

hold on;

for k = 1:numel(ids)

    idx = L.cluster_id == ids(k);

    scatter3(L.x_ego_m(idx), ...
        L.y_ego_m(idx), ...
        L.z_ego_m(idx), ...
        22, colors(k,:), 'filled');

end

scatter3(radarX,radarY,radarZ, ...
    65,[0.9 0.15 0.15],'filled');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');
zlabel('Height Z (m)');

title('Frame 150 - LiDAR Radar 3D Comparison');

axis equal;
grid on;
view(45,25);

exportgraphics(fig2,fullfile(graphDir, ...
    'task11_frame150_lidar_radar_3d.png'), ...
    'Resolution',300);

savefig(fig2,fullfile(graphDir, ...
    'task11_frame150_lidar_radar_3d.fig'));

%% 7. SAVE RADAR POINTS

writetable(R, fullfile(csvDir, ...
    'task11_radar_frame150_points.csv'));

%% 8. SIMPLE SPATIAL DISTANCE DIAGNOSTIC

% Compare each Radar point with LiDAR candidate points.
% This is NOT object-level association.

lidarXYZ = [
    L.x_ego_m, ...
    L.y_ego_m, ...
    L.z_ego_m
];

radarXYZ = [radarX, radarY, radarZ];

nearestDistance = nan(height(R),1);

if ~isempty(lidarXYZ)

    for i = 1:height(R)

        delta = lidarXYZ - radarXYZ(i,:);

        distance = sqrt(sum(delta.^2,2));

        nearestDistance(i) = min(distance);

    end

end

R.nearest_lidar_distance_m = nearestDistance;

writetable(R, fullfile(csvDir, ...
    'task11_radar_lidar_distance_frame150.csv'));

fprintf('\n===== NEAREST LIDAR DISTANCE =====\n');

fprintf('Mean: %.3f m\n', ...
    mean(nearestDistance,'omitnan'));

fprintf('Minimum: %.3f m\n', ...
    min(nearestDistance));

fprintf('Maximum: %.3f m\n', ...
    max(nearestDistance));

%% 9. SAVE RESEARCH NOTES

fid = fopen(fullfile(findingsDir, ...
    'task11_frame150_lidar_radar_comparison.txt'),'w');

assert(fid ~= -1, 'Cannot write findings.');

fprintf(fid,'TASK 11.7A - LIDAR RADAR COMPARISON\n');
fprintf(fid,'Frame: 150\n');
fprintf(fid,'LiDAR candidate points: %d\n',height(L));
fprintf(fid,'Radar reflections: %d\n',height(R));
fprintf(fid,'LiDAR clusters: %d\n',numel(ids));
fprintf(fid,'Coordinates: provisional ego-local\n');
fprintf(fid,'GT used for association: No\n');
fprintf(fid,'Association status: NOT CONFIRMED\n');

fclose(fid);

%% 10. ARCHIVE SCRIPT

sourceFile = fullfile(root,'matlab', ...
    'task11_lidar_radar_frame150.m');

if isfile(sourceFile)
    copyfile(sourceFile,codeDir);
end

fprintf('\nTASK 11.7A COMPLETED\n');
