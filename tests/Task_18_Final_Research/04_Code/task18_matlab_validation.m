%% TASK 18.4B - TOOLBOX-FREE MATLAB CAMERA VALIDATION
clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research";

imageDir = fullfile(base, "08_Extracted_Images");
graphDir = fullfile(base, "01_Graphs");
csvDir = fullfile(base, "02_CSV_Data");

%% 1. Read actual GEMSTAR image
rgb = imread(fullfile(imageDir, ...
    "task18_frame000_rgb_interpretation.png"));

%% 2. Grayscale conversion
% Standard RGB-to-grayscale luminance approximation
grayFloat = 0.299 * double(rgb(:,:,1)) + ...
            0.587 * double(rgb(:,:,2)) + ...
            0.114 * double(rgb(:,:,3));

gray = uint8(round(grayFloat));

%% 3. Gaussian smoothing - kernel size 5x5, sigma 1
[x, y] = meshgrid(-2:2, -2:2);

kernel = exp(-(x.^2 + y.^2) / (2 * 1.0^2));
kernel = kernel / sum(kernel(:));

% Replicate edge pixels to match OpenCV's reference
% more closely after we check border differences.
padded = zeros(size(gray,1)+4, size(gray,2)+4);
padded(3:end-2,3:end-2) = double(gray);

padded(1:2,3:end-2) = repmat(double(gray(1,:)),2,1);
padded(end-1:end,3:end-2) = repmat(double(gray(end,:)),2,1);
padded(:,1:2) = repmat(padded(:,3),1,2);
padded(:,end-1:end) = repmat(padded(:,end-2),1,2);

blurFloat = conv2(padded, kernel, "valid");
blur = uint8(round(blurFloat));

%% 4. Sobel edge detection
kx = [-1 0 1; -2 0 2; -1 0 1];
ky = [-1 -2 -1; 0 0 0; 1 2 1];

% Use symmetric padding for a closer OpenCV comparison.
b = double(blur);
bpad = [b(:,2) b b(:,end-1)];
bpad = [bpad(2,:); bpad; bpad(end-1,:)];

gx = conv2(bpad, rot90(kx,2), "valid");
gy = conv2(bpad, rot90(ky,2), "valid");

magnitude = hypot(gx, gy);
edges = uint8(min(round(magnitude), 255));

%% 5. Load Python outputs
pyGray = imread(fullfile(imageDir, ...
    "task18_frame000_grayscale.png"));

pyBlur = imread(fullfile(imageDir, ...
    "task18_frame000_gaussian.png"));

pyEdges = imread(fullfile(imageDir, ...
    "task18_frame000_sobel.png"));

%% 6. Compare MATLAB and Python
maeGray = mean(abs(double(gray(:)) - double(pyGray(:))));
maeBlur = mean(abs(double(blur(:)) - double(pyBlur(:))));
maeEdges = mean(abs(double(edges(:)) - double(pyEdges(:))));

fprintf("\n=== TASK 18.4B MATLAB VALIDATION ===\n");
fprintf("Resolution: %d x %d\n", size(rgb,2), size(rgb,1));
fprintf("Grayscale MAE: %.6f\n", maeGray);
fprintf("Gaussian MAE: %.6f\n", maeBlur);
fprintf("Sobel MAE: %.6f\n", maeEdges);

%% 7. Save output images
imwrite(gray, fullfile(imageDir,"task18_matlab_grayscale.png"));
imwrite(blur, fullfile(imageDir,"task18_matlab_gaussian.png"));
imwrite(edges, fullfile(imageDir,"task18_matlab_sobel.png"));

%% 8. Save numerical comparison
Operation = ["Grayscale";"Gaussian";"Sobel"];
MAE = [maeGray;maeBlur;maeEdges];

results = table(Operation, MAE);

writetable(results,fullfile(csvDir, ...
    "task18_matlab_python_comparison.csv"));

disp(results);

%% 9. Save comparison figure without tiledlayout/ toolboxes
fig = figure("Color","w", "Position",[100 100 1100 750]);

subplot(2,2,1);
image(rgb);
axis image off;
title("Original GEMSTAR RGB");

subplot(2,2,2);
imagesc(gray);
colormap(gca,repmat((0:255)'/255,1,3));
axis image off;
title("MATLAB Grayscale");

subplot(2,2,3);
imagesc(blur);
colormap(gca,repmat((0:255)'/255,1,3));
axis image off;
title("MATLAB Gaussian");

subplot(2,2,4);
imagesc(edges);
colormap(gca,repmat((0:255)'/255,1,3));
axis image off;
title("MATLAB Sobel");

exportgraphics(fig,fullfile(graphDir, ...
    "task18_matlab_preprocessing_comparison.png"), ...
    "Resolution",200);

fprintf("\n=== MATLAB VALIDATION COMPLETE ===\n");
fprintf("Comparison CSV saved.\n");
fprintf("MATLAB images saved.\n");
fprintf("Comparison graph saved.\n");

