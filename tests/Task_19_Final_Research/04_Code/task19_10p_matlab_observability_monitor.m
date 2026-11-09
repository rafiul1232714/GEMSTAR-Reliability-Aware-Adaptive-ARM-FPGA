
%% TASK 19.10P - Multi-Feature LiDAR Observability Monitor
% GEMSTAR Task 19
% Uses existing Task 19.10O feature CSV.
%
% Offline diagnostic prototype.
% No ground-truth health labels.
% No RANSAC rerun. No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inputFile = fullfile(dataDir, ...
    "task19_10o_lidar_observability_features.csv");

assert(isfile(inputFile),"Task 19.10O features missing.");

F = readtable(inputFile,"TextType","string");

%% 2. Provisional diagnostic thresholds
% These are engineering test parameters, NOT
% calibrated sensor reliability boundaries.
%
% Do not change them after seeing results and then
% claim an independent validation on these frames.

minimumValidPoints = 30;
lowValidReturnPercent = 25;
shortMedianRangeM = 5.5;
minimumOccupiedXYCells = 40;

% Temporal change uses sampled observations only.
largeReturnChangePercentPoints = 20;

%% 3. Classify each observation

N = height(F);

states = strings(N,1);
reasonCodes = strings(N,1);

insufficientFlag = false(N,1);
lowReturnFlag = false(N,1);
shortRangeFlag = false(N,1);
lowCoverageFlag = false(N,1);
temporalChangeFlag = false(N,1);

fprintf("\n=== TASK 19.10P OBSERVABILITY MONITOR ===\n");

for k = 1:N

    insufficientFlag(k) = ...
        F.ValidPoints(k)<minimumValidPoints;

    lowReturnFlag(k) = ...
        F.ValidReturnPercent(k)<lowValidReturnPercent;

    shortRangeFlag(k) = ...
        isfinite(F.MedianRangeM(k)) && ...
        F.MedianRangeM(k)<shortMedianRangeM;

    lowCoverageFlag(k) = ...
        F.OccupiedXYCells(k)<minimumOccupiedXYCells;

    temporalChangeFlag(k) = ...
        isfinite(F.ValidPercentChange(k)) && ...
        abs(F.ValidPercentChange(k)) > ...
        largeReturnChangePercentPoints;

    reasons = strings(0,1);

    if insufficientFlag(k)
        reasons(end+1) = "TOO_FEW_RETURNS";
    end

    if lowReturnFlag(k)
        reasons(end+1) = "LOW_RETURN_FRACTION";
    end

    if shortRangeFlag(k)
        reasons(end+1) = "SHORT_MEDIAN_RANGE";
    end

    if lowCoverageFlag(k)
        reasons(end+1) = "LOW_SPATIAL_COVERAGE";
    end

    if temporalChangeFlag(k)
        reasons(end+1) = "LARGE_SAMPLED_CHANGE";
    end

    if insufficientFlag(k)

        states(k) = "INSUFFICIENT";

    elseif ~isempty(reasons)

        states(k) = "REVIEW";

    else

        states(k) = "OBSERVABLE";

    end

    if isempty(reasons)
        reasonCodes(k) = "NONE";
    else
        reasonCodes(k) = strjoin(reasons,";");
    end

    fprintf( ...
        "%s | frame %3d | valid=%4d | state=%s | %s\n", ...
        F.Scenario(k), ...
        F.FrameIndex(k), ...
        F.ValidPoints(k), ...
        states(k), ...
        reasonCodes(k));

end

%% 4. Save diagnostic results

report = F;

report.ObservabilityState = states;
report.ReasonCodes = reasonCodes;

report.InsufficientFlag = insufficientFlag;
report.LowReturnFlag = lowReturnFlag;
report.ShortRangeFlag = shortRangeFlag;
report.LowCoverageFlag = lowCoverageFlag;
report.TemporalChangeFlag = temporalChangeFlag;

reportFile = fullfile(dataDir, ...
    "task19_10p_observability_monitor_results.csv");

writetable(report,reportFile);

%% 5. Summarize by recording

scenarios = unique(report.Scenario,"stable");

