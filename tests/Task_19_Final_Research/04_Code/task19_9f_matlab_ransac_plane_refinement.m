
%% TASK 19.9F - RANSAC Plane Refinement and Stability
% GEMSTAR frame 150
% Compare raw and SVD-refined RANSAC models.
% Full resolution versus 0.25 m voxel-assisted estimation.
% All models classify the same 1922 ROI points.
% No additional toolbox required.

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

assert(isfile(inputFile),"ROI CSV missing.");

T = readtable(inputFile);
P = double([T.X,T.Y,T.Z]);

assert(size(P,1)==1922,"Unexpected ROI count.");

%% 2. Parameters
voxelSize = 0.25;
iterations = 1000;
tolerance = 0.08;
maxTilt = 15;
runs = 30;

V = makeVoxels(P,voxelSize);

assert(size(V,1)==418,"Unexpected voxel point count.");

fprintf("\n=== TASK 19.9F RANSAC REFINEMENT ===\n");
fprintf("Original points: %d\n",size(P,1));
fprintf("Voxel points: %d\n",size(V,1));

%% 3. Storage
agreementRaw = zeros(runs,1);
agreementRefined = zeros(runs,1);

falseRaw = zeros(runs,1);
falseRefined = zeros(runs,1);

missedRaw = zeros(runs,1);
missedRefined = zeros(runs,1);

angleRaw = zeros(runs,1);
angleRefined = zeros(runs,1);

offsetRaw = zeros(runs,1);
offsetRefined = zeros(runs,1);

refinedFullMasks = false(size(P,1),runs);
refinedVoxelMasks = false(size(P,1),runs);

timeFullMs = zeros(runs,1);
timeVoxelMs = zeros(runs,1);

%% 4. Repeat comparisons
for k = 1:runs

    seed = 6000+k;

    % Full-resolution model
    rng(seed);
    tic;

    [nf,df] = ransacPlane( ...
        P,iterations,tolerance,maxTilt);

    [nf2,df2] = refinePlane(P,nf,df,tolerance);

    timeFullMs(k) = toc*1000;

    % Reduced-resolution model
    rng(seed);
    tic;

    [nv,dv] = ransacPlane( ...
        V,iterations,tolerance,maxTilt);

    [nv2,dv2] = refinePlane(V,nv,dv,tolerance);

    timeVoxelMs(k) = toc*1000;

    % Classify original points using all four models
    fRaw = classify(P,nf,df,tolerance);
    vRaw = classify(P,nv,dv,tolerance);

    fRef = classify(P,nf2,df2,tolerance);
    vRef = classify(P,nv2,dv2,tolerance);

    % Compare raw and refined outputs separately
    agreementRaw(k) = 100*mean(fRaw==vRaw);
    agreementRefined(k) = 100*mean(fRef==vRef);

    falseRaw(k) = sum(~fRaw & vRaw);
    falseRefined(k) = sum(~fRef & vRef);

    missedRaw(k) = sum(fRaw & ~vRaw);
    missedRefined(k) = sum(fRef & ~vRef);

    % Plane geometry comparison
    angleRaw(k) = acosd( ...
        min(1,max(-1,dot(nf,nv))));

    angleRefined(k) = acosd( ...
        min(1,max(-1,dot(nf2,nv2))));

    offsetRaw(k) = abs(df-dv);
    offsetRefined(k) = abs(df2-dv2);

    refinedFullMasks(:,k) = fRef;
    refinedVoxelMasks(:,k) = vRef;

end

%% 5. Evaluate classification stability
% A point's consensus fraction = fraction of runs
% classifying that point as ground.

fullConsensus = mean(refinedFullMasks,2);
voxelConsensus = mean(refinedVoxelMasks,2);

% A stable point has the same label in every run.
stableFull = sum( ...
    fullConsensus==0 | fullConsensus==1);

stableVoxel = sum( ...
    voxelConsensus==0 | voxelConsensus==1);

fprintf("\n=== AGREEMENT ===\n");

fprintf("Raw median agreement: %.3f%%\n", ...
    median(agreementRaw));

fprintf("Refined median agreement: %.3f%%\n", ...
    median(agreementRefined));

fprintf("\n=== DIRECTIONAL DISAGREEMENTS ===\n");

fprintf("Raw median false ground: %.1f\n", ...
    median(falseRaw));

fprintf("Refined median false ground: %.1f\n", ...
    median(falseRefined));

fprintf("Raw median missed ground: %.1f\n", ...
    median(missedRaw));

fprintf("Refined median missed ground: %.1f\n", ...
    median(missedRefined));

fprintf("\n=== PLANE DIFFERENCES ===\n");

fprintf("Raw median normal angle: %.5f deg\n", ...
    median(angleRaw));

fprintf("Refined median normal angle: %.5f deg\n", ...
    median(angleRefined));

fprintf("Raw median offset difference: %.5f m\n", ...
    median(offsetRaw));

fprintf("Refined median offset difference: %.5f m\n", ...
    median(offsetRefined));

fprintf("\n=== ACROSS-RUN STABILITY ===\n");

fprintf("Stable points, refined full: %d / %d\n", ...
    stableFull,size(P,1));

fprintf("Stable points, refined voxel: %d / %d\n", ...
    stableVoxel,size(P,1));

fprintf("\n=== FITTING LATENCY ===\n");

fprintf("Full RANSAC + refinement median: %.4f ms\n", ...
    median(timeFullMs));

