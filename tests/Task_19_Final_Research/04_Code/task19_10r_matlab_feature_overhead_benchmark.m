
%% TASK 19.10R - Sensor Monitor Feature Overhead
% GEMSTAR - 48 point clouds from 3 recordings
%
% Benchmark:
% A: ROI + count + median range
% B: A + 1 m XY occupancy
% C: B + 0.25 m 3D voxel occupancy
%
% PC MATLAB wall-clock timings only.
% CSV reading excluded from timed region.
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inventoryFile = fullfile(dataDir, ...
    "task19_10l_cross_recording_inventory.csv");

assert(isfile(inventoryFile), ...
    "Task 19.10L inventory missing.");

I = readtable(inventoryFile,"TextType","string");

%% 2. Parameters

runs = 50;

roiX = [0 20];
roiY = [-6 6];

cellSize = 1.0;
voxelSize = 0.25;

samples = table();
summary = table();

fprintf("\n=== TASK 19.10R FEATURE OVERHEAD ===\n");
fprintf("Frames: %d\n",height(I));
fprintf("Runs per frame: %d\n",runs);

%% 3. Process each point cloud

for fi = 1:height(I)

    scenario = I.Scenario(fi);
    frameID = I.FrameIndex(fi);

    file = I.CandidateCSV(fi);

    assert(isfile(file),"Missing CSV: %s",file);

    T = readtable(file);

    P = double([T.X,T.Y,T.Z]);

    assert(all(isfinite(P(:))), ...
        "Nonfinite point coordinates.");

    %% Warm-up
    a = featuresA(P,roiX,roiY);
    b = featuresB(P,roiX,roiY,cellSize);
    c = featuresC(P,roiX,roiY,cellSize,voxelSize);

    assert(a.ROIPoints==I.ROIPoints(fi));
    assert(b.ROIPoints==a.ROIPoints);
    assert(c.ROIPoints==a.ROIPoints);

    %% Timing arrays

    timeA = zeros(runs,1);
    timeB = zeros(runs,1);
    timeC = zeros(runs,1);

    for k = 1:runs

        tic;
        a = featuresA(P,roiX,roiY);
        timeA(k) = toc*1000;

        tic;
        b = featuresB(P,roiX,roiY,cellSize);
        timeB(k) = toc*1000;

        tic;
        c = featuresC( ...
            P,roiX,roiY,cellSize,voxelSize);
        timeC(k) = toc*1000;

    end

    %% Save raw samples

    for k = 1:runs

        row = table();

        row.Scenario = scenario;
        row.FrameIndex = frameID;
        row.Run = k;

        row.LightweightMs = timeA(k);
        row.SpatialMs = timeB(k);
        row.VoxelFeatureMs = timeC(k);

        samples = [samples;row];

    end

    %% Save frame summary

    row = table();

    row.Scenario = scenario;
    row.FrameIndex = frameID;

    row.CandidatePoints = size(P,1);
    row.ROIPoints = I.ROIPoints(fi);

    row.LightweightMedianMs = median(timeA);
    row.SpatialMedianMs = median(timeB);
    row.VoxelFeatureMedianMs = median(timeC);

    row.LightweightP95Ms = percentile95(timeA);
    row.SpatialP95Ms = percentile95(timeB);
    row.VoxelFeatureP95Ms = percentile95(timeC);

    row.OccupiedXYCells = c.OccupiedXYCells;
    row.OccupiedVoxels = c.OccupiedVoxels;

    summary = [summary;row];

    fprintf( ...
        "%s | frame %3d | ROI=%4d | " + ...
        "A=%.4f ms | B=%.4f ms | C=%.4f ms\n", ...
        scenario,frameID,row.ROIPoints, ...
        row.LightweightMedianMs, ...
        row.SpatialMedianMs, ...
        row.VoxelFeatureMedianMs);

end

%% 4. Save outputs

sampleFile = fullfile(dataDir, ...
    "task19_10r_feature_overhead_samples.csv");

summaryFile = fullfile(dataDir, ...
    "task19_10r_feature_overhead_summary.csv");

writetable(samples,sampleFile);
writetable(summary,summaryFile);

%% 5. Aggregate results by recording

scenarios = unique(summary.Scenario,"stable");

recordingSummary = table();

for k = 1:numel(scenarios)

    S = summary(summary.Scenario==scenarios(k),:);

    row = table();

    row.Scenario = scenarios(k);
    row.Frames = height(S);

    row.LightweightMedianMs = ...
        median(S.LightweightMedianMs);

    row.SpatialMedianMs = ...
        median(S.SpatialMedianMs);

    row.VoxelFeatureMedianMs = ...
        median(S.VoxelFeatureMedianMs);

    recordingSummary = [recordingSummary;row];

end

recordingFile = fullfile(dataDir, ...
    "task19_10r_feature_overhead_recording_summary.csv");

writetable(recordingSummary,recordingFile);

%% 6. Visualization

