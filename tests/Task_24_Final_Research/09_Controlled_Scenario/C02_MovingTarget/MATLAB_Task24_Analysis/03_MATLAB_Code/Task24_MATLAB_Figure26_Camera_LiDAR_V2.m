%% TASK 24.10.5.3D.2 — FIGURE 26
% Camera-LiDAR geometric compatibility and depth.
% Nominal mounting/intrinsic geometry; NOT calibrated.
% No Ground Truth used for association.
% Original CSVs/images are read-only.

clear; clc; close all;

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';
dataDir = fullfile(base,'C02_V2_EKF_Input_53Frames_V1');
analysisDir = fullfile(base,'MATLAB_Task24_Analysis');

figDir = fullfile(analysisDir,'01_Graphs');
csvDir = fullfile(analysisDir,'02_CSV_Data');

if ~isfolder(figDir), mkdir(figDir); end
if ~isfolder(csvDir), mkdir(csvDir); end

imagePath = fullfile(base, ...
    'Camera_NoVisualizer_V2_2122', ...
    'clean_camera_02_frame00530.png');

lidarPath = fullfile(dataDir,'lidar_points.csv');

detectionPath = fullfile(base, ...
    'C02_V2_Frame0530_Deduplicated_Detections.csv');

figurePath = fullfile(figDir,'Task24_Figure_26_V2.png');
csvPath = fullfile(csvDir, ...
    'Task24_Figure26_Camera_LiDAR_Depth_V2.csv');

assert(isfile(imagePath),'Missing Camera image');
assert(isfile(lidarPath),'Missing LiDAR CSV');
assert(isfile(detectionPath),'Missing Camera detections');

assert(~isfile(figurePath),'Figure already exists');
assert(~isfile(csvPath),'Output CSV already exists');

%% LOAD CAMERA AND LIDAR

I = imread(imagePath);
[h,w,~] = size(I);

L = readtable(lidarPath);
D = readtable(detectionPath, ...
    'VariableNamingRule','preserve');

frame = 530;
lf = L(L.frame == frame,:);

assert(~isempty(lf),'No LiDAR data at frame 530');
assert(~isempty(D),'No Camera detections');

%% SELECT THE MERGED TRUCK|BOAT HYPOTHESIS

classes = string(D.OriginalClasses);

idx = find(contains(classes,'truck'),1,'first');

assert(~isempty(idx), ...
    'Merged truck detection not found');

x1 = double(D.X1(idx));
y1 = double(D.Y1(idx));
x2 = double(D.X2(idx));
y2 = double(D.Y2(idx));

confidence = double(D.Confidence(idx));

assert(x2>x1 && y2>y1,'Invalid detection box');

%% NOMINAL CAMERA PROJECTION

% Nominal Camera vehicle coordinates:
% X=0.7m, Y=0m, Z=1.6m.
% Horizontal FOV approximately 90 degrees.
% fx=fy=w/2 is a nominal approximation.

camX = 0.7;
camY = 0.0;
camZ = 1.6;

fx = w/2;
fy = w/2;
cx = w/2;
cy = h/2;

X = lf.x_vehicle_m - camX;
Y = lf.y_vehicle_m - camY;
Z = lf.z_vehicle_m - camZ;

valid = isfinite(X) & isfinite(Y) & ...
    isfinite(Z) & X>1.0;

X = X(valid);
Y = Y(valid);
Z = Z(valid);

u = cx - fx .* Y ./ X;
v = cy - fy .* Z ./ X;

insideImage = ...
    isfinite(u) & isfinite(v) & ...
    u>=1 & u<=w & v>=1 & v<=h;

u = u(insideImage);
v = v(insideImage);
depth = X(insideImage);

insideBox = ...
    u>=x1 & u<=x2 & ...
    v>=y1 & v<=y2;

boxU = u(insideBox);
boxV = v(insideBox);
boxDepth = depth(insideBox);

assert(~isempty(boxDepth), ...
    'No projected LiDAR points inside selected box');

%% DEPTH STATISTICS

nAll = numel(depth);
nBox = numel(boxDepth);

medDepth = median(boxDepth);
meanDepth = mean(boxDepth);
minDepth = min(boxDepth);
maxDepth = max(boxDepth);

% The 20–22 m interval is a previously examined
% depth region, not an estimated GT object range.
lidarForwardDepth = boxDepth - (2.6 - camX);
in20to22 = sum(lidarForwardDepth>=20 & lidarForwardDepth<=22);
fraction20to22 = in20to22/nBox;

% Robust depth dispersion.
madDepth = median(abs(boxDepth-medDepth));

fprintf('\n=== FIGURE 26: CAMERA-LIDAR DEPTH RESULTS ===\n');

