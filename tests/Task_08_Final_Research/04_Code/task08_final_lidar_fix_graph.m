
%% TASK 8.17 - Final LiDAR Weather Fix Validation

clc;
clear;
close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor";

archive = root + "\tests\Task_08_Final_Research";

graphFolder = archive + "\01_Graphs";
csvFolder = archive + "\02_CSV_Data";

% Read the already verified measurements
T = readtable(csvFolder + ...
    "\task08_lidar_before_vs_after_fix.csv");

% One row per experiment is sufficient
experiments = unique(string(T.experiment), 'stable');

rates = zeros(numel(experiments), 1);
maxRanges = zeros(numel(experiments), 1);

for i = 1:numel(experiments)

    rows = strcmp(string(T.experiment), experiments(i));

    rates(i) = T.positive_return_rate_pct(find(rows,1));
    maxRanges(i) = ...
        T.maximum_positive_distance_m(find(rows,1));

end

labels = replace(experiments, "_", " ");

%% Figure 1: Positive return rate

fig1 = figure('Color','w');

bar(categorical(labels), rates);

ylabel('Positive LiDAR Returns (%)');
title('LiDAR Fog Model: Before vs After Correction');
ylim([0 55]);
grid on;

exportgraphics(fig1, ...
    graphFolder + "\task08_final_lidar_return_rate.png", ...
    'Resolution',300);

savefig(fig1, ...
    graphFolder + "\task08_final_lidar_return_rate.fig");

%% Figure 2: Maximum positive range

fig2 = figure('Color','w');

bar(categorical(labels), maxRanges);

ylabel('Maximum Positive LiDAR Range (m)');
title('LiDAR Fog Model: Maximum Detection Range');
ylim([0 25]);
grid on;

exportgraphics(fig2, ...
    graphFolder + "\task08_final_lidar_max_range.png", ...
    'Resolution',300);

savefig(fig2, ...
    graphFolder + "\task08_final_lidar_max_range.fig");

%% Create concise research summary CSV

summary = table(experiments, rates, maxRanges, ...
    'VariableNames', ...
    {'Experiment','PositiveReturnRatePct','MaxPositiveRangeM'});

writetable(summary, ...
    csvFolder + "\task08_final_lidar_fix_summary.csv");

disp(summary);
disp('Task 8.17 research graphs saved successfully.');
