
%% TASK 19.9C - Voxel-Assisted RANSAC Tradeoff
% GEMSTAR frame 150
% Compare full-resolution and voxel-assisted plane estimation.
% Evaluate both models on the SAME original ROI points.
% PC MATLAB timing only. No additional toolbox required.

clear;
clc;
close all;

%% Paths
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

roiFile = fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv");

assert(isfile(roiFile),"ROI CSV missing.");

T = readtable(roiFile);
P = double([T.X,T.Y,T.Z]);

assert(size(P,1)==1922,"Unexpected ROI point count.");

%% Parameters
voxelSize = 0.25;
iterations = 1000;
tolerance = 0.08;
maxTilt = 15;
runs = 30;

%% Voxel cloud
V = makeVoxels(P,voxelSize);

fprintf("\n=== TASK 19.9C VOXEL-RANSAC TRADEOFF ===\n");
fprintf("Full ROI points: %d\n",size(P,1));
fprintf("Voxel centroids: %d\n",size(V,1));

assert(size(V,1)==418, ...
    "Voxel count differs from Task 19.5A.");

%% Warm-up
rng(42);
[~,~] = estimateGroundPlane(P,iterations,tolerance,maxTilt);
[~,~] = estimateGroundPlane(V,iterations,tolerance,maxTilt);

%% Benchmark
fullTimes = zeros(runs,1);
voxelTimes = zeros(runs,1);
voxelBuildTimes = zeros(runs,1);
classifyTimes = zeros(runs,1);

fullGroundCounts = zeros(runs,1);
voxelGroundCounts = zeros(runs,1);
agreementPct = zeros(runs,1);
disagreementCounts = zeros(runs,1);

lastFullMask = [];
lastVoxelMask = [];

for k = 1:runs

    % Deterministic, repeatable random stream per run.
    rng(2000+k);

    tic;
    [normalA,dA] = estimateGroundPlane( ...
        P,iterations,tolerance,maxTilt);
    fullTimes(k) = toc*1000;

    % Use the same seed for reproducibility.
    rng(2000+k);

    tic;
    Vk = makeVoxels(P,voxelSize);
    voxelBuildTimes(k) = toc*1000;

    tic;
    [normalB,dB] = estimateGroundPlane( ...
        Vk,iterations,tolerance,maxTilt);
    voxelTimes(k) = toc*1000;

    % Evaluate BOTH models on the ORIGINAL 1922 points.
    tic;
    maskA = abs(P*normalA+dA) <= tolerance;
    maskB = abs(P*normalB+dB) <= tolerance;
    classifyTimes(k) = toc*1000;

    fullGroundCounts(k) = sum(maskA);
    voxelGroundCounts(k) = sum(maskB);

    agreementPct(k) = 100*mean(maskA==maskB);
    disagreementCounts(k) = sum(maskA~=maskB);

    lastFullMask = maskA;
    lastVoxelMask = maskB;

end

%% Summaries
fullTotal = fullTimes;
voxelTotal = voxelBuildTimes+voxelTimes+classifyTimes;

summary = table();

summary.Method = [ ...
    "Full-resolution RANSAC"; ...
    "Voxel-assisted RANSAC"];

summary.InputPoints = [size(P,1);size(V,1)];
summary.Runs = [runs;runs];

summary.MedianTimeMs = [ ...
    median(fullTotal);median(voxelTotal)];

summary.MeanTimeMs = [ ...
    mean(fullTotal);mean(voxelTotal)];

summary.P95TimeMs = [ ...
    percentile95(fullTotal);percentile95(voxelTotal)];

summary.MedianGroundCountOnOriginalROI = [ ...
    median(fullGroundCounts);median(voxelGroundCounts)];

fprintf("\n=== METHOD COMPARISON ===\n");
disp(summary);

fprintf("\n=== CLASSIFICATION AGREEMENT ===\n");
fprintf("Median agreement: %.2f%%\n",median(agreementPct));
fprintf("Minimum agreement: %.2f%%\n",min(agreementPct));
fprintf("Median changed labels: %.0f points\n", ...
    median(disagreementCounts));

