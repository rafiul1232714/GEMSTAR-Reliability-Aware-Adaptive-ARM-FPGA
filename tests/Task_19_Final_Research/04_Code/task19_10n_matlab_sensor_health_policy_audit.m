
%% TASK 19.10N - Sensor Health and Scheduler Policy Audit
% Uses saved Task 19.10L and 19.10M results.
% No OSI decoding or RANSAC rerun.
% Diagnostic experiment, not validated sensor health.
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inventoryFile = fullfile(dataDir, ...
    "task19_10l_cross_recording_inventory.csv");

evaluationFile = fullfile(dataDir, ...
    "task19_10m_cross_recording_evaluation.csv");

assert(isfile(inventoryFile),"Inventory CSV missing.");
assert(isfile(evaluationFile),"Evaluation CSV missing.");

I = readtable(inventoryFile,"TextType","string");
E = readtable(evaluationFile,"TextType","string");

assert(height(I)==48,"Expected 48 inventory records.");
assert(height(E)==48,"Expected 48 evaluation records.");

%% 2. Diagnostic operating states
% These are provisional boundaries:
% <30 points: insufficient for our chosen evaluation.
% 30-1599 points: low workload / low-return review.
% >=1600 points: normal/high workload review.
%
% Do NOT interpret these as calibrated fog or
% sensor-failure detection thresholds.

minimumPoints = 30;
lowReturnBoundary = 1600;

report = table();

fprintf("\n=== TASK 19.10N SENSOR HEALTH AUDIT ===\n");

%% 3. Assess each recorded frame

for k = 1:height(E)

    scenario = E.Scenario(k);
    frameID = E.FrameIndex(k);
    N = E.ROIPoints(k);

    matched = ...
        I.Scenario==scenario & ...
        I.FrameIndex==frameID;

    assert(sum(matched)==1, ...
        "Missing or duplicate inventory row.");

    candidateCount = I.CandidatePoints(matched);

    if N < minimumPoints
        state = "INSUFFICIENT_DATA";
        proposedAction = "FLAG_AND_SKIP_GROUND_MODEL";
    elseif N < lowReturnBoundary
        state = "LOW_RETURN_REVIEW";
        proposedAction = "QUALITY_CHECK_BEFORE_SELECTION";
    else
        state = "PROCESSING_AVAILABLE";
        proposedAction = "ALLOW_CONFIG_SELECTION";
    end

    row = table();

    row.Scenario = scenario;
    row.FrameIndex = frameID;

    row.CandidatePoints = candidateCount;
    row.ROIPoints = N;

    row.ValidFractionPercent = ...
        100*candidateCount/5271;

    row.DiagnosticState = state;
    row.ProposedAction = proposedAction;

    row.OriginalRuleMethod = E.RuleMethod(k);
    row.EvaluationStatus = E.EvaluationStatus(k);

    row.VoxelPassesCriteria = E.VoxelPassesCriteria(k);
    row.RulePassesCriteria = E.RulePassesCriteria(k);

    row.FullMedianMs = E.FullMedianMs(k);
    row.VoxelMedianMs = E.VoxelMedianMs(k);

    if isfinite(E.FullMedianMs(k)) && ...
       isfinite(E.VoxelMedianMs(k))

        row.PotentialVoxelLatencyDifferenceMs = ...
            E.FullMedianMs(k)-E.VoxelMedianMs(k);
    else
        row.PotentialVoxelLatencyDifferenceMs = NaN;
    end

    report = [report;row];

end

%% 4. Summary by recording

scenarios = unique(report.Scenario,"stable");

summary = table();

