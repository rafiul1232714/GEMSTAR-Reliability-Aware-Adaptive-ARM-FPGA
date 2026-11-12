%% Task 26.4K - YOLO CPU MATLAB Analysis
% Uses 50 actual measurements from Task 26.4J.
% Read-only access to existing benchmark results.
% No ARM/FPGA energy measurements included.

clear; clc; close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_26_Final_Research";

csvDir = fullfile(root, "02_CSV_Data");
plotDir = fullfile(root, "04_Plots");
reportDir = fullfile(root, "06_Research_Findings");

timingPath = fullfile(csvDir, ...
    "task26_4J_yolo_cpu_timing.csv");

summaryPath = fullfile(csvDir, ...
    "task26_4J_yolo_cpu_summary.csv");

cameraPath = fullfile(csvDir, ...
    "task26_4B_camera_cpu_summary.csv");

reportPath = fullfile(reportDir, ...
    "task26_4K_yolo_cpu_findings.txt");

outputNames = [
    "task26_4K_yolo_latency_by_frame.png"
    "task26_4K_yolo_detection_count.png"
    "task26_4K_yolo_latency_distribution.png"
    "task26_4K_yolo_vs_camera_preprocessing.png"
];

%% Verify input files

if ~isfile(timingPath) || ~isfile(summaryPath)
    error("Task 26.4J YOLO benchmark CSV files are missing.");
end

if ~isfile(cameraPath)
    error("Task 26.4B Camera comparison CSV is missing.");
end

if isfile(reportPath)
    error("Existing findings report preserved.");
end

for k = 1:numel(outputNames)
    if isfile(fullfile(plotDir,outputNames(k)))
        error("Existing plot preserved: %s",outputNames(k));
    end
end

if ~isfolder(plotDir)
    mkdir(plotDir);
end

%% Load measured results

T = readtable(timingPath);
S = readtable(summaryPath);
C = readtable(cameraPath, "TextType", "string");

if height(T) ~= 50 || height(S) ~= 5
    error("Expected 50 YOLO runs and five frame summaries.");
end

requiredTiming = [
    "frame","filename","repeat","detections","elapsed_ms"
];

requiredSummary = [
    "frame","median_ms","p95_ms","p99_ms","detections"
];

requiredCamera = ["mode","median_ms"];

if ~all(ismember(requiredTiming, ...
        string(T.Properties.VariableNames)))
    error("Unexpected YOLO timing CSV columns.");
end

if ~all(ismember(requiredSummary, ...
        string(S.Properties.VariableNames)))
    error("Unexpected YOLO summary CSV columns.");
end

if ~all(ismember(requiredCamera, ...
        string(C.Properties.VariableNames)))
    error("Unexpected Camera summary CSV columns.");
end

S = sortrows(S,"frame");

frames = S.frame;
medianMs = S.median_ms;
p95Ms = S.p95_ms;
p99Ms = S.p99_ms;
detections = S.detections;

%% Figure 1 - YOLO latency by frame

f1 = figure("Color","w","Position",[100 100 950 480]);

plot(frames,medianMs,"-o","LineWidth",1.8);
hold on;
plot(frames,p95Ms,"-s","LineWidth",1.8);
plot(frames,p99Ms,"-^","LineWidth",1.8);
hold off;

xlabel("GEMSTAR frame number");
ylabel("CPU prediction latency (ms)");
title("Task 26 - YOLO11s CPU latency across five frames");
legend("Median","p95","p99","Location","best");
grid on;

saveas(f1,fullfile(plotDir,outputNames(1)));

%% Figure 2 - Detection counts

f2 = figure("Color","w","Position",[100 100 900 480]);

bar(categorical(string(frames)),detections);

xlabel("GEMSTAR frame number");
ylabel("YOLO detection count");
title("Task 26 - YOLO detections in selected frames");
grid on;

saveas(f2,fullfile(plotDir,outputNames(2)));

%% Figure 3 - Timing distribution

f3 = figure("Color","w","Position",[100 100 950 480]);

frameLabels = categorical(string(T.frame));

% Toolbox-free distribution plot with individual timed runs.
frameIDs = unique(T.frame);

hold on;

for i = 1:numel(frameIDs)
    mask = T.frame == frameIDs(i);
    values = T.elapsed_ms(mask);

    x = repmat(i,numel(values),1);

    scatter(x,values,45,"filled", ...
        "MarkerFaceAlpha",0.65);

    plot(i,median(values),"kd", ...
        "MarkerSize",9, ...
        "MarkerFaceColor","k");
end

hold off;

set(gca,"XTick",1:numel(frameIDs), ...
    "XTickLabel",string(frameIDs));

xlabel("GEMSTAR frame number");
ylabel("CPU prediction latency (ms)");
title("Task 26 - YOLO latency distribution");
grid on;

