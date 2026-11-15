% ============================================================
% GEMSTAR TASK 28.3C.3
% CPU Workload and Latency Research Analysis
% ============================================================

clear;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

task26 = fullfile(root,'tests', ...
    'Task_26_Final_Research','02_CSV_Data');

task28 = fullfile(root,'tests','Task_28_Final_Research');

plotDir = fullfile(task28,'04_Plots', ...
    'CPU_Workload_Latency');

if ~exist(plotDir,'dir')
    mkdir(plotDir);
end

%% Read original benchmark datasets

EKF = readtable(fullfile(task26, ...
    'task26_3B_ekf_cpu_timing.csv'), ...
    'TextType','string');

Camera = readtable(fullfile(task26, ...
    'task26_4B_camera_cpu_timing.csv'), ...
    'TextType','string');

LiDAR = readtable(fullfile(task26, ...
    'task26_4D_lidar_cpu_timing.csv'), ...
    'TextType','string');

Radar = readtable(fullfile(task26, ...
    'task26_4G_radar_cpu_timing.csv'));

YOLO = readtable(fullfile(task26, ...
    'task26_4J_yolo_cpu_timing.csv'));

Integrated = readtable(fullfile(task26, ...
    'task26_5C_integrated_cpu_timing.csv'));

assert(height(EKF)==200 && ...
       height(Camera)==600 && ...
       height(LiDAR)==2650 && ...
       height(Radar)==1200 && ...
       height(YOLO)==50 && ...
       height(Integrated)==1325, ...
       'CPU benchmark row counts do not match.');

%% Prepare stage-specific measurements

LF = LiDAR(LiDAR.stage=="filter",:);
LC = LiDAR(LiDAR.stage=="cluster",:);

CF = Camera(Camera.mode=="FULL",:);
CR = Camera(Camera.mode=="ROI",:);

EB = EKF(EKF.workload=="baseline",:);
ES = EKF(EKF.workload=="seven_scenarios",:);

assert(height(LF)==1325 && height(LC)==1325, ...
    'LiDAR stages incomplete.');

assert(height(CF)==300 && height(CR)==300, ...
    'Camera modes incomplete.');

assert(height(EB)==100 && height(ES)==100, ...
    'EKF workloads incomplete.');

%% Verify latency fields before plotting

latencySets = {
    LF.elapsed_ms
    LC.elapsed_ms
    CF.elapsed_ms
    CR.elapsed_ms
    Radar.batch_elapsed_ms
    YOLO.elapsed_ms
    EB.elapsed_ms
    ES.elapsed_ms
    Integrated.total_ms
    Integrated.filter_ms
    Integrated.cluster_ms
    Integrated.radar_ms
};

for k=1:numel(latencySets)
    v = latencySets{k};
    assert(all(isfinite(v)) && all(v>=0), ...
        'Nonfinite or negative CPU timing detected.');
end

%% FIGURE 1 — LiDAR workload vs CPU latency

f1 = figure('Color','w', ...
    'Name','LiDAR Workload Latency', ...
    'Position',[100 100 1100 540]);

tiledlayout(1,2);

nexttile;
scatter(LF.input_points,LF.elapsed_ms,9,'filled');
grid on;
xlabel('Input points');
ylabel('CPU latency (ms)');
title('LiDAR Filtering');

nexttile;
scatter(LC.input_points,LC.elapsed_ms,9,'filled');
grid on;
xlabel('Input points');
ylabel('CPU latency (ms)');
title('LiDAR Clustering');

sgtitle('LiDAR: Measured Input Workload vs Stage Latency');

%% FIGURE 2 — Radar batch workload

f2 = figure('Color','w', ...
    'Name','Radar Workload Latency', ...
    'Position',[120 120 1050 540]);

scatter(Radar.returns_processed, ...
    Radar.batch_elapsed_ms,12,'filled');
grid on;
xlabel('Radar returns processed');
ylabel('Batch CPU latency (ms)');
title('Radar: Measured Returns vs Batch Execution Time');

%% FIGURE 3 — Camera ROI versus FULL

f3 = figure('Color','w', ...
    'Name','Camera Processing Modes', ...
    'Position',[140 140 1100 540]);

tiledlayout(1,2);

nexttile;
histogram(CF.elapsed_ms,25);
hold on;
histogram(CR.elapsed_ms,25);
grid on;
xlabel('CPU latency (ms)');
ylabel('Benchmark observations');
title('Camera Processing Latency');
legend({'FULL','ROI'},'Location','best');

nexttile;
bar([median(CF.elapsed_ms),median(CR.elapsed_ms); ...
     prctile(CF.elapsed_ms,99),prctile(CR.elapsed_ms,99)]);

xticks([1 2]);
xticklabels({'Median','P99'});
ylabel('CPU latency (ms)');
title('Camera Latency Percentiles');
legend({'FULL','ROI'},'Location','best');
grid on;

sgtitle('Camera: Different Processing Boundaries');

%% FIGURE 4 — Integrated stage timings

f4 = figure('Color','w', ...
    'Name','Integrated CPU Stage Breakdown', ...
    'Position',[160 160 1100 570]);

tiledlayout(2,2);

nexttile;
scatter(Integrated.lidar_input_points, ...
    Integrated.filter_ms,9,'filled');
