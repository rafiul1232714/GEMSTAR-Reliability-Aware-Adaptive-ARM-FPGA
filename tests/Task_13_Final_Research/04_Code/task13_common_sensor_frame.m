
%% ============================================================
% TASK 13.2A - COMMON LIDAR AND RADAR COORDINATE FRAME
%
% GEMSTAR MOR100 - Frame 150
%
% FIXED VERSION
%
% Main corrections:
% 1. MATLAB table variable names fixed.
% 2. Row/column dimensions standardized.
% 3. LiDAR ray indices checked.
% 4. Invalid measurements filtered.
% 5. Reconstruction comparison added.
% 6. Research outputs archived automatically.
%
% IMPORTANT:
% The reconstruction uses OSI-derived Task 11 CSV files.
% It does not independently re-decode the original OSI.
% Sensor mounting rotations are assumed to be zero.
%% ============================================================

clc;
clear;
close all;

%% 1. PROJECT PATHS

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

task11 = fullfile(root, ...
    'tests', 'Task_11_Final_Research');

task13 = fullfile(root, ...
    'tests', 'Task_13_Final_Research');

graphDir = fullfile(task13, '01_Graphs');
csvDir   = fullfile(task13, '02_CSV_Data');
findDir  = fullfile(task13, '06_Research_Findings');
codeDir  = fullfile(task13, '04_Code');
refDir   = fullfile(task13, '05_Raw_Data_References');

folders = {graphDir, csvDir, findDir, codeDir, refDir};

for k = 1:numel(folders)

    if ~isfolder(folders{k})
        mkdir(folders{k});
    end

end

%% 2. INPUT FILES

lidarFile = fullfile(task11, ...
    '02_CSV_Data', ...
    'task11_lidar_frame150_geometry.csv');

radarFile = fullfile(task11, ...
    '02_CSV_Data', ...
    'task11_frame150_radar_cluster_association.csv');

assert(isfile(lidarFile), ...
    'Task 11 LiDAR geometry CSV is missing.');

assert(isfile(radarFile), ...
    'Task 11 Radar CSV is missing.');

L = readtable(lidarFile, ...
    'VariableNamingRule', 'preserve');

R = readtable(radarFile, ...
    'VariableNamingRule', 'preserve');

fprintf('\n========================================\n');
fprintf('TASK 13.2A - COMMON SENSOR FRAME\n');
fprintf('========================================\n');

fprintf('Original LiDAR rows: %d\n', height(L));
fprintf('Original Radar rows: %d\n', height(R));

%% 3. CHECK REQUIRED COLUMNS

lidarRequired = { ...
    'frame', ...
    'ray_index', ...
    'range_m', ...
    'x_ego_m', ...
    'y_ego_m', ...
    'z_ego_m'};

radarRequired = { ...
    'frame', ...
    'range_m', ...
    'horizontal_angle_rad', ...
    'vertical_angle_rad', ...
    'x_ego_m', ...
    'y_ego_m', ...
    'z_ego_m'};

assert(all(ismember(lidarRequired, ...
    L.Properties.VariableNames)), ...
    'Required LiDAR columns are missing.');

assert(all(ismember(radarRequired, ...
    R.Properties.VariableNames)), ...
    'Required Radar columns are missing.');

%% 4. SENSOR MOUNTING POSITIONS

% GEMSTAR DefaultGemstar.ini configuration
% Units: metres
%
% Zero rotations assumed.

cameraPos = [0.70, 0.00, 1.60];
lidarPos  = [2.60, 0.00, 0.70];
radarPos  = [2.00, 0.00, 0.80];

%% 5. LIDAR CONFIGURATION

% Values from previously inspected GEMSTAR configuration.

nH = 251;
nV = 21;

fovH = deg2rad(90);
fovV = deg2rad(20);

totalRays = nH * nV;

fprintf('\nLiDAR horizontal rays: %d\n', nH);
fprintf('LiDAR vertical rays: %d\n', nV);
fprintf('LiDAR total rays: %d\n', totalRays);

%% 6. PREPARE LIDAR DATA

lidarFrame = double(L.frame(:));
rayIndex   = double(L.ray_index(:));
lidarRange = double(L.range_m(:));

oldLX = double(L.x_ego_m(:));
oldLY = double(L.y_ego_m(:));
oldLZ = double(L.z_ego_m(:));

% Verify zero-based ray indices.
validL = ...
    isfinite(lidarFrame) & ...
    isfinite(rayIndex) & ...
    isfinite(lidarRange) & ...
    lidarRange > 0 & ...
    rayIndex >= 0 & ...
    rayIndex < totalRays & ...
    rayIndex == floor(rayIndex);

