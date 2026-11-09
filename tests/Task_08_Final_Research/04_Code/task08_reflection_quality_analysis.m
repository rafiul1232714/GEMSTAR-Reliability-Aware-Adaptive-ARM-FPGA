
%% TASK 8.13 - LiDAR AND RADAR REFLECTION QUALITY
% GEMSTAR Multi-Sensor Reliability Monitoring
% Comparison: Fog vs Clear

clc;
clear;
close all;

%% Project paths
project = "E:\GEMSTAR_Project\sensor-health-monitor";

inputFile = project + "\data\processed\task08_reflection_quality.csv";

figureFolder = project + "\results\figures";
tableFolder = project + "\results\tables";

if ~isfolder(figureFolder)
    mkdir(figureFolder);
end

if ~isfolder(tableFolder)
    mkdir(tableFolder);
end

%% Read data
data = readtable(inputFile);

fog = data(strcmp(string(data.weather), "fog"), :);
clearData = data(strcmp(string(data.weather), "clear"), :);

fprintf('\n========== TASK 8.13 ==========\n');
fprintf('Fog frames: %d\n', height(fog));
fprintf('Clear frames: %d\n', height(clearData));

%% Measurements to analyze
metrics = [
    "lidar_mean_strength"
    "lidar_mean_range_m"
    "radar_mean_strength"
    "radar_mean_range_m"
];

titles = [
    "LiDAR Mean Signal Strength"
    "LiDAR Mean Derived Range"
    "Radar Mean Signal Strength"
    "Radar Mean Derived Range"
];

units = [
    "Recorded Signal Strength"
    "Derived Range (m)"
    "Recorded Signal Strength"
    "Derived Range (m)"
];

fogMeans = zeros(4,1);
clearMeans = zeros(4,1);

%% Plot each metric separately
for k = 1:4

    metric = metrics(k);

    fogValues = fog.(metric);
    clearValues = clearData.(metric);

    % Ignore missing or non-finite values
    fogValues(~isfinite(fogValues)) = NaN;
    clearValues(~isfinite(clearValues)) = NaN;

    fogMeans(k) = mean(fogValues, 'omitnan');
    clearMeans(k) = mean(clearValues, 'omitnan');

    fig = figure('Color', 'w');

    plot(fog.time_s, fogValues, ...
        'b', 'LineWidth', 1.2);
    hold on;

    plot(clearData.time_s, clearValues, ...
        'r', 'LineWidth', 1.2);

    xlabel('Simulation Time (s)');
    ylabel(units(k));
    title("GEMSTAR: " + titles(k));

    legend('Fog', 'Clear', 'Location', 'best');
    grid on;

    filename = "task08_" + metric + "_fog_vs_clear";

    exportgraphics(fig, ...
        figureFolder + "\" + filename + ".png", ...
        'Resolution', 300);

    savefig(fig, ...
        figureFolder + "\" + filename + ".fig");

end

%% Create research summary table
difference = clearMeans - fogMeans;

summary = table( ...
    metrics, ...
    fogMeans, ...
    clearMeans, ...
    difference, ...
    'VariableNames', { ...
        'Metric', ...
        'FogMean', ...
        'ClearMean', ...
        'ClearMinusFog' ...
    });

disp(' ');
disp('========== REFLECTION COMPARISON ==========');
disp(summary);

%% Save numerical results
csvFile = tableFolder + "\task08_reflection_quality_summary.csv";

writetable(summary, csvFile);

disp(' ');
disp('TASK 8.13 COMPLETED SUCCESSFULLY');
disp('Saved four research graphs.');
disp('Saved summary: ' + csvFile);
