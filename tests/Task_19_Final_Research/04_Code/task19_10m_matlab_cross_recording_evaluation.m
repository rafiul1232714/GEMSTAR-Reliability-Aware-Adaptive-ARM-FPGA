
%% TASK 19.10M - Cross-Recording Scheduler Evaluation
% GEMSTAR - 3 separate recordings, 48 sampled frames
%
% Frozen ROI scheduler, no threshold tuning.
% Full RANSAC + SVD vs voxel 0.25 m RANSAC + SVD.
% PC MATLAB only. No additional toolboxes required.
%
% Full RANSAC = reference, NOT semantic ground truth.
% No FPGA power or acceleration measurement.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inventoryFile = fullfile(dataDir, ...
    "task19_10l_cross_recording_inventory.csv");

assert(isfile(inventoryFile),"Task 19.10L inventory missing.");

I = readtable(inventoryFile,"TextType","string");

%% 2. Frozen parameters

runs = 3;
iterations = 1000;
tolerance = 0.08;
maxTilt = 15;
voxelSize = 0.25;

lowROI = 1600;
highROI = 2200;

minAgreement = 95;
maxFalseGroundROI = 0.02;

minPointsForExperiment = 30;

samples = table();
results = table();

fprintf("\n=== TASK 19.10M CROSS-RECORDING EVALUATION ===\n");
fprintf("Recordings: %d\n",numel(unique(I.Scenario)));
fprintf("Total selected frames: %d\n",height(I));

%% 3. Evaluate every extracted frame

