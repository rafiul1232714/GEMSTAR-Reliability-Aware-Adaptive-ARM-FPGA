
%% TASK 19.10Q - Two-Level Policy Integration Audit
% GEMSTAR - 48 cross-recording frames
%
% Level 1: Observability monitor from Task 19.10P
% Level 2: Frozen processing rule from Task 19.10M
%
% No RANSAC rerun, no threshold tuning.
% This is an offline integration analysis.
% Not a validated live scheduler.
% No additional MATLAB toolbox required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

monitorFile = fullfile(dataDir, ...
    "task19_10p_observability_monitor_results.csv");

processingFile = fullfile(dataDir, ...
    "task19_10m_cross_recording_evaluation.csv");

assert(isfile(monitorFile),"Observability results missing.");
assert(isfile(processingFile),"Processing results missing.");

H = readtable(monitorFile,"TextType","string");
P = readtable(processingFile,"TextType","string");

assert(height(H)==48,"Unexpected monitor frame count.");
assert(height(P)==48,"Unexpected processing frame count.");

%% 2. Integrate the two decision layers

report = table();

fprintf("\n=== TASK 19.10Q TWO-LEVEL POLICY AUDIT ===\n");

for k = 1:height(H)

    scenario = H.Scenario(k);
    frameID = H.FrameIndex(k);

    match = ...
        P.Scenario==scenario & ...
        P.FrameIndex==frameID;

    assert(sum(match)==1, ...
        "Missing or duplicate processing result.");

    p = P(match,:);

    state = H.ObservabilityState(k);

    if state=="INSUFFICIENT"

        action = "SKIP_GROUND_MODEL";
        processingMode = "NOT_RUN";
        requiresReview = true;

    elseif state=="REVIEW"

        action = "REVIEW_AND_BASELINE_PROCESSING";
        processingMode = p.RuleMethod;
        requiresReview = true;

    else

        action = "BASELINE_PROCESSING";
        processingMode = p.RuleMethod;
        requiresReview = false;

    end

    row = table();

    row.Scenario = scenario;
    row.FrameIndex = frameID;

    row.ValidPoints = H.ValidPoints(k);
    row.ROIPoints = H.ROIPoints(k);

    row.ObservabilityState = state;
    row.ObservationReasons = H.ReasonCodes(k);

    row.ProposedAction = action;
    row.ProcessingMode = processingMode;
    row.RequiresReview = requiresReview;

    row.EvaluationStatus = p.EvaluationStatus;

    row.BaselineRulePassesCriteria = ...
        p.RulePassesCriteria;

    row.VoxelPassesCriteria = ...
        p.VoxelPassesCriteria;

    row.ReferenceAgreementPercent = ...
        p.AgreementPercent;

    row.ReferenceFalseGroundCount = ...
        p.FalseGroundCount;

    row.FullMedianMs = p.FullMedianMs;
    row.VoxelMedianMs = p.VoxelMedianMs;

    if processingMode=="NOT_RUN"
        row.EstimatedProcessingMs = NaN;
    else
        row.EstimatedProcessingMs = p.RuleMedianMs;
    end

    % This is a previously measured processing median,
    % not a newly timed integrated pipeline.
    report = [report;row];

end

%% 3. Analyze reference-consistency failures by state

states = ["OBSERVABLE";"REVIEW";"INSUFFICIENT"];

summary = table();

for k = 1:numel(states)

    S = report(report.ObservabilityState==states(k),:);

    evaluated = S.EvaluationStatus=="EVALUATED";

    failures = evaluated & ...
        ~S.BaselineRulePassesCriteria;

    row = table();

    row.ObservabilityState = states(k);
    row.Frames = height(S);
    row.EvaluatedFrames = sum(evaluated);

    row.RuleCriteriaFailures = sum(failures);

    row.ProcessingSkipped = sum( ...
        S.ProcessingMode=="NOT_RUN");

    row.FullSelections = sum( ...
        S.ProcessingMode=="Full-reference fallback");

    row.VoxelSelections = sum( ...
        S.ProcessingMode=="Voxel-assisted");

    if any(evaluated)
        row.DiagnosticFailureRatePercent = ...
            100*sum(failures)/sum(evaluated);
    else
        row.DiagnosticFailureRatePercent = NaN;
    end

    summary = [summary;row];

end

%% 4. Print findings

fprintf("\n=== QUALITY FAILURES BY OBSERVABILITY STATE ===\n");
disp(summary);

