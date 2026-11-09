
%% TASK 19.10O - LiDAR Observability and Scene Features
% GEMSTAR - 48 selected frames across 3 recordings
%
% Input: Task 19.10L candidate XYZ CSV files.
% No RANSAC rerun; no ground-truth labels.
% No additional MATLAB toolbox required.
%
% Features are descriptive diagnostics.
% They are NOT calibrated sensor-failure indicators.

clear;
clc;
close all;

%% 1. Directories

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir  = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inventoryFile = fullfile(dataDir, ...
    "task19_10l_cross_recording_inventory.csv");

assert(isfile(inventoryFile),"Inventory CSV missing.");

I = readtable(inventoryFile,"TextType","string");

%% 2. Feature settings

totalRays = 5271;
voxelSize = 0.25;

% Three equal-width scan-index sectors.
% Valid for the current 251-column GEMSTAR scan geometry.
sectorBoundaries = [0 83 167 251];

% XY occupancy cells in the existing sensor-local ROI.
cellSize = 1.0;

features = table();

fprintf("\n=== TASK 19.10O LIDAR FEATURE EXTRACTION ===\n");

%% 3. Process every exported frame

for k = 1:height(I)

    scenario = string(I.Scenario(k));
    frameID = I.FrameIndex(k);

    file = string(I.CandidateCSV(k));

    assert(isfile(file),"Missing cloud: %s",file);

    T = readtable(file);

    required = ["X","Y","Z","RangeM", ...
        "SignalStrength","RayIndex"];

    assert(all(ismember(required, ...
        string(T.Properties.VariableNames))), ...
        "Required point-cloud columns missing.");

    P = double([T.X,T.Y,T.Z]);

    rangeM = double(T.RangeM);
    strength = double(T.SignalStrength);
    rayIndex = double(T.RayIndex);

    assert(all(isfinite(P(:))), ...
        "Nonfinite XYZ values.");

    %% Candidate count and percentage

    N = height(T);
    validPercent = 100*N/totalRays;

    %% ROI selection

    roiMask = ...
        P(:,1)>=0 & P(:,1)<=20 & ...
        P(:,2)>=-6 & P(:,2)<=6;

    R = P(roiMask,:);
    nROI = size(R,1);

    assert(nROI==I.ROIPoints(k), ...
        "ROI count mismatch at frame %d",frameID);

    %% Return-range statistics

    if N>0
        medianRange = median(rangeM);

        sortedRanges = sort(rangeM);
        p10Index = max(1,ceil(0.10*N));
        p10Range = sortedRanges(p10Index);

        medianStrength = median(strength);
    else
        medianRange = NaN;
        p10Range = NaN;
        medianStrength = NaN;
    end

    %% Horizontal sector coverage
    % Horizontal ray index changes fastest.
    % Zero-based index 0...250.

    horizontalIndex = mod(rayIndex,251);

    sectorCounts = zeros(1,3);

    for s = 1:3

        sectorCounts(s) = sum( ...
            horizontalIndex>=sectorBoundaries(s) & ...
            horizontalIndex<sectorBoundaries(s+1));

    end

    occupiedSectors = sum(sectorCounts>0);

    %% Spatial occupancy and voxel compression

    if nROI>0

        % 1 m XY occupancy cells
        xyCells = floor(R(:,1:2)./cellSize);
        uniqueXY = unique(xyCells,"rows");
        occupiedXYCells = size(uniqueXY,1);

        % 0.25 m 3D occupied voxels
        voxelIdx = floor(R./voxelSize);
        uniqueVoxels = unique(voxelIdx,"rows");

        voxelCount = size(uniqueVoxels,1);

        compression = 100*(1-voxelCount/nROI);

        medianROIRange = ...
            median(sqrt(sum(R.^2,2)));

    else

        occupiedXYCells = 0;
        voxelCount = 0;
        compression = NaN;
        medianROIRange = NaN;

    end

    %% Save a feature row

    row = table();

    row.Scenario = scenario;
    row.FrameIndex = frameID;

    row.ValidPoints = N;
    row.ROIPoints = nROI;
    row.ValidReturnPercent = validPercent;

    row.MedianRangeM = medianRange;
    row.P10RangeM = p10Range;
    row.MedianSignalStrength = medianStrength;

    row.LeftSectorReturns = sectorCounts(1);
    row.MiddleSectorReturns = sectorCounts(2);
    row.RightSectorReturns = sectorCounts(3);
    row.OccupiedHorizontalSectors = occupiedSectors;

    row.OccupiedXYCells = occupiedXYCells;

    row.VoxelCount025 = voxelCount;
    row.VoxelCompressionPercent = compression;

    row.MedianROIRangeM = medianROIRange;

    features = [features;row];

    fprintf( ...
        "%s | frame %3d | valid=%4d | ROI=%4d | strength=%.4g | range=%.2f m\n", ...
        scenario,frameID,N,nROI, ...
        medianStrength,medianRange);

