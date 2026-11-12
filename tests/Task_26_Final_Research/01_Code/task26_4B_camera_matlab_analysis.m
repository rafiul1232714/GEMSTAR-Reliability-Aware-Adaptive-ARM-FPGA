%% Task 26.4B - GEMSTAR Camera CPU Research Analysis
% Real measurements from the Ryzen CPU.
% No hardware energy or YOLO inference included.
% Read-only access to timing and summary CSV files.

clear; clc; close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_26_Final_Research";

rawPath = fullfile(root, "02_CSV_Data", ...
    "task26_4B_camera_cpu_timing.csv");

summaryPath = fullfile(root, "02_CSV_Data", ...
    "task26_4B_camera_cpu_summary.csv");

plotDir = fullfile(root, "04_Plots");

if ~isfile(rawPath) || ~isfile(summaryPath)
    error("Task 26.4B input CSV files are missing.");
end

T = readtable(rawPath, "TextType", "string");
S = readtable(summaryPath, "TextType", "string");

if height(T) ~= 600 || height(S) ~= 6
    error("Unexpected number of benchmark measurements.");
end

weather = ["CLEAR","FOG100","FOG20"];
fullMs = zeros(3,1);
roiMs = zeros(3,1);
reduction = zeros(3,1);

for i = 1:3
    a = S(S.weather == weather(i) & S.mode == "FULL", :);
    b = S(S.weather == weather(i) & S.mode == "ROI", :);

    if height(a) ~= 1 || height(b) ~= 1
        error("Missing unique weather/ROI configuration.");
    end

    fullMs(i) = a.median_ms;
    roiMs(i) = b.median_ms;
    reduction(i) = 100*(1-roiMs(i)/fullMs(i));
end

%% Figure 1 - Full versus ROI latency
f1 = figure("Color","w","Position",[100 100 900 480]);
bar([fullMs roiMs]);
set(gca,"XTick",1:3,"XTickLabel", ...
    ["Clear","Fog MOR100","Fog MOR20"]);
ylabel("Median CPU processing time (ms)");
title("Task 26.4B - Camera full image vs ROI");
legend("Full image","384 x 288 ROI","Location","best");
grid on;
saveas(f1,fullfile(plotDir, ...
    "task26_4B_full_vs_roi.png"));

%% Figure 2 - Latency distributions
f2 = figure("Color","w","Position",[100 100 950 480]);

fullRuns = T.elapsed_ms(T.mode == "FULL");
roiRuns = T.elapsed_ms(T.mode == "ROI");

histogram(fullRuns,25,"FaceAlpha",0.65);
hold on;
histogram(roiRuns,25,"FaceAlpha",0.65);
hold off;

xlabel("Execution duration (ms)");
ylabel("Number of timed runs");
title("Task 26.4B - Camera CPU latency distribution");
legend("Full image","ROI","Location","best");
grid on;
saveas(f2,fullfile(plotDir, ...
    "task26_4B_latency_distribution.png"));

%% Figure 3 - Processing cost per pixel
f3 = figure("Color","w","Position",[100 100 900 480]);

cost = 1e6 * S.median_ms ./ S.processed_pixels;
labels = S.weather + " " + S.mode;

bar(cost);
set(gca,"XTick",1:height(S), ...
    "XTickLabel",cellstr(labels));
xtickangle(30);

ylabel("Median time per pixel (ns)");
title("Task 26.4B - Normalized Camera processing cost");
grid on;
saveas(f3,fullfile(plotDir, ...
    "task26_4B_time_per_pixel.png"));

%% Figure 4 - Image quality features
% Use the FULL region for comparable weather conditions.
f4 = figure("Color","w","Position",[100 100 900 480]);

C = S(S.mode == "FULL", :);
contrast = zeros(3,1);
edgeDensity = zeros(3,1);

for i = 1:3
    c = C(C.weather == weather(i), :);
    contrast(i) = c.contrast_std;
    edgeDensity(i) = c.edge_density;
end

% Two separate y-axes because metrics have different units.
yyaxis left;
plot(1:3,contrast,"-o","LineWidth",2);
ylabel("Grayscale contrast standard deviation");

yyaxis right;
plot(1:3,edgeDensity,"-s","LineWidth",2);
ylabel("Canny edge density");

set(gca,"XTick",1:3,"XTickLabel", ...
    ["Clear","Fog MOR100","Fog MOR20"]);
xlim([0.7 3.3]);
title("Task 26.4B - Sampled Camera quality features");
grid on;
saveas(f4,fullfile(plotDir, ...
    "task26_4B_weather_quality_features.png"));

%% Text summary
disp("=== TASK 26.4B MATLAB ANALYSIS ===");

for i = 1:3
    fprintf("%s: FULL=%.4f ms ROI=%.4f ms REDUCTION=%.2f%%\n", ...
        weather(i),fullMs(i),roiMs(i),reduction(i));
end

disp("NOTE: Only three sampled images were analyzed.");
disp("NOTE: Timing reduction is not measured energy saving.");
disp("NOTE: ROI detection accuracy has not been validated.");
disp("TASK26_4B_MATLAB_ANALYSIS_PASS");
