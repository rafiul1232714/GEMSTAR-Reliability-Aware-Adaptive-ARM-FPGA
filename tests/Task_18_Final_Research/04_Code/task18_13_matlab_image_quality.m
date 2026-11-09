
%% TASK 18.13A - MATLAB CAMERA IMAGE QUALITY ANALYSIS
clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

inputDir = fullfile(base,"08_Extracted_Images","Selected_Frames");
outputDir = fullfile(base,"08_Extracted_Images","MATLAB_Processed");
csvDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

frames = [0 50 100 150 200 250 300 350 400 423 424 450];
N = numel(frames);

Brightness = zeros(N,1);
Contrast = zeros(N,1);
ImageEntropy = zeros(N,1);
GaussianMAE = zeros(N,1);
EdgeDensity = zeros(N,1);

% Fixed illustrative threshold on the saved uint8 edge image.
edgeThreshold = 40;

for k = 1:N
    f = frames(k);

    grayImg = imread(fullfile(outputDir, ...
        sprintf("frame_%03d_gray.png",f)));

    blurImg = imread(fullfile(outputDir, ...
        sprintf("frame_%03d_gaussian.png",f)));

    edgeImg = imread(fullfile(outputDir, ...
        sprintf("frame_%03d_sobel.png",f)));

    G = double(grayImg);
    B = double(blurImg);
    E = double(edgeImg);

    % Average image intensity: 0 = black, 255 = white
    Brightness(k) = mean(G(:));

    % Global intensity variation (contrast proxy)
    Contrast(k) = std(G(:));

    % Shannon entropy of the grayscale image
    ImageEntropy(k) = entropy(grayImg);

    % Average pixel change introduced by Gaussian filtering
    GaussianMAE(k) = mean(abs(G(:)-B(:)));

    % Percentage of pixels whose Sobel magnitude exceeds 40
    EdgeDensity(k) = 100 * mean(E(:) > edgeThreshold);

    fprintf("Frame %3d | Brightness %.2f | Contrast %.2f | Edge %.2f%%\n", ...
        f, Brightness(k), Contrast(k), EdgeDensity(k));
end

%% Save research data
Frame = frames(:);

T = table(Frame, Brightness, Contrast, ImageEntropy, ...
    GaussianMAE, EdgeDensity);

csvPath = fullfile(csvDir, ...
    "task18_13_matlab_image_quality.csv");

writetable(T,csvPath);

%% Visualize scene quality
fig = figure("Color","w","Position",[100 100 1150 800]);
tiledlayout(2,2);

nexttile;
plot(frames,Brightness,"-o","LineWidth",1.6);
xlabel("GEMSTAR frame");
ylabel("Mean grayscale intensity");
title("Camera brightness");
grid on;

nexttile;
plot(frames,Contrast,"-o","LineWidth",1.6);
xlabel("GEMSTAR frame");
ylabel("Intensity standard deviation");
title("Global contrast proxy");
grid on;

nexttile;
plot(frames,ImageEntropy,"-o","LineWidth",1.6);
xlabel("GEMSTAR frame");
ylabel("Entropy (bits/pixel)");
title("Grayscale image entropy");
grid on;

nexttile;
plot(frames,EdgeDensity,"-o","LineWidth",1.6);
xlabel("GEMSTAR frame");
ylabel("Edge pixels (%)");
title("Sobel edge density (threshold = 40)");
grid on;

graphPath = fullfile(graphDir, ...
    "task18_13_matlab_image_quality.png");

exportgraphics(fig,graphPath,"Resolution",200);

fprintf("\n=== TASK 18.13A COMPLETE ===\n");
fprintf("Frames analyzed: %d\n",N);
fprintf("Mean brightness: %.3f\n",mean(Brightness));
fprintf("Mean contrast: %.3f\n",mean(Contrast));
fprintf("Mean edge density: %.3f%%\n",mean(EdgeDensity));
fprintf("CSV saved: %d\n",isfile(csvPath));
fprintf("Graph saved: %d\n",isfile(graphPath));
disp(T);
