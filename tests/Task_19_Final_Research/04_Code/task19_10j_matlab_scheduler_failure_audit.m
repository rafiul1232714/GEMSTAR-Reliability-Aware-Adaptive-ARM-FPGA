
%% TASK 19.10J - Held-Out Scheduler Failure Audit
% GEMSTAR - Task 19 research
%
% Reuses existing Task 19.10I measurements.
% No RANSAC rerun. No additional toolbox required.
%
% IMPORTANT:
% The thresholds are diagnostic, not vehicle safety limits.
% Full RANSAC is a reference, not semantic ground truth.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

decisionFile = fullfile(dataDir, ...
    "task19_10i_heldout_scheduler_decisions.csv");

sampleFile = fullfile(dataDir, ...
    "task19_10i_heldout_benchmark_samples.csv");

assert(isfile(decisionFile), "Decision CSV missing.");
assert(isfile(sampleFile), "Benchmark samples missing.");

D = readtable(decisionFile);
S = readtable(sampleFile);

%% 2. Diagnostic thresholds

minAgreement = 95;
maxFalseGroundROI = 0.02;

N = height(D);

audit = table();

fprintf("\n=== TASK 19.10J SCHEDULER FAILURE AUDIT ===\n");

%% 3. Analyze each held-out frame

for k = 1:N

    frameID = D.FrameIndex(k);
    roiCount = D.ROIPoints(k);

    ruleMethod = string(D.RuleMethod(k));
    oracleMethod = string(D.OracleMethod(k));

    allowedFalse = maxFalseGroundROI*roiCount;

    % Rule-specific quality results
    agreementPass = ...
        D.RuleAgreementPercent(k)>=minAgreement;

    falseGroundPass = ...
        D.RuleFalseGround(k)<=allowedFalse;

    qualityPass = agreementPass && falseGroundPass;

    fallbackMatch = ...
        (ruleMethod=="Full-reference fallback") == ...
        (oracleMethod=="Full-reference fallback");

    %% Retrieve per-configuration measured medians

    frameSamples = S(S.FrameIndex==frameID,:);

    sizes = unique(frameSamples.VoxelSizeM);

    eligibleSizes = [];

    for j = 1:numel(sizes)

        V = frameSamples( ...
            abs(frameSamples.VoxelSizeM-sizes(j))<1e-9,:);

        medAgreement = median(V.AgreementPercent);
        medFalse = median(V.FalseGround);

        if medAgreement>=minAgreement && ...
                medFalse<=allowedFalse
            eligibleSizes(end+1) = sizes(j);
        end
    end

    %% Latency comparisons (processing only)

    fullMs = D.FullMedianMs(k);
    ruleMs = D.RuleMedianMs(k);
    oracleMs = D.OracleMedianMs(k);

    %% Store a complete audit row

    row = table();

    row.FrameIndex = frameID;
    row.ROIPoints = roiCount;

    row.RuleMethod = ruleMethod;
    row.RuleVoxelM = D.RuleVoxelM(k);

    row.OracleMethod = oracleMethod;
    row.OracleVoxelM = D.OracleVoxelM(k);

    row.FallbackMatch = fallbackMatch;

    row.RuleAgreementPercent = ...
        D.RuleAgreementPercent(k);

    row.RuleFalseGround = D.RuleFalseGround(k);

    row.MaxAllowedFalseGround = allowedFalse;

    row.AgreementPass = agreementPass;
    row.FalseGroundPass = falseGroundPass;
    row.RuleQualityPass = qualityPass;

    row.NumberOfEligibleVoxelSizes = ...
        numel(eligibleSizes);

    row.EligibleVoxelSizes = ...
        string(mat2str(eligibleSizes));

    row.FullProcessingMs = fullMs;
    row.RuleProcessingMs = ruleMs;
    row.OracleProcessingMs = oracleMs;

    row.RuleMinusOracleMs = ruleMs-oracleMs;

    audit = [audit;row];

    %% Print per-frame findings

    fprintf("\n--- Frame %d ---\n",frameID);

    fprintf("ROI points: %d\n",roiCount);
    fprintf("Rule: %s\n",ruleMethod);
    fprintf("Oracle: %s\n",oracleMethod);

    fprintf("Fallback match: %d\n",fallbackMatch);

    fprintf("Agreement: %.3f%% | Pass: %d\n", ...
        row.RuleAgreementPercent,agreementPass);

    fprintf("False-ground disagreements: %.1f\n", ...
        row.RuleFalseGround);

    fprintf("Allowed false-ground disagreements: %.2f\n", ...
        allowedFalse);

    fprintf("False-ground criterion pass: %d\n", ...
        falseGroundPass);

    fprintf("Both criteria pass: %d\n",qualityPass);

    fprintf("Eligible voxel sizes: %s\n", ...
        row.EligibleVoxelSizes);

