
%% TASK 19.9D - Voxel Size vs RANSAC Latency and Agreement
% GEMSTAR frame 150
% Compare 0.10, 0.25 and 0.50 m voxel grids.
% Both reference and voxel models classify all original ROI points.
% No additional toolbox required.
%
% IMPORTANT:
% Agreement with full RANSAC is NOT ground-truth accuracy.
% Timing applies only to this MATLAB PC implementation.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inputFile = fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv");

assert(isfile(inputFile),"ROI point cloud missing.");

T = readtable(inputFile);
P = double([T.X,T.Y,T.Z]);

assert(size(P,1)==1922,"Unexpected ROI point count.");

%% 2. Experiment settings

voxelSizes = [0.10;0.25;0.50];

iterations = 1000;
distanceThreshold = 0.08;
maxTilt = 15;

runs = 20;

nSizes = numel(voxelSizes);

%% 3. Preallocate samples

fullTimes = zeros(runs,1);
fullCounts = zeros(runs,1);

voxelCounts = zeros(runs,nSizes);
voxelBuildTimes = zeros(runs,nSizes);
reducedRansacTimes = zeros(runs,nSizes);
classificationTimes = zeros(runs,nSizes);
pipelineTimes = zeros(runs,nSizes);

agreement = zeros(runs,nSizes);
changedLabels = zeros(runs,nSizes);
groundCountDifference = zeros(runs,nSizes);

%% 4. Warm-up

rng(42);

[n0,d0] = estimatePlane( ...
    P,iterations,distanceThreshold,maxTilt);

classifyPlane(P,n0,d0,distanceThreshold);

for j = 1:nSizes
    V = voxelCentroids(P,voxelSizes(j));

    [n1,d1] = estimatePlane( ...
        V,iterations,distanceThreshold,maxTilt);

    classifyPlane(P,n1,d1,distanceThreshold);
end

fprintf("\n=== TASK 19.9D VOXEL-SIZE TRADEOFF ===\n");

fprintf("Original ROI points: %d\n",size(P,1));
fprintf("Benchmark runs: %d\n",runs);

%% 5. Benchmark full-resolution reference and voxel methods

for k = 1:runs

    seed = 3000+k;

    %% Full-resolution reference

    rng(seed);

    tic;
    [normalFull,dFull] = estimatePlane( ...
        P,iterations,distanceThreshold,maxTilt);
    fullTimes(k) = toc*1000;

    maskFull = classifyPlane( ...
        P,normalFull,dFull,distanceThreshold);

    fullCounts(k) = sum(maskFull);

    %% Voxel-assisted methods

    for j = 1:nSizes

        rng(seed);

        tic;
        V = voxelCentroids(P,voxelSizes(j));
        voxelBuildTimes(k,j) = toc*1000;

        voxelCounts(k,j) = size(V,1);

        tic;
        [normalVoxel,dVoxel] = estimatePlane( ...
            V,iterations,distanceThreshold,maxTilt);
        reducedRansacTimes(k,j) = toc*1000;

        tic;
        maskVoxel = classifyPlane( ...
            P,normalVoxel,dVoxel,distanceThreshold);
        classificationTimes(k,j) = toc*1000;

        pipelineTimes(k,j) = ...
            voxelBuildTimes(k,j) + ...
            reducedRansacTimes(k,j) + ...
            classificationTimes(k,j);

        agreement(k,j) = ...
            100*mean(maskFull==maskVoxel);

        changedLabels(k,j) = ...
            sum(maskFull~=maskVoxel);

        groundCountDifference(k,j) = ...
            sum(maskVoxel)-sum(maskFull);

    end
end

%% 6. Summary statistics

summary = table();

summary.VoxelSizeM = voxelSizes;

summary.ReducedPointCount = ...
    round(median(voxelCounts,1))';

summary.MedianVoxelBuildMs = ...
    median(voxelBuildTimes,1)';

summary.MedianReducedRANSACMs = ...
    median(reducedRansacTimes,1)';

summary.MedianClassificationMs = ...
    median(classificationTimes,1)';

summary.MedianTotalMs = ...
    median(pipelineTimes,1)';

summary.P95TotalMs = zeros(nSizes,1);

for j = 1:nSizes
    values = sort(pipelineTimes(:,j));
    summary.P95TotalMs(j) = ...
        values(ceil(0.95*runs));
end

summary.MedianAgreementPercent = ...
    median(agreement,1)';

summary.MinAgreementPercent = ...
    min(agreement,[],1)';

summary.MedianChangedLabels = ...
    median(changedLabels,1)';

summary.MedianGroundCountDifference = ...
    median(groundCountDifference,1)';

summary.FullReferenceMedianMs = ...
    repmat(median(fullTimes),nSizes,1);

summary.MedianSpeedRatio = ...
    median(fullTimes) ./ summary.MedianTotalMs;

%% 7. Print findings

fprintf("\n=== FULL-RESOLUTION REFERENCE ===\n");

fprintf("Median latency: %.5f ms\n",median(fullTimes));
fprintf("Ground count range: %d to %d\n", ...
    min(fullCounts),max(fullCounts));

fprintf("\n=== VOXEL-SIZE COMPARISON ===\n");

disp(summary);

