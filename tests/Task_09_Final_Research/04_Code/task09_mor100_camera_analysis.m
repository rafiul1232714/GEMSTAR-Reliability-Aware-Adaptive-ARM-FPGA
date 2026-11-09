
%% TASK 9.2.4 - CAMERA QUALITY ANALYSIS
% GEMSTAR - Light Fog MOR 100 m
% Analyze 47 actual camera images

clc;
clear;
close all;

%% 1. Define project paths

root = "E:\GEMSTAR_Project\sensor-health-monitor";

imageFolder = fullfile(root, ...
    "results", "figures", "fog_mor100_camera");

archive = fullfile(root, ...
    "tests", "Task_09_Final_Research");

csvFolder = fullfile(archive, "02_CSV_Data");
graphFolder = fullfile(archive, "01_Graphs");
codeFolder = fullfile(archive, "04_Code");

if ~isfolder(csvFolder), mkdir(csvFolder); end
if ~isfolder(graphFolder), mkdir(graphFolder); end
if ~isfolder(codeFolder), mkdir(codeFolder); end

%% 2. Read extracted camera metadata

metadataFile = fullfile(csvFolder, ...
    "task09_mor100_camera_frames.csv");

assert(isfile(metadataFile), ...
    "Camera metadata CSV not found.");

T = readtable(metadataFile, "TextType", "string");

T = sortrows(T, "frame");

n = height(T);

assert(n > 0, "No camera images available.");

fprintf("\nTASK 9.2.4 - CAMERA QUALITY\n");
fprintf("Camera images: %d\n", n);

%% 3. Prepare output arrays

frame = T.frame;
time_s = T.timestamp_s;

brightness = zeros(n, 1);
contrast = zeros(n, 1);
edgeStrength = zeros(n, 1);
sharpness = zeros(n, 1);

%% 4. Analyze each image

for i = 1:n

    file = fullfile(imageFolder, T.filename(i));

    assert(isfile(file), ...
        "Missing camera image: %s", file);

    img = imread(file);

    % Convert RGB into normalized grayscale.
    % Values between 0 and 1.
    rgb = double(img) / 255.0;

    gray = ...
        0.2989 * rgb(:,:,1) + ...
        0.5870 * rgb(:,:,2) + ...
        0.1140 * rgb(:,:,3);

    % Metric 1: Mean brightness
    brightness(i) = mean(gray(:));

    % Metric 2: Image contrast
    contrast(i) = std(gray(:));

    % Metric 3: Mean image gradient magnitude
    % Central-difference gradient
    [gx, gy] = gradient(gray);

    magnitude = hypot(gx, gy);

    edgeStrength(i) = mean(magnitude(:));

    % Metric 4: Laplacian variance
    % Basic sharpness proxy
    kernel = [0 1 0; 1 -4 1; 0 1 0];

    lap = conv2(gray, kernel, "valid");

    sharpness(i) = var(lap(:));

    fprintf("Processed camera frame: %d\n", frame(i));

end

%% 5. Create camera quality CSV

results = table( ...
    frame, ...
    time_s, ...
    brightness, ...
    contrast, ...
    edgeStrength, ...
    sharpness);

csvFile = fullfile(csvFolder, ...
    "task09_mor100_camera_quality.csv");

writetable(results, csvFile);

%% 6. Plot brightness

fig1 = figure("Color", "w");

plot(time_s, brightness, ...
    "LineWidth", 1.5);

xlabel("Simulation Time (s)");
ylabel("Mean Brightness (0-1)");
title("Camera Brightness - Fog MOR 100 m");

ylim([0 1]);
grid on;

exportgraphics(fig1, fullfile(graphFolder, ...
    "task09_mor100_camera_brightness.png"), ...
    "Resolution", 300);

savefig(fig1, fullfile(graphFolder, ...
    "task09_mor100_camera_brightness.fig"));

%% 7. Plot contrast

fig2 = figure("Color", "w");

plot(time_s, contrast, ...
    "LineWidth", 1.5);

xlabel("Simulation Time (s)");
ylabel("Grayscale Standard Deviation");
title("Camera Contrast - Fog MOR 100 m");

grid on;

exportgraphics(fig2, fullfile(graphFolder, ...
    "task09_mor100_camera_contrast.png"), ...
    "Resolution", 300);

savefig(fig2, fullfile(graphFolder, ...
    "task09_mor100_camera_contrast.fig"));

%% 8. Plot edge strength

fig3 = figure("Color", "w");

plot(time_s, edgeStrength, ...
    "LineWidth", 1.5);

xlabel("Simulation Time (s)");
ylabel("Mean Gradient Magnitude");
title("Camera Edge Strength - Fog MOR 100 m");

grid on;

exportgraphics(fig3, fullfile(graphFolder, ...
    "task09_mor100_camera_edges.png"), ...
    "Resolution", 300);

savefig(fig3, fullfile(graphFolder, ...
    "task09_mor100_camera_edges.fig"));

%% 9. Plot sharpness

fig4 = figure("Color", "w");

plot(time_s, sharpness, ...
    "LineWidth", 1.5);

xlabel("Simulation Time (s)");
ylabel("Laplacian Variance");
title("Camera Sharpness - Fog MOR 100 m");

grid on;

exportgraphics(fig4, fullfile(graphFolder, ...
    "task09_mor100_camera_sharpness.png"), ...
    "Resolution", 300);

savefig(fig4, fullfile(graphFolder, ...
    "task09_mor100_camera_sharpness.fig"));

%% 10. Save summary statistics

metric = [
    "Camera Images Analyzed"
    "Mean Brightness"
    "Mean Contrast"
    "Mean Edge Strength"
    "Mean Sharpness"
];

value = [
    n
    mean(brightness)
    mean(contrast)
    mean(edgeStrength)
    mean(sharpness)
];

summary = table(metric, value);

summaryFile = fullfile(csvFolder, ...
    "task09_mor100_camera_matlab_summary.csv");

writetable(summary, summaryFile);

disp(" ");
disp("===== CAMERA ANALYSIS RESULTS =====");
disp(summary);

%% 11. Archive source code

source = fullfile(root, "matlab", ...
    "task09_mor100_camera_analysis.m");

if isfile(source)
    copyfile(source, codeFolder);
end

fprintf("\nTASK 9.2.4 COMPLETED\n");
fprintf("Results saved in Task_09_Final_Research\n");
