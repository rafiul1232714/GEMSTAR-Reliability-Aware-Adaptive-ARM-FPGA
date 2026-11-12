%% Task 26.4H - GEMSTAR Radar CPU Benchmark Analysis
% Measurements from Task 26.4G.
% Original input datasets remain unchanged.
% Valid-return batch processing only. No energy measured.

clear; clc; close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_26_Final_Research";

csvDir = fullfile(root,"02_CSV_Data");
plotDir = fullfile(root,"04_Plots");

timingPath = fullfile(csvDir,"task26_4G_radar_cpu_timing.csv");
summaryPath = fullfile(csvDir,"task26_4G_radar_cpu_summary.csv");

if ~isfile(timingPath) || ~isfile(summaryPath)
    error("Required Radar benchmark CSV files are missing.");
end

T = readtable(timingPath);
S = readtable(summaryPath);

if height(T) ~= 1200 || height(S) ~= 12
    error("Unexpected Radar benchmark dataset size.");
end

names = [
    "task26_4H_radar_median_p99.png"
    "task26_4H_radar_workload_scaling.png"
    "task26_4H_radar_latency_distribution.png"
    "task26_4H_radar_per_return_cost.png"
];

for k = 1:numel(names)
    if isfile(fullfile(plotDir,names(k)))
        error("Existing plot preserved: %s",names(k));
    end
end

if ~isfolder(plotDir)
    mkdir(plotDir);
end

labels = strings(height(S),1);

for i = 1:height(S)
    labels(i) = "P" + string(S.pair_id(i)) + ...
        "-F" + string(S.frame(i));
end

%% Figure 1 - Median and p99 batch latency

f1 = figure("Color","w","Position",[100 100 1000 480]);

bar([S.median_ms S.p99_ms]);

set(gca,"XTick",1:height(S), ...
    "XTickLabel",cellstr(labels));
xtickangle(45);

ylabel("Radar batch execution time (ms)");
title("Task 26 - Radar median versus p99 CPU latency");
legend("Median","p99","Location","best");
grid on;

saveas(f1,fullfile(plotDir,names(1)));

%% Figure 2 - Batch workload scaling

f2 = figure("Color","w","Position",[100 100 900 480]);

scatter(S.returns_processed,S.median_ms,65,"filled");

xlabel("Valid Radar returns per batch");
ylabel("Median batch duration (ms)");
title("Task 26 - Radar workload scaling");
grid on;

saveas(f2,fullfile(plotDir,names(2)));

%% Figure 3 - Timing distribution

f3 = figure("Color","w","Position",[100 100 950 480]);

histogram(T.batch_elapsed_ms,35);

xlabel("Valid-return batch execution time (ms)");
ylabel("Number of timed runs");
title("Task 26 - Radar CPU batch latency distribution");
grid on;

saveas(f3,fullfile(plotDir,names(3)));

%% Figure 4 - Cost per processed return

f4 = figure("Color","w","Position",[100 100 1000 480]);

costUs = 1000 * S.median_ms_per_return;

bar(costUs);

set(gca,"XTick",1:height(S), ...
    "XTickLabel",cellstr(labels));
xtickangle(45);

ylabel("Median batch time per valid return (microseconds)");
title("Task 26 - Radar normalized CPU processing cost");
grid on;

saveas(f4,fullfile(plotDir,names(4)));

%% Numerical summary

disp("=== TASK 26.4H RADAR MATLAB ANALYSIS ===");

fprintf("FRAME_GROUPS: %d\n",height(S));
fprintf("TIMED_BATCH_RUNS: %d\n",height(T));

fprintf("MIN_MEDIAN_BATCH_MS: %.6f\n",min(S.median_ms));
fprintf("MAX_MEDIAN_BATCH_MS: %.6f\n",max(S.median_ms));

fprintf("MAX_FRAME_P99_MS: %.6f\n",max(S.p99_ms));

fprintf("MEDIAN_OF_FRAME_MEDIANS_MS: %.6f\n", ...
    median(S.median_ms));

fprintf("MEDIAN_NORMALIZED_COST_US: %.6f\n", ...
    median(costUs));

disp("REFERENCE_VALIDATION: Verified by Task 26.4G");
disp("INVALID_RETURNS_TIMED: NO");
disp("RADAR_ASSOCIATION_TIMED: NO");
disp("ENERGY_MEASURED: NO");
disp("TASK26_4H_RADAR_MATLAB_ANALYSIS_PASS");
