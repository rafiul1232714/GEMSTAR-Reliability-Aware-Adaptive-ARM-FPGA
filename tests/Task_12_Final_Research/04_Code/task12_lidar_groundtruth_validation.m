
%% ============================================================
% TASK 12.3 - LIDAR VS GROUND TRUTH VEHICLE VALIDATION
% GEMSTAR MOR100 - Frame 150
%
% Objective:
% Compare reconstructed LiDAR points with the Ground Truth
% position of vehicle ID 76865.
%
% Experiments:
% 1. Original LiDAR lateral-axis convention
% 2. Mirrored LiDAR lateral-axis convention
% 3. Points within 1 m and 2 m of Ground Truth center
% 4. Height distribution and diagnostic object IDs
%
% IMPORTANT:
% Geometric proximity does not prove vehicle identification.
%% ============================================================

clc;
clear;
close all;

%% 1. PROJECT PATHS

root = "E:\GEMSTAR_Project\sensor-health-monitor";

task11 = fullfile(root, ...
    "tests", "Task_11_Final_Research");

task12 = fullfile(root, ...
    "tests", "Task_12_Final_Research");

dataDir = fullfile(task12, "02_CSV_Data");
graphDir = fullfile(task12, "01_Graphs");
findDir = fullfile(task12, "06_Research_Findings");
codeDir = fullfile(task12, "04_Code");

folders = [dataDir, graphDir, findDir, codeDir];

for k = 1:numel(folders)
    if ~isfolder(folders(k))
        mkdir(folders(k));
    end
end

%% 2. LOAD THE RECORDED DATA

lidarFile = fullfile(task11, ...
    "02_CSV_Data", ...
    "task11_lidar_frame150_geometry.csv");

gtFile = fullfile(task11, ...
    "02_CSV_Data", ...
    "task11_groundtruth_objects.csv");

assert(isfile(lidarFile), ...
    "LiDAR geometry CSV not found.");

assert(isfile(gtFile), ...
    "Ground Truth CSV not found.");

L = readtable(lidarFile);
G = readtable(gtFile);

frame = 150;
egoID = 76895;
targetID = 76865;

ego = G(G.frame == frame & ...
    G.object_id == egoID, :);

target = G(G.frame == frame & ...
    G.object_id == targetID, :);

assert(height(ego) == 1, ...
    "Ego Ground Truth object missing.");

assert(height(target) == 1, ...
    "Target Ground Truth object missing.");

assert(all(L.frame == frame), ...
    "LiDAR CSV contains unexpected frame numbers.");

fprintf('\n============================================\n');
fprintf('TASK 12.3 - LIDAR VS GROUND TRUTH\n');
fprintf('============================================\n');

fprintf('Frame: %d\n', frame);
fprintf('Ego ID: %d\n', egoID);
fprintf('Target ID: %d\n', targetID);
fprintf('LiDAR points: %d\n', height(L));

%% 3. WORLD TO EGO TRANSFORMATION

dx = target.x_m - ego.x_m;
dy = target.y_m - ego.y_m;

yaw = ego.yaw_rad;

targetX = cos(yaw)*dx + sin(yaw)*dy;
targetY = -sin(yaw)*dx + cos(yaw)*dy;

fprintf('\nGround Truth target position:\n');
fprintf('Forward X: %.4f m\n', targetX);
fprintf('Lateral Y: %.4f m\n', targetY);

%% 4. LIDAR COORDINATES

x = L.x_ego_m;
y = L.y_ego_m;
z = L.z_ego_m;

% The lateral-axis sign remains unverified.
% Compare both hypotheses.

signs = [1, -1];

% Explicit numeric matrix prevents array2table errors.
resultRows = zeros(numel(signs), 8);

% Store near-GT measurements for both hypotheses.
nearPointTables = cell(numel(signs), 1);

%% 5. CREATE COMPARISON FIGURE

fig = figure( ...
    'Color', 'w', ...
    'Position', [80 80 1400 680]);

t = tiledlayout(1, 2, ...
    'TileSpacing', 'compact', ...
    'Padding', 'compact');

