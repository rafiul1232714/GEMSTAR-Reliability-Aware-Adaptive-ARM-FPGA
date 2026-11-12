%% Task 26.4L - Consolidated CPU Benchmark Analysis
% Original measurements: EKF, Camera, LiDAR, Radar, YOLO.
% No Statistics Toolbox required.
% Different operations have different timing units.
% Do NOT interpret this as end-to-end pipeline latency.

clear; clc; close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_26_Final_Research";

csvDir = fullfile(root,"02_CSV_Data");
plotDir = fullfile(root,"04_Plots");
reportDir = fullfile(root,"06_Research_Findings");

ekfFile = fullfile(csvDir,"task26_3B_ekf_cpu_timing.csv");
cameraFile = fullfile(csvDir,"task26_4B_camera_cpu_summary.csv");
lidarFile = fullfile(csvDir,"task26_4D_lidar_cpu_summary.csv");
radarFile = fullfile(csvDir,"task26_4G_radar_cpu_summary.csv");
yoloFile = fullfile(csvDir,"task26_4J_yolo_cpu_summary.csv");

reportPath = fullfile(reportDir, ...
    "task26_4L_consolidated_cpu_findings.txt");

summaryPath = fullfile(csvDir, ...
    "task26_4L_consolidated_cpu_summary.csv");

plotNames = [
    "task26_4L_cpu_workload_overview.png"
    "task26_4L_timing_variability.png"
    "task26_4L_lidar_processing_breakdown.png"
    "task26_4L_camera_vs_yolo.png"
];

%% Verify inputs

inputs = [ekfFile,cameraFile,lidarFile,radarFile,yoloFile];

for k = 1:numel(inputs)
    if ~isfile(inputs(k))
        error("Missing benchmark input: %s",inputs(k));
    end
end

if isfile(reportPath) || isfile(summaryPath)
    error("Existing consolidated output preserved.");
end

for k = 1:numel(plotNames)
    if isfile(fullfile(plotDir,plotNames(k)))
        error("Existing plot preserved: %s",plotNames(k));
    end
end

if ~isfolder(plotDir)
    mkdir(plotDir);
end

%% Read actual benchmark data

E = readtable(ekfFile,"TextType","string");
C = readtable(cameraFile,"TextType","string");
L = readtable(lidarFile,"TextType","string");
R = readtable(radarFile,"TextType","string");
Y = readtable(yoloFile,"TextType","string");

if height(E) ~= 200 || height(C) ~= 6 || ...
   height(L) ~= 106 || height(R) ~= 12 || ...
   height(Y) ~= 5
    error("Unexpected benchmark input dimensions.");
end

baseline = E(E.workload == "baseline",:);

if height(baseline) ~= 100 || ...
        any(baseline.observations ~= 24)
    error("Invalid baseline EKF measurements.");
end

cameraROI = C(C.mode == "ROI",:);
cameraFull = C(C.mode == "FULL",:);

lidarFilter = L(L.stage == "filter",:);
lidarCluster = L(L.stage == "cluster",:);

if height(cameraROI) ~= 3 || height(cameraFull) ~= 3 ...
        || height(lidarFilter) ~= 53 ...
        || height(lidarCluster) ~= 53
    error("Missing processing configurations.");
end

lidarFilter = sortrows(lidarFilter,"frame");
lidarCluster = sortrows(lidarCluster,"frame");

if any(lidarFilter.frame ~= lidarCluster.frame)
    error("LiDAR frame IDs do not match.");
end

%% Representative latency statistics
% EKF: median of 100 complete 24-observation replays.
% Others: median of per-configuration or per-frame medians.

names = [
    "EKF baseline"
    "Camera ROI"
    "Camera full"
    "LiDAR filter"
    "LiDAR cluster"
    "Radar valid batch"
    "YOLO11s"
];

units = [
    "24-observation replay"
    "384x288 region"
    "640x480 image"
    "selected LiDAR frame"
    "filtered LiDAR frame"
    "valid-return batch"
    "selected Camera image"
];

medianMs = [
    median(baseline.elapsed_ms)
    median(cameraROI.median_ms)
    median(cameraFull.median_ms)
    median(lidarFilter.median_ms)
    median(lidarCluster.median_ms)
    median(R.median_ms)
    median(Y.median_ms)
];

%% Timing variability
% For EKF, compute one p99 from the baseline replay runs.
% For other operations, take the median of within-group
% p99 estimates, NOT a pooled system-wide p99.

sortedEKF = sort(baseline.elapsed_ms);
position = 1 + (numel(sortedEKF)-1)*0.99;
low = floor(position);
high = ceil(position);

ekfP99 = sortedEKF(low) + ...
    (sortedEKF(high)-sortedEKF(low))*(position-low);

representativeP99 = [
    ekfP99
    median(cameraROI.p99_ms)
    median(cameraFull.p99_ms)
    median(lidarFilter.p99_ms)
    median(lidarCluster.p99_ms)
    median(R.p99_ms)
    median(Y.p99_ms)
];