fprintf("\n=== EVALUATED RULE FAILURES ===\n");

failureRows = report( ...
    report.EvaluationStatus=="EVALUATED" & ...
    ~report.BaselineRulePassesCriteria,:);

if isempty(failureRows)

    fprintf("No diagnostic rule failures found.\n");

else

    disp(failureRows(:,{ ...
        'Scenario','FrameIndex', ...
        'ObservabilityState', ...
        'ProcessingMode', ...
        'ReferenceAgreementPercent', ...
        'ReferenceFalseGroundCount'}));

end

%% 5. Export integrated decisions

reportFile = fullfile(dataDir, ...
    "task19_10q_two_level_policy_decisions.csv");

summaryFile = fullfile(dataDir, ...
    "task19_10q_two_level_policy_summary.csv");

writetable(report,reportFile);
writetable(summary,summaryFile);

%% 6. Plot integrated policy analysis

fig = figure("Color","w", ...
    "Position",[100 100 1200 750]);

subplot(2,2,1);

bar(categorical(summary.ObservabilityState), ...
    [summary.FullSelections, ...
     summary.VoxelSelections, ...
     summary.ProcessingSkipped], ...
    "stacked");

ylabel("Frames");
title("Two-Level Policy Actions");

legend("Full RANSAC","Voxel RANSAC","Skip", ...
    "Location","best");

grid on;

subplot(2,2,2);

bar(categorical(summary.ObservabilityState), ...
    [summary.EvaluatedFrames, ...
     summary.RuleCriteriaFailures]);

ylabel("Frames");
title("Evaluated Frames and Rule Failures");

legend("Evaluated","Diagnostic failures", ...
    "Location","best");

grid on;

subplot(2,2,3);

hold on;

scenarios = unique(report.Scenario,"stable");

for k = 1:numel(scenarios)

    S = report(report.Scenario==scenarios(k),:);

    plot(S.FrameIndex, ...
        S.ValidPoints, ...
        "-o","LineWidth",1.2, ...
        "DisplayName",scenarios(k));

end

xlabel("Frame index");
ylabel("Valid LiDAR points");
title("Input Availability Across Recordings");

legend("Location","best");
grid on;

subplot(2,2,4);

E = report( ...
    report.EvaluationStatus=="EVALUATED",:);

stateNumber = zeros(height(E),1);

stateNumber(E.ObservabilityState=="REVIEW") = 1;
stateNumber(E.ObservabilityState=="INSUFFICIENT") = 2;

scatter(E.ROIPoints, ...
    E.ReferenceAgreementPercent, ...
    70,stateNumber,"filled");

hold on;
yline(95,"r--","Reference agreement criterion");

xlabel("ROI point count");
ylabel("Full vs voxel agreement (%)");

title("Observability State vs Processing Consistency");

cb = colorbar;
cb.Ticks = [0 1 2];
cb.TickLabels = {"Observable","Review","Insufficient"};
clim([-0.5 2.5]);

grid on;

sgtitle("GEMSTAR - Two-Level Sensor/Processing Policy Audit");

graphFile = fullfile(graphDir, ...
    "task19_10q_two_level_policy_audit.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 7. Completion

fprintf("\n=== TASK 19.10Q COMPLETE ===\n");

fprintf("Integrated decisions CSV saved: %d\n", ...
    isfile(reportFile));

fprintf("Summary CSV saved: %d\n", ...
    isfile(summaryFile));

fprintf("Graph saved: %d\n", ...
    isfile(graphFile));

fprintf("\nTotal observations: %d\n",height(report));

fprintf("Processing skipped for insufficient data: %d\n", ...
    sum(report.ProcessingMode=="NOT_RUN"));

fprintf("Observations requiring review: %d\n", ...
    sum(report.RequiresReview));

fprintf("Evaluated rule-quality failures: %d\n", ...
    sum(report.EvaluationStatus=="EVALUATED" & ...
    ~report.BaselineRulePassesCriteria));

fprintf("\nIMPORTANT:\n");
fprintf("REVIEW does not prove sensor failure.\n");
fprintf("OBSERVABLE does not prove sensor accuracy.\n");
fprintf("Reference agreement is not detection accuracy.\n");
fprintf("Processing times are reused from prior PC benchmarks.\n");
fprintf("No actual camera/radar fallback or FPGA scheduling yet.\n");
