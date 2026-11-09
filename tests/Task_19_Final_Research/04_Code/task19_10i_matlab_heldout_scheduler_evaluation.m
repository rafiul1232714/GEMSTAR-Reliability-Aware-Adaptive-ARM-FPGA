
%% TASK 19.10I - Held-Out Scheduler Evaluation
% GEMSTAR fog_mor100
% Frozen rule vs newly calculated offline reference
%
% No scheduler threshold tuning.
% No additional MATLAB toolbox required.
%
% Full RANSAC is a reference, NOT ground truth.
% MATLAB PC timings, NOT ARM/FPGA measurements.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inventoryFile = fullfile(dataDir, ...
    "task19_10h_heldout_frame_inventory.csv");

assert(isfile(inventoryFile),"Held-out inventory missing.");

inventory = readtable(inventoryFile);

frames = [25 75 125 175 225 275 325 425];
voxelSizes = [0.10 0.25 0.50];

%% 2. Fixed experiment parameters

runs = 5;
iterations = 1000;
tolerance = 0.08;
maxTilt = 15;

minAgreement = 95;
maxFalseGroundFraction = 0.02;

% FROZEN scheduler thresholds from Task 19.10G.
lowROILimit = 1600;
highROILimit = 2200;

samples = table();
decisions = table();

fprintf("\n=== TASK 19.10I HELD-OUT EVALUATION ===\n");
fprintf("Scheduler thresholds are FROZEN.\n");

%% 3. Evaluate held-out frames