end

%% 4. Temporal feature changes
% Difference between consecutively sampled frames
% WITHIN the same recording.
% Samples are separated by ~50 frame indices, so these
% are not instantaneous frame-to-frame rates.

features.ValidPercentChange = nan(height(features),1);
features.ROIPointChange = nan(height(features),1);

scenarios = unique(features.Scenario,"stable");

for s = 1:numel(scenarios)

    idx = find(features.Scenario==scenarios(s));

    [~,order] = sort(features.FrameIndex(idx));
    idx = idx(order);

    for j = 2:numel(idx)

        current = idx(j);
        previous = idx(j-1);

        features.ValidPercentChange(current) = ...
            features.ValidReturnPercent(current) - ...
            features.ValidReturnPercent(previous);

        features.ROIPointChange(current) = ...
            features.ROIPoints(current) - ...
            features.ROIPoints(previous);

    end

end

%% 5. Save features

featureFile = fullfile(dataDir, ...
    "task19_10o_lidar_observability_features.csv");

writetable(features,featureFile);

%% 6. Plot cross-recording differences

fig = figure("Color","w", ...
    "Position",[100 100 1200 780]);

subplot(2,2,1);
hold on;

for s = 1:numel(scenarios)

    F = features(features.Scenario==scenarios(s),:);

    plot(F.FrameIndex,F.ValidReturnPercent, ...
        "-o","LineWidth",1.3, ...
        "DisplayName",scenarios(s));
end

xlabel("Frame index");
ylabel("Valid returns (%)");
title("LiDAR Candidate-Return Availability");
legend("Location","best");
grid on;

subplot(2,2,2);
hold on;

for s = 1:numel(scenarios)

    F = features(features.Scenario==scenarios(s),:);

    plot(F.FrameIndex,F.MedianRangeM, ...
        "-o","LineWidth",1.3, ...
        "DisplayName",scenarios(s));
end

xlabel("Frame index");
ylabel("Median candidate range (m)");
title("Recorded Return-Range Distribution");
grid on;

subplot(2,2,3);
hold on;

for s = 1:numel(scenarios)

    F = features(features.Scenario==scenarios(s),:);

    scatter(F.ROIPoints,F.OccupiedXYCells, ...
        65,"filled","DisplayName",scenarios(s));
end

xlabel("ROI point count");
ylabel("Occupied 1 m XY cells");
title("Workload vs Spatial Occupancy");
legend("Location","best");
grid on;

subplot(2,2,4);
hold on;

for s = 1:numel(scenarios)

    F = features(features.Scenario==scenarios(s),:);

    scatter(F.ValidReturnPercent, ...
        F.VoxelCompressionPercent, ...
        65,"filled","DisplayName",scenarios(s));
end

xlabel("Valid returns (%)");
ylabel("0.25 m voxel compression (%)");
title("Return Availability vs Compression");
legend("Location","best");
grid on;

sgtitle("GEMSTAR - LiDAR Observability and Workload Features");

graphFile = fullfile(graphDir, ...
    "task19_10o_lidar_observability_features.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 7. Recording-level summaries

recordingSummary = table();

for s = 1:numel(scenarios)

    F = features(features.Scenario==scenarios(s),:);

    row = table();

    row.Scenario = scenarios(s);
    row.Frames = height(F);

    row.MedianValidReturnPercent = ...
        median(F.ValidReturnPercent);

    row.MedianROIPoints = ...
        median(F.ROIPoints);

    row.MedianRangeM = ...
        median(F.MedianRangeM,"omitnan");

    row.MedianSignalStrength = ...
        median(F.MedianSignalStrength,"omitnan");

    row.MedianVoxelCompressionPercent = ...
        median(F.VoxelCompressionPercent,"omitnan");

    row.MedianOccupiedXYCells = ...
        median(F.OccupiedXYCells);

    recordingSummary = [recordingSummary;row];

end

summaryFile = fullfile(dataDir, ...
    "task19_10o_recording_feature_summary.csv");

writetable(recordingSummary,summaryFile);

%% 8. Completion

fprintf("\n=== RECORDING FEATURE SUMMARY ===\n");
disp(recordingSummary);

fprintf("\n=== TASK 19.10O COMPLETE ===\n");

fprintf("Feature CSV saved: %d\n",isfile(featureFile));
fprintf("Recording summary saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nIMPORTANT:\n");
fprintf("These are descriptive features, not calibrated health scores.\n");
fprintf("Valid-return percentage is affected by scene geometry.\n");
fprintf("Signal strength is a simulator output, not verified SNR.\n");
fprintf("Temporal changes are between sampled observations.\n");
fprintf("No live scheduler, AI model or FPGA measurements yet.\n");