summary = table();

for k = 1:numel(scenarios)

    S = report(report.Scenario==scenarios(k),:);

    row = table();

    row.Scenario = scenarios(k);
    row.Frames = height(S);

    row.Insufficient = sum( ...
        S.ObservabilityState=="INSUFFICIENT");

    row.Review = sum( ...
        S.ObservabilityState=="REVIEW");

    row.Observable = sum( ...
        S.ObservabilityState=="OBSERVABLE");

    row.LowReturnFlags = sum(S.LowReturnFlag);
    row.ShortRangeFlags = sum(S.ShortRangeFlag);
    row.LowCoverageFlags = sum(S.LowCoverageFlag);
    row.TemporalChangeFlags = sum(S.TemporalChangeFlag);

    summary = [summary;row];

end

summaryFile = fullfile(dataDir, ...
    "task19_10p_observability_monitor_summary.csv");

writetable(summary,summaryFile);

fprintf("\n=== RECORDING SUMMARY ===\n");
disp(summary);

%% 6. Visualize results

fig = figure("Color","w", ...
    "Position",[100 100 1200 780]);

subplot(2,2,1);

bar(categorical(summary.Scenario), ...
    [summary.Insufficient, ...
     summary.Review, ...
     summary.Observable], ...
    "stacked");

ylabel("Number of sampled frames");
title("Provisional Observability States");
legend("Insufficient","Review","Observable", ...
    "Location","best");
grid on;

subplot(2,2,2);

bar(categorical(summary.Scenario), ...
    [summary.LowReturnFlags, ...
     summary.ShortRangeFlags, ...
     summary.LowCoverageFlags, ...
     summary.TemporalChangeFlags], ...
    "grouped");

ylabel("Flagged frames");
title("Diagnostic Warning Reasons");

legend("Low returns","Short range", ...
       "Low coverage","Sampled change", ...
       "Location","best");

grid on;

subplot(2,2,3);

hold on;

for k = 1:numel(scenarios)

    S = report(report.Scenario==scenarios(k),:);

    plot(S.FrameIndex,S.ValidReturnPercent, ...
        "-o","LineWidth",1.2, ...
        "DisplayName",scenarios(k));

end

yline(lowValidReturnPercent,"k--", ...
    "Experimental low-return threshold");

xlabel("Frame index");
ylabel("Valid returns (%)");
title("Return Availability Diagnostic");
legend("Location","best");
grid on;

subplot(2,2,4);

hold on;

for k = 1:numel(scenarios)

    S = report(report.Scenario==scenarios(k),:);

    scatter(S.MedianRangeM, ...
        S.OccupiedXYCells,70, ...
        "filled", ...
        "DisplayName",scenarios(k));

end

xline(shortMedianRangeM,"k--");
yline(minimumOccupiedXYCells,"k--");

xlabel("Median return range (m)");
ylabel("Occupied 1 m XY cells");
title("Range and Spatial Coverage");

legend("Location","best");
grid on;

sgtitle("GEMSTAR - Multi-Feature LiDAR Observability Monitor");

graphFile = fullfile(graphDir, ...
    "task19_10p_observability_monitor.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 7. Finish

fprintf("\n=== TASK 19.10P COMPLETE ===\n");

fprintf("Monitor results CSV saved: %d\n", ...
    isfile(reportFile));

fprintf("Summary CSV saved: %d\n", ...
    isfile(summaryFile));

fprintf("Graph saved: %d\n", ...
    isfile(graphFile));

fprintf("\nTotal insufficient frames: %d\n", ...
    sum(states=="INSUFFICIENT"));

fprintf("Total review frames: %d\n", ...
    sum(states=="REVIEW"));

fprintf("Total observable frames: %d\n", ...
    sum(states=="OBSERVABLE"));

fprintf("\nIMPORTANT:\n");
fprintf("Diagnostic thresholds are provisional.\n");
fprintf("OBSERVABLE does not mean verified healthy.\n");
fprintf("REVIEW does not mean a sensor has failed.\n");
fprintf("No AI, live scheduling, or FPGA testing here.\n");
