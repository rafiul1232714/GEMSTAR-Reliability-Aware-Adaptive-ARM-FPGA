
%% TASK 19.10T - Complete Observability Monitor Integration
% GEMSTAR - 48 sampled frames / 3 recordings
%
% Full observability monitor + frozen processing rule.
% Monitor should reproduce Task 19.10P states.
%
% Compare:
% Baseline: complete monitor + full RANSAC + SVD
% Policy:   complete monitor + decision + selected processing
%
% Insufficient-data frames skip segmentation in BOTH paths.
% PC MATLAB only. No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inventoryFile = fullfile(dataDir, ...
    "task19_10l_cross_recording_inventory.csv");

monitorFile = fullfile(dataDir, ...
    "task19_10p_observability_monitor_results.csv");

assert(isfile(inventoryFile));
assert(isfile(monitorFile));

I = readtable(inventoryFile,"TextType","string");
H = readtable(monitorFile,"TextType","string");

assert(height(I)==48);
assert(height(H)==48);

%% 2. Frozen parameters
runs = 5;

iterations = 1000;
tolerance = 0.08;
maxTilt = 15;
voxelSize = 0.25;

minimumValidPoints = 30;
lowReturnPercent = 25;
shortRangeM = 5.5;
minimumXYCells = 40;
largeChangePercent = 20;

lowROI = 1600;
highROI = 2200;

samples = table();
results = table();

fprintf("\n=== TASK 19.10T FULL MONITOR INTEGRATION ===\n");

%% 3. Process all frames in scenario/time order

previousScenario = "";
previousValidPercent = NaN;

for fi = 1:height(I)

    scenario = I.Scenario(fi);
    frameID = I.FrameIndex(fi);

    if scenario~=previousScenario
        previousValidPercent = NaN;
        previousScenario = scenario;
    end

    T = readtable(I.CandidateCSV(fi));

    P = double([T.X,T.Y,T.Z]);
    ranges = double(T.RangeM);

    assert(all(isfinite(P(:))));
    assert(all(isfinite(ranges)));

    currentValidPercent = 100*size(P,1)/5271;

    expected = H( ...
        H.Scenario==scenario & H.FrameIndex==frameID,:);

    assert(height(expected)==1, ...
        "Missing Task 19.10P monitor reference.");

    %% Warm up
    [R,state] = assessObservation( ...
        P,ranges,previousValidPercent, ...
        minimumValidPoints,lowReturnPercent, ...
        shortRangeM,minimumXYCells,largeChangePercent);

    if state~="INSUFFICIENT" && size(R,1)>=3
        rng(42);
        [n,d] = fitPlane(R,iterations,tolerance,maxTilt);
        classify(R,n,d,tolerance);

        V = voxelCloud(R,voxelSize);
        if size(V,1)>=3
            rng(42);
            [n,d] = fitPlane(V,iterations,tolerance,maxTilt);
            classify(R,n,d,tolerance);
        end
    end

    %% Compare monitor state against previous research
    expectedState = string(expected.ObservabilityState);
    stateMatches = state==expectedState;

    if ~stateMatches
        error( ...
            "Monitor state mismatch: %s frame %d (%s vs %s)", ...
            scenario,frameID,state,expectedState);
    end

    %% Benchmark both executable processing paths

    baselineTime = zeros(runs,1);
    policyTime = zeros(runs,1);
    monitorTime = zeros(runs,1);

    policyMode = "";

    for k = 1:runs

        seed = 500000+100*fi+k;

        % Baseline: complete monitoring + full processing
        rng(seed);
        tic;

        [Rb,stateB] = assessObservation( ...
            P,ranges,previousValidPercent, ...
            minimumValidPoints,lowReturnPercent, ...
            shortRangeM,minimumXYCells,largeChangePercent);

        if stateB~="INSUFFICIENT"
            [nb,db] = fitPlane( ...
                Rb,iterations,tolerance,maxTilt);
            baselineMask = classify( ...
                Rb,nb,db,tolerance);
        else
            baselineMask = false(size(Rb,1),1);
        end

        baselineTime(k) = toc*1000;

        % Policy: full monitor + scheduling + processing
        rng(seed);
        tic;

        [Ra,stateA] = assessObservation( ...
            P,ranges,previousValidPercent, ...
            minimumValidPoints,lowReturnPercent, ...
            shortRangeM,minimumXYCells,largeChangePercent);

        monitorTime(k) = toc*1000;

        N = size(Ra,1);

        if stateA=="INSUFFICIENT"

            policyMode = "SKIP";
            policyMask = false(N,1);

        elseif N<lowROI || N>highROI

            policyMode = "FULL";

            [np,dp] = fitPlane( ...
                Ra,iterations,tolerance,maxTilt);

            policyMask = classify( ...
                Ra,np,dp,tolerance);

        else

            policyMode = "VOXEL";

            Vp = voxelCloud(Ra,voxelSize);

            [np,dp] = fitPlane( ...
                Vp,iterations,tolerance,maxTilt);

            policyMask = classify( ...
                Ra,np,dp,tolerance);

        end

        policyTime(k) = toc*1000;

        assert(numel(policyMask)==numel(baselineMask));

    end

    %% Record frame results

    row = table();

    row.Scenario = scenario;
    row.FrameIndex = frameID;

    row.ValidPoints = size(P,1);
    row.ROIPoints = size(R,1);

    row.ObservabilityState = state;
    row.MonitorMatchesTask19P = stateMatches;
    row.PolicyMode = policyMode;

    row.MonitorMedianMs = median(monitorTime);
    row.BaselineMedianMs = median(baselineTime);
    row.PolicyMedianMs = median(policyTime);

    row.SpeedRatio = ...
        row.BaselineMedianMs / max(row.PolicyMedianMs,eps);

    results = [results;row];

    %% Raw timing samples

    for k = 1:runs

        sample = table();

        sample.Scenario = scenario;
        sample.FrameIndex = frameID;
        sample.Run = k;

        sample.MonitorMs = monitorTime(k);
        sample.BaselineMs = baselineTime(k);
        sample.PolicyMs = policyTime(k);

        samples = [samples;sample];

    end

    fprintf( ...
        "%s | frame %3d | state=%s | mode=%s | " + ...
        "monitor=%.4f ms | baseline=%.4f | policy=%.4f\n", ...
        scenario,frameID,state,policyMode, ...
        row.MonitorMedianMs, ...
        row.BaselineMedianMs, ...
        row.PolicyMedianMs);

    previousValidPercent = currentValidPercent;