for fi = 1:numel(frames)

    frameID = frames(fi);

    filename = sprintf( ...
        "task19_10h_frame%03d_candidate_xyz.csv",frameID);

    path = fullfile(cloudDir,filename);

    assert(isfile(path),"Missing frame file: %s",path);

    T = readtable(path);

    Praw = double([T.X,T.Y,T.Z]);

    mask = ...
        Praw(:,1)>=0 & Praw(:,1)<=20 & ...
        Praw(:,2)>=-6 & Praw(:,2)<=6;

    P = Praw(mask,:);

    N = size(P,1);

    assert(N>=10,"Insufficient ROI points.");

    inventoryRow = inventory( ...
        inventory.FrameIndex==frameID,:);

    assert(height(inventoryRow)==1);
    assert(N==inventoryRow.ROIPoints);

    %% Frozen scheduler prediction (input-only)

    if N<lowROILimit || N>highROILimit
        ruleMethod = "Full-reference fallback";
    else
        ruleMethod = "Voxel-assisted";
    end

    %% Prepare voxel clouds and verify sizes

    grids = cell(numel(voxelSizes),1);

    for vi = 1:numel(voxelSizes)
        grids{vi} = makeVoxels(P,voxelSizes(vi));
        assert(size(grids{vi},1)>=10);
    end

    %% Warm-up

    rng(42);
    [n,d] = fitPlane(P,iterations,tolerance,maxTilt);
    groundMask(P,n,d,tolerance);

    for vi = 1:numel(voxelSizes)
        rng(42);
        [n,d] = fitPlane( ...
            grids{vi},iterations,tolerance,maxTilt);
        groundMask(P,n,d,tolerance);
    end

    %% Repeat randomized benchmark

    fullTimes = zeros(runs,1);

    times = zeros(runs,numel(voxelSizes));
    agreements = zeros(runs,numel(voxelSizes));
    falseGround = zeros(runs,numel(voxelSizes));
    missedGround = zeros(runs,numel(voxelSizes));

    for k = 1:runs

        seed = 200000+100*fi+k;

        % Full reference
        rng(seed);
        tic;

        [nf,df] = fitPlane( ...
            P,iterations,tolerance,maxTilt);

        refGround = groundMask(P,nf,df,tolerance);

        fullTimes(k) = toc*1000;

        % Voxel alternatives
        for vi = 1:numel(voxelSizes)

            rng(seed);
            tic;

            V = makeVoxels(P,voxelSizes(vi));

            [nv,dv] = fitPlane( ...
                V,iterations,tolerance,maxTilt);

            voxelGround = groundMask(P,nv,dv,tolerance);

            times(k,vi) = toc*1000;

            agreements(k,vi) = ...
                100*mean(refGround==voxelGround);

            falseGround(k,vi) = ...
                sum(~refGround & voxelGround);

            missedGround(k,vi) = ...
                sum(refGround & ~voxelGround);

            row = table();
            row.FrameIndex = frameID;
            row.Run = k;
            row.VoxelSizeM = voxelSizes(vi);
            row.ROIPoints = N;
            row.VoxelPoints = size(V,1);

            row.FullTimeMs = fullTimes(k);
            row.VoxelTimeMs = times(k,vi);
            row.AgreementPercent = agreements(k,vi);
            row.FalseGround = falseGround(k,vi);
            row.MissedGround = missedGround(k,vi);

            samples = [samples;row];

        end
    end

    %% Newly calculated offline reference

    medianFull = median(fullTimes);
    medianTimes = median(times,1);
    medianAgreements = median(agreements,1);
    medianFalse = median(falseGround,1);

    eligible = ...
        medianAgreements>=minAgreement & ...
        medianFalse<=maxFalseGroundFraction*N;

    if any(eligible)

        choices = find(eligible);
        [~,bestIndex] = min(medianTimes(choices));
        bestVoxelIndex = choices(bestIndex);

        oracleMethod = "Voxel-assisted";
        oracleVoxel = voxelSizes(bestVoxelIndex);
        oracleTime = medianTimes(bestVoxelIndex);

    else

        oracleMethod = "Full-reference fallback";
        oracleVoxel = NaN;
        oracleTime = medianFull;

    end

    %% Evaluate frozen rule
    % The rule always uses 0.25m when voxel-assisted.

    idx025 = find(abs(voxelSizes-0.25)<1e-9);

    if ruleMethod=="Voxel-assisted"
        ruleTime = medianTimes(idx025);
        ruleAgreement = medianAgreements(idx025);
        ruleFalse = medianFalse(idx025);
        rulePassesCriteria = eligible(idx025);
        ruleVoxel = 0.25;
    else
        ruleTime = medianFull;
        ruleAgreement = 100;
        ruleFalse = 0;
        rulePassesCriteria = true;
        ruleVoxel = NaN;
    end

    fallbackMatch = ...
        (ruleMethod=="Full-reference fallback") == ...
        (oracleMethod=="Full-reference fallback");

    %% Save per-frame decision

    decision = table();

    decision.FrameIndex = frameID;
    decision.ROIPoints = N;

    decision.RuleMethod = ruleMethod;
    decision.RuleVoxelM = ruleVoxel;
    decision.RuleMedianMs = ruleTime;

    decision.RuleAgreementPercent = ruleAgreement;
    decision.RuleFalseGround = ruleFalse;
    decision.RulePassesCriteria = rulePassesCriteria;

    decision.OracleMethod = oracleMethod;
    decision.OracleVoxelM = oracleVoxel;
    decision.OracleMedianMs = oracleTime;

    decision.FallbackMatch = fallbackMatch;

    decision.FullMedianMs = medianFull;
    decision.RuleSpeedRatio = medianFull/ruleTime;

    decisions = [decisions;decision];

    fprintf("\nFrame %d | ROI %d\n",frameID,N);
    fprintf("Rule: %s\n",ruleMethod);
    fprintf("Oracle: %s\n",oracleMethod);

    fprintf("Rule agreement: %.2f%%\n",ruleAgreement);
    fprintf("Rule false-ground points: %.1f\n",ruleFalse);
    fprintf("Rule passes criteria: %d\n",rulePassesCriteria);
    fprintf("Fallback decision match: %d\n",fallbackMatch);

end

%% 4. Aggregate held-out results

correct = sum(decisions.FallbackMatch);

missedFallback = sum( ...
    decisions.RuleMethod=="Voxel-assisted" & ...
    decisions.OracleMethod=="Full-reference fallback");

