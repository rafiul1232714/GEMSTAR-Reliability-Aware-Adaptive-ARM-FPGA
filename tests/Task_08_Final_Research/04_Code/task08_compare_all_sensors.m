
%% TASK 8.11 - CLEAR VS FOG: ALL THREE SENSORS
% GEMSTAR Multi-Sensor Reliability Monitoring

clc;
clear;
close all;

%% 1. Project folders
project = "E:\GEMSTAR_Project\sensor-health-monitor";

figureFolder = project + "\results\figures";
tableFolder = project + "\results\tables";

if ~isfolder(figureFolder)
    mkdir(figureFolder);
end

if ~isfolder(tableFolder)
    mkdir(tableFolder);
end

%% 2. Read Camera data
fogCamera = readtable( ...
    project + "\results\tables\task0715_fog_camera_quality.csv");

clearCamera = readtable( ...
    project + "\results\tables\task08_clear_camera_quality.csv");

%% 3. Read LiDAR and Radar data
fogSensor = readtable( ...
    project + "\data\processed\task07_radar_mount_test.csv");

clearSensor = readtable( ...
    project + "\data\processed\task08_clear_sensor_diagnostics.csv");

%% 4. Camera comparison
% The sampled scenes are not guaranteed to be identical.

fig1 = figure('Color', 'w');
tiledlayout(3,1);

metrics = ["Brightness", "Contrast", "EdgeStrength"];

for k = 1:3

    nexttile;

    metric = metrics(k);

    plot(fogCamera.Timestamp_s, ...
        fogCamera.(metric), '-ob', 'LineWidth', 1.5);

    hold on;

    plot(clearCamera.Timestamp_s, ...
        clearCamera.(metric), '-sr', 'LineWidth', 1.5);

    xlabel('Simulation Time (s)');
    ylabel(metric);

    legend('Fog', 'Clear', 'Location', 'best');
    title("Camera " + metric);
    grid on;

end

sgtitle('GEMSTAR Camera: Fog vs Clear');

exportgraphics(fig1, ...
    figureFolder + "\task08_camera_fog_vs_clear.png", ...
    'Resolution', 300);

savefig(fig1, ...
    figureFolder + "\task08_camera_fog_vs_clear.fig");

%% 5. Calculate LiDAR positive-return percentages

fogLidar = 100 * fogSensor.lidar_positive ...
    ./ fogSensor.lidar_records;

clearLidar = 100 * clearSensor.lidar_positive ...
    ./ clearSensor.lidar_records;

%% 6. Plot LiDAR comparison

fig2 = figure('Color', 'w');

plot(fogSensor.time_s, fogLidar, ...
    'b', 'LineWidth', 1.3);

hold on;

plot(clearSensor.time_s, clearLidar, ...
    'r', 'LineWidth', 1.3);

xlabel('Simulation Time (s)');
ylabel('Positive Return Percentage (%)');

title('GEMSTAR LiDAR: Fog vs Clear');

legend('Fog', 'Clear', 'Location', 'best');
ylim([0 100]);
grid on;

exportgraphics(fig2, ...
    figureFolder + "\task08_lidar_fog_vs_clear.png", ...
    'Resolution', 300);

savefig(fig2, ...
    figureFolder + "\task08_lidar_fog_vs_clear.fig");

%% 7. Calculate Radar positive-return percentages

fogRadar = 100 * fogSensor.radar_positive ...
    ./ fogSensor.radar_records;

clearRadar = 100 * clearSensor.radar_positive ...
    ./ clearSensor.radar_records;

%% 8. Plot Radar comparison

fig3 = figure('Color', 'w');

plot(fogSensor.time_s, fogRadar, ...
    'b', 'LineWidth', 1.3);

hold on;

plot(clearSensor.time_s, clearRadar, ...
    'r', 'LineWidth', 1.3);

xlabel('Simulation Time (s)');
ylabel('Positive Return Percentage (%)');

title('GEMSTAR Radar: Fog vs Clear');

legend('Fog', 'Clear', 'Location', 'best');
ylim([0 100]);
grid on;

exportgraphics(fig3, ...
    figureFolder + "\task08_radar_fog_vs_clear.png", ...
    'Resolution', 300);

savefig(fig3, ...
    figureFolder + "\task08_radar_fog_vs_clear.fig");

%% 9. Summary statistics

metricNames = [
    "Camera Brightness"
    "Camera Contrast"
    "Camera Edge Strength"
    "LiDAR Positive Return %"
    "Radar Positive Return %"
];

fogMean = [
    mean(fogCamera.Brightness)
    mean(fogCamera.Contrast)
    mean(fogCamera.EdgeStrength)
    mean(fogLidar)
    mean(fogRadar)
];

clearMean = [
    mean(clearCamera.Brightness)
    mean(clearCamera.Contrast)
    mean(clearCamera.EdgeStrength)
    mean(clearLidar)
    mean(clearRadar)
];

difference = clearMean - fogMean;

summary = table( ...
    metricNames, fogMean, clearMean, difference, ...
    'VariableNames', { ...
        'Metric', 'FogMean', 'ClearMean', ...
        'ClearMinusFog' ...
    });

disp('======================================');
disp('TASK 8.11 - CLEAR VS FOG COMPARISON');
disp('======================================');

disp(summary);

%% 10. Save research summary

outputCSV = tableFolder + ...
    "\task08_all_sensors_fog_vs_clear.csv";

writetable(summary, outputCSV);

disp(' ');
disp('TASK 8.11 COMPLETED!');
disp('Saved Camera comparison graph.');
disp('Saved LiDAR comparison graph.');
disp('Saved Radar comparison graph.');
disp('Saved numerical summary CSV.');
