
%% TASK 19.13 - LiDAR INT8 / INT16 Quantization Assessment
% GEMSTAR frame 150 - hardware-oriented precision experiment
%
% Input:
%   Task 19.4A ROI points
%   Task 19.6A RANSAC ground inliers
%
% Compares DOUBLE, INT16 and INT8 XYZ representation.
% Uses a single reference plane fitted from saved ground points.
%
% Quantization simulation only:
% NOT an FPGA implementation or integer-only RANSAC.
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

roiFile = fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv");

groundFile = fullfile(cloudDir, ...
    "task19_6a_frame150_ransac_ground.csv");

assert(isfile(roiFile),"ROI point cloud missing.");
assert(isfile(groundFile),"RANSAC ground CSV missing.");

T = readtable(roiFile);
G = readtable(groundFile);

P = double([T.X,T.Y,T.Z]);
groundP = double([G.X,G.Y,G.Z]);

assert(size(P,1)==1922,"Unexpected frame-150 ROI.");
assert(size(groundP,1)>=3,"Insufficient ground points.");

%% 2. Reference plane from saved ground inliers

center = mean(groundP,1);
[~,~,B] = svd(groundP-center,0);

normal = B(:,3);

if normal(3)<0
    normal = -normal;
end

offset = -center*normal;

distanceTol = 0.08;

referenceDistance = abs(P*normal+offset);
referenceGround = referenceDistance<=distanceTol;

fprintf("\n=== TASK 19.13 QUANTIZATION ===\n");
fprintf("ROI points: %d\n",size(P,1));
fprintf("Ground reference points: %d\n",size(groundP,1));

fprintf("Plane: %.6f X + %.6f Y + %.6f Z + %.6f = 0\n", ...
    normal(1),normal(2),normal(3),offset);

%% 3. Fixed symmetric, per-axis quantization scales
% Scale based on observed ROI coordinate magnitudes.
% Same fixed scale for every point WITHIN this frame.
%
% This is not yet a globally calibrated quantizer.
% Deployment scales must be fixed using training data
% or engineering bounds, then tested on unseen frames.

maxAbs = max(abs(P),[],1);
maxAbs = max(maxAbs,1e-9);

bitWidths = [8 16];
summary = table();

quantizedPoints = cell(2,1);

for k = 1:numel(bitWidths)

    bits = bitWidths(k);

    qmax = 2^(bits-1)-1;

    scale = maxAbs/qmax;

    Q = round(P./scale);

    Q = max(-qmax,min(qmax,Q));

    if bits==8
        Qinteger = int8(Q);
    else
        Qinteger = int16(Q);
    end

    reconstructed = double(Qinteger).*scale;

    quantizedPoints{k} = reconstructed;

    %% Geometric error

    errorXYZ = reconstructed-P;
    pointError = sqrt(sum(errorXYZ.^2,2));

    rmse = sqrt(mean(pointError.^2));
    maxError = max(pointError);

    %% Reference-plane classification comparison

    newDistance = abs(reconstructed*normal+offset);
    quantizedGround = newDistance<=distanceTol;

    labelChanges = sum( ...
        referenceGround~=quantizedGround);

    nonGroundToGround = sum( ...
        ~referenceGround & quantizedGround);

    groundToNonGround = sum( ...
        referenceGround & ~quantizedGround);

    agreement = 100*mean( ...
        referenceGround==quantizedGround);

    %% Signed distance perturbation

    planeDistanceError = abs( ...
        newDistance-referenceDistance);

    %% Save detailed results

    details = table();

    details.PointIndex = (1:size(P,1))';

    details.OriginalX = P(:,1);
    details.OriginalY = P(:,2);
    details.OriginalZ = P(:,3);

    details.QuantizedX = reconstructed(:,1);
    details.QuantizedY = reconstructed(:,2);
    details.QuantizedZ = reconstructed(:,3);

    details.PositionErrorM = pointError;
    details.PlaneDistanceErrorM = planeDistanceError;

    details.ReferenceGround = referenceGround;
    details.QuantizedGround = quantizedGround;

    detailFile = fullfile(dataDir, ...
        sprintf("task19_13_int%d_pointwise_results.csv",bits));

    writetable(details,detailFile);

    %% Summary

    row = table();

    row.BitWidth = bits;
    row.PointCount = size(P,1);

    row.ScaleX = scale(1);
    row.ScaleY = scale(2);
    row.ScaleZ = scale(3);

    row.PositionRMSEM = rmse;
    row.MaxPositionErrorM = maxError;

    row.MaxPlaneDistanceErrorM = max(planeDistanceError);

    row.ClassificationAgreementPercent = agreement;

    row.ChangedGroundLabels = labelChanges;
    row.NonGroundToGround = nonGroundToGround;
    row.GroundToNonGround = groundToNonGround;

    row.CoordinateStorageBytes = ...
        size(P,1)*3*bits/8;

    row.StorageReductionVsDoublePercent = ...
        100*(1-bits/64);

    summary = [summary;row];

    fprintf("\nINT%d\n",bits);
    fprintf("Position RMSE: %.6f m\n",rmse);
    fprintf("Maximum position error: %.6f m\n",maxError);
    fprintf("Ground-label agreement: %.3f%%\n",agreement);
    fprintf("Changed labels: %d\n",labelChanges);

