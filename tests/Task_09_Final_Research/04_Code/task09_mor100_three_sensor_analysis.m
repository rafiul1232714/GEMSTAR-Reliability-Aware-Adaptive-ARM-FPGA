
%% TASK 9.2.5 - COMBINED THREE SENSOR ANALYSIS
% GEMSTAR - Fog MOR 100 m
% Camera + LiDAR + Radar
% Matches measurements by exact frame number

clc;
clear;
close all;

%% 1. Project paths

root = "E:\GEMSTAR_Project\sensor-health-monitor";

archive = fullfile(root, ...
    "tests", "Task_09_Final_Research");

csvFolder = fullfile(archive, "02_CSV_Data");
graphFolder = fullfile(archive, "01_Graphs");
codeFolder = fullfile(archive, "04_Code");

if ~isfolder(graphFolder), mkdir(graphFolder); end
if ~isfolder(codeFolder), mkdir(codeFolder); end

%% 2. Load the previously generated CSV files

sensorFile = fullfile(csvFolder, ...
    "task09_mor100_sensor_diagnostics.csv");

cameraFile = fullfile(csvFolder, ...
    "task09_mor100_camera_quality.csv");

assert(isfile(sensorFile), "Sensor CSV is missing");
assert(isfile(cameraFile), "Camera CSV is missing");

S = readtable(sensorFile);
C = readtable(cameraFile);

fprintf("\nTASK 9.2.5 - THREE SENSOR ANALYSIS\n");
fprintf("Sensor frames: %d\n", height(S));
fprintf("Camera samples: %d\n", height(C));

%% 3. Match Camera samples with LiDAR and Radar
% Camera was extracted from every 10th frame.
% Join only the exact matching frame IDs.

combined = innerjoin(C, S, ...
    "Keys", "frame");

combined = sortrows(combined, "frame");

assert(height(combined) == height(C), ...
    "Some Camera samples lack matching sensor data");

% Ensure there is no unexpected timing mismatch
% between measurements at the same frame.
if ismember("time_s", combined.Properties.VariableNames) && ...
   ismember("timestamp_s", combined.Properties.VariableNames)

    maxTimeError = max(abs( ...
        combined.time_s - combined.timestamp_s));

    fprintf("Maximum joined timestamp error: %.9f s\n", ...
        maxTimeError);
end

%% 4. Export combined sensor dataset

combinedFile = fullfile(csvFolder, ...
    "task09_mor100_three_sensor_combined.csv");

writetable(combined, combinedFile);

fprintf("Combined sensor samples: %d\n", height(combined));

%% 5. Graph 1: Camera reliability indicators

fig1 = figure("Color", "w");

plot(combined.timestamp_s, ...
    combined.contrast, "LineWidth", 1.5);

hold on;

plot(combined.timestamp_s, ...
    combined.edgeStrength, "LineWidth", 1.5);

grid on;
xlabel("Simulation Time (s)");
ylabel("Image Quality Metric");
title("Camera Contrast and Edge Strength - MOR 100");

legend("Contrast", "Edge Strength", ...
    "Location", "best");

savefig(fig1, fullfile(graphFolder, ...
    "task09_mor100_combined_camera.fig"));

exportgraphics(fig1, fullfile(graphFolder, ...
    "task09_mor100_combined_camera.png"), ...
    "Resolution", 300);

%% 6. Graph 2: LiDAR and Radar return percentages

fig2 = figure("Color", "w");

plot(combined.timestamp_s, ...
    combined.lidar_positive_pct, ...
    "LineWidth", 1.5);

hold on;

plot(combined.timestamp_s, ...
    combined.radar_positive_pct, ...
    "LineWidth", 1.5);

grid on;
xlabel("Simulation Time (s)");
ylabel("Positive Return Rate (%)");

title("LiDAR vs Radar - Fog MOR 100");

legend("LiDAR", "Radar", ...
    "Location", "best");

ylim([0 100]);

savefig(fig2, fullfile(graphFolder, ...
    "task09_mor100_combined_lidar_radar.fig"));

exportgraphics(fig2, fullfile(graphFolder, ...
    "task09_mor100_combined_lidar_radar.png"), ...
    "Resolution", 300);

%% 7. Graph 3: Camera and LiDAR together

fig3 = figure("Color", "w");

yyaxis left;

plot(combined.timestamp_s, ...
    combined.contrast, ...
    "LineWidth", 1.5);

ylabel("Camera Contrast");

yyaxis right;

plot(combined.timestamp_s, ...
    combined.lidar_positive_pct, ...
    "LineWidth", 1.5);

ylabel("LiDAR Positive Returns (%)");

xlabel("Simulation Time (s)");
title("Camera and LiDAR Measurements - MOR 100");

legend("Camera Contrast", ...
    "LiDAR Positive Returns", ...
    "Location", "best");

grid on;

savefig(fig3, fullfile(graphFolder, ...
    "task09_mor100_combined_camera_lidar.fig"));

exportgraphics(fig3, fullfile(graphFolder, ...
    "task09_mor100_combined_camera_lidar.png"), ...
    "Resolution", 300);

%% 8. Graph 4: Three-sensor dashboard

fig4 = figure("Color", "w", ...
    "Position", [100 100 1100 850]);

tiledlayout(3, 1);

nexttile;

plot(combined.timestamp_s, ...
    combined.contrast, "LineWidth", 1.5);

ylabel("Contrast");
title("Camera");
grid on;

nexttile;

plot(combined.timestamp_s, ...
    combined.lidar_positive_pct, "LineWidth", 1.5);

ylabel("Returns (%)");
title("LiDAR");
ylim([0 100]);
grid on;

nexttile;

plot(combined.timestamp_s, ...
    combined.radar_positive_pct, "LineWidth", 1.5);

ylabel("Returns (%)");
xlabel("Simulation Time (s)");
title("Radar");
ylim([0 100]);
grid on;

sgtitle("GEMSTAR Three-Sensor Baseline - Fog MOR 100");

savefig(fig4, fullfile(graphFolder, ...
    "task09_mor100_three_sensor_dashboard.fig"));

exportgraphics(fig4, fullfile(graphFolder, ...
    "task09_mor100_three_sensor_dashboard.png"), ...
    "Resolution", 300);

%% 9. Create a summary of the matched samples

metric = [
    "Matched Samples"
    "Mean Camera Brightness"
    "Mean Camera Contrast"
    "Mean Camera Edge Strength"
    "Mean Camera Sharpness"
    "Mean LiDAR Positive Return (%)"
    "Mean Radar Positive Return (%)"
    "Maximum LiDAR Range (m)"
    "Maximum Radar Range (m)"
];

value = [
    height(combined)
    mean(combined.brightness)
    mean(combined.contrast)
    mean(combined.edgeStrength)
    mean(combined.sharpness)
    mean(combined.lidar_positive_pct)
    mean(combined.radar_positive_pct)
    max(combined.lidar_max_range_m)
    max(combined.radar_max_range_m)
];

summary = table(metric, value);

summaryFile = fullfile(csvFolder, ...
    "task09_mor100_three_sensor_summary.csv");

writetable(summary, summaryFile);

disp(" ");
disp("===== THREE SENSOR RESULTS =====");
disp(summary);

%% 10. Archive MATLAB script

source = fullfile(root, "matlab", ...
    "task09_mor100_three_sensor_analysis.m");

if isfile(source)
    copyfile(source, codeFolder);
end

fprintf("\nTASK 9.2.5 COMPLETED\n");
fprintf("Combined CSV, graphs and code saved.\n");
