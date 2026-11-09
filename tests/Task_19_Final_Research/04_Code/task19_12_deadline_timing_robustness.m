
%% TASK 19.12 - Timing Robustness and Deadline Analysis
% GEMSTAR Task 19
% Input: Task 19.10T timing samples and pipeline results
%
% Analyzes already measured PC MATLAB timings.
% No RANSAC rerun. No additional toolbox required.
%
% Deadline is illustrative, NOT a certified system requirement.
% OSI decoding, communication and downstream fusion excluded.

clear;
clc;
close all;

%% 1. Paths
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

sampleFile = fullfile(dataDir, ...
    "task19_10t_full_monitor_timing_samples.csv");

resultFile = fullfile(dataDir, ...
    "task19_10t_full_monitor_pipeline_results.csv");

assert(isfile(sampleFile),"Timing samples missing.");
assert(isfile(resultFile),"Pipeline results missing.");

S = readtable(sampleFile,"TextType","string");
R = readtable(resultFile,"TextType","string");

%% 2. Experimental timing budget
deadlineMs = 3.0;

assert(height(R)==48);
assert(all(isfinite(S.BaselineMs)));
assert(all(isfinite(S.PolicyMs)));

%% 3. Per-frame analysis

frameSummary = table();

fprintf("\n=== TASK 19.12 TIMING ROBUSTNESS ===\n");
fprintf("Illustrative deadline: %.2f ms\n",deadlineMs);

for k = 1:height(R)

    scenario = R.Scenario(k);
    frameID = R.FrameIndex(k);

    X = S( ...
        S.Scenario==scenario & ...
        S.FrameIndex==frameID,:);

    assert(height(X)==5, ...
        "Expected 5 timing samples per frame.");

    full = X.BaselineMs;
    policy = X.PolicyMs;
    monitor = X.MonitorMs;

    row = table();

    row.Scenario = scenario;
    row.FrameIndex = frameID;
    row.PolicyMode = R.PolicyMode(k);

    row.BaselineMedianMs = median(full);
    row.PolicyMedianMs = median(policy);

    row.BaselineP95Ms = nearestRank95(full);
    row.PolicyP95Ms = nearestRank95(policy);

    row.BaselineMaximumMs = max(full);
    row.PolicyMaximumMs = max(policy);

    row.BaselineStdMs = std(full);
    row.PolicyStdMs = std(policy);

    row.MonitorMedianMs = median(monitor);

    row.BaselineDeadlineMisses = sum(full>deadlineMs);
    row.PolicyDeadlineMisses = sum(policy>deadlineMs);

    row.SampleCount = numel(full);

    row.MedianTimeSavedMs = ...
        row.BaselineMedianMs-row.PolicyMedianMs;

    frameSummary = [frameSummary;row];

end

%% 4. Aggregate by recording

scenarios = unique(frameSummary.Scenario,"stable");
scenarioSummary = table();

for k = 1:numel(scenarios)

    scenario = scenarios(k);

    F = frameSummary( ...
        frameSummary.Scenario==scenario,:);

    X = S(S.Scenario==scenario,:);

    row = table();

    row.Scenario = scenario;
    row.Frames = height(F);
    row.TimingSamples = height(X);

    row.BaselineMedianMs = median(X.BaselineMs);
    row.PolicyMedianMs = median(X.PolicyMs);

    row.BaselineP95Ms = nearestRank95(X.BaselineMs);
    row.PolicyP95Ms = nearestRank95(X.PolicyMs);

    row.BaselineMaxMs = max(X.BaselineMs);
    row.PolicyMaxMs = max(X.PolicyMs);

    row.BaselineMisses = ...
        sum(X.BaselineMs>deadlineMs);

    row.PolicyMisses = ...
        sum(X.PolicyMs>deadlineMs);

    row.BaselineMissRatePercent = ...
        100*row.BaselineMisses/height(X);

    row.PolicyMissRatePercent = ...
        100*row.PolicyMisses/height(X);

    scenarioSummary = [scenarioSummary;row];

end

%% 5. Save data

frameFile = fullfile(dataDir, ...
    "task19_12_deadline_frame_statistics.csv");

scenarioFile = fullfile(dataDir, ...
    "task19_12_deadline_scenario_summary.csv");