for j = 1:nSizes

    fprintf("\nVoxel size: %.2f m\n",voxelSizes(j));

    fprintf("Points: %.0f\n", ...
        summary.ReducedPointCount(j));

    fprintf("Median total latency: %.5f ms\n", ...
        summary.MedianTotalMs(j));

    fprintf("Median speed ratio: %.3fx\n", ...
        summary.MedianSpeedRatio(j));

    fprintf("Median agreement: %.3f%%\n", ...
        summary.MedianAgreementPercent(j));

    fprintf("Minimum agreement: %.3f%%\n", ...
        summary.MinAgreementPercent(j));

    fprintf("Median changed labels: %.1f\n", ...
        summary.MedianChangedLabels(j));

end

%% 8. Save raw benchmark samples

samples = table();

samples.Run = repelem((1:runs)',nSizes);
samples.VoxelSizeM = repmat(voxelSizes,runs,1);

samples.VoxelPoints = reshape(voxelCounts',[],1);

samples.VoxelBuildMs = ...
    reshape(voxelBuildTimes',[],1);

samples.ReducedRANSACMs = ...
    reshape(reducedRansacTimes',[],1);

samples.ClassificationMs = ...
    reshape(classificationTimes',[],1);

samples.TotalMs = ...
    reshape(pipelineTimes',[],1);

samples.AgreementPercent = ...
    reshape(agreement',[],1);

samples.ChangedLabels = ...
    reshape(changedLabels',[],1);

samples.GroundCountDifference = ...
    reshape(groundCountDifference',[],1);

samples.FullReferenceMs = ...
    repelem(fullTimes,nSizes);

samplesFile = fullfile(dataDir, ...
    "task19_9d_voxel_size_benchmark_samples.csv");

summaryFile = fullfile(dataDir, ...
    "task19_9d_voxel_size_tradeoff_summary.csv");

writetable(samples,samplesFile);
writetable(summary,summaryFile);

%% 9. Visualization

fig = figure("Color","w", ...
    "Position",[100 100 1200 750]);

subplot(2,2,1);

bar(summary.MedianTotalMs);
hold on;

yline(median(fullTimes),"r--","Full RANSAC");

xticks(1:nSizes);
xticklabels(string(voxelSizes));

xlabel("Voxel size (m)");
ylabel("Median latency (ms)");
title("Processing Latency");
grid on;

subplot(2,2,2);

bar(summary.MedianAgreementPercent);

xticks(1:nSizes);
xticklabels(string(voxelSizes));

xlabel("Voxel size (m)");
ylabel("Agreement with full RANSAC (%)");
title("Ground Classification Consistency");
ylim([0 100]);
grid on;

subplot(2,2,3);

bar(summary.ReducedPointCount);

xticks(1:nSizes);
xticklabels(string(voxelSizes));

xlabel("Voxel size (m)");
ylabel("Points used for RANSAC");
title("Computational Workload");
grid on;

subplot(2,2,4);

scatter(summary.MedianTotalMs, ...
    summary.MedianAgreementPercent, ...
    100,voxelSizes,"filled");

hold on;

for j = 1:nSizes
    text(summary.MedianTotalMs(j), ...
        summary.MedianAgreementPercent(j), ...
        sprintf("  %.2f m",voxelSizes(j)));
end

xlabel("Median latency (ms)");
ylabel("Agreement with full RANSAC (%)");

title("Latency vs Classification Agreement");
grid on;
colorbar;

sgtitle("GEMSTAR - Voxel-Assisted RANSAC Tradeoff");

graphFile = fullfile(graphDir, ...
    "task19_9d_voxel_size_tradeoff.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 10. Completion

fprintf("\n=== TASK 19.9D COMPLETE ===\n");

fprintf("Samples CSV saved: %d\n",isfile(samplesFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nAgreement is not semantic accuracy.\n");
fprintf("Timing is PC MATLAB execution time only.\n");

%% LOCAL FUNCTIONS

function V = voxelCentroids(P,voxelSize)

    indexes = floor(P./voxelSize);

    [~,~,group] = unique(indexes,"rows");

    counts = accumarray(group,1);

    V = zeros(numel(counts),3);

    for col = 1:3
        V(:,col) = ...
            accumarray(group,P(:,col))./counts;
    end

end

function [bestNormal,bestD] = estimatePlane( ...
    P,nIterations,tolerance,maxTilt)

    n = size(P,1);

    bestCount = -1;
    bestNormal = [0;0;1];
    bestD = -median(P(:,3));

    for iter = 1:nIterations

        idx = randperm(n,3);

        p1 = P(idx(1),:);
        p2 = P(idx(2),:);
        p3 = P(idx(3),:);

        normal = cross(p2-p1,p3-p1);
        magnitude = norm(normal);

        if magnitude<1e-10
            continue;
        end

        normal = normal(:)/magnitude;

        if abs(normal(3))<cosd(maxTilt)
            continue;
        end

        d = -p1*normal;

        count = sum( ...
            abs(P*normal+d)<=tolerance);

        if count>bestCount
            bestCount = count;
            bestNormal = normal;
            bestD = d;
        end

    end

end

function mask = classifyPlane(P,normal,d,tolerance)

    mask = abs(P*normal+d)<=tolerance;

end