unnecessaryFallback = sum( ...
    decisions.RuleMethod=="Full-reference fallback" & ...
    decisions.OracleMethod=="Voxel-assisted");

unsafeByDiagnosticCriteria = sum( ...
    ~decisions.RulePassesCriteria);

fprintf("\n=== HELD-OUT DECISION RESULTS ===\n");

fprintf("Fallback decision matches: %d / %d\n", ...
    correct,height(decisions));

fprintf("Missed offline fallbacks: %d\n", ...
    missedFallback);

fprintf("Unnecessary full fallbacks: %d\n", ...
    unnecessaryFallback);

fprintf("Rule selections failing diagnostic criteria: %d\n", ...
    unsafeByDiagnosticCriteria);

fprintf("Median rule processing ratio: %.3fx\n", ...
    median(decisions.RuleSpeedRatio));

%% 5. Export CSV files

sampleFile = fullfile(dataDir, ...
    "task19_10i_heldout_benchmark_samples.csv");

decisionFile = fullfile(dataDir, ...
    "task19_10i_heldout_scheduler_decisions.csv");

writetable(samples,sampleFile);
writetable(decisions,decisionFile);

%% 6. Visualization

fig = figure("Color","w", ...
    "Position",[100 100 1200 750]);

subplot(2,2,1);

bar(decisions.FrameIndex, ...
    [double(decisions.RuleMethod=="Full-reference fallback"), ...
     double(decisions.OracleMethod=="Full-reference fallback")], ...
    "grouped");

xlabel("Held-out frame");
ylabel("Full fallback (1 = yes)");
title("Frozen Rule vs Offline Oracle");
legend("Rule","Oracle","Location","best");
ylim([0 1.3]);
grid on;

subplot(2,2,2);

plot(decisions.FrameIndex,decisions.FullMedianMs, ...
    "-o","LineWidth",1.3);
hold on;

plot(decisions.FrameIndex,decisions.RuleMedianMs, ...
    "-s","LineWidth",1.3);

xlabel("Held-out frame");
ylabel("Median processing latency (ms)");
title("Full Reference vs Rule");
legend("Full","Frozen rule","Location","best");
grid on;

subplot(2,2,3);

bar(decisions.FrameIndex, ...
    decisions.RuleAgreementPercent);

hold on;
yline(minAgreement,"r--","95% criterion");

xlabel("Held-out frame");
ylabel("Agreement with reference (%)");
title("Rule Segmentation Consistency");
ylim([0 100]);
grid on;

subplot(2,2,4);

bar(decisions.FrameIndex, ...
    decisions.RuleFalseGround);

hold on;

plot(decisions.FrameIndex, ...
    maxFalseGroundFraction*decisions.ROIPoints, ...
    "r--o","LineWidth",1.2);

xlabel("Held-out frame");
ylabel("Reference non-ground -> rule ground");
title("Diagnostic False-Ground Criterion");
legend("Measured disagreements","2% ROI criterion", ...
    "Location","best");
grid on;

sgtitle("GEMSTAR - Held-Out Frozen Scheduler Evaluation");

graphFile = fullfile(graphDir, ...
    "task19_10i_heldout_scheduler_evaluation.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 7. Final results

fprintf("\n=== TASK 19.10I COMPLETE ===\n");

fprintf("Samples CSV saved: %d\n",isfile(sampleFile));
fprintf("Decision CSV saved: %d\n",isfile(decisionFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

disp(decisions(:,{ ...
    'FrameIndex','ROIPoints','RuleMethod', ...
    'OracleMethod','RulePassesCriteria', ...
    'FallbackMatch','RuleMedianMs'}));

fprintf("\nIMPORTANT:\n");
fprintf("The oracle uses full RANSAC reference agreement.\n");
fprintf("This does not establish obstacle detection safety.\n");
fprintf("Held-out frames are from the same recording.\n");
fprintf("Decision overhead is excluded from these timings.\n");
fprintf("No FPGA performance or energy was measured.\n");

%% LOCAL FUNCTIONS

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

function mask = groundMask(P,n,d,tol)

    mask = abs(P*n+d)<=tol;

end
