
%% TASK 19.10C - Multi-Frame RANSAC Benchmark
% GEMSTAR fog_mor100 - 8 selected frames
%
% Compare:
% A: ROI -> Full RANSAC -> SVD refinement -> classify ROI
% B: ROI -> Voxel 0.25m -> RANSAC -> SVD -> classify ROI
%
% Benchmarks processing on Windows PC MATLAB only.
% Full RANSAC is a reference, NOT ground truth.
% CSV I/O and reconstruction excluded from timing.
% No additional toolboxes required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

frames = [0 50 100 150 200 250 350 450];

%% 2. Settings

voxelSize = 0.25;
iterations = 1000;
distanceTol = 0.08;
maxTilt = 15;
runs = 10;

xmin = 0;
xmax = 20;
ymin = -6;
ymax = 6;

nFrames = numel(frames);

summaryRows = table();
sampleRows = table();

fprintf("\n=== TASK 19.10C MULTI-FRAME BENCHMARK ===\n");

%% 3. Analyze each frame

for fi = 1:nFrames

    frameID = frames(fi);

    filename = sprintf( ...
        "task19_10b_frame%03d_candidate_xyz.csv",frameID);

    path = fullfile(cloudDir,filename);

    assert(isfile(path),"Missing frame CSV: %s",path);

    T = readtable(path);

    allPoints = double([T.X,T.Y,T.Z]);

    assert(all(isfinite(allPoints(:))), ...
        "Nonfinite XYZ values at frame %d",frameID);

    %% Apply the SAME ROI as Task 19.4A

    mask = ...
        allPoints(:,1)>=xmin & ...
        allPoints(:,1)<=xmax & ...
        allPoints(:,2)>=ymin & ...
        allPoints(:,2)<=ymax;

    P = allPoints(mask,:);

    if size(P,1)<10
        error("Too few ROI points at frame %d",frameID);
    end

    V = makeVoxels(P,voxelSize);

    if size(V,1)<10
        error("Too few voxel points at frame %d",frameID);
    end

    if frameID==150
        assert(size(P,1)==1922, ...
            "Frame 150 ROI differs from earlier result");
        assert(size(V,1)==418, ...
            "Frame 150 voxel count differs");
    end

    %% Warm-up

    rng(42);
    [n,d] = ransacRefined( ...
        P,iterations,distanceTol,maxTilt);
    classify(P,n,d,distanceTol);

    rng(42);
    [n,d] = ransacRefined( ...
        V,iterations,distanceTol,maxTilt);
    classify(P,n,d,distanceTol);

    %% Repeated benchmark

    fullTimes = zeros(runs,1);
    voxelTimes = zeros(runs,1);
    agree = zeros(runs,1);

    falseGround = zeros(runs,1);
    missedGround = zeros(runs,1);

    fullCounts = zeros(runs,1);
    voxelCounts = zeros(runs,1);

    for k = 1:runs

        % Same seed for reproducibility of each run.
        % Different point sets do not create identical samples.
        seed = 10000 + 100*fi + k;

        %% Full-resolution processing

        rng(seed);
        tic;

        [nf,df] = ransacRefined( ...
            P,iterations,distanceTol,maxTilt);

        fullMask = classify( ...
            P,nf,df,distanceTol);

        fullTimes(k) = toc*1000;

        %% Voxel-assisted processing
        % Includes voxel construction in the timed region.

        rng(seed);
        tic;

        Vk = makeVoxels(P,voxelSize);

        [nv,dv] = ransacRefined( ...
            Vk,iterations,distanceTol,maxTilt);

        voxelMask = classify( ...
            P,nv,dv,distanceTol);

        voxelTimes(k) = toc*1000;

        %% Classification comparisons

        agree(k) = ...
            100*mean(fullMask==voxelMask);

        falseGround(k) = ...
            sum(~fullMask & voxelMask);

        missedGround(k) = ...
            sum(fullMask & ~voxelMask);

        fullCounts(k) = sum(fullMask);
        voxelCounts(k) = sum(voxelMask);

        sample = table();

        sample.FrameIndex = frameID;
        sample.Run = k;
        sample.InputPoints = size(allPoints,1);
        sample.ROIPoints = size(P,1);
        sample.VoxelPoints = size(V,1);

        sample.FullMs = fullTimes(k);
        sample.VoxelMs = voxelTimes(k);

        sample.AgreementPercent = agree(k);
        sample.FalseGround = falseGround(k);
        sample.MissedGround = missedGround(k);

        sample.FullGroundCount = fullCounts(k);
        sample.VoxelGroundCount = voxelCounts(k);

        sampleRows = [sampleRows;sample];

    end

    %% Summary for this frame

    medFull = median(fullTimes);
    medVoxel = median(voxelTimes);

    row = table();

    row.FrameIndex = frameID;
    row.CandidatePoints = size(allPoints,1);
    row.ROIPoints = size(P,1);
    row.VoxelPoints = size(V,1);

    row.FullMedianMs = medFull;
    row.VoxelMedianMs = medVoxel;

    row.SpeedRatio = medFull/medVoxel;
    row.LatencyReductionPercent = ...
        100*(1-medVoxel/medFull);

    row.FullP95Ms = percentile95(fullTimes);
    row.VoxelP95Ms = percentile95(voxelTimes);

    row.MedianAgreementPercent = median(agree);
    row.MinimumAgreementPercent = min(agree);

    row.MedianFalseGround = median(falseGround);
    row.MedianMissedGround = median(missedGround);

    row.MaxFalseGround = max(falseGround);
    row.MaxMissedGround = max(missedGround);

    row.MedianFullGround = median(fullCounts);
    row.MedianVoxelGround = median(voxelCounts);

    summaryRows = [summaryRows;row];

    fprintf("\n--- Frame %d ---\n",frameID);

    fprintf("Candidates: %d | ROI: %d | Voxels: %d\n", ...
        row.CandidatePoints,row.ROIPoints,row.VoxelPoints);

    fprintf("Full median: %.4f ms\n",medFull);
    fprintf("Voxel median: %.4f ms\n",medVoxel);
    fprintf("Speed ratio: %.3fx\n",row.SpeedRatio);
    fprintf("Median agreement: %.2f%%\n", ...
        row.MedianAgreementPercent);

    fprintf("Median false-ground: %.1f points\n", ...
        row.MedianFalseGround);

    fprintf("Median missed-ground: %.1f points\n", ...
        row.MedianMissedGround);