fig = figure("Color","w", ...
    "Position",[100 100 1200 760]);

subplot(2,2,1);

bar(categorical(recordingSummary.Scenario), ...
    [recordingSummary.LightweightMedianMs, ...
     recordingSummary.SpatialMedianMs, ...
     recordingSummary.VoxelFeatureMedianMs]);

ylabel("Median feature time (ms)");
title("Feature Cost by Recording");

legend("Lightweight","Spatial","Voxel", ...
    "Location","best");

grid on;

subplot(2,2,2);

scatter(summary.ROIPoints, ...
    summary.LightweightMedianMs,65,"filled");

hold on;

scatter(summary.ROIPoints, ...
    summary.VoxelFeatureMedianMs,65,"filled");

xlabel("ROI points");
ylabel("Median execution time (ms)");

title("Feature Cost vs Input Workload");

legend("Lightweight","Voxel features", ...
    "Location","best");

grid on;

subplot(2,2,3);

boxData = [ ...
    summary.LightweightMedianMs, ...
    summary.SpatialMedianMs, ...
    summary.VoxelFeatureMedianMs];

plot(boxData',"-o");

xticks(1:3);
xticklabels(["Lightweight","Spatial","Voxel"]);

ylabel("Frame median time (ms)");
title("Feature-Cost Progression");
grid on;

subplot(2,2,4);

bar([ ...
    median(summary.LightweightMedianMs), ...
    median(summary.SpatialMedianMs), ...
    median(summary.VoxelFeatureMedianMs)]);

xticks(1:3);
xticklabels(["Lightweight","Spatial","Voxel"]);

ylabel("Median across frame medians (ms)");
title("Overall Feature Computation Cost");

grid on;

sgtitle("GEMSTAR - Sensor Monitor Computational Overhead");

graphFile = fullfile(graphDir, ...
    "task19_10r_feature_overhead_benchmark.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 7. Results

fprintf("\n=== RECORDING-LEVEL SUMMARY ===\n");
disp(recordingSummary);

fprintf("\n=== TASK 19.10R COMPLETE ===\n");

fprintf("Samples CSV saved: %d\n",isfile(sampleFile));
fprintf("Frame summary saved: %d\n",isfile(summaryFile));
fprintf("Recording summary saved: %d\n", ...
    isfile(recordingFile));

fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nIMPORTANT:\n");
fprintf("These are MATLAB PC timings only.\n");
fprintf("CSV I/O, OSI decoding and hardware transfer excluded.\n");
fprintf("Scheduling decision logic is not timed here.\n");
fprintf("Features B and C include all operations in A.\n");
fprintf("Voxel features are computed separately from RANSAC.\n");

%% LOCAL FUNCTIONS

function out = featuresA(P,roiX,roiY)

    mask = ...
        P(:,1)>=roiX(1) & ...
        P(:,1)<=roiX(2) & ...
        P(:,2)>=roiY(1) & ...
        P(:,2)<=roiY(2);

    R = P(mask,:);

    out = struct();

    out.ROIPoints = size(R,1);

    if isempty(R)
        out.MedianRange = NaN;
    else
        out.MedianRange = ...
            median(sqrt(sum(R.^2,2)));
    end

end

function out = featuresB(P,roiX,roiY,cellSize)

    mask = ...
        P(:,1)>=roiX(1) & ...
        P(:,1)<=roiX(2) & ...
        P(:,2)>=roiY(1) & ...
        P(:,2)<=roiY(2);

    R = P(mask,:);

    out = struct();
    out.ROIPoints = size(R,1);

    if isempty(R)
        out.MedianRange = NaN;
        out.OccupiedXYCells = 0;
    else
        out.MedianRange = ...
            median(sqrt(sum(R.^2,2)));

        xyCells = floor(R(:,1:2)./cellSize);

        out.OccupiedXYCells = ...
            size(unique(xyCells,"rows"),1);
    end

end

function out = featuresC( ...
    P,roiX,roiY,cellSize,voxelSize)

    mask = ...
        P(:,1)>=roiX(1) & ...
        P(:,1)<=roiX(2) & ...
        P(:,2)>=roiY(1) & ...
        P(:,2)<=roiY(2);

    R = P(mask,:);

    out = struct();

    out.ROIPoints = size(R,1);

    if isempty(R)

        out.MedianRange = NaN;
        out.OccupiedXYCells = 0;
        out.OccupiedVoxels = 0;

    else

        out.MedianRange = ...
            median(sqrt(sum(R.^2,2)));

        xyCells = floor(R(:,1:2)./cellSize);

        out.OccupiedXYCells = ...
            size(unique(xyCells,"rows"),1);

        voxelCells = floor(R./voxelSize);

        out.OccupiedVoxels = ...
            size(unique(voxelCells,"rows"),1);

    end

end

function p = percentile95(x)

    x = sort(x(:));
    p = x(ceil(0.95*numel(x)));

end