fprintf("Voxel RANSAC + refinement median: %.4f ms\n", ...
    median(timeVoxelMs));

fprintf("Timing excludes voxel construction,");
fprintf(" original-point classification and CSV I/O.\n");

%% 6. Save samples

samples = table();

samples.Run = (1:runs)';
samples.RawAgreementPercent = agreementRaw;
samples.RefinedAgreementPercent = agreementRefined;

samples.RawFalseGround = falseRaw;
samples.RefinedFalseGround = falseRefined;

samples.RawMissedGround = missedRaw;
samples.RefinedMissedGround = missedRefined;

samples.RawAngleDeg = angleRaw;
samples.RefinedAngleDeg = angleRefined;

samples.RawOffsetDifferenceM = offsetRaw;
samples.RefinedOffsetDifferenceM = offsetRefined;

samples.FullFitMs = timeFullMs;
samples.VoxelFitMs = timeVoxelMs;

samplesFile = fullfile(dataDir, ...
    "task19_9f_refinement_samples.csv");

writetable(samples,samplesFile);

%% 7. Save summary

summary = table();

summary.RawMedianAgreementPercent = median(agreementRaw);
summary.RefinedMedianAgreementPercent = median(agreementRefined);

summary.RawMedianFalseGround = median(falseRaw);
summary.RefinedMedianFalseGround = median(falseRefined);

summary.RawMedianMissedGround = median(missedRaw);
summary.RefinedMedianMissedGround = median(missedRefined);

summary.RawMedianAngleDeg = median(angleRaw);
summary.RefinedMedianAngleDeg = median(angleRefined);

summary.StableFullPoints = stableFull;
summary.StableVoxelPoints = stableVoxel;

summary.MedianFullFitMs = median(timeFullMs);
summary.MedianVoxelFitMs = median(timeVoxelMs);

summaryFile = fullfile(dataDir, ...
    "task19_9f_refinement_summary.csv");

writetable(summary,summaryFile);

%% 8. Visualization

fig = figure("Color","w", ...
    "Position",[100 100 1200 760]);

subplot(2,2,1);

plot(1:runs,agreementRaw,"LineWidth",1.2);
hold on;
plot(1:runs,agreementRefined,"LineWidth",1.2);

xlabel("Run");
ylabel("Agreement (%)");
title("Raw vs Refined Classification Agreement");
legend("Raw","Refined","Location","best");
grid on;

subplot(2,2,2);

plot(1:runs,angleRaw,"LineWidth",1.2);
hold on;
plot(1:runs,angleRefined,"LineWidth",1.2);

xlabel("Run");
ylabel("Plane normal angle difference (deg)");
title("Full vs Voxel Model Orientation");
legend("Raw","Refined","Location","best");
grid on;

subplot(2,2,3);

scatter(P(:,1),P(:,2),12,fullConsensus,"filled");

xlabel("Sensor X (m)");
ylabel("Sensor Y (m)");
title("Full-Resolution Ground Consensus");
axis equal;
grid on;
colorbar;
clim([0 1]);

subplot(2,2,4);

scatter(P(:,1),P(:,2),12,voxelConsensus,"filled");

xlabel("Sensor X (m)");
ylabel("Sensor Y (m)");
title("Voxel-Assisted Ground Consensus");
axis equal;
grid on;
colorbar;
clim([0 1]);

sgtitle("GEMSTAR - RANSAC Refinement and Stability");

graphFile = fullfile(graphDir, ...
    "task19_9f_ransac_refinement_stability.png");

exportgraphics(fig,graphFile,"Resolution",200);

fprintf("\n=== TASK 19.9F COMPLETE ===\n");
fprintf("Samples CSV saved: %d\n",isfile(samplesFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

disp(summary);

%% LOCAL FUNCTIONS

function V = makeVoxels(P,sz)

    idx = floor(P./sz);
    [~,~,g] = unique(idx,"rows");
    count = accumarray(g,1);

    V = zeros(numel(count),3);

    for j = 1:3
        V(:,j) = accumarray(g,P(:,j))./count;
    end
end

function [bestN,bestD] = ransacPlane(P,nIter,tol,maxTilt)

    n = size(P,1);
    bestCount = -1;

    bestN = [0;0;1];
    bestD = -median(P(:,3));

    for j = 1:nIter

        idx = randperm(n,3);

        a = P(idx(1),:);
        b = P(idx(2),:);
        c = P(idx(3),:);

        normal = cross(b-a,c-a);
        mag = norm(normal);

        if mag<1e-10
            continue;
        end

        normal = normal(:)/mag;

        if abs(normal(3))<cosd(maxTilt)
            continue;
        end

        % Consistent normal direction
        if normal(3)<0
            normal = -normal;
        end

        d = -a*normal;

        count = sum(abs(P*normal+d)<=tol);

        if count>bestCount
            bestCount = count;
            bestN = normal;
            bestD = d;
        end
    end
end

function [n,d] = refinePlane(P,n0,d0,tol)

    inliers = abs(P*n0+d0)<=tol;

    if sum(inliers)<3
        n = n0;
        d = d0;
        return;
    end

    Q = P(inliers,:);
    centroid = mean(Q,1);

    centered = Q-centroid;

    [~,~,V] = svd(centered,0);

    n = V(:,3);

    if n(3)<0
        n = -n;
    end

    d = -centroid*n;

end

function mask = classify(P,n,d,tol)

    mask = abs(P*n+d)<=tol;

end