for fi = 1:height(I)

    scenario = I.Scenario(fi);
    frameID = I.FrameIndex(fi);

    file = I.CandidateCSV(fi);

    assert(isfile(file),"Missing point cloud: %s",file);

    T = readtable(file);

    points = double([T.X,T.Y,T.Z]);

    roiMask = ...
        points(:,1)>=0 & points(:,1)<=20 & ...
        points(:,2)>=-6 & points(:,2)<=6;

    P = points(roiMask,:);
    N = size(P,1);

    assert(N==I.ROIPoints(fi), ...
        "ROI count mismatch for %s frame %d", ...
        scenario,frameID);

    %% Frozen scheduling rule

    if N<lowROI || N>highROI
        selectedMethod = "Full-reference fallback";
    else
        selectedMethod = "Voxel-assisted";
    end

    result = table();

    result.Scenario = scenario;
    result.FrameIndex = frameID;
    result.CandidatePoints = size(points,1);
    result.ROIPoints = N;
    result.RuleMethod = selectedMethod;

    %% Low-data handling
    % The existing rule still selects Full fallback.
    % We mark processing as not evaluated when very few
    % points are available.

    if N<minPointsForExperiment

        result.EvaluationStatus = "INSUFFICIENT_POINTS";
        result.VoxelPoints = NaN;

        result.FullMedianMs = NaN;
        result.VoxelMedianMs = NaN;
        result.RuleMedianMs = NaN;

        result.SpeedRatio = NaN;
        result.AgreementPercent = NaN;
        result.FalseGroundCount = NaN;
        result.MissedGroundCount = NaN;

        result.VoxelPassesCriteria = false;
        result.RulePassesCriteria = false;

        results = [results;result];

        fprintf( ...
            "%s frame %d | ROI=%d | insufficient points\n", ...
            scenario,frameID,N);

        continue;
    end

    %% Create reduced cloud

    V = makeVoxels(P,voxelSize);

    if size(V,1)<3
        error("Too few voxel points: %s frame %d", ...
            scenario,frameID);
    end

    %% Warm-up

    rng(42);
    [n,d] = fitPlane(P,iterations,tolerance,maxTilt);
    classify(P,n,d,tolerance);

    rng(42);
    [n,d] = fitPlane(V,iterations,tolerance,maxTilt);
    classify(P,n,d,tolerance);

    %% Repeated benchmarks

    fullTimes = zeros(runs,1);
    voxelTimes = zeros(runs,1);

    agreements = zeros(runs,1);
    falseCounts = zeros(runs,1);
    missedCounts = zeros(runs,1);

    for k = 1:runs

        seed = 300000+1000*fi+k;

        %% Full RANSAC + SVD + classify

        rng(seed);
        tic;

        [nf,df] = fitPlane( ...
            P,iterations,tolerance,maxTilt);

        fullGround = classify( ...
            P,nf,df,tolerance);

        fullTimes(k) = toc*1000;

        %% Voxel construction + RANSAC + SVD + classify

        rng(seed);
        tic;

        Vk = makeVoxels(P,voxelSize);

        [nv,dv] = fitPlane( ...
            Vk,iterations,tolerance,maxTilt);

        voxelGround = classify( ...
            P,nv,dv,tolerance);

        voxelTimes(k) = toc*1000;

        %% Reference comparisons

        agreements(k) = ...
            100*mean(fullGround==voxelGround);

        falseCounts(k) = ...
            sum(~fullGround & voxelGround);

        missedCounts(k) = ...
            sum(fullGround & ~voxelGround);

        sample = table();

        sample.Scenario = scenario;
        sample.FrameIndex = frameID;
        sample.Run = k;
        sample.ROIPoints = N;

        sample.FullMs = fullTimes(k);
        sample.VoxelMs = voxelTimes(k);

        sample.AgreementPercent = agreements(k);
        sample.FalseGround = falseCounts(k);
        sample.MissedGround = missedCounts(k);

        samples = [samples;sample];
    end

    %% Evaluate the frozen rule
    % Both models are benchmarked, but the rule's quality
    % is evaluated using only its actual selected method.

    medFull = median(fullTimes);
    medVoxel = median(voxelTimes);

    medAgreement = median(agreements);
    medFalse = median(falseCounts);
    medMissed = median(missedCounts);

    voxelPass = ...
        medAgreement>=minAgreement && ...
        medFalse<=maxFalseGroundROI*N;

    if selectedMethod=="Voxel-assisted"
        ruleTime = medVoxel;
        rulePass = voxelPass;
    else
        ruleTime = medFull;
        rulePass = true;
    end

    result.EvaluationStatus = "EVALUATED";
    result.VoxelPoints = size(V,1);

    result.FullMedianMs = medFull;
    result.VoxelMedianMs = medVoxel;
    result.RuleMedianMs = ruleTime;

    result.SpeedRatio = medFull/medVoxel;

    result.AgreementPercent = medAgreement;
    result.FalseGroundCount = medFalse;
    result.MissedGroundCount = medMissed;

    result.VoxelPassesCriteria = voxelPass;
    result.RulePassesCriteria = rulePass;

    results = [results;result];

    fprintf( ...
        "%s | frame %3d | ROI=%4d | " + ...
        "speed=%.2fx | agreement=%.1f%% | " + ...
        "rulePass=%d\n", ...
        scenario,frameID,N, ...
        result.SpeedRatio,medAgreement,rulePass);

end

%% 4. Save complete results

sampleFile = fullfile(dataDir, ...
    "task19_10m_cross_recording_timing_samples.csv");

resultFile = fullfile(dataDir, ...
    "task19_10m_cross_recording_evaluation.csv");

writetable(samples,sampleFile);
writetable(results,resultFile);

%% 5. Summarize each recording

scenarios = unique(results.Scenario,"stable");

scenarioSummary = table();

for k = 1:numel(scenarios)

    S = results(results.Scenario==scenarios(k),:);

    valid = S.EvaluationStatus=="EVALUATED";
    E = S(valid,:);

    row = table();

    row.Scenario = scenarios(k);
    row.TotalFrames = height(S);
    row.EvaluatedFrames = height(E);
    row.InsufficientDataFrames = sum(~valid);

    row.RuleFullDecisions = sum( ...
        S.RuleMethod=="Full-reference fallback");

    row.RuleVoxelDecisions = sum( ...
        S.RuleMethod=="Voxel-assisted");

    row.VoxelFasterFrames = ...
        sum(E.SpeedRatio>1);

    row.VoxelCriteriaPassFrames = ...
        sum(E.VoxelPassesCriteria);

    row.RuleCriteriaFailFrames = ...
        sum(~E.RulePassesCriteria);

    if ~isempty(E)
        row.MedianVoxelSpeedRatio = median(E.SpeedRatio);
        row.MedianVoxelAgreement = ...
            median(E.AgreementPercent);
        row.MedianRuleLatencyMs = ...
            median(E.RuleMedianMs);
    else
        row.MedianVoxelSpeedRatio = NaN;
        row.MedianVoxelAgreement = NaN;
        row.MedianRuleLatencyMs = NaN;
    end

    scenarioSummary = [scenarioSummary;row];

