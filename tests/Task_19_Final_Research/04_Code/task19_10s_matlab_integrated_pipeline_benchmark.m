
%% TASK 19.10S - Integrated Monitoring and Processing Benchmark
% GEMSTAR - 48 frames from three separate recordings.
%
% Executable timed path:
% ROI -> lightweight features -> decision ->
% optional voxel construction -> RANSAC -> SVD -> classify
%
% Compare against full-resolution processing with the same
% ROI extraction and lightweight feature overhead.
%
% No CSV I/O in timed region.
% No FPGA or ARM measurements.
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

assert(isfile(inventoryFile),"Inventory missing.");

I = readtable(inventoryFile,"TextType","string");

%% 2. Frozen configuration

runs = 5;

iterations = 1000;
tolerance = 0.08;
maxTilt = 15;
voxelSize = 0.25;

minimumPoints = 30;
lowROILimit = 1600;
highROILimit = 2200;

summary = table();
samples = table();

fprintf("\n=== TASK 19.10S INTEGRATED BENCHMARK ===\n");

%% 3. Evaluate every recording

for fi = 1:height(I)

    scenario = I.Scenario(fi);
    frameID = I.FrameIndex(fi);

    filename = I.CandidateCSV(fi);

    assert(isfile(filename), ...
        "Missing candidate cloud: %s",filename);

    T = readtable(filename);

    P = double([T.X,T.Y,T.Z]);

    assert(all(isfinite(P(:))), ...
        "Invalid XYZ data.");

    %% Warm-up

    [R,~,~] = lightFeatures(P);

    if size(R,1)>=minimumPoints
        rng(42);
        [n,d] = fitPlane(R,iterations,tolerance,maxTilt);
        classifyGround(R,n,d,tolerance);

        V = makeVoxels(R,voxelSize);

        if size(V,1)>=3
            rng(42);
            [n,d] = fitPlane(V,iterations,tolerance,maxTilt);
            classifyGround(R,n,d,tolerance);
        end
    end

    %% Timed executable pipelines

    baselineMs = zeros(runs,1);
    adaptiveMs = zeros(runs,1);

    featureMs = zeros(runs,1);

    selectedMode = "";
    roiCount = 0;

    for runID = 1:runs

        seed = 400000 + fi*100 + runID;

        %% Baseline: lightweight features + full RANSAC
        % Includes ROI and feature overhead.

        rng(seed);
        tic;

        [Rb,~,~] = lightFeatures(P);

        if size(Rb,1)>=minimumPoints
            [nb,db] = fitPlane( ...
                Rb,iterations,tolerance,maxTilt);
            maskBaseline = classifyGround( ...
                Rb,nb,db,tolerance);
        else
            maskBaseline = false(size(Rb,1),1);
        end

        baselineMs(runID) = toc*1000;

        %% Integrated policy:
        % ROI + features + decision + selected processing.
        % No precomputed voxel grid reused outside timer.

        rng(seed);
        tic;

        [Ra,roiCount,medianRange] = lightFeatures(P);

        featureMs(runID) = toc*1000;

        if roiCount<minimumPoints

            selectedMode = "SKIP_INSUFFICIENT";

            maskAdaptive = false(roiCount,1);

        elseif roiCount<lowROILimit || roiCount>highROILimit

            selectedMode = "FULL";

            [na,da] = fitPlane( ...
                Ra,iterations,tolerance,maxTilt);

            maskAdaptive = classifyGround( ...
                Ra,na,da,tolerance);

        else

            selectedMode = "VOXEL";

            Va = makeVoxels(Ra,voxelSize);

            [na,da] = fitPlane( ...
                Va,iterations,tolerance,maxTilt);

            maskAdaptive = classifyGround( ...
                Ra,na,da,tolerance);

        end

        adaptiveMs(runID) = toc*1000;

        % Protect against unused-output optimization.
        assert(numel(maskAdaptive)==roiCount);
        assert(numel(maskBaseline)==roiCount);

        row = table();

        row.Scenario = scenario;
        row.FrameIndex = frameID;
        row.Run = runID;

        row.ROIPoints = roiCount;
        row.MedianROIRangeM = medianRange;

        row.Mode = selectedMode;

        row.BaselineMs = baselineMs(runID);
        row.IntegratedMs = adaptiveMs(runID);
        row.LightweightFeatureMs = featureMs(runID);

        samples = [samples;row];

    end

    %% Per-frame results

    result = table();

    result.Scenario = scenario;
    result.FrameIndex = frameID;

    result.CandidatePoints = size(P,1);
    result.ROIPoints = roiCount;

    result.Mode = selectedMode;
    result.Runs = runs;

    result.BaselineMedianMs = median(baselineMs);
    result.IntegratedMedianMs = median(adaptiveMs);

    result.FeatureMedianMs = median(featureMs);

    result.SpeedRatio = ...
        result.BaselineMedianMs / ...
        max(result.IntegratedMedianMs,eps);

    result.TimeSavedMs = ...
        result.BaselineMedianMs - ...
        result.IntegratedMedianMs;

    summary = [summary;result];

    fprintf( ...
        "%s | frame %3d | ROI=%4d | mode=%s | " + ...
        "baseline=%.4f ms | integrated=%.4f ms\n", ...
        scenario,frameID,roiCount,selectedMode, ...
        result.BaselineMedianMs, ...
        result.IntegratedMedianMs);

end

%% 4. Save data

