
%% TASK 19.10G - First Rule-Based Scheduler
% GEMSTAR fog_mor100 - 8 selected frames
%
% Rule uses ONLY ROI point count.
% Offline oracle is used for evaluation, never for decisions.
% Thresholds are exploratory and informed by these same frames.
% This is NOT independent validation or an AI model.
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths
base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

featureFile = fullfile(dataDir, ...
    "task19_10f_runtime_observable_features.csv");

oracleFile = fullfile(dataDir, ...
    "task19_10e_offline_configuration_decisions.csv");

timingFile = fullfile(dataDir, ...
    "task19_10d_multiframe_voxel_summary.csv");

assert(isfile(featureFile));
assert(isfile(oracleFile));
assert(isfile(timingFile));

F = readtable(featureFile);
O = readtable(oracleFile);
B = readtable(timingFile);

%% 2. Parameters

lowROILimit = 1600;
highROILimit = 2200;

runtimeRuns = 100;

results = table();
overheadSamples = table();

fprintf("\n=== TASK 19.10G RULE-BASED SCHEDULER ===\n");

%% 3. Process each frame independently

for k = 1:height(F)

    frameID = F.FrameIndex(k);

    filename = sprintf( ...
        "task19_10b_frame%03d_candidate_xyz.csv", ...
        frameID);

    file = fullfile(cloudDir,filename);

    assert(isfile(file),"Missing LiDAR CSV: %s",file);

    T = readtable(file);
    P = double([T.X,T.Y,T.Z]);

    %% 4. Measure the decision-input computation
    % CSV I/O excluded.
    % Includes ROI masking, point count and the decision.
    % Does NOT include ground processing.

    decisionTimes = zeros(runtimeRuns,1);

    for r = 1:runtimeRuns

        tic;

        roiCount = sum( ...
            P(:,1)>=0 & P(:,1)<=20 & ...
            P(:,2)>=-6 & P(:,2)<=6);

        if roiCount < lowROILimit || ...
           roiCount > highROILimit

            predicted = "Full-reference fallback";

        else

            predicted = "Voxel-assisted";

        end

        decisionTimes(r) = toc*1000;

    end

    assert(roiCount==F.ROIPoints(k), ...
        "ROI point count mismatch.");

    %% 5. Retrieve oracle for evaluation only

    oracleIndex = find( ...
        O.FrameIndex==frameID,1);

    assert(~isempty(oracleIndex), ...
        "Offline decision missing.");

    oracleMethod = string( ...
        O.SelectedMethod(oracleIndex));

    oracleLatency = O.SelectedLatencyMs(oracleIndex);

    %% 6. Retrieve measured latency for selected method

    if predicted=="Full-reference fallback"

        methodLatency = O.FullReferenceLatencyMs(oracleIndex);
        selectedVoxel = NaN;

    else

        benchmarkIndex = find( ...
            B.FrameIndex==frameID & ...
            abs(B.VoxelSizeM-0.25)<1e-9,1);

        assert(~isempty(benchmarkIndex), ...
            "0.25m benchmark missing.");

        methodLatency = B.VoxelMedianMs(benchmarkIndex);
        selectedVoxel = 0.25;

    end

    % Cross-run median estimates plus median scheduler
    % overhead. This is not a measured combined runtime.
    estimatedTotalMs = ...
        methodLatency + median(decisionTimes);

    %% 7. Save result row

    row = table();

    row.FrameIndex = frameID;
    row.ROIPoints = roiCount;

    row.RuleMethod = predicted;
    row.RuleVoxelSizeM = selectedVoxel;

    row.OracleMethod = oracleMethod;

    row.FallbackAgreement = ...
        double( ...
        (predicted=="Full-reference fallback") == ...
        (oracleMethod=="Full-reference fallback"));

    row.ProcessingMedianMs = methodLatency;
    row.DecisionOverheadMedianMs = ...
        median(decisionTimes);

    row.EstimatedCombinedMedianMs = ...
        estimatedTotalMs;

    row.OracleLatencyMs = oracleLatency;

    row.EstimatedLatencyDifferenceMs = ...
        estimatedTotalMs-oracleLatency;

    row.FullReferenceLatencyMs = ...
        O.FullReferenceLatencyMs(oracleIndex);

    results = [results;row];

    %% Save raw overhead measurements

    runTable = table();

    runTable.FrameIndex = ...
        repmat(frameID,runtimeRuns,1);

    runTable.Run = (1:runtimeRuns)';
    runTable.DecisionOverheadMs = decisionTimes;

    overheadSamples = [overheadSamples;runTable];

    fprintf( ...
        "Frame %3d | ROI=%4d | Rule=%s | Oracle=%s\n", ...
        frameID,roiCount,predicted,oracleMethod);