end

summaryFile = fullfile(dataDir, ...
    "task19_10m_cross_recording_scenario_summary.csv");

writetable(scenarioSummary,summaryFile);

%% 6. Visualization

fig = figure("Color","w", ...
    "Position",[100 100 1250 800]);

subplot(2,2,1);
bar(categorical(scenarioSummary.Scenario), ...
    [scenarioSummary.RuleFullDecisions, ...
     scenarioSummary.RuleVoxelDecisions],"stacked");

ylabel("Frames");
title("Frozen Scheduler Decisions");

legend("Full","Voxel","Location","best");
grid on;

subplot(2,2,2);
bar(categorical(scenarioSummary.Scenario), ...
    [scenarioSummary.VoxelCriteriaPassFrames, ...
     scenarioSummary.RuleCriteriaFailFrames]);

ylabel("Number of evaluated frames");
title("Voxel Eligibility and Rule Failures");

legend("Voxel qualifies","Rule fails", ...
    "Location","best");
grid on;

subplot(2,2,3);
hold on;

for k = 1:numel(scenarios)

    S = results( ...
        results.Scenario==scenarios(k) & ...
        results.EvaluationStatus=="EVALUATED",:);

    plot(S.FrameIndex,S.SpeedRatio, ...
        "-o","LineWidth",1.2, ...
        "DisplayName",scenarios(k));
end

yline(1,"k--","Equal processing time");

xlabel("Frame index");
ylabel("Full / voxel latency ratio");
title("Processing Speed Across Recordings");

legend("Location","best");
grid on;

subplot(2,2,4);
hold on;

for k = 1:numel(scenarios)

    S = results( ...
        results.Scenario==scenarios(k) & ...
        results.EvaluationStatus=="EVALUATED",:);

    plot(S.FrameIndex,S.AgreementPercent, ...
        "-o","LineWidth",1.2, ...
        "DisplayName",scenarios(k));
end

yline(minAgreement,"k--","95% criterion");

xlabel("Frame index");
ylabel("Agreement with full RANSAC (%)");
title("Cross-Recording Classification Consistency");

ylim([0 105]);
legend("Location","best");
grid on;

sgtitle("GEMSTAR - Frozen Scheduler Cross-Recording Evaluation");

graphFile = fullfile(graphDir, ...
    "task19_10m_cross_recording_scheduler_evaluation.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 7. Completion

fprintf("\n=== CROSS-RECORDING SUMMARY ===\n");
disp(scenarioSummary);

fprintf("\n=== TASK 19.10M COMPLETE ===\n");

fprintf("Timing samples CSV saved: %d\n",isfile(sampleFile));
fprintf("Frame evaluation CSV saved: %d\n",isfile(resultFile));
fprintf("Scenario summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nFull RANSAC is only a reference.\n");
fprintf("No obstacle-detection accuracy established.\n");
fprintf("No ARM/FPGA power or latency measured.\n");

%% LOCAL FUNCTIONS

function V = makeVoxels(P,sz)

    index = floor(P./sz);
    [~,~,g] = unique(index,"rows");

    count = accumarray(g,1);

    V = zeros(numel(count),3);

    for c = 1:3
        V(:,c) = accumarray(g,P(:,c))./count;
    end
end

function [n,d] = fitPlane(P,iterations,tol,maxTilt)

    N = size(P,1);

    bestCount = -1;
    n = [0;0;1];
    d = -median(P(:,3));

    for iter = 1:iterations

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

function mask = classify(P,n,d,tol)
    mask = abs(P*n+d)<=tol;
end
