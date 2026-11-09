
%% TASK 19.9G - Complete Refined Pipeline Benchmark
% GEMSTAR - Frame 150
% Full RANSAC+SVD vs voxel-assisted RANSAC+SVD
% PC MATLAB benchmark only. No additional toolbox required.

clear;
clc;
close all;

%% 1. Directories
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

file = fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv");

assert(isfile(file),"ROI cloud missing.");

T = readtable(file);
P = double([T.X,T.Y,T.Z]);

assert(size(P,1)==1922,"Unexpected ROI point count.");

%% 2. Experiment configuration
voxelSize = 0.25;
iterations = 1000;
tolerance = 0.08;
maxTilt = 15;
runs = 30;

fullMs = zeros(runs,1);
reducedMs = zeros(runs,1);
voxelBuildMs = zeros(runs,1);
agreementPct = zeros(runs,1);
falseGround = zeros(runs,1);
missedGround = zeros(runs,1);
fullGroundCount = zeros(runs,1);
reducedGroundCount = zeros(runs,1);

fprintf("\n=== TASK 19.9G COMPLETE PIPELINE ===\n");
fprintf("ROI input: %d points\n",size(P,1));

%% 3. Warm-up
rng(42);
[n,d] = ransacRefined(P,iterations,tolerance,maxTilt);
classifyGround(P,n,d,tolerance);

V = voxelCloud(P,voxelSize);
[n,d] = ransacRefined(V,iterations,tolerance,maxTilt);
classifyGround(P,n,d,tolerance);

fprintf("Voxel centroids: %d\n",size(V,1));

assert(size(V,1)==418,"Unexpected voxel point count.");

%% 4. Benchmark
for k = 1:runs

    seed = 7000+k;

    % Full-resolution pipeline
    rng(seed);
    tic;

    [nFull,dFull] = ransacRefined( ...
        P,iterations,tolerance,maxTilt);

    groundFull = classifyGround( ...
        P,nFull,dFull,tolerance);

    fullMs(k) = toc*1000;

    % Voxel-assisted pipeline
    rng(seed);
    tic;

    Vrun = voxelCloud(P,voxelSize);

    voxelBuildMs(k) = toc*1000;

    [nReduced,dReduced] = ransacRefined( ...
        Vrun,iterations,tolerance,maxTilt);

    groundReduced = classifyGround( ...
        P,nReduced,dReduced,tolerance);

    reducedMs(k) = toc*1000;

    % Compare on the same original points
    agreementPct(k) = ...
        100*mean(groundFull==groundReduced);

    falseGround(k) = ...
        sum(~groundFull & groundReduced);

    missedGround(k) = ...
        sum(groundFull & ~groundReduced);

    fullGroundCount(k) = sum(groundFull);
    reducedGroundCount(k) = sum(groundReduced);

end

%% 5. Summary
medFull = median(fullMs);
medReduced = median(reducedMs);

speedRatio = medFull/medReduced;
latencyReduction = 100*(1-medReduced/medFull);

fprintf("\n=== END-TO-END COMPUTATION ===\n");

fprintf("Full median: %.5f ms\n",medFull);
fprintf("Voxel-assisted median: %.5f ms\n",medReduced);

fprintf("Measured speed ratio: %.3fx\n",speedRatio);
fprintf("Latency reduction: %.2f%%\n",latencyReduction);

fprintf("Voxel-build median: %.5f ms\n", ...
    median(voxelBuildMs));

fprintf("\n=== MODEL CONSISTENCY ===\n");

fprintf("Median agreement: %.3f%%\n", ...
    median(agreementPct));

fprintf("Minimum agreement: %.3f%%\n", ...
    min(agreementPct));

fprintf("Median false-ground points: %.1f\n", ...
    median(falseGround));

fprintf("Median missed-ground points: %.1f\n", ...
    median(missedGround));

fprintf("Maximum false-ground points: %d\n", ...
    max(falseGround));

fprintf("Maximum missed-ground points: %d\n", ...
    max(missedGround));

%% 6. Save samples
samples = table();

samples.Run = (1:runs)';
samples.FullPipelineMs = fullMs;
samples.VoxelPipelineMs = reducedMs;
samples.VoxelBuildMs = voxelBuildMs;
samples.AgreementPercent = agreementPct;
samples.FalseGround = falseGround;
samples.MissedGround = missedGround;
samples.FullGroundCount = fullGroundCount;
samples.VoxelGroundCount = reducedGroundCount;

