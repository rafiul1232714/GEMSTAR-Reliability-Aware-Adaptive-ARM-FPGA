
clear; clc; close all;

%% Task 18.11 - MATLAB Camera Preprocessing
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

inputDir = fullfile(base, "08_Extracted_Images", "Selected_Frames");
outputDir = fullfile(base, "08_Extracted_Images", "MATLAB_Processed");
csvDir = fullfile(base, "02_CSV_Data");
graphDir = fullfile(base, "01_Graphs");

if ~isfolder(outputDir)
    mkdir(outputDir);
end

frames = [0 50 100 150 200 250 300 350 400 423 424 450];

N = numel(frames);
MeanGray = zeros(N,1);
MeanBlur = zeros(N,1);
MeanEdge = zeros(N,1);

for k = 1:N
    f = frames(k);

    filename = sprintf("task18_camera_frame_%03d.png", f);
    imagePath = fullfile(inputDir, filename);

    assert(isfile(imagePath), "Missing image: %s", imagePath);

    %% Load real GEMSTAR image
    rgb = imread(imagePath);

    %% Grayscale conversion
    grayImg = rgb2gray(rgb);

    %% Gaussian smoothing
    H = fspecial("gaussian", [5 5], 1);
    blurImg = imfilter(grayImg, H, "replicate");

    %% Sobel edge detection
    [Gmag, ~] = imgradient(blurImg, "sobel");
    edgeImg = uint8(min(round(Gmag), 255));

    %% Save image results
    imwrite(grayImg, fullfile(outputDir, ...
        sprintf("frame_%03d_gray.png",f)));

    imwrite(blurImg, fullfile(outputDir, ...
        sprintf("frame_%03d_gaussian.png",f)));

    imwrite(edgeImg, fullfile(outputDir, ...
        sprintf("frame_%03d_sobel.png",f)));

    %% Basic processing statistics
    MeanGray(k) = mean(double(grayImg(:)));
    MeanBlur(k) = mean(double(blurImg(:)));
    MeanEdge(k) = mean(double(edgeImg(:)));

    fprintf("Frame %d processed successfully\n", f);
end

%% Save CSV
Frame = frames(:);

T = table(Frame, MeanGray, MeanBlur, MeanEdge);

csvPath = fullfile(csvDir, ...
    "task18_matlab_full_preprocessing_metrics.csv");

writetable(T,csvPath);

%% Plot representative frame
f = 150;

rgb = imread(fullfile(inputDir, ...
    sprintf("task18_camera_frame_%03d.png",f)));

grayImg = imread(fullfile(outputDir, ...
    sprintf("frame_%03d_gray.png",f)));

blurImg = imread(fullfile(outputDir, ...
    sprintf("frame_%03d_gaussian.png",f)));

edgeImg = imread(fullfile(outputDir, ...
    sprintf("frame_%03d_sobel.png",f)));

fig = figure("Color","w","Position",[100 100 1100 700]);

tiledlayout(2,2);

nexttile;
imshow(rgb);
title("Original RGB");

nexttile;
imshow(grayImg);
title("MATLAB Grayscale");

nexttile;
imshow(blurImg);
title("MATLAB Gaussian");

nexttile;
imshow(edgeImg);
title("MATLAB Sobel Magnitude");

exportgraphics(fig,fullfile(graphDir, ...
    "task18_matlab_full_camera_pipeline.png"), ...
    "Resolution",200);

fprintf("\n=== TASK 18.11 COMPLETE ===\n");
fprintf("Processed frames: %d\n",N);
fprintf("Output images: %d\n",N*3);
fprintf("Research CSV saved: %d\n",isfile(csvPath));
fprintf("Research graph saved: %d\n", ...
    isfile(fullfile(graphDir, ...
    "task18_matlab_full_camera_pipeline.png")));