end

%% 4. Save measurements

samplesFile = fullfile(dataDir, ...
    "task19_10t_full_monitor_timing_samples.csv");

resultsFile = fullfile(dataDir, ...
    "task19_10t_full_monitor_pipeline_results.csv");

writetable(samples,samplesFile);
writetable(results,resultsFile);

%% 5. Summary by recording

scenarios = unique(results.Scenario,"stable");

summary = table();

for j = 1:numel(scenarios)

    S = results(results.Scenario==scenarios(j),:);
    processed = S(S.PolicyMode~="SKIP",:);

    row = table();

    row.Scenario = scenarios(j);
    row.Frames = height(S);

    row.FullSelections = sum(S.PolicyMode=="FULL");
    row.VoxelSelections = sum(S.PolicyMode=="VOXEL");
    row.Skips = sum(S.PolicyMode=="SKIP");

    row.MedianMonitorMs = median(S.MonitorMedianMs);
    row.MedianBaselineMs = median(processed.BaselineMedianMs);
    row.MedianPolicyMs = median(processed.PolicyMedianMs);
    row.MedianSpeedRatio = median(processed.SpeedRatio);

    summary = [summary;row];

end

summaryFile = fullfile(dataDir, ...
    "task19_10t_full_monitor_scenario_summary.csv");

writetable(summary,summaryFile);

%% 6. Plot results

fig = figure("Color","w", ...
    "Position",[100 100 1200 760]);

subplot(2,2,1);

bar(categorical(summary.Scenario), ...
    [summary.MedianBaselineMs, ...
     summary.MedianPolicyMs]);

ylabel("Median latency (ms)");
title("Full Monitor: Baseline vs Policy");
legend("Full baseline","Policy","Location","best");
grid on;

