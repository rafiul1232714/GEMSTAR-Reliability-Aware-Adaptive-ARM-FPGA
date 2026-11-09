
%% TASK 18.15B - INTEGER SOBEL FPGA REFERENCE
clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

inputDir = fullfile(base,"08_Extracted_Images","MATLAB_Processed");
csvDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");
outDir = fullfile(base,"08_Extracted_Images","MATLAB_FixedPoint");

if ~isfolder(outDir)
    mkdir(outDir);
end

frames = [0 50 100 150 200 250 300 350 400 423 424 450];
N = numel(frames);

% Sobel kernels
Kx = int32([-1 0 1; -2 0 2; -1 0 1]);
Ky = int32([-1 -2 -1; 0 0 0; 1 2 1]);

MAE = zeros(N,1);
RMSE = zeros(N,1);
MaxError = zeros(N,1);
ExactMatchPercent = zeros(N,1);
MaxAbsGx = zeros(N,1);
MaxAbsGy = zeros(N,1);

for k = 1:N
    f = frames(k);

    blurImg = imread(fullfile(inputDir, ...
        sprintf("frame_%03d_gaussian.png",f)));

    % Shared floating-point reference:
    % Same Sobel kernels and replicate boundary handling.
    F = double(blurImg);
    paddedF = padarray(F,[1 1],"replicate","both");

    refGx = conv2(paddedF, rot90(double(Kx),2),"valid");
    refGy = conv2(paddedF, rot90(double(Ky),2),"valid");

    % Integer arithmetic with signed 32-bit accumulators.
    I = int32(blurImg);
    paddedI = padarray(I,[1 1],"replicate","both");

    Gx = zeros(size(I),"int32");
    Gy = zeros(size(I),"int32");

    for row = 1:3
        for col = 1:3
            region = paddedI(row:row+size(I,1)-1, ...
                             col:col+size(I,2)-1);

            Gx = Gx + Kx(row,col)*region;
            Gy = Gy + Ky(row,col)*region;
        end
    end

    % Both paths use the same magnitude and saturation rule.
    refMag = uint8(min(round(hypot(refGx,refGy)),255));
    intMag = uint8(min(round(hypot(double(Gx),double(Gy))),255));

    D = double(refMag)-double(intMag);

    MAE(k) = mean(abs(D(:)));
    RMSE(k) = sqrt(mean(D(:).^2));
    MaxError(k) = max(abs(D(:)));
    ExactMatchPercent(k) = 100*mean(D(:)==0);
    MaxAbsGx(k) = max(abs(double(Gx(:))));
    MaxAbsGy(k) = max(abs(double(Gy(:))));

    imwrite(intMag,fullfile(outDir, ...
        sprintf("frame_%03d_integer_sobel.png",f)));

    fprintf("Frame %3d | MAE %.6f | Exact %.2f%% | Max Gx %.0f\n", ...
        f, MAE(k), ExactMatchPercent(k), MaxAbsGx(k));
end

%% Save CSV
Frame = frames(:);

T = table(Frame,MAE,RMSE,MaxError,ExactMatchPercent, ...
    MaxAbsGx,MaxAbsGy);

csvPath = fullfile(csvDir, ...
    "task18_15b_integer_sobel_accuracy.csv");

writetable(T,csvPath);

%% Save a representative comparison
f = 150;

blurImg = imread(fullfile(inputDir, ...
    "frame_150_gaussian.png"));

refEdge = imread(fullfile(inputDir, ...
    "frame_150_sobel.png"));

integerEdge = imread(fullfile(outDir, ...
    "frame_150_integer_sobel.png"));

fig = figure("Color","w","Position",[100 100 1100 450]);
tiledlayout(1,3);

nexttile;
imshow(blurImg);
title("Gaussian input");

nexttile;
imshow(refEdge);
title("Previous MATLAB Sobel");

nexttile;
imshow(integerEdge);
title("Integer Sobel");

graphPath = fullfile(graphDir, ...
    "task18_15b_integer_sobel_comparison.png");

exportgraphics(fig,graphPath,"Resolution",200);

fprintf("\n=== TASK 18.15B COMPLETE ===\n");
fprintf("Frames analyzed: %d\n",N);
fprintf("Overall mean MAE: %.6f\n",mean(MAE));
fprintf("Mean exact-match: %.3f%%\n",mean(ExactMatchPercent));
fprintf("Largest |Gx|: %.0f\n",max(MaxAbsGx));
fprintf("Largest |Gy|: %.0f\n",max(MaxAbsGy));
fprintf("CSV saved: %d\n",isfile(csvPath));
fprintf("Graph saved: %d\n",isfile(graphPath));

disp(T);
