
%% TASK 18.14A - MATLAB PREPROCESSING CPU BENCHMARK

clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

inputDir = fullfile(base,"08_Extracted_Images","Selected_Frames");
csvDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

frames = [0 50 100 150 200 250 300 350 400 423 424 450];

repetitions = 10;
warmups = 3;
N = numel(frames);

kernel = fspecial("gaussian",[5 5],1);

Frame = zeros(N*repetitions*3,1);
Operation = strings(N*repetitions*3,1);
LatencyMs = zeros(N*repetitions*3,1);

index = 0;

for k = 1:N

    f = frames(k);

    rgb = imread(fullfile(inputDir, ...
        sprintf("task18_camera_frame_%03d.png",f)));

    grayImg = rgb2gray(rgb);
    blurImg = imfilter(grayImg,kernel,"replicate");

    % Warm-up each operation
    for w = 1:warmups
        tmp1 = rgb2gray(rgb);
        tmp2 = imfilter(grayImg,kernel,"replicate");
        [tmp3,~] = imgradient(blurImg,"sobel");
    end

    for r = 1:repetitions

        % Grayscale
        tic;
        a = rgb2gray(rgb);
        tGray = toc * 1000;

        % Gaussian
        tic;
        b = imfilter(grayImg,kernel,"replicate");
        tGaussian = toc * 1000;

        % Sobel
        tic;
        [c,~] = imgradient(blurImg,"sobel");
        tSobel = toc * 1000;

        names = ["Grayscale","Gaussian","Sobel"];
        times = [tGray,tGaussian,tSobel];

        for j = 1:3
            index = index + 1;
            Frame(index) = f;
            Operation(index) = names(j);
            LatencyMs(index) = times(j);
        end
    end

    fprintf("Frame %d benchmarked\n",f);
end

%% Save all measurements
T = table(Frame,Operation,LatencyMs);

rawPath = fullfile(csvDir, ...
    "task18_14_matlab_preprocessing_latency_raw.csv");

writetable(T,rawPath);

%% Summary statistics
names = ["Grayscale";"Gaussian";"Sobel"];

Measurements = zeros(3,1);
MedianMs = zeros(3,1);
MeanMs = zeros(3,1);
P95Ms = zeros(3,1);
StdDevMs = zeros(3,1);

for i = 1:3

    values = sort(LatencyMs(Operation == names(i)));

    Measurements(i) = numel(values);
    MedianMs(i) = median(values);
    MeanMs(i) = mean(values);
    StdDevMs(i) = std(values);

    % Interpolated 95th percentile
    n = numel(values);
    position = 1 + (n-1)*0.95;
    lo = floor(position);
    hi = ceil(position);
    alpha = position-lo;

    P95Ms(i) = values(lo)*(1-alpha) + values(hi)*alpha;
end

Operation = names;

S = table(Operation,Measurements,MedianMs, ...
    MeanMs,P95Ms,StdDevMs);

summaryPath = fullfile(csvDir, ...
    "task18_14_matlab_preprocessing_latency_summary.csv");

writetable(S,summaryPath);

%% Plot summary
fig = figure("Color","w","Position",[100 100 1000 600]);

bar([MedianMs MeanMs P95Ms]);

set(gca,"XTick",1:3,"XTickLabel",cellstr(names));

ylabel("MATLAB CPU execution time (ms)");
title("Task 18 - Camera Preprocessing CPU Benchmark");
legend("Median","Mean","P95","Location","best");
grid on;

graphPath = fullfile(graphDir, ...
    "task18_14_matlab_preprocessing_latency.png");

exportgraphics(fig,graphPath,"Resolution",200);

fprintf("\n=== TASK 18.14A COMPLETE ===\n");
disp(S);

fprintf("Measurements: %d\n",height(T));
fprintf("Raw CSV saved: %d\n",isfile(rawPath));
fprintf("Summary CSV saved: %d\n",isfile(summaryPath));
fprintf("Graph saved: %d\n",isfile(graphPath));
