
%% TASK 19.9B - RANSAC and DBSCAN CPU Benchmark
% GEMSTAR frame 150
% MATLAB on Windows PC - not ARM or FPGA measurements.
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

roiFile = fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv");

nonplaneFile = fullfile(cloudDir, ...
    "task19_6a_frame150_ransac_nonplane.csv");

assert(isfile(roiFile),"ROI CSV missing.");
assert(isfile(nonplaneFile),"RANSAC nonplane CSV missing.");

ROI = readtable(roiFile);
NP = readtable(nonplaneFile);

P = double([ROI.X,ROI.Y,ROI.Z]);
Q = double([NP.X,NP.Y,NP.Z]);

assert(size(P,1)==1922,"Unexpected ROI count.");
assert(size(Q,1)==351,"Unexpected nonplane count.");

%% 2. Benchmark parameters

ransacIterations = 1000;
distanceThreshold = 0.08;
maxTiltDegrees = 15;

dbscanEpsilon = 0.60;
dbscanMinPoints = 5;

runs = 30;

ransacTimes = zeros(runs,1);
dbscanTimes = zeros(runs,1);

groundCounts = zeros(runs,1);
clusterCounts = zeros(runs,1);
noiseCounts = zeros(runs,1);

%% 3. Warm up functions

rng(42);
testGround = ransacGround(P, ...
    ransacIterations,distanceThreshold,maxTiltDegrees);

testLabels = simpleDBSCAN(Q, ...
    dbscanEpsilon,dbscanMinPoints);

fprintf("\n=== TASK 19.9B BENCHMARK ===\n");
fprintf("ROI input points: %d\n",size(P,1));
fprintf("Saved nonplane points: %d\n",size(Q,1));
fprintf("Warm-up ground count: %d\n",sum(testGround));
fprintf("Warm-up DBSCAN clusters: %d\n", ...
    max(testLabels));

%% 4. Repeated CPU timing

for k = 1:runs

    % Fixed random seed makes the RANSAC experiment
    % reproducible, with distinct samples per run.
    rng(1000+k);

    tic;
    groundMask = ransacGround(P, ...
        ransacIterations,distanceThreshold,maxTiltDegrees);
    ransacTimes(k) = toc*1000;

    % Benchmark DBSCAN on the SAME saved 351 points.
    % This isolates DBSCAN from RANSAC output variation.

    tic;
    labels = simpleDBSCAN(Q, ...
        dbscanEpsilon,dbscanMinPoints);
    dbscanTimes(k) = toc*1000;

    groundCounts(k) = sum(groundMask);
    clusterCounts(k) = max(labels);
    noiseCounts(k) = sum(labels==-1);

end

%% 5. Timing summary

names = ["RANSAC ground segmentation"; ...
         "DBSCAN clustering"];

timing = [ransacTimes,dbscanTimes];

summary = table();

summary.Operation = names;
summary.Runs = repmat(runs,2,1);
summary.MeanMs = mean(timing,1)';
summary.MedianMs = median(timing,1)';
summary.MinMs = min(timing,[],1)';
summary.MaxMs = max(timing,[],1)';

summary.P95Ms = zeros(2,1);

for k = 1:2
    values = sort(timing(:,k));
    summary.P95Ms(k) = values(ceil(0.95*runs));
end

summary.InputPoints = [size(P,1);size(Q,1)];

fprintf("\n=== TIMING RESULTS (ms) ===\n");
disp(summary);

fprintf("\nRANSAC ground count range: %d to %d\n", ...
    min(groundCounts),max(groundCounts));

fprintf("DBSCAN cluster count range: %d to %d\n", ...
    min(clusterCounts),max(clusterCounts));

fprintf("DBSCAN noise count range: %d to %d\n", ...
    min(noiseCounts),max(noiseCounts));

%% 6. Save benchmark CSVs

samples = table();

samples.Run = (1:runs)';
samples.RANSAC_Ms = ransacTimes;
samples.DBSCAN_Ms = dbscanTimes;
samples.RANSACGroundCount = groundCounts;
samples.DBSCANClusterCount = clusterCounts;
samples.DBSCANNoiseCount = noiseCounts;

