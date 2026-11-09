
%% TASK 18.12A - MATLAB vs Python/OpenCV
% Compare grayscale, Gaussian and Sobel on GEMSTAR frame 0

clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

pythonDir = fullfile(base, "08_Extracted_Images");
matlabDir = fullfile(pythonDir, "MATLAB_Processed");
csvDir = fullfile(base, "02_CSV_Data");
graphDir = fullfile(base, "01_Graphs");

operations = ["Grayscale"; "Gaussian"; "Sobel"];

pythonFiles = [
    "task18_frame000_grayscale.png"
    "task18_frame000_gaussian.png"
    "task18_frame000_sobel.png"
];

matlabFiles = [
    "frame_000_gray.png"
    "frame_000_gaussian.png"
    "frame_000_sobel.png"
];

MAE = zeros(3,1);
RMSE = zeros(3,1);
MaxError = zeros(3,1);
ExactMatchPercent = zeros(3,1);

fig = figure("Color", "w", ...
    "Position", [100 100 1200 900]);

tiledlayout(3,3, "TileSpacing", "compact");

for k = 1:3

    pythonPath = fullfile(pythonDir, pythonFiles(k));
    matlabPath = fullfile(matlabDir, matlabFiles(k));

    assert(isfile(pythonPath), ...
        "Missing Python result: %s", pythonPath);

    assert(isfile(matlabPath), ...
        "Missing MATLAB result: %s", matlabPath);

    P = imread(pythonPath);
    M = imread(matlabPath);

    assert(isequal(size(P), size(M)), ...
        "Different image dimensions for %s", operations(k));

    D = double(M) - double(P);

    MAE(k) = mean(abs(D(:)));
    RMSE(k) = sqrt(mean(D(:).^2));
    MaxError(k) = max(abs(D(:)));

    ExactMatchPercent(k) = ...
        100 * nnz(D == 0) / numel(D);

    fprintf("\n%s\n", operations(k));
    fprintf("MAE: %.6f\n", MAE(k));
    fprintf("RMSE: %.6f\n", RMSE(k));
    fprintf("Maximum error: %.0f\n", MaxError(k));
    fprintf("Exact pixels: %.2f%%\n", ...
        ExactMatchPercent(k));

    nexttile;
    imshow(P);
    title(operations(k) + " - Python");

    nexttile;
    imshow(M);
    title(operations(k) + " - MATLAB");

    nexttile;
    imshow(abs(D), [0 255]);
    colorbar;
    title(operations(k) + " - Absolute difference");
end

%% Save graph
graphPath = fullfile(graphDir, ...
    "task18_12_matlab_python_comparison.png");

exportgraphics(fig, graphPath, "Resolution", 200);

%% Save numerical results
Operation = operations;

T = table(Operation, MAE, RMSE, ...
    MaxError, ExactMatchPercent);

csvPath = fullfile(csvDir, ...
    "task18_12_matlab_python_comparison.csv");

writetable(T, csvPath);

fprintf("\n=== TASK 18.12A COMPLETE ===\n");

disp(T);

fprintf("Comparison graph saved: %d\n", isfile(graphPath));
fprintf("Comparison CSV saved: %d\n", isfile(csvPath));
