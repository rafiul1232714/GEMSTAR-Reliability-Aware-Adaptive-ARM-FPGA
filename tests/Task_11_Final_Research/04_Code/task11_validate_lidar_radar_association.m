
%% TASK 11.7C - VALIDATE LIDAR RADAR ASSOCIATION
% Frame 150, GEMSTAR MOR100
% No Statistics Toolbox required.
% No Ground Truth or simulator IDs used for association.

clc;
clear;
close all;

%% 1. PROJECT FOLDERS

root = "E:\GEMSTAR_Project\sensor-health-monitor";
archive = fullfile(root, "tests", "Task_11_Final_Research");

csvDir = fullfile(archive, "02_CSV_Data");
graphDir = fullfile(archive, "01_Graphs");
codeDir = fullfile(archive, "04_Code");
findDir = fullfile(archive, "06_Research_Findings");

if ~isfolder(graphDir), mkdir(graphDir); end
if ~isfolder(codeDir), mkdir(codeDir); end
if ~isfolder(findDir), mkdir(findDir); end

%% 2. LOAD PREVIOUS RESULTS

L = readtable(fullfile(csvDir, ...
    "task11_frame150_independent_cluster_labels.csv"));

R = readtable(fullfile(csvDir, ...
    "task11_frame150_radar_cluster_association.csv"));

%% 3. SELECT LIDAR CLUSTER 1

Q = L(L.cluster_id == 1, :);

assert(~isempty(Q), "LiDAR Cluster 1 is empty.");

xyz = [Q.x_ego_m, Q.y_ego_m, Q.z_ego_m];

centroid = mean(xyz,1);
extent = max(xyz,[],1) - min(xyz,[],1);

fprintf('\nTASK 11.7C - ASSOCIATION VALIDATION\n');

fprintf('\n===== LIDAR CLUSTER =====\n');
fprintf('Points: %d\n',height(Q));

fprintf('Center X: %.3f m\n',centroid(1));
fprintf('Center Y: %.3f m\n',centroid(2));
fprintf('Center Z: %.3f m\n',centroid(3));

fprintf('X extent: %.3f m\n',extent(1));
fprintf('Y extent: %.3f m\n',extent(2));
fprintf('Z extent: %.3f m\n',extent(3));

%% 4. SELECT RADAR RETURNS WITHIN 1 M

threshold = 1.0;

near = R.nearest_cluster_xy_m <= threshold;
A = R(near,:);

fprintf('\n===== RADAR ASSOCIATION =====\n');

fprintf('Total Radar points: %d\n',height(R));
fprintf('Nearby Radar points: %d\n',height(A));

if ~isempty(A)
    disp(A(:, { ...
        'ray_index', ...
        'range_m', ...
        'doppler_hz', ...
        'x_ego_m', ...
        'y_ego_m', ...
        'nearest_cluster_xy_m'}));
end

%% 5. EXPERIMENTAL GEOMETRY FLAG

% Simple diagnostic rules, NOT a trained classifier.
% Long and narrow structures are flagged for review.

elongated = ...
    max(extent(1:2)) > 5.0 && ...
    min(extent(1:2)) < 1.0;

% A visible vehicle cluster may be only a partial surface,
% so this flag does not prove vehicle presence or absence.
if elongated
    geometryFlag = "ELONGATED_STRUCTURE";
else
    geometryFlag = "GEOMETRY_REQUIRES_REVIEW";
end

fprintf('\nGeometry flag: %s\n',geometryFlag);
fprintf('Vehicle detection: NOT CONFIRMED\n');

%% 6. VISUALIZATION

fig = figure('Color','w', ...
    'Position',[100 100 1100 700]);

hold on;

scatter(Q.x_ego_m, Q.y_ego_m, ...
    22,[0.1 0.45 0.9],'filled', ...
    'DisplayName','LiDAR Cluster 1');

scatter(R.x_ego_m(~near),R.y_ego_m(~near), ...
    45,[0.65 0.65 0.65],'filled', ...
    'DisplayName','Other Radar returns');

scatter(A.x_ego_m,A.y_ego_m, ...
    70,[0.9 0.2 0.1],'filled', ...
    'DisplayName','Radar within 1 m');

plot(centroid(1),centroid(2),'kp', ...
    'MarkerSize',15,'LineWidth',2, ...
    'DisplayName','LiDAR centroid');

xlabel('Forward X (m)');
ylabel('Lateral Y (m)');

title('Frame 150 - LiDAR Radar Association Validation');

axis equal;
grid on;
legend('Location','bestoutside');

exportgraphics(fig,fullfile(graphDir, ...
    'task11_frame150_association_validation.png'), ...
    'Resolution',300);

savefig(fig,fullfile(graphDir, ...
    'task11_frame150_association_validation.fig'));

%% 7. SAVE CSV DATA

writetable(A,fullfile(csvDir, ...
    'task11_frame150_nearby_radar_returns.csv'));

summary = table( ...
    height(Q), ...
    centroid(1),centroid(2),centroid(3), ...
    extent(1),extent(2),extent(3), ...
    height(R),height(A), ...
    geometryFlag, ...
    'VariableNames',{ ...
    'lidar_points', ...
    'center_x_m','center_y_m','center_z_m', ...
    'extent_x_m','extent_y_m','extent_z_m', ...
    'radar_total','radar_nearby', ...
    'geometry_flag'});

writetable(summary,fullfile(csvDir, ...
    'task11_frame150_association_summary.csv'));

%% 8. SAVE RESEARCH FINDINGS

reportFile = fullfile(findDir, ...
    'task11_frame150_association_validation.txt');

fid = fopen(reportFile,'w');

assert(fid ~= -1,'Cannot save research findings.');

fprintf(fid,'TASK 11.7C - ASSOCIATION VALIDATION\n');
fprintf(fid,'Frame: 150\n');
fprintf(fid,'LiDAR cluster points: %d\n',height(Q));
fprintf(fid,'Radar total: %d\n',height(R));
fprintf(fid,'Radar within 1 m: %d\n',height(A));
fprintf(fid,'LiDAR X extent: %.3f m\n',extent(1));
fprintf(fid,'LiDAR Y extent: %.3f m\n',extent(2));
fprintf(fid,'LiDAR Z extent: %.3f m\n',extent(3));
fprintf(fid,'Geometry flag: %s\n',char(geometryFlag));
fprintf(fid,'Coordinates: provisional\n');
fprintf(fid,'Ground Truth used for association: No\n');
fprintf(fid,'Vehicle detection: NOT CONFIRMED\n');

fclose(fid);

%% 9. ARCHIVE CODE

sourceFile = fullfile(root,'matlab', ...
    'task11_validate_lidar_radar_association.m');

if isfile(sourceFile)
    copyfile(sourceFile,codeDir,'f');
end

fprintf('\n===== SUMMARY =====\n');
disp(summary);

fprintf('\nTASK 11.7C COMPLETED\n');