end

%% 4. Save summary

summaryFile = fullfile(dataDir, ...
    "task19_13_quantization_summary.csv");

writetable(summary,summaryFile);

%% 5. Visualize

fig = figure("Color","w", ...
    "Position",[100 100 1200 760]);

subplot(2,2,1);

bar(summary.BitWidth, ...
    summary.PositionRMSEM*1000);

xlabel("Integer bit width");
ylabel("Position RMSE (mm)");
title("XYZ Quantization Error");
xticks(bitWidths);
grid on;

subplot(2,2,2);

bar(summary.BitWidth, ...
    summary.ChangedGroundLabels);

xlabel("Integer bit width");
ylabel("Changed ground labels");
title("Classification Sensitivity");
xticks(bitWidths);
grid on;

subplot(2,2,3);

scatter(P(:,1),P(:,3),8, ...
    P(:,2),"filled");

hold on;

scatter(quantizedPoints{1}(:,1), ...
    quantizedPoints{1}(:,3),8, ...
    "MarkerEdgeColor","k");

xlabel("X (m)");
ylabel("Z (m)");
title("Original XYZ and INT8 Reconstruction");
grid on;

subplot(2,2,4);

bar(summary.BitWidth, ...
    summary.CoordinateStorageBytes/1024);

xlabel("Integer bit width");
ylabel("Raw XYZ storage (KiB)");
title("Integer Coordinate Storage");
xticks(bitWidths);
grid on;

sgtitle("GEMSTAR - INT8 and INT16 LiDAR Precision Study");

graphFile = fullfile(graphDir, ...
    "task19_13_quantization_comparison.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 6. Final report

fprintf("\n=== QUANTIZATION SUMMARY ===\n");
disp(summary);

fprintf("\n=== TASK 19.13 COMPLETE ===\n");

fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("INT8 detail CSV saved: %d\n", ...
    isfile(fullfile(dataDir, ...
    "task19_13_int8_pointwise_results.csv")));

fprintf("INT16 detail CSV saved: %d\n", ...
    isfile(fullfile(dataDir, ...
    "task19_13_int16_pointwise_results.csv")));

fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nIMPORTANT:\n");
fprintf("Quantizer scales are calibrated on frame 150.\n");
fprintf("Fixed-plane classification only; no integer RANSAC.\n");
fprintf("Storage estimates exclude scales, IDs and metadata.\n");
fprintf("No FPGA power, resource usage or latency measured.\n");
