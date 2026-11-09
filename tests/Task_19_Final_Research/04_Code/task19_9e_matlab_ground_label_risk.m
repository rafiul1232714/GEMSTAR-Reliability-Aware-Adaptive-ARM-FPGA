
%% TASK 19.9E - Ground Label Disagreement Risk
% GEMSTAR frame 150
% Compares 0.25 m voxel-assisted RANSAC to full RANSAC.
% Full RANSAC is a REFERENCE, not ground truth.
% No additional toolboxes required.

clear;
clc;
close all;

%% Paths
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inputFile = fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv");

assert(isfile(inputFile),"ROI CSV not found.");

T = readtable(inputFile);
P = double([T.X,T.Y,T.Z]);

assert(size(P,1)==1922,"Unexpected ROI point count.");

%% Parameters
voxelSize = 0.25;
iterations = 1000;
threshold = 0.08;
maxTilt = 15;
runs = 30;

V = makeVoxelCentroids(P,voxelSize);

assert(size(V,1)==418,"Unexpected voxel count.");

results = table();

% Save the classification of the last run for plotting
lastFull = [];
lastReduced = [];

fprintf("\n=== TASK 19.9E LABEL RISK ANALYSIS ===\n");

%% Repeat using deterministic random seeds

for k = 1:runs

    rng(5000+k);
    [nFull,dFull] = fitGround(P,iterations,threshold,maxTilt);

    rng(5000+k);
    [nReduced,dReduced] = fitGround( ...
        V,iterations,threshold,maxTilt);

    fullGround = abs(P*nFull+dFull)<=threshold;
    reducedGround = abs(P*nReduced+dReduced)<=threshold;

    % Compare reduced model against full-resolution reference.
    bothGround = sum(fullGround & reducedGround);

    bothNonGround = sum(~fullGround & ~reducedGround);

    % Potential risk: reference says non-ground,
    % reduced model says ground.
    falseGround = sum(~fullGround & reducedGround);

    % Reference says ground, reduced model says non-ground.
    missedGround = sum(fullGround & ~reducedGround);

    refNonGround = sum(~fullGround);
    refGround = sum(fullGround);

    row = table();
    row.Run = k;
    row.ReferenceGround = refGround;
    row.ReferenceNonGround = refNonGround;
    row.BothGround = bothGround;
    row.BothNonGround = bothNonGround;
    row.FalseGround = falseGround;
    row.MissedGround = missedGround;

    row.FalseGroundRatePercent = ...
        100*falseGround/max(refNonGround,1);

    row.MissedGroundRatePercent = ...
        100*missedGround/max(refGround,1);

    row.OverallAgreementPercent = ...
        100*(bothGround+bothNonGround)/size(P,1);

    results = [results;row];

    lastFull = fullGround;
    lastReduced = reducedGround;

end

%% Summarize results

fprintf("\n=== MEDIAN OVER %d RUNS ===\n",runs);

fprintf("Agreement: %.3f%%\n", ...
    median(results.OverallAgreementPercent));

fprintf("False-ground points: %.1f\n", ...
    median(results.FalseGround));

fprintf("Missed-ground points: %.1f\n", ...
    median(results.MissedGround));

fprintf("False-ground rate: %.3f%%\n", ...
    median(results.FalseGroundRatePercent));

fprintf("Missed-ground rate: %.3f%%\n", ...
    median(results.MissedGroundRatePercent));

fprintf("\n=== WORST OBSERVED RUN ===\n");

fprintf("Maximum false-ground points: %d\n", ...
    max(results.FalseGround));

fprintf("Maximum missed-ground points: %d\n", ...
    max(results.MissedGround));

%% Save detailed measurements

sampleFile = fullfile(dataDir, ...
    "task19_9e_ground_label_risk_samples.csv");

writetable(results,sampleFile);

summary = table();

summary.VoxelSizeM = voxelSize;
summary.InputPoints = size(P,1);
summary.VoxelPoints = size(V,1);
summary.Runs = runs;

summary.MedianAgreementPercent = ...
    median(results.OverallAgreementPercent);

summary.MedianFalseGround = median(results.FalseGround);
summary.MedianMissedGround = median(results.MissedGround);

summary.MedianFalseGroundRatePercent = ...
    median(results.FalseGroundRatePercent);

summary.MedianMissedGroundRatePercent = ...
    median(results.MissedGroundRatePercent);

summary.MaxFalseGround = max(results.FalseGround);
summary.MaxMissedGround = max(results.MissedGround);

summaryFile = fullfile(dataDir, ...
    "task19_9e_ground_label_risk_summary.csv");

writetable(summary,summaryFile);

%% Visualize disagreement

% Labels:
% 0 = Both say non-ground
% 1 = Both say ground
% 2 = False ground assignment
% 3 = Missed ground assignment

labels = zeros(size(P,1),1);

labels(lastFull & lastReduced) = 1;
labels(~lastFull & lastReduced) = 2;
labels(lastFull & ~lastReduced) = 3;

fig = figure("Color","w", ...
    "Position",[100 100 1100 500]);

subplot(1,2,1);

scatter(P(:,1),P(:,2),15,labels,"filled");

xlabel("Sensor X (m)");
ylabel("Sensor Y (m)");
title("Last Run - Ground Label Agreement");
axis equal;
grid on;

colormap(gca,lines(4));
clim([-0.5 3.5]);

cb = colorbar;
cb.Ticks = 0:3;
cb.TickLabels = { ...
    "Both non-ground", ...
    "Both ground", ...
    "False ground", ...
    "Missed ground"};

subplot(1,2,2);

plot(results.Run,results.FalseGround, ...
    "LineWidth",1.4);

hold on;

plot(results.Run,results.MissedGround, ...
    "LineWidth",1.4);

xlabel("Run");
ylabel("Disagreeing points");
title("Label Disagreement Across Runs");

legend("False ground","Missed ground", ...
    "Location","best");

grid on;

graphFile = fullfile(graphDir, ...
    "task19_9e_ground_label_risk.png");

exportgraphics(fig,graphFile,"Resolution",200);

fprintf("\n=== TASK 19.9E COMPLETE ===\n");
fprintf("Samples CSV saved: %d\n",isfile(sampleFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nThese are disagreements against full RANSAC,");
fprintf("\nnot measured obstacle false-positive or false-negative rates.\n");

%% Local functions

function V = makeVoxelCentroids(P,sz)

    idx = floor(P./sz);
    [~,~,g] = unique(idx,"rows");

    counts = accumarray(g,1);

    V = zeros(numel(counts),3);

    for c = 1:3
        V(:,c) = accumarray(g,P(:,c))./counts;
    end

end

function [bestN,bestD] = fitGround(P,nIter,tol,maxTilt)

    n = size(P,1);
    bestCount = -1;

    bestN = [0;0;1];
    bestD = -median(P(:,3));

    for i = 1:nIter

        ind = randperm(n,3);

        a = P(ind(1),:);
        b = P(ind(2),:);
        c = P(ind(3),:);

        normal = cross(b-a,c-a);
        magnitude = norm(normal);

        if magnitude<1e-10
            continue;
        end

        normal = normal(:)/magnitude;

        if abs(normal(3))<cosd(maxTilt)
            continue;
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
