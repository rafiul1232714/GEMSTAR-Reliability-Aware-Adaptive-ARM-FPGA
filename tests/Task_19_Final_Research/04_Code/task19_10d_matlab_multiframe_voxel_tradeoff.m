
%% TASK 19.10D - Multi-Frame Voxel Configuration Tradeoff
% GEMSTAR fog_mor100
% 8 frames x 3 voxel sizes x 5 repeat runs
%
% RANSAC + SVD refinement.
% Classification performed on original ROI points.
%
% Agreement is with full RANSAC, NOT ground truth.
% Timings represent PC MATLAB, NOT ARM or FPGA.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

frames = [0 50 100 150 200 250 350 450];
voxelSizes = [0.10 0.25 0.50];

runs = 5;
iterations = 1000;
tol = 0.08;
maxTilt = 15;

%% 2. Output containers

samples = table();

fprintf("\n=== TASK 19.10D MULTIFRAME VOXEL TRADEOFF ===\n");

%% 3. Process frames

for fi = 1:numel(frames)

    frameID = frames(fi);

    filename = sprintf( ...
        "task19_10b_frame%03d_candidate_xyz.csv", ...
        frameID);

    inputFile = fullfile(cloudDir,filename);

    assert(isfile(inputFile), ...
        "Missing frame %d CSV",frameID);

    T = readtable(inputFile);

    P = double([T.X,T.Y,T.Z]);

    roiMask = ...
        P(:,1)>=0 & P(:,1)<=20 & ...
        P(:,2)>=-6 & P(:,2)<=6;

    P = P(roiMask,:);

    fprintf("\nFrame %d | ROI points %d\n", ...
        frameID,size(P,1));

    % Cache voxel grids. Their construction will still be
    % included separately in each timed pipeline.
    for runID = 1:runs

        seed = 190000 + 100*fi + runID;

        %% Full RANSAC reference

        rng(seed);
        tic;

        [nRef,dRef] = fitPlane( ...
            P,iterations,tol,maxTilt);

        refMask = abs(P*nRef+dRef)<=tol;

        fullTime = toc*1000;

        %% Compare all voxel sizes

        for vi = 1:numel(voxelSizes)

            sz = voxelSizes(vi);

            rng(seed);

            tic;

            V = makeVoxels(P,sz);

            [nVoxel,dVoxel] = fitPlane( ...
                V,iterations,tol,maxTilt);

            voxelMask = abs(P*nVoxel+dVoxel)<=tol;

            voxelTime = toc*1000;

            agree = 100*mean(refMask==voxelMask);

            falseGround = sum( ...
                ~refMask & voxelMask);

            missedGround = sum( ...
                refMask & ~voxelMask);

            row = table();

            row.FrameIndex = frameID;
            row.Run = runID;
            row.VoxelSizeM = sz;

            row.ROIPoints = size(P,1);
            row.VoxelPoints = size(V,1);

            row.FullTimeMs = fullTime;
            row.VoxelTimeMs = voxelTime;

            row.SpeedRatio = fullTime/voxelTime;
            row.AgreementPercent = agree;

            row.FalseGround = falseGround;
            row.MissedGround = missedGround;

            samples = [samples;row];

        end
    end
end

%% 4. Summarize per frame and voxel size

summary = table();

for fi = 1:numel(frames)

    for vi = 1:numel(voxelSizes)

        mask = ...
            samples.FrameIndex==frames(fi) & ...
            abs(samples.VoxelSizeM-voxelSizes(vi))<1e-9;

        S = samples(mask,:);

        row = table();

        row.FrameIndex = frames(fi);
        row.VoxelSizeM = voxelSizes(vi);

        row.ROIPoints = S.ROIPoints(1);
        row.VoxelPoints = S.VoxelPoints(1);

        row.FullMedianMs = median(S.FullTimeMs);
        row.VoxelMedianMs = median(S.VoxelTimeMs);

        row.SpeedRatio = ...
            row.FullMedianMs/row.VoxelMedianMs;

        row.MedianAgreementPercent = ...
            median(S.AgreementPercent);

        row.MinAgreementPercent = ...
            min(S.AgreementPercent);

        row.MedianFalseGround = ...
            median(S.FalseGround);

        row.MaxFalseGround = ...
            max(S.FalseGround);

        row.MedianMissedGround = ...
            median(S.MissedGround);

        summary = [summary;row];

    end
end

%% 5. Save CSVs

samplesFile = fullfile(dataDir, ...
    "task19_10d_multiframe_voxel_samples.csv");

