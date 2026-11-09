
%% TASK 8.9.2 - FOG VS CLEAR EGO TRAJECTORY
% GEMSTAR / SUMO scenario comparison

clc;
clear;
close all;

project = "E:\GEMSTAR_Project\sensor-health-monitor";

fogFile = project + "\data\processed\task0715_groundtruth_vehicles.csv";
clearFile = project + "\data\processed\task08_clear_groundtruth_vehicles.csv";

figureFolder = project + "\results\figures";
tableFolder = project + "\results\tables";

if ~isfolder(figureFolder)
    mkdir(figureFolder);
end

if ~isfolder(tableFolder)
    mkdir(tableFolder);
end

%% Load ground-truth files
fogData = readtable(fogFile);
clearData = readtable(clearFile);

% Ego IDs from the SUMO vehicle mapping files
fogEgoID = 76889;
clearEgoID = 76795;

fog = fogData(fogData.object_id == fogEgoID, :);
clear = clearData(clearData.object_id == clearEgoID, :);

fog = sortrows(fog, "timestamp_s");
clear = sortrows(clear, "timestamp_s");

if isempty(fog) || isempty(clear)
    error("Ego vehicle missing from one of the datasets");
end

%% Figure 1 - XY trajectories
fig1 = figure('Color', 'w');

plot(fog.position_x_m, fog.position_y_m, ...
    'b-', 'LineWidth', 1.5);
hold on;

plot(clear.position_x_m, clear.position_y_m, ...
    'r--', 'LineWidth', 1.5);

plot(fog.position_x_m(1), fog.position_y_m(1), ...
    'bo', 'MarkerFaceColor', 'b');

plot(clear.position_x_m(1), clear.position_y_m(1), ...
    'ro', 'MarkerFaceColor', 'r');

xlabel('X Position (m)');
ylabel('Y Position (m)');
title('GEMSTAR Ego Trajectory: Fog vs Clear');

legend('Fog', 'Clear', ...
       'Fog Start', 'Clear Start', ...
       'Location', 'best');

axis equal;
grid on;

exportgraphics(fig1, ...
    figureFolder + "\task08_fog_vs_clear_trajectory.png", ...
    'Resolution', 300);

savefig(fig1, ...
    figureFolder + "\task08_fog_vs_clear_trajectory.fig");

%% Compare common timestamps by interpolation
% Skip times where either dataset has no samples.
startTime = max( ...
    min(fog.timestamp_s), ...
    min(clear.timestamp_s));

endTime = min( ...
    max(fog.timestamp_s), ...
    max(clear.timestamp_s));

% Compare both trajectories at regular 0.1-second intervals
commonTime = (startTime:0.1:endTime)';

fogX = interp1(fog.timestamp_s, fog.position_x_m, ...
    commonTime, 'linear');

fogY = interp1(fog.timestamp_s, fog.position_y_m, ...
    commonTime, 'linear');

clearX = interp1(clear.timestamp_s, clear.position_x_m, ...
    commonTime, 'linear');

clearY = interp1(clear.timestamp_s, clear.position_y_m, ...
    commonTime, 'linear');

distanceDifference = hypot( ...
    fogX - clearX, ...
    fogY - clearY);

%% Figure 2 - Position difference over time
fig2 = figure('Color', 'w');

plot(commonTime, distanceDifference, ...
    'LineWidth', 1.5);

xlabel('Simulation Time (s)');
ylabel('Ego Position Difference (m)');
title('Fog vs Clear: Ego Trajectory Difference');
grid on;

exportgraphics(fig2, ...
    figureFolder + "\task08_ego_trajectory_difference.png", ...
    'Resolution', 300);

savefig(fig2, ...
    figureFolder + "\task08_ego_trajectory_difference.fig");

%% Print statistics
fprintf('\n========== TASK 8.9 RESULTS ==========\n');

fprintf('Fog ego records: %d\n', height(fog));
fprintf('Clear ego records: %d\n', height(clear));

fprintf('Common duration: %.2f seconds\n', ...
    endTime - startTime);

fprintf('Mean position difference: %.3f m\n', ...
    mean(distanceDifference));

fprintf('Maximum position difference: %.3f m\n', ...
    max(distanceDifference));

%% Save comparison CSV
results = table( ...
    commonTime, ...
    fogX, fogY, ...
    clearX, clearY, ...
    distanceDifference, ...
    'VariableNames', { ...
        'Time_s', ...
        'Fog_X_m', 'Fog_Y_m', ...
        'Clear_X_m', 'Clear_Y_m', ...
        'PositionDifference_m' ...
    });

outputCSV = tableFolder + "\task08_ego_trajectory_comparison.csv";
writetable(results, outputCSV);

disp(' ');
disp('TASK 8.9.2 COMPLETED');
disp('Research graphs and comparison CSV saved.');
