
%% TASK 18.16 - INTEGER SOBEL MAGNITUDE APPROXIMATION
clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

inputDir = fullfile(base,"08_Extracted_Images","MATLAB_Processed");
outDir = fullfile(base,"08_Extracted_Images","MATLAB_FixedPoint");
csvDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

if ~isfolder(outDir)
    mkdir(outDir);
end

frames = [0 50 100 150 200 250 300 350 400 423 424 450];
N = numel(frames);

MAE = zeros(N,1);
RMSE = zeros(N,1);
MaxError = zeros(N,1);
ExactMatchPercent = zeros(N,1);
ApproxSaturationPercent = zeros(N,1);

Kx = int32([-1 0 1; -2 0 2; -1 0 1]);
Ky = int32([-1 -2 -1; 0 0 0; 1 2 1]);

for k = 1:N

    f = frames(k);
    I = int32(imread(fullfile(inputDir, ...
        sprintf("frame_%03d_gaussian.png",f))));

    P = padarray(I,[1 1],"replicate","both");

    Gx = zeros(size(I),"int32");
    Gy = zeros(size(I),"int32");

    for row = 1:3
        for col = 1:3
            region = P(row:row+size(I,1)-1, ...
                       col:col+size(I,2)-1);

            Gx = Gx + Kx(row,col)*region;
            Gy = Gy + Ky(row,col)*region;
        end
    end

    % Floating-point magnitude reference
    reference = uint8(min(255, ...
        round(hypot(double(Gx),double(Gy)))));

    % Integer-only L1 magnitude approximation
    approxWide = abs(Gx) + abs(Gy);
    approximation = uint8(min(int32(255),approxWide));

    D = double(reference)-double(approximation);

    MAE(k) = mean(abs(D(:)));
    RMSE(k) = sqrt(mean(D(:).^2));
    MaxError(k) = max(abs(D(:)));
    ExactMatchPercent(k) = 100*mean(D(:)==0);

    ApproxSaturationPercent(k) = ...
        100*mean(approxWide(:)>255);

    imwrite(approximation,fullfile(outDir, ...
        sprintf("frame_%03d_sobel_L1.png",f)));

    fprintf("Frame %3d | MAE %.4f | Exact %.2f%%\n", ...
        f,MAE(k),ExactMatchPercent(k));
end

%% Save research metrics
Frame = frames(:);

T = table(Frame,MAE,RMSE,MaxError, ...
    ExactMatchPercent,ApproxSaturationPercent);

csvPath = fullfile(csvDir, ...
    "task18_16_integer_sobel_approximation.csv");

writetable(T,csvPath);

%% Visual comparison
f = 150;

I = int32(imread(fullfile(inputDir, ...
    "frame_150_gaussian.png")));

P = padarray(I,[1 1],"replicate","both");
Gx = zeros(size(I),"int32");
Gy = zeros(size(I),"int32");

for row = 1:3
    for col = 1:3
        region = P(row:row+size(I,1)-1, ...
                   col:col+size(I,2)-1);
        Gx = Gx + Kx(row,col)*region;
        Gy = Gy + Ky(row,col)*region;
    end
end

reference = uint8(min(255, ...
    round(hypot(double(Gx),double(Gy)))));

approximation = imread(fullfile(outDir, ...
    "frame_150_sobel_L1.png"));

fig = figure("Color","w","Position",[100 100 1100 450]);
tiledlayout(1,3);

nexttile;
imshow(reference);
title("Sobel L2 magnitude reference");

nexttile;
imshow(approximation);
title("Integer L1 magnitude");

nexttile;
imshow(abs(double(reference)-double(approximation)),[0 255]);
colorbar;
title("Absolute difference");

graphPath = fullfile(graphDir, ...
    "task18_16_integer_sobel_approximation.png");

exportgraphics(fig,graphPath,"Resolution",200);

fprintf("\n=== TASK 18.16 COMPLETE ===\n");
fprintf("Mean MAE: %.5f\n",mean(MAE));
fprintf("Mean exact match: %.3f%%\n",mean(ExactMatchPercent));
fprintf("Mean approximation saturation: %.3f%%\n", ...
    mean(ApproxSaturationPercent));
fprintf("CSV saved: %d\n",isfile(csvPath));
fprintf("Graph saved: %d\n",isfile(graphPath));

disp(T);