end

%% 4. Aggregate findings

matches = sum(audit.FallbackMatch);
qualityFailures = sum(~audit.RuleQualityPass);

agreementFailures = sum(~audit.AgreementPass);
falseGroundFailures = sum(~audit.FalseGroundPass);

missedFallbacks = sum( ...
    audit.RuleMethod=="Voxel-assisted" & ...
    audit.OracleMethod=="Full-reference fallback");

unnecessaryFallbacks = sum( ...
    audit.RuleMethod=="Full-reference fallback" & ...
    audit.OracleMethod=="Voxel-assisted");

fprintf("\n=== AGGREGATE RESULTS ===\n");

fprintf("Fallback matches: %d / %d\n",matches,N);
fprintf("Fallback agreement: %.2f%%\n",100*matches/N);

fprintf("Missed fallbacks: %d\n",missedFallbacks);
fprintf("Unnecessary fallbacks: %d\n",unnecessaryFallbacks);

fprintf("Rule quality failures: %d / %d\n", ...
    qualityFailures,N);

fprintf("Agreement criterion failures: %d\n", ...
    agreementFailures);

fprintf("False-ground criterion failures: %d\n", ...
    falseGroundFailures);

fprintf("Both criteria passed: %d / %d\n", ...
    N-qualityFailures,N);

%% 5. Save detailed audit

auditFile = fullfile(dataDir, ...
    "task19_10j_heldout_scheduler_failure_audit.csv");

writetable(audit,auditFile);

%% 6. Save aggregate summary

summary = table();

summary.HeldoutFrames = N;
summary.FallbackMatches = matches;
summary.FallbackAgreementPercent = 100*matches/N;

summary.MissedFallbacks = missedFallbacks;
summary.UnnecessaryFallbacks = unnecessaryFallbacks;

summary.QualityFailures = qualityFailures;
summary.AgreementFailures = agreementFailures;
summary.FalseGroundFailures = falseGroundFailures;

summary.FramesPassingBothCriteria = N-qualityFailures;

summaryFile = fullfile(dataDir, ...
    "task19_10j_heldout_scheduler_audit_summary.csv");

writetable(summary,summaryFile);

%% 7. Visualize audit results

fig = figure("Color","w", ...
    "Position",[100 100 1200 750]);

subplot(2,2,1);

bar(audit.FrameIndex, ...
    [double(audit.FallbackMatch), ...
     double(audit.RuleQualityPass)], ...
    "grouped");

xlabel("Held-out frame");
ylabel("Pass (1) / Fail (0)");

title("Decision Match vs Actual Rule Eligibility");

legend("Fallback match","Diagnostic quality pass", ...
    "Location","best");

ylim([0 1.3]);
grid on;

subplot(2,2,2);

bar(audit.FrameIndex,audit.RuleAgreementPercent);

hold on;
yline(minAgreement,"r--","95% threshold");

xlabel("Held-out frame");
ylabel("Agreement (%)");

title("Selected Rule: Reference Agreement");

ylim([0 105]);
grid on;

subplot(2,2,3);

bar(audit.FrameIndex,audit.RuleFalseGround);

hold on;

plot(audit.FrameIndex, ...
    audit.MaxAllowedFalseGround, ...
    "r--o","LineWidth",1.3);

xlabel("Held-out frame");
ylabel("Point count");

title("Reference Non-Ground -> Rule Ground");

legend("Observed disagreement","2% ROI limit", ...
    "Location","best");

grid on;

subplot(2,2,4);

bar(audit.FrameIndex,audit.RuleMinusOracleMs);

hold on;
yline(0,"k--","Equal processing latency");

xlabel("Held-out frame");
ylabel("Rule - oracle (ms)");

title("Measured Processing Cost Difference");

grid on;

sgtitle("GEMSTAR - Held-Out Scheduler Failure Audit");

graphFile = fullfile(graphDir, ...
    "task19_10j_heldout_scheduler_failure_audit.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 8. Completion

fprintf("\n=== TASK 19.10J COMPLETE ===\n");

fprintf("Detailed audit CSV: %d\n",isfile(auditFile));
fprintf("Summary CSV: %d\n",isfile(summaryFile));
fprintf("Audit graph: %d\n",isfile(graphFile));

disp(audit(:,{ ...
    'FrameIndex', ...
    'RuleMethod', ...
    'OracleMethod', ...
    'OracleVoxelM', ...
    'FallbackMatch', ...
    'AgreementPass', ...
    'FalseGroundPass', ...
    'RuleQualityPass'}));

fprintf("\nNote: Processing costs exclude decision overhead.\n");
fprintf("Agreement is against full RANSAC, not ground truth.\n");