for k = 1:numel(scenarios)

    S = report(report.Scenario==scenarios(k),:);

    evaluated = S.EvaluationStatus=="EVALUATED";

    low = S.DiagnosticState=="LOW_RETURN_REVIEW";
    insufficient = ...
        S.DiagnosticState=="INSUFFICIENT_DATA";

    row = table();

    row.Scenario = scenarios(k);
    row.TotalFrames = height(S);

    row.InsufficientFrames = sum(insufficient);
    row.LowReturnReviewFrames = sum(low);

    row.ProcessingAvailableFrames = sum( ...
        S.DiagnosticState=="PROCESSING_AVAILABLE");

    row.LowReturnVoxelCriteriaPass = sum( ...
        low & evaluated & S.VoxelPassesCriteria);

    row.LowReturnVoxelCriteriaFail = sum( ...
        low & evaluated & ~S.VoxelPassesCriteria);

    row.OriginalRuleFailures = sum( ...
        evaluated & ~S.RulePassesCriteria);

    summary = [summary;row];

end

%% 5. Print findings

fprintf("\n=== RECORDING SUMMARY ===\n");
disp(summary);

fprintf("\n=== LOW RETURN / INSUFFICIENT FRAMES ===\n");

special = report( ...
    report.DiagnosticState~="PROCESSING_AVAILABLE",:);

disp(special(:,{ ...
    'Scenario','FrameIndex','ROIPoints', ...
    'DiagnosticState','VoxelPassesCriteria', ...
    'FullMedianMs','VoxelMedianMs'}));

%% 6. Save output tables

reportFile = fullfile(dataDir, ...
    "task19_10n_sensor_health_policy_audit.csv");

summaryFile = fullfile(dataDir, ...
    "task19_10n_sensor_health_summary.csv");

writetable(report,reportFile);
writetable(summary,summaryFile);

%% 7. Visualizations

fig = figure("Color","w", ...
    "Position",[100 100 1200 760]);

subplot(2,2,1);

bar(categorical(summary.Scenario), ...
    [summary.InsufficientFrames, ...
     summary.LowReturnReviewFrames, ...
     summary.ProcessingAvailableFrames], ...
    "stacked");

ylabel("Frame count");
title("Provisional Sensor-Data States");

legend("Insufficient","Low-return review", ...
    "Processing available","Location","best");
grid on;

subplot(2,2,2);

bar(categorical(summary.Scenario), ...
    [summary.LowReturnVoxelCriteriaPass, ...
     summary.LowReturnVoxelCriteriaFail]);

ylabel("Frames");
title("Voxel Eligibility in Low-Return Frames");

legend("Criteria pass","Criteria fail", ...
    "Location","best");
grid on;

subplot(2,2,3);

hold on;

for k = 1:numel(scenarios)

    S = report(report.Scenario==scenarios(k),:);

    plot(S.FrameIndex,S.ValidFractionPercent, ...
        "-o","LineWidth",1.2, ...
        "DisplayName",scenarios(k));

end

xlabel("Frame index");
ylabel("Valid candidate returns (%)");
title("Recorded LiDAR Return Availability");
legend("Location","best");
grid on;

subplot(2,2,4);

S = report( ...
    report.DiagnosticState=="LOW_RETURN_REVIEW" & ...
    isfinite(report.PotentialVoxelLatencyDifferenceMs),:);

if ~isempty(S)

    scatter(S.ROIPoints, ...
        S.PotentialVoxelLatencyDifferenceMs, ...
        70,double(S.VoxelPassesCriteria),"filled");

    colorbar;
end

hold on;
yline(0,"k--");

xlabel("ROI points");
ylabel("Full - voxel latency (ms)");
title("Low-Return Processing Tradeoff");
grid on;

sgtitle("GEMSTAR - Sensor Health vs Processing Selection");

graphFile = fullfile(graphDir, ...
    "task19_10n_sensor_health_policy_audit.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 8. Completion

fprintf("\n=== TASK 19.10N COMPLETE ===\n");

fprintf("Audit CSV saved: %d\n",isfile(reportFile));
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nIMPORTANT:\n");
fprintf("Low return count is not proof of fog or sensor failure.\n");
fprintf("Voxel eligibility uses full-RANSAC reference agreement.\n");
fprintf("This is an offline audit, not a live scheduler.\n");
fprintf("No ARM/FPGA power or latency measured.\n");
