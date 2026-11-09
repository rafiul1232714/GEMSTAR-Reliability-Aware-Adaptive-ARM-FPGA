
%% TASK 18.15A - INTEGER GRAYSCALE FOR FPGA RESEARCH
clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

inputDir = fullfile(base,"08_Extracted_Images","Selected_Frames");
csvDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");
outDir = fullfile(base,"08_Extracted_Images","MATLAB_FixedPoint");

if ~isfolder(outDir)
    mkdir(outDir);
end

frames = [0 50 100 150 200 250 300 350 400 423 424 450];
N = numel(frames);

MAE = zeros(N,1);
RMSE = zeros(N,1);
MaxError = zeros(N,1);
ExactMatchPercent = zeros(N,1);

for k = 1:N

    f = frames(k);

    rgb = imread(fullfile(inputDir, ...
        sprintf("task18_camera_frame_%03d.png",f)));

    % MATLAB reference grayscale
    reference = rgb2gray(rgb);

    % Integer-only weighted RGB calculation.
    % uint32 avoids overflow in weighted accumulation.
    R = uint32(rgb(:,:,1));
    G = uint32(rgb(:,:,2));
    B = uint32(rgb(:,:,3));

    % Add 128 for nearest-integer rounding before shift.
    accumulator = 77*R + 150*G + 29*B + 128;

    % Divide by 256 using integer right shift.
    integerGray = uint8(bitshift(accumulator,-8));

    D = double(reference) - double(integerGray);

    MAE(k) = mean(abs(D(:)));
    RMSE(k) = sqrt(mean(D(:).^2));
    MaxError(k) = max(abs(D(:)));
    ExactMatchPercent(k) = 100*mean(D(:)==0);

    imwrite(integerGray,fullfile(outDir, ...
        sprintf("frame_%03d_integer_gray.png",f)));

    fprintf("Frame %3d | MAE %.5f | Exact %.2f%%\n", ...
        f, MAE(k), ExactMatchPercent(k));
end

%% Save CSV
Frame = frames(:);

T = table(Frame,MAE,RMSE,MaxError,ExactMatchPercent);

csvPath = fullfile(csvDir, ...
    "task18_15_integer_grayscale_accuracy.csv");

writetable(T,csvPath);

%% Visual comparison for frame 150
rgb = imread(fullfile(inputDir, ...
    "task18_camera_frame_150.png"));

reference = rgb2gray(rgb);

integerGray = imread(fullfile(outDir, ...
    "frame_150_integer_gray.png"));

difference = abs(double(reference)-double(integerGray));

fig = figure("Color","w","Position",[100 100 1200 450]);
tiledlayout(1,3);

nexttile;
imshow(reference);
title("MATLAB grayscale reference");

nexttile;
imshow(integerGray);
title("Integer arithmetic grayscale");

nexttile;
imshow(difference,[0 max(1,max(difference(:)))]);
colorbar;
title("Absolute pixel difference");

graphPath = fullfile(graphDir, ...
    "task18_15_integer_grayscale_comparison.png");

exportgraphics(fig,graphPath,"Resolution",200);

fprintf("\n=== TASK 18.15A COMPLETE ===\n");
fprintf("Frames analyzed: %d\n",N);
fprintf("Overall mean MAE: %.6f\n",mean(MAE));
fprintf("Overall mean exact match: %.3f%%\n", ...
    mean(ExactMatchPercent));
fprintf("CSV saved: %d\n",isfile(csvPath));
fprintf("Graph saved: %d\n",isfile(graphPath));

disp(T);