saveas(f3,fullfile(plotDir,outputNames(3)));

%% Figure 4 - YOLO versus conventional preprocessing
% These are different workloads and software environments.
% This comparison is descriptive, not matched energy evidence.

fullCamera = C(C.mode == "FULL",:);
roiCamera = C(C.mode == "ROI",:);

if height(fullCamera) ~= 3 || height(roiCamera) ~= 3
    error("Expected three Camera weather cases per mode.");
end

cameraFullMedian = median(fullCamera.median_ms);
cameraRoiMedian = median(roiCamera.median_ms);
yoloMedian = median(medianMs);

comparison = [
    cameraRoiMedian
    cameraFullMedian
    yoloMedian
];

f4 = figure("Color","w","Position",[100 100 950 480]);

bar(comparison);

set(gca,"XTick",1:3, ...
    "XTickLabel",{ ...
    "Camera ROI", ...
    "Camera Full", ...
    "YOLO11s CPU"});

ylabel("Median processing time (ms)");
title("Task 26 - CPU processing workload comparison");
grid on;

saveas(f4,fullfile(plotDir,outputNames(4)));

%% Numerical results

disp("=== TASK 26.4K YOLO MATLAB ANALYSIS ===");

fprintf("YOLO_FRAMES: %d\n",height(S));
fprintf("YOLO_TIMING_RUNS: %d\n",height(T));

fprintf("MEDIAN_OF_YOLO_FRAME_MEDIANS_MS: %.4f\n", ...
    yoloMedian);

fprintf("MIN_FRAME_MEDIAN_MS: %.4f\n",min(medianMs));
fprintf("MAX_FRAME_MEDIAN_MS: %.4f\n",max(medianMs));
fprintf("MAX_FRAME_P99_MS: %.4f\n",max(p99Ms));

fprintf("TOTAL_DETECTIONS_ACROSS_FIVE_FRAMES: %d\n", ...
    sum(detections));

fprintf("CAMERA_FULL_MEDIAN_OF_MEDIANS_MS: %.4f\n", ...
    cameraFullMedian);

fprintf("CAMERA_ROI_MEDIAN_OF_MEDIANS_MS: %.4f\n", ...
    cameraRoiMedian);

fprintf("YOLO_TO_CAMERA_FULL_RATIO: %.2f\n", ...
    yoloMedian/cameraFullMedian);

fprintf("YOLO_TO_CAMERA_ROI_RATIO: %.2f\n", ...
    yoloMedian/cameraRoiMedian);

%% Save research findings

fid = fopen(reportPath,"w");

if fid == -1
    error("Cannot create research findings report.");
end

fprintf(fid,"TASK 26.4K - YOLO CPU MATLAB ANALYSIS\n");
fprintf(fid,"====================================\n\n");

fprintf(fid,"YOLO frames analyzed: %d\n",height(S));
fprintf(fid,"YOLO timed runs: %d\n",height(T));

fprintf(fid,"Median of YOLO frame medians: %.4f ms\n", ...
    yoloMedian);

fprintf(fid,"Maximum frame p99 estimate: %.4f ms\n", ...
    max(p99Ms));

fprintf(fid,"Total detections across five frames: %d\n\n", ...
    sum(detections));

fprintf(fid,"Median Camera full preprocessing: %.4f ms\n", ...
    cameraFullMedian);

fprintf(fid,"Median Camera ROI preprocessing: %.4f ms\n", ...
    cameraRoiMedian);

fprintf(fid,"YOLO / Camera full ratio: %.2f\n", ...
    yoloMedian/cameraFullMedian);

fprintf(fid,"YOLO / Camera ROI ratio: %.2f\n\n", ...
    yoloMedian/cameraRoiMedian);

fprintf(fid,"RESEARCH INTERPRETATION\n");
fprintf(fid,"- YOLO CPU prediction is computationally heavier than conventional Camera preprocessing.\n");
fprintf(fid,"- YOLO includes its internal preprocessing, model inference, and postprocessing.\n");
fprintf(fid,"- The Camera comparison uses different images, processing operations, and OpenCV environments.\n");
fprintf(fid,"- Only five selected frames and ten timed YOLO runs per frame were evaluated.\n");
fprintf(fid,"- These p99 values are exploratory estimates, not hard real-time guarantees.\n");
fprintf(fid,"- Detection count is not a validated accuracy metric.\n");
fprintf(fid,"- CPU measurements were collected on the development workstation, not the target ARM processor.\n");
fprintf(fid,"- No system energy or FPGA acceleration was measured.\n");

fclose(fid);

disp("TASK26_4K_YOLO_MATLAB_ANALYSIS_PASS");
disp("REPORT: " + reportPath);
disp("PLOTS: " + plotDir);