tailRatio = representativeP99 ./ medianMs;

result = table(names,units,medianMs,representativeP99,tailRatio, ...
    'VariableNames', ...
    {'Workload','TimingUnit','RepresentativeMedianMs', ...
     'RepresentativeP99Ms','DescriptiveTailRatio'});

disp("=== TASK 26.4L CONSOLIDATED CPU ANALYSIS ===");
disp(result);

%% Figure 1 - Workload overview
% Logarithmic vertical axis because the workloads
% differ by several orders of magnitude.

f1 = figure("Color","w","Position",[100 100 1150 550]);

bar(medianMs);
set(gca,"YScale","log");
set(gca,"XTick",1:numel(names), ...
    "XTickLabel",cellstr(names));

xtickangle(30);
ylabel("Representative execution duration (ms), log scale");
title("Task 26 - CPU workload overview");
grid on;

saveas(f1,fullfile(plotDir,plotNames(1)));

%% Figure 2 - Descriptive timing variability
% Values are within-workload tail ratios.
% They are NOT comparable real-time deadline guarantees.

f2 = figure("Color","w","Position",[100 100 1150 500]);

bar(tailRatio);

set(gca,"XTick",1:numel(names), ...
    "XTickLabel",cellstr(names));

xtickangle(30);
ylabel("Representative p99 / median ratio");
title("Task 26 - CPU execution-time variability");
grid on;

saveas(f2,fullfile(plotDir,plotNames(2)));

%% Figure 3 - LiDAR processing breakdown

f3 = figure("Color","w","Position",[100 100 1100 500]);

plot(lidarFilter.frame,lidarFilter.median_ms, ...
    "-o","LineWidth",1.4);

hold on;

plot(lidarCluster.frame,lidarCluster.median_ms, ...
    "-s","LineWidth",1.4);

hold off;

xlabel("GEMSTAR frame");
ylabel("Median CPU stage latency (ms)");
title("Task 26 - LiDAR filtering versus clustering");

legend("Filtering","Clustering","Location","best");
grid on;

saveas(f3,fullfile(plotDir,plotNames(3)));

%% Figure 4 - Camera preprocessing versus YOLO
% Descriptive comparison only.
% Different inputs, image sizes and software environments.

cameraValues = [
    median(cameraROI.median_ms)
    median(cameraFull.median_ms)
    median(Y.median_ms)
];

f4 = figure("Color","w","Position",[100 100 950 500]);

bar(cameraValues);

set(gca,"XTick",1:3, ...
    "XTickLabel", ...
    {"Camera ROI","Camera full","YOLO11s"});

ylabel("Representative CPU duration (ms)");
title("Task 26 - Conventional Camera versus YOLO11s");
grid on;

saveas(f4,fullfile(plotDir,plotNames(4)));

%% Export numerical summary

writetable(result,summaryPath);

%% Research report

fid = fopen(reportPath,"w");

if fid == -1
    error("Cannot create consolidated findings report.");
end

fprintf(fid,"TASK 26.4L - CONSOLIDATED CPU ANALYSIS\n");
fprintf(fid,"=====================================\n\n");

for k = 1:numel(names)
    fprintf(fid,"%s\n",names(k));
    fprintf(fid,"  Timing unit: %s\n",units(k));
    fprintf(fid,"  Representative median: %.6f ms\n",medianMs(k));
    fprintf(fid,"  Representative p99: %.6f ms\n", ...
        representativeP99(k));
    fprintf(fid,"  Descriptive tail ratio: %.3f\n\n", ...
        tailRatio(k));
end

fprintf(fid,"RESEARCH FINDINGS AND LIMITATIONS\n");
fprintf(fid,"- YOLO11s is the highest-duration tested workload.\n");
fprintf(fid,"- Radar valid-return processing is lightweight.\n");
fprintf(fid,"- LiDAR filtering takes longer than clustering in this selected scenario.\n");
fprintf(fid,"- EKF is timed per 24-observation replay, not per sensor frame.\n");
fprintf(fid,"- Measurements have different timing units and cannot be summed into a pipeline latency.\n");
fprintf(fid,"- Some comparisons use different images and software environments.\n");
fprintf(fid,"- p99 estimates are exploratory; YOLO has only ten runs per image.\n");
fprintf(fid,"- No final ARM CPU performance was measured.\n");
fprintf(fid,"- No FPGA performance or board energy was measured.\n");
fprintf(fid,"- Perception quality must remain a hard constraint.\n");
fprintf(fid,"- Hardware allocation is provisional until ARM/FPGA measurements.\n");

fclose(fid);

%% Final checks

disp("BENCHMARK_DATASETS: 5");
disp("RESEARCH_FIGURES: 4");
disp("END_TO_END_PIPELINE_MEASURED: NO");
disp("ENERGY_MEASURED: NO");
disp("TASK26_4L_CONSOLIDATED_CPU_ANALYSIS_PASS");
disp("SUMMARY: " + summaryPath);
disp("REPORT: " + reportPath);
disp("PLOTS: " + plotDir);
