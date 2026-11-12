%% Task 26.3B - CPU EKF Benchmark MATLAB Analysis
% Uses actual measured CSV timing data.
% Does not execute or modify original Task 24/25 code.
% All times are full replay execution durations.

clear; clc; close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_26_Final_Research";

inputCSV = fullfile(root, "02_CSV_Data", ...
    "task26_3B_ekf_cpu_timing.csv");

plotDir = fullfile(root, "04_Plots");
outputCSV = fullfile(root, "02_CSV_Data", ...
    "task26_3B_matlab_latency_summary.csv");

if ~isfile(inputCSV)
    error("Benchmark CSV was not found.");
end

if isfile(outputCSV)
    error("MATLAB summary already exists. Preserving it.");
end

if ~isfolder(plotDir)
    mkdir(plotDir);
end

T = readtable(inputCSV, "TextType", "string");

required = ["workload","observations","elapsed_ms", ...
    "ms_per_observation"];

if ~all(ismember(required, string(T.Properties.VariableNames)))
    error("Required benchmark columns are missing.");
end

baseline = T(T.workload == "baseline", :);
faults = T(T.workload == "seven_scenarios", :);

if height(baseline) ~= 100 || height(faults) ~= 100
    error("Expected 100 runs for each workload.");
end

if any(baseline.observations ~= 24) || ...
        any(faults.observations ~= 168)
    error("Unexpected observation counts.");
end

groups = {baseline, faults};
names = ["Baseline EKF","Seven scenarios"];

medianMs = zeros(2,1);
p95Ms = zeros(2,1);
p99Ms = zeros(2,1);
meanMs = zeros(2,1);
perObs = zeros(2,1);

for k = 1:2
    A = groups{k};
    values = A.elapsed_ms;

    medianMs(k) = median(values);
    meanMs(k) = mean(values);

    sorted = sort(values);
    n = numel(sorted);
    positions = 1:n;

    % Linear interpolation matching the Python benchmark.
    p95Ms(k) = interp1(positions,sorted, ...
        1+(n-1)*0.95);
    p99Ms(k) = interp1(positions,sorted, ...
        1+(n-1)*0.99);

    perObs(k) = median(A.ms_per_observation);
end

summary = table(names',meanMs,medianMs,p95Ms,p99Ms,perObs, ...
    'VariableNames', ...
    {'Workload','Mean_ms','Median_ms','P95_ms', ...
    'P99_ms','Median_ms_per_observation'});

disp("=== TASK 26 MATLAB ANALYSIS ===");
disp(summary);

writetable(summary,outputCSV);

%% Figure 1 - Timing distributions
figure('Color','w','Position',[100,100,1000,450]);

histogram(baseline.elapsed_ms,20, ...
    'FaceAlpha',0.7);
hold on;
histogram(faults.elapsed_ms,20, ...
    'FaceAlpha',0.5);
hold off;

xlabel('Complete replay duration (ms)');
ylabel('Number of runs');
title('Task 26.3B - CPU EKF replay latency distribution');
legend('Baseline (24 observations)', ...
    'Seven scenarios (168 observations)');
grid on;

saveas(gcf,fullfile(plotDir, ...
    'task26_3B_latency_distribution.png'));

%% Figure 2 - Latency percentiles
figure('Color','w','Position',[100,100,850,450]);

bar([medianMs,p95Ms,p99Ms]);

set(gca,'XTick',1:2,'XTickLabel',cellstr(names));
ylabel('Complete replay duration (ms)');
title('Task 26.3B - Median, p95 and p99 latency');
legend('Median','p95','p99','Location','northwest');
grid on;

saveas(gcf,fullfile(plotDir, ...
    'task26_3B_latency_percentiles.png'));

%% Figure 3 - Normalized execution time
figure('Color','w','Position',[100,100,850,450]);

bar(perObs);
set(gca,'XTick',1:2,'XTickLabel',cellstr(names));

ylabel('Median milliseconds per observation');
title('Task 26.3B - Normalized EKF processing cost');
grid on;

saveas(gcf,fullfile(plotDir, ...
    'task26_3B_normalized_processing.png'));

disp("TASK26_3B_MATLAB_ANALYSIS_PASS");
disp("Plots saved to:");
disp(plotDir);