fprintf('Valid LiDAR measurements: %d\n', sum(validL));
fprintf('Rejected LiDAR measurements: %d\n', sum(~validL));

lidarFrame = lidarFrame(validL);
rayIndex   = rayIndex(validL);
lidarRange = lidarRange(validL);

oldLX = oldLX(validL);
oldLY = oldLY(validL);
oldLZ = oldLZ(validL);

%% 7. RECONSTRUCT LIDAR ANGLES

% Verified from SimpleLidar.cpp:
%
% horizontal_index = Index % Number_of_rays_horizontal
% vertical_index   = Index / Number_of_rays_horizontal
%
% Horizontal ray index changes fastest.

hIndex = mod(rayIndex, nH);

vIndex = floor(rayIndex ./ nH);

thetaL = ...
    -fovH / 2 + ...
    hIndex .* fovH / (nH - 1);

phiL = ...
    -fovV / 2 + ...
    vIndex .* fovV / (nV - 1);

%% 8. RECONSTRUCT LIDAR LOCAL COORDINATES

% Unreal ray direction:
%
% X = r*cos(pitch)*cos(yaw)
% Y = r*cos(pitch)*sin(yaw)
% Z = r*sin(pitch)

xLlocal = lidarRange .* cos(phiL) .* cos(thetaL);

yLlocal = lidarRange .* cos(phiL) .* sin(thetaL);

zLlocal = lidarRange .* sin(phiL);

%% 9. TRANSFORM LIDAR INTO EGO FRAME

% Zero sensor mounting rotation.
% Apply translation offsets.

xL = xLlocal + lidarPos(1);

yL = yLlocal + lidarPos(2);

zL = zLlocal + lidarPos(3);

%% 10. CREATE FIXED LIDAR TABLE

% FIX: Use explicit character-vector names in table().
% This avoids the table VariableNames assignment error.

L13 = table( ...
    lidarFrame, ...
    rayIndex, ...
    lidarRange, ...
    thetaL, ...
    phiL, ...
    xL, ...
    yL, ...
    zL, ...
    'VariableNames', { ...
        'frame', ...
        'ray_index', ...
        'range_m', ...
        'azimuth_rad', ...
        'elevation_rad', ...
        'x_ego_m', ...
        'y_ego_m', ...
        'z_ego_m' ...
    });

%% 11. PREPARE RADAR DATA

radarFrame = double(R.frame(:));
radarRange = double(R.range_m(:));

thetaR = double(R.horizontal_angle_rad(:));
phiR   = double(R.vertical_angle_rad(:));

oldRX = double(R.x_ego_m(:));
oldRY = double(R.y_ego_m(:));
oldRZ = double(R.z_ego_m(:));

validR = ...
    isfinite(radarFrame) & ...
    isfinite(radarRange) & ...
    isfinite(thetaR) & ...
    isfinite(phiR) & ...
    radarRange > 0;

fprintf('\nValid Radar measurements: %d\n', sum(validR));
fprintf('Rejected Radar measurements: %d\n', sum(~validR));

radarFrame = radarFrame(validR);
radarRange = radarRange(validR);

thetaR = thetaR(validR);
phiR   = phiR(validR);

oldRX = oldRX(validR);
oldRY = oldRY(validR);
oldRZ = oldRZ(validR);

%% 12. RECONSTRUCT RADAR LOCAL COORDINATES

xRlocal = ...
    radarRange .* cos(phiR) .* cos(thetaR);

yRlocal = ...
    radarRange .* cos(phiR) .* sin(thetaR);

zRlocal = ...
    radarRange .* sin(phiR);

%% 13. TRANSFORM RADAR INTO EGO FRAME

xR = xRlocal + radarPos(1);

yR = yRlocal + radarPos(2);

zR = zRlocal + radarPos(3);

%% 14. CREATE FIXED RADAR TABLE

R13 = table( ...
    radarFrame, ...
    radarRange, ...
    thetaR, ...
    phiR, ...
    xR, ...
    yR, ...
    zR, ...
    'VariableNames', { ...
        'frame', ...
        'range_m', ...
        'azimuth_rad', ...
        'elevation_rad', ...
        'x_ego_m', ...
        'y_ego_m', ...
        'z_ego_m' ...
    });

%% 15. SAVE RECONSTRUCTED DATA

lidarOut = fullfile(csvDir, ...
    'task13_2a_lidar_common_frame.csv');

radarOut = fullfile(csvDir, ...
    'task13_2a_radar_common_frame.csv');

writetable(L13, lidarOut);
writetable(R13, radarOut);