grid on;
xlabel('LiDAR input points');
ylabel('Filtering (ms)');
title('LiDAR Filter');

nexttile;
scatter(Integrated.lidar_filtered_points, ...
    Integrated.cluster_ms,9,'filled');
grid on;
xlabel('Filtered points');
ylabel('Clustering (ms)');
title('LiDAR Cluster');

nexttile;
scatter(Integrated.radar_input_returns, ...
    Integrated.radar_ms,9,'filled');
grid on;
xlabel('Radar input returns');
ylabel('Radar processing (ms)');
title('Radar');

nexttile;
scatter(Integrated.lidar_input_points, ...
    Integrated.total_ms,9,'filled');
grid on;
xlabel('LiDAR input points');
ylabel('Integrated measured latency (ms)');
title('Integrated Benchmark Total');

sgtitle('Integrated CPU Benchmark: Stage-Specific Measurements');

%% FIGURE 5 — EKF and YOLO timing distributions

f5 = figure('Color','w', ...
    'Name','EKF and YOLO Timings', ...
    'Position',[180 180 1100 540]);

tiledlayout(1,3);

nexttile;
histogram(EB.elapsed_ms,20);
grid on;
xlabel('Batch latency (ms)');
ylabel('Observations');
title('EKF Baseline: 24 Observations');

nexttile;
histogram(ES.elapsed_ms,20);
grid on;
xlabel('Batch latency (ms)');
ylabel('Observations');
title('EKF: 168 Observations');

nexttile;
histogram(YOLO.elapsed_ms,20);
grid on;
xlabel('Inference latency (ms)');
ylabel('Observations');
title('YOLO CPU Inference');

sgtitle('Separate CPU Workload Timing Distributions');

%% Calculate descriptive workload relationships

% Correlations are descriptive, not causal models.
Names = [
    "LiDAR_Filter"
    "LiDAR_Cluster"
    "Radar_Batch"
    "Integrated_Filter"
    "Integrated_Cluster"
    "Integrated_Radar"
    "Integrated_Total"
];

X = {
    LF.input_points
    LC.input_points
    Radar.returns_processed
    Integrated.lidar_input_points
    Integrated.lidar_filtered_points
    Integrated.radar_input_returns
    Integrated.lidar_input_points
};

Y = {
    LF.elapsed_ms
    LC.elapsed_ms
    Radar.batch_elapsed_ms
    Integrated.filter_ms
    Integrated.cluster_ms
    Integrated.radar_ms
    Integrated.total_ms
};

N = zeros(numel(Names),1);
InputMin = zeros(numel(Names),1);
InputMax = zeros(numel(Names),1);
MedianMs = zeros(numel(Names),1);
P99Ms = zeros(numel(Names),1);
Correlation = nan(numel(Names),1);

for k=1:numel(Names)

    x = double(X{k});
    y = double(Y{k});

    assert(all(isfinite(x)) && all(isfinite(y)), ...
        'Nonfinite workload/latency values.');

    N(k) = numel(y);
    InputMin(k) = min(x);
    InputMax(k) = max(x);
    MedianMs(k) = median(y);
    P99Ms(k) = prctile(y,99);

    if numel(unique(x))>1 && numel(unique(y))>1
        C = corrcoef(x,y);
        Correlation(k) = C(1,2);
    end
end

Summary = table(Names,N,InputMin,InputMax, ...
    MedianMs,P99Ms,Correlation);

%% Save outputs

dataDir = fullfile(task28,'02_CSV_Data');

csvFile = fullfile(dataDir, ...
    'task28_3C3_cpu_workload_correlations.csv');

figs = {f1,f2,f3,f4,f5};

names = {
    'task28_3C3_lidar_workload_latency'
    'task28_3C3_radar_workload_latency'
    'task28_3C3_camera_modes'
    'task28_3C3_integrated_stages'
    'task28_3C3_ekf_yolo_distributions'
};

assert(~isfile(csvFile), ...
    'Output statistics already exist.');

for k=1:numel(figs)
    assert(~isfile(fullfile(plotDir,[names{k} '.png'])) && ...
           ~isfile(fullfile(plotDir,[names{k} '.fig'])), ...
        'Output figures already exist.');
end

writetable(Summary,csvFile);

for k=1:numel(figs)

    savefig(figs{k}, ...
        fullfile(plotDir,[names{k} '.fig']));

    exportgraphics(figs{k}, ...
        fullfile(plotDir,[names{k} '.png']), ...
        'Resolution',300);
end

fprintf('\n============================================\n');
fprintf('TASK 28.3C.3 COMPLETE\n');
fprintf('============================================\n');

fprintf('Benchmark observations validated: 6025\n');
fprintf('Figures: 5 PNG + 5 FIG\n');
fprintf('Statistics CSV: %s\n',csvFile);
fprintf('Plots: %s\n',plotDir);

fprintf('\nWorkload correlations:\n');
disp(Summary);

fprintf('\nIMPORTANT LIMITATIONS:\n');
fprintf('- Correlation does not prove workload causality.\n');
fprintf('- Separate benchmark stages have different boundaries.\n');
fprintf('- These timings are not KR260 hardware measurements.\n');
fprintf('- YOLO detections are not input workload size.\n');
fprintf('- No measured energy savings are claimed.\n');
