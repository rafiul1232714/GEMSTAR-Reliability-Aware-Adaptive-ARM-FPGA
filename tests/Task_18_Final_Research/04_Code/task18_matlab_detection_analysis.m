%% TASK 18.8A - MATLAB DETECTION ACCURACY AND LATENCY ANALYSIS
% Uses standard MATLAB functions; no extra toolbox required.

clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

csvDir = fullfile(base, "02_CSV_Data");
graphDir = fullfile(base, "01_Graphs");

accuracy = readtable(fullfile(csvDir, ...
    "task18_controlled_accuracy_results.csv"));

timings = readtable(fullfile(csvDir, ...
    "task18_controlled_inference_summary.csv"));

%% 1. Independently calculate metrics
tp = accuracy.TP;
fp = accuracy.FP;
fn = accuracy.FN;

precision = tp ./ (tp + fp);
recall = tp ./ (tp + fn);
f1 = 2 .* precision .* recall ./ (precision + recall);

fprintf("\n=== TASK 18.8A MATLAB ACCURACY ===\n");

for i = 1:height(accuracy)
    fprintf("%s\n", string(accuracy.Model(i)));
    fprintf("  Precision: %.2f %%\n", precision(i)*100);
    fprintf("  Recall: %.2f %%\n", recall(i)*100);
    fprintf("  F1: %.2f %%\n", f1(i)*100);
end

%% 2. Confirm MATLAB and Python agreement
assert(max(abs(precision - accuracy.Precision)) < 1e-9);
assert(max(abs(recall - accuracy.Recall)) < 1e-9);
assert(max(abs(f1 - accuracy.F1)) < 1e-9);

fprintf("Python-MATLAB metric agreement: PASS\n");

%% 3. Calculate median inference latency
modelNames = ["yolo11n"; "yolo11s"];
medianLatency = zeros(2,1);
meanLatency = zeros(2,1);

for i = 1:2
    idx = strcmp(string(timings.Model), modelNames(i));
    values = timings.InferenceMs(idx);

    assert(~isempty(values), "Missing timing measurements");

    medianLatency(i) = median(values);
    meanLatency(i) = mean(values);
end

%% 4. Accuracy comparison graph
fig1 = figure("Color","w", "Position",[100 100 950 550]);

metricMatrix = [precision recall f1] * 100;

bar(metricMatrix');
set(gca, "XTickLabel", ...
    {"Precision","Recall","F1 Score"});

ylabel("Percentage (%)");
ylim([0 100]);
legend(cellstr(string(accuracy.Model)), ...
    "Location","northwest");

title("GEMSTAR Camera - Controlled YOLO Accuracy");
grid on;

exportgraphics(fig1, fullfile(graphDir, ...
    "task18_matlab_detection_accuracy.png"), ...
    "Resolution",200);

%% 5. Latency comparison graph
fig2 = figure("Color","w", "Position",[100 100 800 500]);

bar(medianLatency);
set(gca, "XTickLabel", cellstr(modelNames));

ylabel("Median CPU inference time (ms)");
title("GEMSTAR Camera - YOLO CPU Inference Latency");
grid on;

exportgraphics(fig2, fullfile(graphDir, ...
    "task18_matlab_detection_latency.png"), ...
    "Resolution",200);

%% 6. Export comparison
Model = modelNames;
Precision = precision;
Recall = recall;
F1 = f1;
MedianInferenceMs = medianLatency;
MeanInferenceMs = meanLatency;

results = table(Model, Precision, Recall, F1, ...
    MedianInferenceMs, MeanInferenceMs);

writetable(results, fullfile(csvDir, ...
    "task18_matlab_detection_summary.csv"));

fprintf("\n=== TASK 18.8A COMPLETE ===\n");
fprintf("Accuracy graph saved.\n");
fprintf("Latency graph saved.\n");
fprintf("MATLAB summary CSV saved.\n");

disp(results);