writetable(frameSummary,frameFile);
writetable(scenarioSummary,scenarioFile);

%% 6. Visualizations

fig = figure("Color","w", ...
    "Position",[100 100 1200 780]);

subplot(2,2,1);

bar(categorical(scenarioSummary.Scenario), ...
    [scenarioSummary.BaselineMedianMs, ...
     scenarioSummary.PolicyMedianMs]);

hold on;
yline(deadlineMs,"r--","Illustrative deadline");

ylabel("Latency (ms)");
title("Median Execution Latency");
legend("Full baseline","Adaptive policy", ...
    "Location","best");
grid on;

subplot(2,2,2);

bar(categorical(scenarioSummary.Scenario), ...
    [scenarioSummary.BaselineP95Ms, ...
     scenarioSummary.PolicyP95Ms]);

hold on;
yline(deadlineMs,"r--","Deadline");

ylabel("P95 latency (ms)");
title("95th-Percentile Timing");
legend("Full baseline","Adaptive policy", ...
    "Location","best");
grid on;

subplot(2,2,3);

bar(categorical(scenarioSummary.Scenario), ...
    [scenarioSummary.BaselineMisses, ...
     scenarioSummary.PolicyMisses]);

ylabel("Missed timing samples");
title("Illustrative Deadline Violations");

legend("Full baseline","Adaptive policy", ...
    "Location","best");
grid on;

subplot(2,2,4);

scatter(frameSummary.BaselineMaximumMs, ...
    frameSummary.PolicyMaximumMs, ...
    65,"filled");

hold on;

upper = max([ ...
    frameSummary.BaselineMaximumMs; ...
    frameSummary.PolicyMaximumMs; ...
    deadlineMs])*1.05;

plot([0 upper],[0 upper],"k--");

xline(deadlineMs,"r:");
yline(deadlineMs,"r:");

xlabel("Full baseline maximum (ms)");
ylabel("Policy maximum (ms)");
title("Per-Frame Worst-Observed Timing");

axis equal;
xlim([0 upper]);
ylim([0 upper]);
grid on;

sgtitle("GEMSTAR - Timing Robustness and Deadline Audit");

graphFile = fullfile(graphDir, ...
    "task19_12_timing_deadline_analysis.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 7. Print conclusions

fprintf("\n=== RECORDING TIMING SUMMARY ===\n");
disp(scenarioSummary);

totalBaselineMisses = ...
    sum(S.BaselineMs>deadlineMs);

totalPolicyMisses = ...
    sum(S.PolicyMs>deadlineMs);

processedFrames = frameSummary( ...
    frameSummary.PolicyMode~="SKIP",:);

fprintf("\n=== OVERALL RESULTS ===\n");
fprintf("Total timing samples: %d\n",height(S));
fprintf("Processed frames: %d\n",height(processedFrames));

fprintf("Baseline deadline misses: %d\n", ...
    totalBaselineMisses);

fprintf("Policy deadline misses: %d\n", ...
    totalPolicyMisses);

fprintf("Baseline maximum observed: %.5f ms\n", ...
    max(S.BaselineMs));

fprintf("Policy maximum observed: %.5f ms\n", ...
    max(S.PolicyMs));

fprintf("Overall baseline P95: %.5f ms\n", ...
    nearestRank95(S.BaselineMs));

fprintf("Overall policy P95: %.5f ms\n", ...
    nearestRank95(S.PolicyMs));

fprintf("\n=== TASK 19.12 COMPLETE ===\n");

fprintf("Frame CSV saved: %d\n",isfile(frameFile));
fprintf("Scenario CSV saved: %d\n",isfile(scenarioFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nIMPORTANT:\n");
fprintf("3 ms is an illustrative processing deadline.\n");
fprintf("Five samples per frame are insufficient to establish");
fprintf(" a reliable true tail-latency distribution.\n");
fprintf("P95 is nearest-rank of the saved samples.\n");
fprintf("These results are PC MATLAB wall-clock measurements.\n");
fprintf("No real-time guarantee or FPGA latency established.\n");

%% Local function

function p = nearestRank95(x)

    x = sort(x(:));

    assert(~isempty(x));

    index = ceil(0.95*numel(x));

    p = x(index);

end
