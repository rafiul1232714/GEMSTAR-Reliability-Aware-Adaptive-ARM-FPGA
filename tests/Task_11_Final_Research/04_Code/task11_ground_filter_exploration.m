
%% TASK 11.5A - LIDAR GROUND FILTER EXPLORATION
% GEMSTAR frame 101
% Investigate point heights before object clustering

clc;
clear;
close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor";
archive = fullfile(root, "tests", "Task_11_Final_Research");

csvFolder = fullfile(archive, "02_CSV_Data");
graphFolder = fullfile(archive, "01_Graphs");
codeFolder = fullfile(archive, "04_Code");

inputFile = fullfile(csvFolder, ...
    "task11_lidar_points_frame101.csv");

assert(isfile(inputFile), "LiDAR point CSV missing.");

T = readtable(inputFile);

x = T.x_ego_m;
y = T.y_ego_m;
z = T.z_ego_m;

fprintf("\nTASK 11.5A - GROUND FILTER EXPLORATION\n");
fprintf("Total points: %d\n", height(T));
fprintf("Minimum Z: %.4f m\n", min(z));
fprintf("Maximum Z: %.4f m\n", max(z));
fprintf("Median Z: %.4f m\n", median(z));

%% Explore candidate height thresholds
thresholds = [0.05; 0.10; 0.15; 0.20; 0.30];

counts = zeros(size(thresholds));

for i = 1:numel(thresholds)
    counts(i) = sum(z > thresholds(i));
end

summary = table(thresholds, counts, ...
    'VariableNames', {'HeightThreshold_m', ...
                      'PointsAboveThreshold'});

disp(summary);

writetable(summary, fullfile(csvFolder, ...
    "task11_ground_threshold_exploration.csv"));

%% Graph 1 - Point-height distribution

fig1 = figure("Color", "w");

histogram(z, 50);

xlabel("Reconstructed Z (m)");
ylabel("Number of LiDAR Points");
title("LiDAR Height Distribution - Frame 101");
grid on;

exportgraphics(fig1, fullfile(graphFolder, ...
    "task11_lidar_height_distribution.png"), ...
    "Resolution", 300);

savefig(fig1, fullfile(graphFolder, ...
    "task11_lidar_height_distribution.fig"));

%% Graph 2 - Candidate non-ground points
% A preliminary threshold, not yet validated.

candidateThreshold = 0.15;
candidate = z > candidateThreshold;

fig2 = figure("Color", "w");

scatter(x(~candidate), y(~candidate), ...
    8, [0.7 0.7 0.7], "filled");

hold on;

scatter(x(candidate), y(candidate), ...
    18, [0.9 0.2 0.1], "filled");

plot(0, 0, "ks", "MarkerSize", 10);

xlabel("Forward X (m)");
ylabel("Lateral Y (m)");
title("Exploratory LiDAR Height Filter - Frame 101");

legend("Other points", "Candidate elevated points", ...
    "Ego origin", "Location", "best");

axis equal;
grid on;

exportgraphics(fig2, fullfile(graphFolder, ...
    "task11_lidar_ground_filter_exploration.png"), ...
    "Resolution", 300);

savefig(fig2, fullfile(graphFolder, ...
    "task11_lidar_ground_filter_exploration.fig"));

%% Save point classification for review

T.candidateElevated = candidate;

writetable(T, fullfile(csvFolder, ...
    "task11_lidar_height_candidates_frame101.csv"));

%% Archive code

sourceFile = fullfile(root, "matlab", ...
    "task11_ground_filter_exploration.m");

if isfile(sourceFile)
    copyfile(sourceFile, codeFolder);
end

fprintf("\nPoints above %.2f m: %d\n", ...
    candidateThreshold, sum(candidate));

fprintf("TASK 11.5A COMPLETED\n");