fprintf("\n=== LATENCY COMPARISON ===\n");
fprintf("Full median: %.5f ms\n",median(fullTotal));
fprintf("Voxel-assisted median: %.5f ms\n",median(voxelTotal));

if median(voxelTotal)>0
    fprintf("Measured median ratio A/B: %.3fx\n", ...
        median(fullTotal)/median(voxelTotal));
end

fprintf("Voxel construction median: %.5f ms\n", ...
    median(voxelBuildTimes));
fprintf("Reduced RANSAC median: %.5f ms\n", ...
    median(voxelTimes));
fprintf("Original ROI classification median: %.5f ms\n", ...
    median(classifyTimes));

%% Save samples
samples = table();

samples.Run = (1:runs)';
samples.FullRANSAC_Ms = fullTimes;
samples.VoxelBuild_Ms = voxelBuildTimes;
samples.ReducedRANSAC_Ms = voxelTimes;
samples.Classification_Ms = classifyTimes;
samples.VoxelPipelineTotal_Ms = voxelTotal;

samples.FullGroundCount = fullGroundCounts;
samples.VoxelModelGroundCount = voxelGroundCounts;
samples.AgreementPercent = agreementPct;
samples.DisagreementCount = disagreementCounts;

samplesFile = fullfile(dataDir, ...
    "task19_9c_voxel_ransac_samples.csv");

summaryFile = fullfile(dataDir, ...
    "task19_9c_voxel_ransac_summary.csv");

writetable(samples,samplesFile);
writetable(summary,summaryFile);

%% Visualization
fig = figure("Color","w","Position",[100 100 1150 760]);

subplot(2,2,1);
bar(summary.MedianTimeMs);
xticks(1:2);
xticklabels(["Full RANSAC","Voxel-assisted"]);
ylabel("Median latency (ms)");
title("Total Pipeline Latency");
grid on;

subplot(2,2,2);
plot(1:runs,fullTotal,"LineWidth",1.2);
hold on;
plot(1:runs,voxelTotal,"LineWidth",1.2);
xlabel("Run");
ylabel("Latency (ms)");
title("Latency Across Runs");
legend("Full","Voxel-assisted","Location","best");
grid on;

subplot(2,2,3);
scatter(P(:,1),P(:,2), ...
    10,double(lastFullMask),"filled");
xlabel("Sensor X (m)");
ylabel("Sensor Y (m)");
title("Full RANSAC - Last Run");
axis equal;
grid on;

subplot(2,2,4);
scatter(P(:,1),P(:,2), ...
    10,double(lastVoxelMask),"filled");
xlabel("Sensor X (m)");
ylabel("Sensor Y (m)");
title("Voxel Model on Original ROI");
axis equal;
grid on;

graphFile = fullfile(graphDir, ...
    "task19_9c_voxel_ransac_tradeoff.png");

exportgraphics(fig,graphFile,"Resolution",200);

fprintf("\n=== TASK 19.9C COMPLETE ===\n");
fprintf("Samples CSV saved: %d\n",isfile(samplesFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nAgreement compares two algorithms, not");
fprintf(" detection accuracy against ground truth.\n");

%% Local functions

function V = makeVoxels(P,voxelSize)

    indexes = floor(P./voxelSize);
    [~,~,g] = unique(indexes,"rows");

    counts = accumarray(g,1);
    V = zeros(numel(counts),3);

    for col = 1:3
        V(:,col) = accumarray(g,P(:,col))./counts;
    end

end

function [bestNormal,bestD] = estimateGroundPlane( ...
    P,nIterations,tol,maxTilt)

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

        count = sum(abs(P*normal+d)<=tol);

        if count>bestCount
            bestCount = count;
            bestNormal = normal;
            bestD = d;
        end

    end

end

function p = percentile95(values)

    sorted = sort(values(:));
    p = sorted(ceil(0.95*numel(sorted)));

end
