%% TASK 18.9B - MATLAB REPEATED CPU BENCHMARK VALIDATION
% Standard MATLAB functions only; no extra toolbox required.

clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

csvDir = fullfile(base, "02_CSV_Data");
graphDir = fullfile(base, "01_Graphs");

raw = readtable(fullfile(csvDir, ...
    "task18_repeated_cpu_benchmark.csv"));

pythonSummary = readtable(fullfile(csvDir, ...
    "task18_repeated_cpu_summary.csv"));

models = ["yolo11n"; "yolo11s"];

n = zeros(2,1);
medianMs = zeros(2,1);
meanMs = zeros(2,1);
p95Ms = zeros(2,1);
stdMs = zeros(2,1);

for i = 1:2
    idx = strcmp(string(raw.Model), models(i));
    values = raw.InferenceMs(idx);
    values = sort(values);

    n(i) = numel(values);
    assert(n(i) == 60, "Expected 60 measurements per model");

    medianMs(i) = median(values);
    meanMs(i) = mean(values);
    stdMs(i) = std(values);

    % Linear interpolation, 95th percentile
    position = 1 + (n(i)-1) * 0.95;
    lower = floor(position);
    upper = ceil(position);
    fraction = position - lower;

    p95Ms(i) = values(lower) * (1-fraction) + ...
               values(upper) * fraction;
end

%% Verify independently against Python's saved statistics
for i = 1:2
    idx = strcmp(string(pythonSummary.Model), models(i));
    assert(sum(idx) == 1, "Missing Python model summary");

    assert(abs(medianMs(i)-pythonSummary.MedianMs(idx)) < 1e-6);
    assert(abs(meanMs(i)-pythonSummary.MeanMs(idx)) < 1e-6);
    assert(abs(p95Ms(i)-pythonSummary.P95Ms(idx)) < 1e-6);
    assert(abs(stdMs(i)-pythonSummary.StdDevMs(idx)) < 1e-6);
end

fprintf("\n=== TASK 18.9B MATLAB CPU BENCHMARK ===\n");
fprintf("Python-MATLAB agreement: PASS\n");

for i = 1:2
    fprintf("\n%s\n", models(i));
    fprintf("Measurements: %d\n", n(i));
    fprintf("Median: %.3f ms\n", medianMs(i));
    fprintf("Mean: %.3f ms\n", meanMs(i));
    fprintf("P95: %.3f ms\n", p95Ms(i));
    fprintf("Std Dev: %.3f ms\n", stdMs(i));
end

%% Generate comparison chart
fig = figure("Color","w","Position",[100 100 1000 600]);

valuesChart = [medianMs meanMs p95Ms]';

bar(valuesChart);
set(gca, "XTick", 1:3, ...
    "XTickLabel", {"Median","Mean","P95"});

ylabel("PC CPU inference latency (ms)");
title("Task 18 - Repeated GEMSTAR YOLO CPU Benchmark");
legend(cellstr(models), "Location", "northwest");
grid on;

graphPath = fullfile(graphDir, ...
    "task18_matlab_cpu_benchmark.png");

exportgraphics(fig, graphPath, "Resolution", 200);

%% Save summary CSV
Model = models;
Measurements = n;
MedianMs = medianMs;
MeanMs = meanMs;
P95Ms = p95Ms;
StdDevMs = stdMs;

results = table(Model, Measurements, MedianMs, ...
    MeanMs, P95Ms, StdDevMs);

csvPath = fullfile(csvDir, ...
    "task18_matlab_cpu_benchmark_summary.csv");

writetable(results, csvPath);

fprintf("\n=== TASK 18.9B COMPLETE ===\n");
fprintf("MATLAB benchmark graph saved.\n");
fprintf("MATLAB benchmark CSV saved.\n");

disp(results);