samplesFile = fullfile(dataDir, ...
    "task19_9b_ransac_dbscan_timing_samples.csv");

summaryFile = fullfile(dataDir, ...
    "task19_9b_ransac_dbscan_timing_summary.csv");

writetable(samples,samplesFile);
writetable(summary,summaryFile);

%% 7. Plot benchmark results

fig = figure("Color","w", ...
    "Position",[100 100 1150 470]);

subplot(1,2,1);

bar(summary.MedianMs);

xticks(1:2);
xticklabels(names);
xtickangle(15);

ylabel("Median time (ms)");
title("RANSAC and DBSCAN - CPU Latency");
grid on;

subplot(1,2,2);

plot(samples.Run,samples.RANSAC_Ms, ...
    "LineWidth",1.2);
hold on;

plot(samples.Run,samples.DBSCAN_Ms, ...
    "LineWidth",1.2);

xlabel("Benchmark run");
ylabel("Execution time (ms)");
title("Execution Time Variation");

legend("RANSAC","DBSCAN","Location","best");
grid on;

graphFile = fullfile(graphDir, ...
    "task19_9b_ransac_dbscan_latency.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 8. Completion

fprintf("\n=== TASK 19.9B COMPLETE ===\n");

fprintf("Timing samples saved: %d\n",isfile(samplesFile));
fprintf("Timing summary saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nBenchmark runs: %d\n",runs);
fprintf("PC MATLAB timing only; no FPGA power measured.\n");

%% LOCAL FUNCTIONS

function bestMask = ransacGround(P,nIterations,tolerance,maxTilt)

    n = size(P,1);

    bestMask = false(n,1);
    bestCount = 0;

    minNz = cosd(maxTilt);

    for iter = 1:nIterations

        idx = randperm(n,3);

        a = P(idx(1),:);
        b = P(idx(2),:);
        c = P(idx(3),:);

        normal = cross(b-a,c-a);
        magnitude = norm(normal);

        if magnitude < 1e-10
            continue;
        end

        normal = normal/magnitude;

        % Reject strongly tilted plane hypotheses.
        if abs(normal(3)) < minNz
            continue;
        end

        distances = abs((P-a)*normal');

        mask = distances <= tolerance;
        count = sum(mask);

        if count > bestCount
            bestCount = count;
            bestMask = mask;
        end
    end
end

function labels = simpleDBSCAN(P,epsilon,minPts)
    % Basic deterministic O(N^2) DBSCAN for small clouds.
    % Includes the query point itself in MinPts.

    n = size(P,1);

    labels = zeros(n,1);
    visited = false(n,1);

    % Precompute pairwise neighborhoods.
    % This allocation is inside the timed function.

    distanceSquared = ...
        (P(:,1)-P(:,1)').^2 + ...
        (P(:,2)-P(:,2)').^2 + ...
        (P(:,3)-P(:,3)').^2;

    neighbors = distanceSquared <= epsilon^2;

    clusterID = 0;

    for i = 1:n

        if visited(i)
            continue;
        end

        visited(i) = true;

        seeds = find(neighbors(i,:));

        if numel(seeds) < minPts
            labels(i) = -1;
            continue;
        end

        clusterID = clusterID+1;
        labels(i) = clusterID;

        % Maintain a set of candidate point indices.
        queue = seeds(:);
        inQueue = false(n,1);
        inQueue(queue) = true;

        head = 1;

        while head <= numel(queue)

            j = queue(head);
            head = head+1;

            if ~visited(j)

                visited(j) = true;

                neighborJ = find(neighbors(j,:));

                if numel(neighborJ) >= minPts

                    additions = neighborJ(~inQueue(neighborJ));

                    queue = [queue;additions(:)];
                    inQueue(additions) = true;

                end
            end

            % Previously classified noise can become
            % a border point of the current cluster.
            if labels(j) <= 0
                labels(j) = clusterID;
            end
        end
    end
end