%% 16. COMPARE WITH TASK 11

Ldelta = sqrt( ...
    (xL - oldLX).^2 + ...
    (yL - oldLY).^2 + ...
    (zL - oldLZ).^2);

Rdelta = sqrt( ...
    (xR - oldRX).^2 + ...
    (yR - oldRY).^2 + ...
    (zR - oldRZ).^2);

meanLdelta = mean(Ldelta, 'omitnan');
meanRdelta = mean(Rdelta, 'omitnan');

maxLdelta = max(Ldelta);
maxRdelta = max(Rdelta);

fprintf('\n===== TASK 13.2A RESULTS =====\n');

fprintf('LiDAR points: %d\n', height(L13));
fprintf('Radar returns: %d\n', height(R13));

fprintf('Mean LiDAR difference: %.6f m\n', ...
    meanLdelta);

fprintf('Mean Radar difference: %.6f m\n', ...
    meanRdelta);

fprintf('Maximum LiDAR difference: %.6f m\n', ...
    maxLdelta);

fprintf('Maximum Radar difference: %.6f m\n', ...
    maxRdelta);

%% 17. FIGURE 1 - 2D TOP VIEW

fig1 = figure( ...
    'Color', 'w', ...
    'Position', [80 80 1250 760]);

hold on;

scatter(xL, yL, 8, 'filled');

scatter(xR, yR, 50, 'filled');

scatter( ...
    lidarPos(1), lidarPos(2), ...
    130, 'filled');

scatter( ...
    radarPos(1), radarPos(2), ...
    130, 'filled');

scatter( ...
    cameraPos(1), cameraPos(2), ...
    130, 'filled');

xlabel('Ego X (m)');
ylabel('Ego Y (m)');

title('Task 13.2A - Common Sensor Frame (Top View)');

axis equal;
grid on;

legend( ...
    {'LiDAR points', ...
     'Radar returns', ...
     'LiDAR mount', ...
     'Radar mount', ...
     'Camera mount'}, ...
    'Location', 'bestoutside');

topPNG = fullfile(graphDir, ...
    'task13_2a_common_sensor_top_view.png');

topFIG = fullfile(graphDir, ...
    'task13_2a_common_sensor_top_view.fig');

exportgraphics(fig1, topPNG, ...
    'Resolution', 250);

savefig(fig1, topFIG);

%% 18. FIGURE 2 - 3D SENSOR GEOMETRY

fig2 = figure( ...
    'Color', 'w', ...
    'Position', [100 100 1300 800]);

hold on;

scatter3(xL, yL, zL, 8, 'filled');

scatter3(xR, yR, zR, 55, 'filled');

scatter3( ...
    lidarPos(1), lidarPos(2), lidarPos(3), ...
    150, 'filled');

scatter3( ...
    radarPos(1), radarPos(2), radarPos(3), ...
    150, 'filled');

scatter3( ...
    cameraPos(1), cameraPos(2), cameraPos(3), ...
    150, 'filled');

xlabel('Ego X (m)');
ylabel('Ego Y (m)');
zlabel('Ego Z (m)');

title('Task 13.2A - 3D LiDAR and Radar Reconstruction');

axis equal;
grid on;
view(35,25);

legend( ...
    {'LiDAR points', ...
     'Radar returns', ...
     'LiDAR mount', ...
     'Radar mount', ...
     'Camera mount'}, ...
    'Location', 'bestoutside');

threeDPNG = fullfile(graphDir, ...
    'task13_2a_common_sensor_3d.png');

threeDFIG = fullfile(graphDir, ...
    'task13_2a_common_sensor_3d.fig');

exportgraphics(fig2, threeDPNG, ...
    'Resolution', 250);

savefig(fig2, threeDFIG);

%% 19. FIGURE 3 - CHANGE FROM TASK 11

fig3 = figure( ...
    'Color', 'w', ...
    'Position', [130 130 1250 650]);

tiledlayout(1,2);

nexttile;

histogram(Ldelta, 35);

xlabel('3D coordinate difference (m)');
ylabel('Number of LiDAR points');

title('LiDAR: Task 11 vs Task 13');

grid on;

nexttile;

histogram(Rdelta, 20);

xlabel('3D coordinate difference (m)');
ylabel('Number of Radar returns');

title('Radar: Task 11 vs Task 13');

grid on;

deltaPNG = fullfile(graphDir, ...
    'task13_2a_reconstruction_difference.png');

deltaFIG = fullfile(graphDir, ...
    'task13_2a_reconstruction_difference.fig');

exportgraphics(fig3, deltaPNG, ...
    'Resolution', 250);

savefig(fig3, deltaFIG);

