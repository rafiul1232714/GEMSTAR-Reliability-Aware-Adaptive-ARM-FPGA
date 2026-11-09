
%% TASK 19.11 - Cross-Recording Preprocessing Quality Audit
% Reuses existing Task 19.10M, P and T results.
% No RANSAC rerun. No additional toolbox required.
%
% Checks processing consistency and diagnostic failures.
% Reference agreement is NOT ground-truth accuracy.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

fileM = fullfile(dataDir, ...
    "task19_10m_cross_recording_evaluation.csv");

fileP = fullfile(dataDir, ...
    "task19_10p_observability_monitor_results.csv");

fileT = fullfile(dataDir, ...
    "task19_10t_full_monitor_pipeline_results.csv");

assert(isfile(fileM),"Task 19.10M file missing.");
assert(isfile(fileP),"Task 19.10P file missing.");
assert(isfile(fileT),"Task 19.10T file missing.");

M = readtable(fileM,"TextType","string");
H = readtable(fileP,"TextType","string");
T = readtable(fileT,"TextType","string");

assert(height(M)==48);
assert(height(H)==48);
assert(height(T)==48);

%% 2. Diagnostic thresholds

minAgreement = 95;
maxFalseFraction = 0.02;

audit = table();

fprintf("\n=== TASK 19.11 QUALITY AUDIT ===\n");

%% 3. Inspect every recorded frame

for k = 1:height(M)

    scenario = M.Scenario(k);
    frameID = M.FrameIndex(k);

    hi = find(H.Scenario==scenario & ...
        H.FrameIndex==frameID);

    ti = find(T.Scenario==scenario & ...
        T.FrameIndex==frameID);

    assert(numel(hi)==1);
    assert(numel(ti)==1);

    evaluated = M.EvaluationStatus(k)=="EVALUATED";

    row = table();

    row.Scenario = scenario;
    row.FrameIndex = frameID;
    row.ROIPoints = M.ROIPoints(k);

    row.ObservabilityState = ...
        H.ObservabilityState(hi);

    row.ExecutedMode = T.PolicyMode(ti);

    row.Evaluated = evaluated;

    row.AgreementPercent = M.AgreementPercent(k);
    row.FalseGroundCount = M.FalseGroundCount(k);
    row.MissedGroundCount = M.MissedGroundCount(k);

    row.MaxAllowedFalseGround = ...
        maxFalseFraction*M.ROIPoints(k);

    if evaluated

        row.AgreementPass = ...
            M.AgreementPercent(k)>=minAgreement;

        row.FalseGroundPass = ...
            M.FalseGroundCount(k)<= ...
            row.MaxAllowedFalseGround;

        row.VoxelCriteriaPass = ...
            row.AgreementPass && row.FalseGroundPass;

        row.RuleCriteriaPass = ...
            logical(M.RulePassesCriteria(k));

    else

        row.AgreementPass = false;
        row.FalseGroundPass = false;
        row.VoxelCriteriaPass = false;
        row.RuleCriteriaPass = false;

    end

    row.FullMedianMs = M.FullMedianMs(k);
    row.VoxelMedianMs = M.VoxelMedianMs(k);

    row.IntegratedPolicyMs = T.PolicyMedianMs(ti);
    row.MonitorMs = T.MonitorMedianMs(ti);

    row.RequiresQualityInvestigation = ...
        evaluated && ~row.RuleCriteriaPass;

    audit = [audit;row];

end

%% 4. Find problematic frames

failures = audit(audit.RequiresQualityInvestigation,:);

fprintf("\n=== PROCESSING-POLICY FAILURES ===\n");

if isempty(failures)
    fprintf("No rule failures.\n");
else
    disp(failures(:,{ ...
        'Scenario','FrameIndex','ROIPoints', ...
        'ObservabilityState','ExecutedMode', ...
        'AgreementPercent','FalseGroundCount'}));
end

%% 5. Summarize by recording

scenarios = unique(audit.Scenario,"stable");

summary = table();

for k = 1:numel(scenarios)

    S = audit(audit.Scenario==scenarios(k),:);

    E = S(S.Evaluated,:);

    row = table();

    row.Scenario = scenarios(k);
    row.TotalFrames = height(S);
    row.EvaluatedFrames = height(E);

    row.RuleFailures = sum( ...
        E.RequiresQualityInvestigation);

    row.VoxelCriteriaFailures = sum( ...
        ~E.VoxelCriteriaPass);

    row.ReviewStateFrames = sum( ...
        S.ObservabilityState=="REVIEW");

    row.InsufficientFrames = sum( ...
        S.ObservabilityState=="INSUFFICIENT");

    if ~isempty(E)
        row.MedianAgreementPercent = ...
            median(E.AgreementPercent);
        row.MinAgreementPercent = ...
            min(E.AgreementPercent);
    else
        row.MedianAgreementPercent = NaN;
        row.MinAgreementPercent = NaN;
    end

    summary = [summary;row];

end

fprintf("\n=== QUALITY SUMMARY ===\n");
disp(summary);

%% 6. Export CSVs

auditFile = fullfile(dataDir, ...
    "task19_11_preprocessing_quality_audit.csv");

summaryFile = fullfile(dataDir, ...
    "task19_11_preprocessing_quality_summary.csv");

writetable(audit,auditFile);
writetable(summary,summaryFile);

%% 7. Research graphs

fig = figure("Color","w", ...
    "Position",[100 100 1200 760]);

subplot(2,2,1);

bar(categorical(summary.Scenario), ...
    [summary.RuleFailures, ...
     summary.VoxelCriteriaFailures]);

ylabel("Frame count");
title("Policy vs Voxel Diagnostic Failures");
legend("Selected policy","Voxel configuration", ...
    "Location","best");
grid on;

subplot(2,2,2);

E = audit(audit.Evaluated,:);

scatter(E.ROIPoints,E.AgreementPercent, ...
    70,double(E.RequiresQualityInvestigation), ...
    "filled");

hold on;
yline(minAgreement,"r--","95% criterion");

xlabel("ROI points");
ylabel("Reference agreement (%)");
title("Agreement vs Processing Workload");
grid on;
colorbar;

subplot(2,2,3);

scatter(E.FalseGroundCount,E.MissedGroundCount, ...
    70,double(E.RequiresQualityInvestigation), ...
    "filled");

xlabel("Reference non-ground -> voxel ground");
ylabel("Reference ground -> voxel non-ground");
title("Directional Disagreement");
grid on;
colorbar;

subplot(2,2,4);

bar(categorical(summary.Scenario), ...
    [summary.ReviewStateFrames, ...
     summary.RuleFailures]);

ylabel("Frame count");
title("Observability Warnings vs Policy Failures");
legend("Review state","Policy failure", ...
    "Location","best");
grid on;

sgtitle("GEMSTAR - Preprocessing Quality Audit");

graphFile = fullfile(graphDir, ...
    "task19_11_preprocessing_quality_audit.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 8. Completion

fprintf("\n=== TASK 19.11 COMPLETE ===\n");

fprintf("Total observations: %d\n",height(audit));

fprintf("Evaluated frames: %d\n", ...
    sum(audit.Evaluated));

fprintf("Policy failures: %d\n", ...
    sum(audit.RequiresQualityInvestigation));

fprintf("Quality audit CSV saved: %d\n", ...
    isfile(auditFile));

fprintf("Summary CSV saved: %d\n", ...
    isfile(summaryFile));

fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nIMPORTANT:\n");
fprintf("This is a consistency audit, not ground truth.\n");
fprintf("It does not validate obstacle safety or semantics.\n");
fprintf("No new FPGA latency or energy measurements.\n");