end

%% 4. Export results

summaryFile = fullfile(dataDir, ...
    "task19_10c_multiframe_ransac_summary.csv");

samplesFile = fullfile(dataDir, ...
    "task19_10c_multiframe_ransac_samples.csv");

writetable(summaryRows,summaryFile);
writetable(sampleRows,samplesFile);

%% 5. Visualize across frames

fig = figure("Color","w", ...
    "Position",[100 100 1250 850]);

subplot(2,2,1);

plot(frames,summaryRows.FullMedianMs, ...
    "-o","LineWidth",1.5);

hold on;

plot(frames,summaryRows.VoxelMedianMs, ...
    "-s","LineWidth",1.5);

xlabel("Frame index");
ylabel("Median processing time (ms)");
title("Processing Latency Across Frames");

legend("Full RANSAC + SVD", ...
       "Voxel-assisted + SVD","Location","best");

grid on;

subplot(2,2,2);

plot(frames,summaryRows.SpeedRatio, ...
    "-o","LineWidth",1.5);

hold on;
yline(1,"k--","Equal latency");

xlabel("Frame index");
ylabel("Full / voxel latency ratio");
title("Observed Speed Ratio");
grid on;

subplot(2,2,3);

plot(frames,summaryRows.MedianAgreementPercent, ...
    "-o","LineWidth",1.5);

hold on;

plot(frames,summaryRows.MinimumAgreementPercent, ...
    "--s","LineWidth",1.2);

