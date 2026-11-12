%% Task 26.7C - CPU Timing Reliability Visualization
% Existing measurements only; no benchmark re-execution.
% Descriptive timing statistics, NOT hard real-time guarantees.

clear; clc; close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_26_Final_Research";
dataDir = fullfile(root,"02_CSV_Data");
plotDir = fullfile(root,"04_Plots");
findDir = fullfile(root,"06_Research_Findings");

workloadFile = fullfile(dataDir, ...
    "task26_7B_repeatability_by_workload.csv");

groupFile = fullfile(dataDir, ...
    "task26_7B_repeatability_by_group.csv");

radarFile = fullfile(dataDir, ...
    "task26_4G_radar_cpu_timing.csv");

reportFile = fullfile(findDir, ...
    "task26_7C_timing_reliability_findings.txt");

plotNames = [
    "task26_7C_median_and_maximum.png"
    "task26_7C_timing_variability.png"
    "task26_7C_outlier_rates.png"
    "task26_7C_radar_batch_distribution.png"
];

%% Protect previous research

for p = [workloadFile,groupFile,radarFile]
    if ~isfile(p)
        error("Required CSV missing: %s",p);
    end
end

if isfile(reportFile)
    error("Existing research report preserved.");
end

for k = 1:numel(plotNames)
    if isfile(fullfile(plotDir,plotNames(k)))
        error("Existing plot preserved: %s",plotNames(k));
    end
end

W = readtable(workloadFile,"TextType","string");
G = readtable(groupFile,"TextType","string");
R = readtable(radarFile,"TextType","string");

expectedNames = [
    "EKF"
    "Camera"
    "LiDAR"
    "Radar"
    "YOLO11s"
    "Partial_LiDAR_Radar"
];

if height(W) ~= 6 || height(G) ~= 184 || height(R) ~= 1200
    error("Unexpected benchmark data dimensions.");
end

[found,idx] = ismember(expectedNames,W.workload);
if ~all(found)
    error("Unexpected workload names.");
end

W = W(idx,:);

if sum(W.timing_rows) ~= 6025
    error("Timing row count mismatch.");
end

names = {
    'EKF replay'
    'Camera'
    'LiDAR stages'
    'Radar batches'
    'YOLO11s'
    'Partial pipeline'
};

n = height(W);

%% Figure 1: Representative medians versus maxima
% These are different timing units and are NOT additive.

f1 = figure("Color","w","Position",[100 100 1100 580]);

bar(1:n,[
    W.median_of_group_medians_ms, ...
    W.maximum_observed_ms
]);

set(gca,"XTick",1:n,"XTickLabel",names);
xtickangle(20);
set(gca,"YScale","log");

ylabel("Elapsed time (ms), logarithmic scale");
title("Task 26.7 - Representative median vs observed maximum");
legend("Median of group medians","Maximum observed", ...
    "Location","northwest");
grid on;

%% Figure 2: Within-group timing variability

f2 = figure("Color","w","Position",[100 100 1080 550]);

bar(1:n,[
    W.median_group_cv_percent, ...
    W.max_group_cv_percent
]);

set(gca,"XTick",1:n,"XTickLabel",names);
xtickangle(20);

ylabel("Coefficient of variation (%)");
title("Task 26.7 - Within-group runtime variability");

legend("Median group CV","Maximum group CV", ...
    "Location","best");
grid on;

%% Figure 3: Descriptive outlier rates

f3 = figure("Color","w","Position",[100 100 1080 550]);

bar(1:n,W.outlier_rate_percent);

set(gca,"XTick",1:n,"XTickLabel",names);
xtickangle(20);

ylabel("Within-group Tukey outliers (%)");
title("Task 26.7 - Outlier observations retained");
grid on;

%% Figure 4: Radar batches and extreme observation

radarMs = R.batch_elapsed_ms;

if any(~isfinite(radarMs)) || any(radarMs <= 0)
    error("Invalid Radar batch duration.");
end

radarMax = max(radarMs);
radarMedian = median(radarMs);

f4 = figure("Color","w","Position",[100 100 1050 550]);

histogram(radarMs,60);
set(gca,"XScale","log");