for k = 1:numel(signs)

    signY = signs(k);

    yy = signY .* y;

    %% 5A. DISTANCE TO GT CENTER

    distanceXY = hypot( ...
        x - targetX, ...
        yy - targetY);

    near1 = distanceXY <= 1.0;
    near2 = distanceXY <= 2.0;

    % Descriptive height criterion only.
    elevated = z >= 0.5;

    n1 = sum(near1);
    n2 = sum(near2);
    n2Elevated = sum(near2 & elevated);

    minDistance = min(distanceXY);

    if any(near2)

        minNearZ = min(z(near2));
        maxNearZ = max(z(near2));

        diagnosticIDs = unique( ...
            L.object_id_diagnostic(near2));

    else

        minNearZ = NaN;
        maxNearZ = NaN;
        diagnosticIDs = [];

    end

    %% 5B. PRINT RESULTS

    fprintf('\n--------------------------------------------\n');
    fprintf('LATERAL SIGN %+d\n', signY);
    fprintf('--------------------------------------------\n');

    fprintf('Nearest LiDAR XY distance: %.4f m\n', ...
        minDistance);

    fprintf('Points within 1 m: %d\n', n1);
    fprintf('Points within 2 m: %d\n', n2);

    fprintf('Elevated points within 2 m: %d\n', ...
        n2Elevated);

    fprintf('Near-point Z range: %.4f to %.4f m\n', ...
        minNearZ, maxNearZ);

    fprintf('Near-point diagnostic IDs:\n');
    disp(diagnosticIDs');

    %% 5C. STORE NUMERICAL SUMMARY

    resultRows(k, :) = [ ...
        signY, ...
        minDistance, ...
        n1, ...
        n2, ...
        n2Elevated, ...
        minNearZ, ...
        maxNearZ, ...
        numel(diagnosticIDs) ...
    ];

    %% 5D. SAVE SELECTED NEARBY POINTS

    selected = L(near2, :);

    if ~isempty(selected)

        selected.test_lateral_sign = ...
            repmat(signY, height(selected), 1);

        selected.test_y_ego_m = ...
            signY .* selected.y_ego_m;

        selected.distance_to_gt_xy_m = ...
            distanceXY(near2);

    else

        selected.test_lateral_sign = zeros(0,1);
        selected.test_y_ego_m = zeros(0,1);
        selected.distance_to_gt_xy_m = zeros(0,1);

    end

    nearPointTables{k} = selected;

    %% 5E. PLOT ORIGINAL / MIRRORED GEOMETRY

    nexttile(t, k);
    hold on;

    hAll = scatter( ...
        x, yy, ...
        8, [0.7 0.7 0.7], ...
        'filled');

    hNear = scatter( ...
        x(near2), yy(near2), ...
        25, [0.9 0.2 0.1], ...
        'filled');

    hGT = plot( ...
        targetX, targetY, ...
        'gp', ...
        'MarkerSize', 16, ...
        'LineWidth', 2);

    hEgo = plot( ...
        0, 0, ...
        'ks', ...
        'MarkerSize', 9, ...
        'LineWidth', 2);

    % True 2 m radius circle around GT center.
    theta = linspace(0, 2*pi, 300);

    circleX = targetX + 2*cos(theta);
    circleY = targetY + 2*sin(theta);

    hCircle = plot( ...
        circleX, circleY, ...
        'g--', ...
        'LineWidth', 1.5);

    xlabel('Forward X (m)');
    ylabel('Lateral Y (m)');

    title(sprintf( ...
        'Y sign %+d | %d points within 2 m', ...
        signY, n2));

    axis equal;
    xlim([0 25]);
    ylim([-12 12]);
    grid on;

    % Explicit graphics handles fix the legend warning.
    legend( ...
        [hAll, hNear, hGT, hEgo, hCircle], ...
        {'All LiDAR points', ...
         'Within 2 m of GT', ...
         'GT vehicle center', ...
         'Ego origin', ...
         '2 m search radius'}, ...
        'Location', 'best');

end

sgtitle( ...
    'Task 12.3 - LiDAR vs Ground Truth Vehicle 76865');

%% 6. CREATE RESULTS TABLE

% Build the table explicitly to avoid the earlier error.

summary = table( ...
    resultRows(:,1), ...
    resultRows(:,2), ...
    resultRows(:,3), ...
    resultRows(:,4), ...
    resultRows(:,5), ...
    resultRows(:,6), ...
    resultRows(:,7), ...
    resultRows(:,8), ...
    'VariableNames', { ...
    'lateral_sign', ...
    'nearest_distance_m', ...
    'points_within_1m', ...
    'points_within_2m', ...
    'elevated_within_2m', ...
    'min_near_z_m', ...
    'max_near_z_m', ...
    'unique_diagnostic_ids'});

%% 7. SAVE CSV RESULTS

summaryFile = fullfile(dataDir, ...
    "task12_3_lidar_gt_summary.csv");

writetable(summary, summaryFile);

nearFile = fullfile(dataDir, ...
    "task12_3_lidar_near_gt_points.csv");

allNearPoints = vertcat(nearPointTables{:});

writetable(allNearPoints, nearFile);

%% 8. SAVE MAIN FIGURE

pngFile = fullfile(graphDir, ...
    "task12_3_lidar_gt_validation.png");

figFile = fullfile(graphDir, ...
    "task12_3_lidar_gt_validation.fig");

exportgraphics(fig, pngFile, 'Resolution', 250);
savefig(fig, figFile);

%% 9. CREATE HEIGHT DISTRIBUTION GRAPH

heightFig = figure( ...
    'Color', 'w', ...
    'Position', [150 150 1050 550]);

hold on;

for k = 1:numel(signs)

    yy = signs(k) .* y;

    distanceXY = hypot( ...
        x - targetX, ...
        yy - targetY);

    near2 = distanceXY <= 2.0;

    if any(near2)

        histogram( ...
            z(near2), ...
            20, ...
            'DisplayName', ...
            sprintf('Y sign %+d', signs(k)));

    end

end

xlabel('Reconstructed Z (m)');
ylabel('LiDAR point count');

title('Task 12.3 - Height Distribution Near GT Vehicle');

grid on;
legend('Location', 'best');

heightPNG = fullfile(graphDir, ...
    "task12_3_near_gt_height_distribution.png");

heightFIG = fullfile(graphDir, ...
    "task12_3_near_gt_height_distribution.fig");

exportgraphics(heightFig, heightPNG, ...
    'Resolution', 250);

savefig(heightFig, heightFIG);

%% 10. SAVE RESEARCH FINDINGS

reportFile = fullfile(findDir, ...
    "task12_3_lidar_gt_findings.txt");

fid = fopen(reportFile, 'w');

assert(fid ~= -1, ...
    "Unable to create research findings.");

fprintf(fid, ...
    'TASK 12.3 - LIDAR VS GROUND TRUTH\n\n');

fprintf(fid, 'Scenario: GEMSTAR MOR100\n');
fprintf(fid, 'Frame: %d\n', frame);
fprintf(fid, 'Ego ID: %d\n', egoID);
fprintf(fid, 'GT vehicle ID: %d\n\n', targetID);

fprintf(fid, 'GT forward X: %.4f m\n', targetX);
fprintf(fid, 'GT lateral Y: %.4f m\n', targetY);
fprintf(fid, 'Total LiDAR points: %d\n', height(L));

for k = 1:height(summary)

    fprintf(fid, '\nLATERAL SIGN %+d\n', ...
        summary.lateral_sign(k));

    fprintf(fid, 'Nearest distance: %.4f m\n', ...
        summary.nearest_distance_m(k));

    fprintf(fid, 'Points within 1 m: %d\n', ...
        summary.points_within_1m(k));

    fprintf(fid, 'Points within 2 m: %d\n', ...
        summary.points_within_2m(k));

    fprintf(fid, 'Elevated within 2 m: %d\n', ...
        summary.elevated_within_2m(k));

    fprintf(fid, 'Minimum nearby Z: %.4f m\n', ...
        summary.min_near_z_m(k));

    fprintf(fid, 'Maximum nearby Z: %.4f m\n', ...
        summary.max_near_z_m(k));

end

fprintf(fid, '\nRESEARCH INTERPRETATION\n');

fprintf(fid, ...
    'This experiment evaluates 2D proximity to a GT center.\n');

fprintf(fid, ...
    'Nearby LiDAR points may represent ground or other surfaces.\n');

fprintf(fid, ...
    'A 2 m search radius is not the true vehicle boundary.\n');

fprintf(fid, ...
    'Reconstructed LiDAR coordinates remain provisional.\n');

fprintf(fid, ...
    'Diagnostic object IDs are not OSI GT object IDs.\n');

fprintf(fid, ...
    'No confirmed LiDAR-to-vehicle identification is claimed.\n');

fclose(fid);

%% 11. ARCHIVE THE SOURCE CODE

sourceFile = fullfile(root, ...
    "matlab", ...
    "task12_lidar_groundtruth_validation.m");

if isfile(sourceFile)

    copyfile(sourceFile, codeDir, 'f');

else

    warning( ...
        'MATLAB script was not found for source archiving.');

end

%% 12. FINAL RESULTS

fprintf('\n============================================\n');
fprintf('TASK 12.3 - FINAL RESULTS\n');
fprintf('============================================\n');

disp(summary);

fprintf('\nSaved files:\n');
fprintf('Summary CSV: %s\n', summaryFile);
fprintf('Near-point CSV: %s\n', nearFile);
fprintf('Main figure: %s\n', pngFile);
fprintf('Height figure: %s\n', heightPNG);
fprintf('Findings: %s\n', reportFile);

fprintf('\nTASK 12.3 COMPLETED SUCCESSFULLY\n');