summaryFile = fullfile(dataDir, ...
    "task19_10d_multiframe_voxel_summary.csv");

writetable(samples,samplesFile);
writetable(summary,summaryFile);

%% 6. Visualize configuration differences

latencyGrid = zeros(numel(frames),numel(voxelSizes));
agreementGrid = zeros(size(latencyGrid));
falseGroundGrid = zeros(size(latencyGrid));

for fi = 1:numel(frames)

    for vi = 1:numel(voxelSizes)

        mask = ...
            summary.FrameIndex==frames(fi) & ...
            abs(summary.VoxelSizeM-voxelSizes(vi))<1e-9;

        latencyGrid(fi,vi) = ...
            summary.VoxelMedianMs(mask);

        agreementGrid(fi,vi) = ...
            summary.MedianAgreementPercent(mask);

        falseGroundGrid(fi,vi) = ...
            summary.MedianFalseGround(mask);

    end
end

fig = figure("Color","w", ...
    "Position",[100 100 1200 800]);

subplot(2,2,1);

imagesc(latencyGrid);
colorbar;

xticks(1:3);
xticklabels(string(voxelSizes));

yticks(1:numel(frames));
yticklabels(string(frames));

xlabel("Voxel size (m)");
ylabel("Frame index");
title("Median Pipeline Latency (ms)");

subplot(2,2,2);

imagesc(agreementGrid,[0 100]);
colorbar;

xticks(1:3);
xticklabels(string(voxelSizes));

yticks(1:numel(frames));
yticklabels(string(frames));

xlabel("Voxel size (m)");
ylabel("Frame index");
title("Median Agreement With Full RANSAC (%)");

subplot(2,2,3);

imagesc(falseGroundGrid);
colorbar;

xticks(1:3);
xticklabels(string(voxelSizes));

yticks(1:numel(frames));
yticklabels(string(frames));

xlabel("Voxel size (m)");
ylabel("Frame index");
title("Median Reference Non-Ground -> Voxel Ground");

subplot(2,2,4);

for vi = 1:numel(voxelSizes)

    mask = abs(summary.VoxelSizeM-voxelSizes(vi))<1e-9;

    plot(summary.FrameIndex(mask), ...
        summary.SpeedRatio(mask), ...
        "-o","LineWidth",1.2);

    hold on;

end

yline(1,"k--","Equal latency");

xlabel("Frame index");
ylabel("Speed ratio (full / voxel)");
title("Speed Ratio By Configuration");

legend("0.10 m","0.25 m","0.50 m", ...
    "Equal latency","Location","best");

grid on;

sgtitle("GEMSTAR - Multi-Frame Voxel Configuration Tradeoff");

graphFile = fullfile(graphDir, ...
    "task19_10d_multiframe_voxel_tradeoff.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 7. Print concise results

fprintf("\n=== PER-FRAME CONFIGURATION SUMMARY ===\n");

disp(summary(:,{ ...
    'FrameIndex','VoxelSizeM','VoxelPoints', ...
    'VoxelMedianMs','SpeedRatio', ...
    'MedianAgreementPercent','MedianFalseGround'}));

fprintf("\n=== TASK 19.10D COMPLETE ===\n");

fprintf("Samples CSV saved: %d\n",isfile(samplesFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nThis experiment does NOT validate an");
fprintf(" adaptive scheduler or obstacle-detection safety.\n");

%% Local functions

function V = makeVoxels(P,sz)

    idx = floor(P./sz);
    [~,~,g] = unique(idx,"rows");

    count = accumarray(g,1);

    V = zeros(numel(count),3);

    for c = 1:3
        V(:,c) = accumarray(g,P(:,c))./count;
    end

end

function [n,d] = fitPlane(P,iterations,tol,maxTilt)

    N = size(P,1);

    n = [0;0;1];
    d = -median(P(:,3));

    bestCount = -1;

    for iter = 1:iterations

        idx = randperm(N,3);

        a = P(idx(1),:);
        b = P(idx(2),:);
        c = P(idx(3),:);

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

        count = sum(abs(P*normal+offset)<=tol);

        if count>bestCount
            bestCount = count;
            n = normal;
            d = offset;
        end

    end

    inliers = abs(P*n+d)<=tol;

    if sum(inliers)>=3

        X = P(inliers,:);
        center = mean(X,1);

        [~,~,B] = svd(X-center,0);

        newNormal = B(:,3);

        if newNormal(3)<0
            newNormal = -newNormal;
        end

        if newNormal(3)>=cosd(maxTilt)

            n = newNormal;
            d = -center*n;

        end
    end
end