xlabel("Radar batch elapsed time (ms), log scale");
ylabel("Recorded executions");
title("Task 26.7 - Radar batch timing distribution");

xline(radarMedian,"--", ...
    "Median of pooled Radar batch measurements", ...
    "LabelOrientation","horizontal");

xline(radarMax,":", ...
    "Maximum observed", ...
    "LabelOrientation","horizontal");

grid on;

%% Save all figures only after validation

if ~isfolder(plotDir)
    mkdir(plotDir);
end

saveas(f1,fullfile(plotDir,plotNames(1)));
saveas(f2,fullfile(plotDir,plotNames(2)));
saveas(f3,fullfile(plotDir,plotNames(3)));
saveas(f4,fullfile(plotDir,plotNames(4)));

%% Numerical cross-checks and report

disp("=== TASK 26.7C MATLAB TIMING RELIABILITY ===");

fprintf("TIMING_ROWS: %d\n",sum(W.timing_rows));
fprintf("MEASUREMENT_GROUPS: %d\n",height(G));
fprintf("RADAR_BATCH_ROWS: %d\n",height(R));
fprintf("RADAR_POOLED_MEDIAN_MS: %.6f\n",radarMedian);
fprintf("RADAR_MAX_OBSERVED_MS: %.6f\n",radarMax);
fprintf("RADAR_MAX_TO_POOLED_MEDIAN_RATIO: %.3f\n", ...
    radarMax/radarMedian);

for k = 1:n
    fprintf( ...
        "%s: MEDIAN_CV=%.3f%% OUTLIER_RATE=%.3f%%\n", ...
        expectedNames(k), ...
        W.median_group_cv_percent(k), ...
        W.outlier_rate_percent(k));
end

fid = fopen(reportFile,"w");
if fid == -1
    error("Unable to create findings report.");
end

fprintf(fid,"TASK 26.7C - CPU TIMING RELIABILITY\n");
fprintf(fid,"==================================\n\n");
fprintf(fid,"Timing observations: %d\n",sum(W.timing_rows));
fprintf(fid,"Measurement groups: %d\n\n",height(G));

for k = 1:n
    fprintf(fid,"%s\n",expectedNames(k));
    fprintf(fid,"Groups: %d\n",W.groups(k));
    fprintf(fid,"Timing observations: %d\n",W.timing_rows(k));
    fprintf(fid,"Median of group medians: %.9f ms\n", ...
        W.median_of_group_medians_ms(k));
    fprintf(fid,"Max group descriptive p99: %.9f ms\n", ...
        W.max_group_p99_ms(k));
    fprintf(fid,"Median within-group CV: %.5f%%\n", ...
        W.median_group_cv_percent(k));
    fprintf(fid,"Outlier rate: %.5f%%\n\n", ...
        W.outlier_rate_percent(k));
end

fprintf(fid,"Radar pooled median: %.9f ms\n",radarMedian);
fprintf(fid,"Radar maximum: %.9f ms\n\n",radarMax);

fprintf(fid,"LIMITATIONS\n");
fprintf(fid,"- Measurements use repeated stored inputs.\n");
fprintf(fid,"- Workload timing units differ.\n");
fprintf(fid,"- EKF replay group sizes differ.\n");
fprintf(fid,"- Radar batch return counts differ.\n");
fprintf(fid,"- Some sample groups have only 10 or 25 runs.\n");
fprintf(fid,"- Tail percentiles are descriptive estimates.\n");
fprintf(fid,"- Outliers are retained, not discarded.\n");
fprintf(fid,"- Partial pipeline is not full-system latency.\n");
fprintf(fid,"- No certified worst-case execution time.\n");
fprintf(fid,"- No measured ARM-FPGA board energy.\n");

fclose(fid);

disp("PLOTS_GENERATED: 4");
disp("STATISTICAL_ANALYSIS: DESCRIPTIVE_ONLY");
disp("HARD_REAL_TIME_GUARANTEE: NO");
disp("ENERGY_MEASURED: NO");
disp("TASK26_7C_MATLAB_RELIABILITY_PASS");
disp("REPORT: " + reportFile);
disp("PLOTS: " + plotDir);