fprintf('FRAME=%d\n',frame);
fprintf('CAMERA_IMAGE_SIZE=%dx%d\n',w,h);
fprintf('CAMERA_CLASS_HYPOTHESIS=truck|boat\n');
fprintf('CAMERA_DETECTION_CONFIDENCE=%.6f\n',confidence);
fprintf('PROJECTED_POINTS_INSIDE_IMAGE=%d\n',nAll);
fprintf('PROJECTED_POINTS_INSIDE_BOX=%d\n',nBox);
fprintf('MEDIAN_BOX_DEPTH_M=%.6f\n',medDepth);
fprintf('MEAN_BOX_DEPTH_M=%.6f\n',meanDepth);
fprintf('MIN_BOX_DEPTH_M=%.6f\n',minDepth);
fprintf('MAX_BOX_DEPTH_M=%.6f\n',maxDepth);
fprintf('MEDIAN_ABSOLUTE_DEPTH_DEVIATION_M=%.6f\n',madDepth);
fprintf('MEDIAN_LIDAR_FORWARD_DEPTH_M=%.6f\n',median(lidarForwardDepth));
fprintf('DEPTH_ORIGIN_OFFSET_M=1.900000\n');
fprintf('BOX_POINTS_20_TO_22_M=%d\n',in20to22);
fprintf('BOX_FRACTION_20_TO_22_M=%.6f\n',fraction20to22);

%% FIGURE 26 — THREE PANELS

f = figure('Color','w', ...
    'Position',[60 80 1700 600]);

tiledlayout(1,3, ...
    'TileSpacing','compact', ...
    'Padding','compact');

%% PANEL A: FULL IMAGE

nexttile;

image(I);
axis image;
hold on;

scatter(u,v,7,depth,'filled');

rectangle('Position', ...
    [x1 y1 x2-x1 y2-y1], ...
    'EdgeColor','y','LineWidth',2);

title('A: Full Camera-LiDAR projection');
xlabel('Image X (pixels)');
ylabel('Image Y (pixels)');

%% PANEL B: TARGET CLOSE-UP

nexttile;

image(I);
axis image;
hold on;

% Use the same color mapping for projected points.
scatter(u,v,14,depth,'filled');

scatter(boxU,boxV,32,'r','filled', ...
    'MarkerFaceAlpha',0.75);

rectangle('Position', ...
    [x1 y1 x2-x1 y2-y1], ...
    'EdgeColor','y','LineWidth',2);

padding = 45;

xlim([max(1,x1-padding),min(w,x2+padding)]);
ylim([max(1,y1-padding),min(h,y2+padding)]);

title(sprintf( ...
    'B: Target region, %d LiDAR points',nBox));

xlabel('Image X (pixels)');
ylabel('Image Y (pixels)');

%% PANEL C: DEPTH DISTRIBUTION

nexttile;

histogram(boxDepth, ...
    'BinWidth',0.5, ...
    'FaceColor',[0.2 0.5 0.8]);

hold on;

xline(medDepth,'r--', ...
    'Median depth','LineWidth',1.8);

xline(21.9,'k:','LiDAR 20 m');
xline(23.9,'k:','LiDAR 22 m');

xlabel('Camera-forward depth (m)');
ylabel('Number of points');

title('C: Depth distribution inside target box');
grid on;

sgtitle( ...
    'Figure 26 — Camera-LiDAR compatibility (nominal calibration)');

exportgraphics(f,figurePath,'Resolution',220);
close(f);

%% WRITE NUMERICAL EVIDENCE

Summary = table( ...
    frame,confidence,nAll,nBox, ...
    medDepth,meanDepth,minDepth,maxDepth, ...
    madDepth,in20to22,fraction20to22, ...
    'VariableNames',{ ...
    'Frame', ...
    'CameraConfidence', ...
    'ProjectedImagePoints', ...
    'PointsInsideDetectionBox', ...
    'MedianDepth_m', ...
    'MeanDepth_m', ...
    'MinDepth_m', ...
    'MaxDepth_m', ...
    'MedianAbsoluteDepthDeviation_m', ...
    'PointsDepth20to22m', ...
    'FractionDepth20to22m'});

writetable(Summary,csvPath);

%% FINISH

fprintf('\nFIGURE=%s\n',figurePath);
fprintf('SUMMARY_CSV=%s\n',csvPath);

fprintf('CAMERA_CALIBRATED=NO\n');
fprintf('TARGET_IDENTITY_CONFIRMED=NO\n');
fprintf('RADAR_TRACK2_MATCHES_AT_FRAME530=0\n');
fprintf('ORIGINAL_INPUTS_MODIFIED=NO\n');

fprintf('TASK24_MATLAB_FIGURE26_COMPLETE\n');