%% 20. SAVE RECONSTRUCTION SUMMARY

S = table( ...
    height(L13), ...
    height(R13), ...
    meanLdelta, ...
    meanRdelta, ...
    maxLdelta, ...
    maxRdelta, ...
    'VariableNames', { ...
        'lidar_point_count', ...
        'radar_return_count', ...
        'mean_lidar_difference_m', ...
        'mean_radar_difference_m', ...
        'max_lidar_difference_m', ...
        'max_radar_difference_m' ...
    });

summaryOut = fullfile(csvDir, ...
    'task13_2a_reconstruction_comparison.csv');

writetable(S, summaryOut);

%% 21. SAVE RESEARCH FINDINGS

findFile = fullfile(findDir, ...
    'task13_2a_common_sensor_frame_findings.txt');

fid = fopen(findFile, 'w');

assert(fid ~= -1, ...
    'Unable to write research findings.');

fprintf(fid, ...
    'TASK 13.2A - COMMON SENSOR COORDINATE FRAME\n\n');

fprintf(fid, ...
    'Scenario: GEMSTAR MOR100, frame 150\n');

fprintf(fid, ...
    'LiDAR valid points: %d\n', height(L13));

fprintf(fid, ...
    'Radar valid returns: %d\n', height(R13));

fprintf(fid, ...
    '\nCOMPARISON WITH TASK 11\n');

fprintf(fid, ...
    'Mean LiDAR difference: %.6f m\n', meanLdelta);

fprintf(fid, ...
    'Mean Radar difference: %.6f m\n', meanRdelta);

fprintf(fid, ...
    'Maximum LiDAR difference: %.6f m\n', maxLdelta);

fprintf(fid, ...
    'Maximum Radar difference: %.6f m\n', maxRdelta);

fprintf(fid, ...
    '\nVERIFIED SOURCE-CODE DETAILS\n');

fprintf(fid, ...
    'LiDAR horizontal index changes fastest.\n');

fprintf(fid, ...
    'LiDAR angles are uniformly distributed over FoV.\n');

fprintf(fid, ...
    'LiDAR and Radar use Unreal GetForwardVector.\n');

fprintf(fid, ...
    'Sensor-local positive Y corresponds to positive yaw.\n');

fprintf(fid, ...
    '\nASSUMPTIONS AND LIMITATIONS\n');

fprintf(fid, ...
    'Uses OSI-derived Task 11 CSV files.\n');

fprintf(fid, ...
    'LiDAR ray index is assumed zero-based.\n');

fprintf(fid, ...
    'Sensor mounting rotations are assumed zero.\n');

fprintf(fid, ...
    'Mounting-frame chain requires further validation.\n');

fprintf(fid, ...
    'A difference from Task 11 is not proof of correctness.\n');

fprintf(fid, ...
    'No object-level tri-sensor fusion is demonstrated.\n');

fclose(fid);

%% 22. SAVE SOURCE REFERENCES

referenceFile = fullfile(refDir, ...
    'task13_2a_data_sources.txt');

fid = fopen(referenceFile, 'w');

if fid ~= -1

    fprintf(fid, 'TASK 13.2A DATA SOURCES\n\n');

    fprintf(fid, 'LiDAR: %s\n', lidarFile);
    fprintf(fid, 'Radar: %s\n', radarFile);

    fprintf(fid, '\nOriginal GEMSTAR files:\n');

    fprintf(fid, 'SimpleLidar.cpp\n');
    fprintf(fid, 'SimpleRadar.cpp\n');
    fprintf(fid, 'DefaultGemstar.ini\n');

    fclose(fid);

end

%% 23. ARCHIVE MATLAB SOURCE

sourceFile = fullfile(root, 'matlab', ...
    'task13_common_sensor_frame.m');

if isfile(sourceFile)

    copyfile(sourceFile, codeDir, 'f');

else

    warning('MATLAB source script was not found for archiving.');

end

%% 24. FINAL OUTPUT

fprintf('\n========================================\n');

fprintf('TASK 13.2A - FINAL SUMMARY\n');

fprintf('========================================\n');

disp(S);

fprintf('\nSaved CSV files:\n');
fprintf('%s\n', lidarOut);
fprintf('%s\n', radarOut);
fprintf('%s\n', summaryOut);

fprintf('\nSaved figures:\n');
fprintf('%s\n', topPNG);
fprintf('%s\n', threeDPNG);
fprintf('%s\n', deltaPNG);

fprintf('\nResearch findings:\n');
fprintf('%s\n', findFile);

fprintf('\nTASK 13.2A COMPLETED SUCCESSFULLY\n');