end

%% 8. Compare fallback decisions

oracleFallback = ...
    results.OracleMethod=="Full-reference fallback";

ruleFallback = ...
    results.RuleMethod=="Full-reference fallback";

correct = sum(ruleFallback==oracleFallback);

falseFallback = sum(ruleFallback & ~oracleFallback);
missedFallback = sum(~ruleFallback & oracleFallback);

fprintf("\n=== RULE VS OFFLINE ORACLE ===\n");

fprintf("Fallback decision agreement: %d / %d\n", ...
    correct,height(results));

fprintf("Unnecessary full fallbacks: %d\n", ...
    falseFallback);

fprintf("Missed oracle fallbacks: %d\n", ...
    missedFallback);

fprintf("\n=== ESTIMATED LATENCY ===\n");

fprintf("Median reference processing latency: %.5f ms\n", ...
    median(results.FullReferenceLatencyMs));

fprintf("Median rule processing latency: %.5f ms\n", ...
    median(results.ProcessingMedianMs));

fprintf("Median measured decision overhead: %.5f ms\n", ...
    median(results.DecisionOverheadMedianMs));

fprintf("Median estimated combined latency: %.5f ms\n", ...
    median(results.EstimatedCombinedMedianMs));

fprintf("Median oracle processing latency: %.5f ms\n", ...
    median(results.OracleLatencyMs));

%% 9. Export tables

outputFile = fullfile(dataDir, ...
    "task19_10g_rule_scheduler_decisions.csv");

overheadFile = fullfile(dataDir, ...
    "task19_10g_rule_scheduler_overhead_samples.csv");

writetable(results,outputFile);
writetable(overheadSamples,overheadFile);

%% 10. Visualization

fig = figure("Color","w", ...
    "Position",[100 100 1200 750]);

subplot(2,2,1);

plot(results.FrameIndex,results.ROIPoints, ...
    "-o","LineWidth",1.5);

hold on;

yline(lowROILimit,"r--","Lower threshold");
yline(highROILimit,"r--","Upper threshold");

xlabel("Frame index");
ylabel("ROI points");
title("Runtime-Observable Decision Feature");
grid on;

subplot(2,2,2);

bar(results.FrameIndex, ...
    [double(ruleFallback),double(oracleFallback)], ...
    "grouped");

xlabel("Frame index");
ylabel("Full fallback (1 = yes)");
title("Rule vs Offline Oracle");

legend("Rule","Oracle","Location","best");
grid on;
ylim([0 1.3]);

subplot(2,2,3);

plot(results.FrameIndex, ...
    results.EstimatedCombinedMedianMs, ...
    "-o","LineWidth",1.5);

hold on;

plot(results.FrameIndex, ...
    results.OracleLatencyMs, ...
    "-s","LineWidth",1.5);

xlabel("Frame index");
ylabel("Latency (ms)");
title("Estimated Rule Latency vs Offline Oracle");

legend("Rule + measured decision overhead", ...
    "Oracle processing","Location","best");

grid on;

subplot(2,2,4);

bar(results.FrameIndex, ...
    results.EstimatedLatencyDifferenceMs);

hold on;
yline(0,"k--");

xlabel("Frame index");
ylabel("Estimated latency difference (ms)");
title("Rule Minus Offline Oracle Latency");

grid on;

sgtitle("GEMSTAR - First Rule-Based Scheduler Prototype");

graphFile = fullfile(graphDir, ...
    "task19_10g_rule_scheduler_analysis.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 11. Finish

fprintf("\n=== TASK 19.10G COMPLETE ===\n");

fprintf("Decision CSV saved: %d\n",isfile(outputFile));
fprintf("Overhead samples saved: %d\n",isfile(overheadFile));
fprintf("Analysis graph saved: %d\n",isfile(graphFile));

disp(results(:,{ ...
    'FrameIndex','ROIPoints','RuleMethod', ...
    'OracleMethod','FallbackAgreement', ...
    'EstimatedCombinedMedianMs'}));

fprintf("\nIMPORTANT:\n");
fprintf("The rule was proposed after examining these frames.\n");
fprintf("This is an in-sample feasibility evaluation.\n");
fprintf("The oracle uses reference agreement and is not ground truth.\n");
fprintf("Combined latency is an estimate, not timed end-to-end.\n");
fprintf("No AI learning or actual FPGA measurement performed.\n");