samplesFile = fullfile(dataDir, ...
    "task19_9g_refined_pipeline_samples.csv");

writetable(samples,samplesFile);

%% 7. Save summary
summary = table();

summary.InputPoints = size(P,1);
summary.VoxelPoints = size(V,1);
summary.VoxelSizeM = voxelSize;
summary.Runs = runs;

summary.FullMedianMs = medFull;
summary.VoxelMedianMs = medReduced;
summary.SpeedRatio = speedRatio;
summary.LatencyReductionPercent = latencyReduction;

summary.FullP95Ms = percentile95(fullMs);
summary.VoxelP95Ms = percentile95(reducedMs);

summary.MedianAgreementPercent = median(agreementPct);
summary.MinAgreementPercent = min(agreementPct);

summary.MedianFalseGround = median(falseGround);
summary.MedianMissedGround = median(missedGround);
summary.MaxFalseGround = max(falseGround);
summary.MaxMissedGround = max(missedGround);

summaryFile = fullfile(dataDir, ...
    "task19_9g_refined_pipeline_summary.csv");

writetable(summary,summaryFile);

%% 8. Plots
fig = figure("Color","w", ...
    "Position",[100 100 1100 750]);

subplot(2,2,1);
bar([medFull,medReduced]);
xticks(1:2);
xticklabels(["Full","Voxel-assisted"]);
ylabel("Median latency (ms)");
title("Complete Processing Latency");
grid on;

subplot(2,2,2);
plot(1:runs,fullMs,"LineWidth",1.2);
hold on;
plot(1:runs,reducedMs,"LineWidth",1.2);
xlabel("Run");
ylabel("Latency (ms)");
title("30-Run Timing Comparison");
legend("Full","Voxel-assisted","Location","best");
grid on;

subplot(2,2,3);
plot(1:runs,agreementPct,"LineWidth",1.2);
xlabel("Run");
ylabel("Classification agreement (%)");
title("Agreement on Original ROI");
ylim([0 100]);
grid on;

subplot(2,2,4);
plot(1:runs,falseGround,"LineWidth",1.2);
hold on;
plot(1:runs,missedGround,"LineWidth",1.2);
xlabel("Run");
ylabel("Disagreeing points");
title("Directional Label Disagreement");
legend("False ground","Missed ground", ...
    "Location","best");
grid on;

sgtitle("GEMSTAR - Complete Refined RANSAC Pipeline");

graphFile = fullfile(graphDir, ...
    "task19_9g_refined_pipeline_benchmark.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 9. Finish
fprintf("\n=== TASK 19.9G COMPLETE ===\n");

fprintf("Samples CSV saved: %d\n",isfile(samplesFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

disp(summary);

fprintf("\nTiming excludes OSI decoding, sensor transfer,");
fprintf(" CSV I/O, and downstream clustering.\n");

fprintf("Full RANSAC is a reference, not ground truth.\n");

%% Local functions

function V = voxelCloud(P,sz)

    index = floor(P./sz);
    [~,~,g] = unique(index,"rows");
    counts = accumarray(g,1);

    V = zeros(numel(counts),3);

    for j = 1:3
        V(:,j) = accumarray(g,P(:,j))./counts;
    end

end

function [n,d] = ransacRefined(P,nIter,tol,maxTilt)

    N = size(P,1);

    bestCount = -1;
    n = [0;0;1];
    d = -median(P(:,3));

    for k = 1:nIter

        ind = randperm(N,3);

        a = P(ind(1),:);
        b = P(ind(2),:);
        c = P(ind(3),:);

        normal = cross(b-a,c-a);
        magnitude = norm(normal);

        if magnitude < 1e-10
            continue;
        end

        normal = normal(:)/magnitude;

        if abs(normal(3)) < cosd(maxTilt)
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

    % SVD refinement on RANSAC inliers
    inliers = abs(P*n+d)<=tol;

    if sum(inliers)>=3

        X = P(inliers,:);
        center = mean(X,1);

        [~,~,B] = svd(X-center,0);

        newNormal = B(:,3);

        if newNormal(3)<0
            newNormal = -newNormal;
        end

        n = newNormal;
        d = -center*n;
    end

end

function mask = classifyGround(P,n,d,tol)

    mask = abs(P*n+d)<=tol;

end

function p = percentile95(values)

    x = sort(values(:));
    p = x(ceil(0.95*numel(x)));

end