xlabel("Frame index");
ylabel("Classification agreement (%)");
title("Agreement With Full RANSAC");

legend("Median","Minimum", ...
    "Location","best");

ylim([0 100]);
grid on;

subplot(2,2,4);

plot(frames,summaryRows.MedianFalseGround, ...
    "-o","LineWidth",1.5);

hold on;

plot(frames,summaryRows.MedianMissedGround, ...
    "-s","LineWidth",1.5);

xlabel("Frame index");
ylabel("Median disagreeing points");
title("Directional Label Disagreement");

legend("Reference non-ground -> voxel ground", ...
       "Reference ground -> voxel non-ground", ...
       "Location","best");

grid on;

sgtitle("GEMSTAR - Multi-Frame Voxel-RANSAC Evaluation");

graphFile = fullfile(graphDir, ...
    "task19_10c_multiframe_ransac_benchmark.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 6. Final summary

fprintf("\n=== EIGHT-FRAME SUMMARY ===\n");

fprintf("Frames evaluated: %d\n",nFrames);
fprintf("Runs per frame: %d\n",runs);

fprintf("Median speed ratio across frames: %.3fx\n", ...
    median(summaryRows.SpeedRatio));

fprintf("Median agreement across frames: %.2f%%\n", ...
    median(summaryRows.MedianAgreementPercent));

fprintf("Frames where voxel method faster: %d / %d\n", ...
    sum(summaryRows.SpeedRatio>1),nFrames);

fprintf("\n=== TASK 19.10C COMPLETE ===\n");

fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Samples CSV saved: %d\n",isfile(samplesFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

disp(summaryRows(:,{ ...
    'FrameIndex','ROIPoints','VoxelPoints', ...
    'FullMedianMs','VoxelMedianMs', ...
    'SpeedRatio','MedianAgreementPercent', ...
    'MedianFalseGround','MedianMissedGround'}));

fprintf("\nWARNING: Full RANSAC is not ground truth.\n");
fprintf("No obstacle detection accuracy has been established.\n");
fprintf("PC MATLAB timings only, not ARM/FPGA latency.\n");

%% LOCAL FUNCTIONS

function V = makeVoxels(P,voxelSize)

    idx = floor(P./voxelSize);

    [~,~,group] = unique(idx,"rows");

    counts = accumarray(group,1);

    V = zeros(numel(counts),3);

    for j = 1:3
        V(:,j) = accumarray(group,P(:,j))./counts;
    end

end

function [n,d] = ransacRefined(P,iterations,tol,maxTilt)

    N = size(P,1);
    bestCount = -1;

    n = [0;0;1];
    d = -median(P(:,3));

    for iter = 1:iterations

        indexes = randperm(N,3);

        a = P(indexes(1),:);
        b = P(indexes(2),:);
        c = P(indexes(3),:);

        normal = cross(b-a,c-a);

        mag = norm(normal);

        if mag<1e-10
            continue;
        end

        normal = normal(:)/mag;

        if abs(normal(3))<cosd(maxTilt)
            continue;
        end

        if normal(3)<0
            normal = -normal;
        end

        offset = -a*normal;

        count = sum( ...
            abs(P*normal+offset)<=tol);

        if count>bestCount
            bestCount = count;
            n = normal;
            d = offset;
        end

    end

    %% SVD refinement on RANSAC inliers

    inliers = abs(P*n+d)<=tol;

    if sum(inliers)>=3

        X = P(inliers,:);

        center = mean(X,1);

        [~,~,B] = svd(X-center,0);

        normal = B(:,3);

        if normal(3)<0
            normal = -normal;
        end

        % Protect the intended near-horizontal model family.
        if normal(3)>=cosd(maxTilt)
            n = normal;
            d = -center*n;
        end

    end

end

function mask = classify(P,n,d,tol)

    mask = abs(P*n+d)<=tol;

end

function result = percentile95(values)

    values = sort(values(:));
    result = values(ceil(0.95*numel(values)));

end