subplot(2,2,2);

bar(categorical(summary.Scenario), ...
    summary.MedianMonitorMs);

ylabel("Monitor latency (ms)");
title("Complete Monitor Overhead");
grid on;

subplot(2,2,3);

hold on;

for j = 1:numel(scenarios)

    S = results( ...
        results.Scenario==scenarios(j) & ...
        results.PolicyMode~="SKIP",:);

    plot(S.FrameIndex,S.SpeedRatio, ...
        "-o","LineWidth",1.2, ...
        "DisplayName",scenarios(j));
end

yline(1,"k--","Equal latency");

xlabel("Frame index");
ylabel("Baseline / policy speed ratio");
title("Integrated Processing Tradeoff");
legend("Location","best");
grid on;

subplot(2,2,4);

bar(categorical(summary.Scenario), ...
    [summary.FullSelections, ...
     summary.VoxelSelections, ...
     summary.Skips],"stacked");

ylabel("Frames");
title("Executed Processing Decisions");
legend("Full","Voxel","Skip","Location","best");
grid on;

sgtitle("GEMSTAR - Full Observability Monitor Integration");

graphFile = fullfile(graphDir, ...
    "task19_10t_full_monitor_integration.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 7. Final results

fprintf("\n=== TASK 19.10T SUMMARY ===\n");
disp(summary);

fprintf("Monitor states matching Task 19.10P: %d / %d\n", ...
    sum(results.MonitorMatchesTask19P),height(results));

processed = results(results.PolicyMode~="SKIP",:);

fprintf("Overall processed-frame median speed ratio: %.3fx\n", ...
    median(processed.SpeedRatio));

fprintf("Overall median monitor latency: %.5f ms\n", ...
    median(results.MonitorMedianMs));

fprintf("\n=== TASK 19.10T COMPLETE ===\n");

fprintf("Samples CSV saved: %d\n",isfile(samplesFile));
fprintf("Results CSV saved: %d\n",isfile(resultsFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nNo OSI decoding, CSV I/O or transfer time included.\n");
fprintf("This monitor uses sampled-history changes, not live timing.\n");
fprintf("REVIEW is diagnostic and does not change scheduling.\n");
fprintf("No obstacle accuracy or FPGA power measured.\n");

%% LOCAL FUNCTIONS

function [R,state] = assessObservation( ...
    P,ranges,previousValidPercent, ...
    minValid,lowPercent,shortRange,minCells,maxChange)

    validCount = size(P,1);
    validPercent = 100*validCount/5271;

    keep = P(:,1)>=0 & P(:,1)<=20 & ...
           P(:,2)>=-6 & P(:,2)<=6;

    R = P(keep,:);

    if isempty(ranges)
        medianRange = NaN;
    else
        medianRange = median(ranges);
    end

    if isempty(R)
        cells = 0;
    else
        gridXY = floor(R(:,1:2));
        cells = size(unique(gridXY,"rows"),1);
    end

    insufficient = validCount<minValid;
    lowReturns = validPercent<lowPercent;

    shortReturns = ...
        isfinite(medianRange) && medianRange<shortRange;

    lowCoverage = cells<minCells;

    changed = ...
        isfinite(previousValidPercent) && ...
        abs(validPercent-previousValidPercent)>maxChange;

    if insufficient
        state = "INSUFFICIENT";
    elseif lowReturns || shortReturns || lowCoverage || changed
        state = "REVIEW";
    else
        state = "OBSERVABLE";
    end

end

function V = voxelCloud(P,sz)

    idx = floor(P./sz);
    [~,~,g] = unique(idx,"rows");

    counts = accumarray(g,1);
    V = zeros(numel(counts),3);

    for c = 1:3
        V(:,c) = accumarray(g,P(:,c))./counts;
    end

end

function [n,d] = fitPlane(P,nIter,tol,maxTilt)

    N = size(P,1);

    n = [0;0;1];
    d = -median(P(:,3));

    bestCount = -1;

    for iter = 1:nIter

        idx = randperm(N,3);

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

function mask = classify(P,n,d,tol)
    mask = abs(P*n+d)<=tol;
end