sampleFile = fullfile(dataDir, ...
    "task19_10s_integrated_pipeline_samples.csv");

summaryFile = fullfile(dataDir, ...
    "task19_10s_integrated_pipeline_summary.csv");

writetable(samples,sampleFile);
writetable(summary,summaryFile);

%% 5. Plot integrated results

fig = figure("Color","w", ...
    "Position",[100 100 1200 750]);

scenarios = unique(summary.Scenario,"stable");

subplot(2,2,1);
hold on;

for k = 1:numel(scenarios)

    S = summary(summary.Scenario==scenarios(k),:);

    plot(S.FrameIndex,S.IntegratedMedianMs, ...
        "-o","LineWidth",1.2, ...
        "DisplayName",scenarios(k));

end

xlabel("Frame index");
ylabel("Integrated latency (ms)");
title("Executable Pipeline Latency");
legend("Location","best");
grid on;

subplot(2,2,2);

plot(summary.ROIPoints,summary.SpeedRatio, ...
    "o","MarkerSize",7);

hold on;
yline(1,"k--","Equal latency");

xlabel("ROI points");
ylabel("Baseline / integrated latency");
title("Measured Processing Speed Ratio");
grid on;

subplot(2,2,3);

scatter(summary.ROIPoints, ...
    summary.FeatureMedianMs,70,"filled");

xlabel("ROI points");
ylabel("Lightweight feature time (ms)");
title("Measured Feature Overhead");
grid on;

subplot(2,2,4);

modes = ["FULL","VOXEL","SKIP_INSUFFICIENT"];

counts = zeros(1,numel(modes));

for k = 1:numel(modes)
    counts(k) = sum(summary.Mode==modes(k));
end

bar(counts);
xticks(1:numel(modes));
xticklabels(modes);
xtickangle(15);

ylabel("Frames");
title("Executed Processing Modes");
grid on;

sgtitle("GEMSTAR - Integrated Lightweight Policy Benchmark");

graphFile = fullfile(graphDir, ...
    "task19_10s_integrated_pipeline_benchmark.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 6. Completion

fprintf("\n=== TASK 19.10S SUMMARY ===\n");

fprintf("Total frames: %d\n",height(summary));

fprintf("Full selections: %d\n", ...
    sum(summary.Mode=="FULL"));

fprintf("Voxel selections: %d\n", ...
    sum(summary.Mode=="VOXEL"));

fprintf("Insufficient-data skips: %d\n", ...
    sum(summary.Mode=="SKIP_INSUFFICIENT"));

fprintf("\nMedian feature latency: %.5f ms\n", ...
    median(summary.FeatureMedianMs));

% Compare ratios only where both methods actually
% run ground segmentation.

processed = summary( ...
    summary.Mode~="SKIP_INSUFFICIENT",:);

fprintf("Median processed-frame speed ratio: %.3fx\n", ...
    median(processed.SpeedRatio));

fprintf("\n=== TASK 19.10S COMPLETE ===\n");

fprintf("Samples CSV saved: %d\n",isfile(sampleFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nIMPORTANT:\n");
fprintf("The skip decision is a new low-data safeguard.\n");
fprintf("The other ROI thresholds remain frozen.\n");
fprintf("Full and adaptive pipelines share feature operations.\n");
fprintf("Results exclude CSV I/O, OSI decoding and transfers.\n");
fprintf("The full observability monitor is NOT timed here.\n");
fprintf("No independent obstacle accuracy or hardware power measured.\n");

%% LOCAL FUNCTIONS

function [R,n,medianRange] = lightFeatures(P)

    keep = ...
        P(:,1)>=0 & P(:,1)<=20 & ...
        P(:,2)>=-6 & P(:,2)<=6;

    R = P(keep,:);
    n = size(R,1);

    if n==0
        medianRange = NaN;
    else
        medianRange = median(sqrt(sum(R.^2,2)));
    end

end

function V = makeVoxels(P,sz)

    indexes = floor(P./sz);

    [~,~,g] = unique(indexes,"rows");

    count = accumarray(g,1);

    V = zeros(numel(count),3);

    for j = 1:3
        V(:,j) = accumarray(g,P(:,j))./count;
    end

end

function [n,d] = fitPlane(P,nIterations,tol,maxTilt)

    N = size(P,1);

    n = [0;0;1];
    d = -median(P(:,3));

    bestCount = -1;

    for k = 1:nIterations

        indices = randperm(N,3);

        a = P(indices(1),:);
        b = P(indices(2),:);
        c = P(indices(3),:);

        normal = cross(b-a,c-a);
        magnitude = norm(normal);

        if magnitude<1e-10
            continue;
        end

        normal = normal(:)/magnitude;

        if abs(normal(3))<cosd(maxTilt)
            continue;
        end

        if normal(3)<0
            normal = -normal;
        end

        offset = -a*normal;

        inlierCount = sum( ...
            abs(P*normal+offset)<=tol);

        if inlierCount>bestCount
            bestCount = inlierCount;
            n = normal;
            d = offset;
        end

    end

    inliers = abs(P*n+d)<=tol;

    if sum(inliers)>=3

        X = P(inliers,:);
        center = mean(X,1);

        [~,~,B] = svd(X-center,0);

        normal = B(:,3);

        if normal(3)<0
            normal = -normal;
        end

        if normal(3)>=cosd(maxTilt)
            n = normal;
            d = -center*n;
        end

    end

end

function mask = classifyGround(P,n,d,tol)

    mask = abs(P*n+d)<=tol;

end
