
%% TASK 19.10E - Offline Adaptive Configuration Analysis
% GEMSTAR fog_mor100 - eight frames
%
% Offline oracle and Pareto analysis.
% Uses previously measured reference agreement.
% NOT a live scheduler, NOT a trained AI model.
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inputFile = fullfile(dataDir, ...
    "task19_10d_multiframe_voxel_summary.csv");

assert(isfile(inputFile),"Task 19.10D summary missing.");

T = readtable(inputFile);

frames = unique(T.FrameIndex);
nFrames = numel(frames);

%% 2. Diagnostic acceptance criteria
% These are experimental screening thresholds.
% They are NOT validated safety requirements.
%
% Require:
% - >= 95% median agreement with full RANSAC
% - <= 2% of ROI points assigned ground when
%   reference says non-ground
%
% If no voxel setting passes, select full RANSAC.
% Full RANSAC is a reference, not semantic ground truth.

minAgreement = 95.0;
maxFalseGroundFraction = 0.02;

decision = table();
paretoRows = table();

fprintf("\n=== TASK 19.10E OFFLINE CONFIGURATION ANALYSIS ===\n");

%% 3. Examine every frame

for k = 1:nFrames

    frameID = frames(k);
    F = T(T.FrameIndex==frameID,:);

    assert(height(F)==3, ...
        "Expected three voxel configurations per frame.");

    %% Pareto analysis:
    % Minimize latency, maximize reference agreement.
    % A configuration is dominated if another is no
    % slower and no less consistent, with at least one
    % strict improvement.

    isPareto = true(height(F),1);

    for i = 1:height(F)

        for j = 1:height(F)

            if i==j
                continue;
            end

            noSlower = ...
                F.VoxelMedianMs(j)<=F.VoxelMedianMs(i);

            noWorseAgreement = ...
                F.MedianAgreementPercent(j)>= ...
                F.MedianAgreementPercent(i);

            strictlyBetter = ...
                F.VoxelMedianMs(j)<F.VoxelMedianMs(i) || ...
                F.MedianAgreementPercent(j)> ...
                F.MedianAgreementPercent(i);

            if noSlower && noWorseAgreement && strictlyBetter
                isPareto(i) = false;
                break;
            end
        end
    end

    %% Diagnostic eligibility

    maxAllowedFalseGround = ...
        maxFalseGroundFraction*F.ROIPoints;

    eligible = ...
        F.MedianAgreementPercent>=minAgreement & ...
        F.MedianFalseGround<=maxAllowedFalseGround;

    %% Offline oracle selection
    % This uses measured reference comparisons,
    % so it cannot be directly used at runtime.

    if any(eligible)

        choices = find(eligible);
        [~,position] = min(F.VoxelMedianMs(choices));
        idx = choices(position);

        selectedSize = F.VoxelSizeM(idx);
        selectedLatency = F.VoxelMedianMs(idx);
        selectedAgreement = F.MedianAgreementPercent(idx);
        selectedFalseGround = F.MedianFalseGround(idx);

        selectedMethod = "Voxel-assisted";

    else

        selectedSize = NaN;
        selectedLatency = F.FullMedianMs(1);
        selectedAgreement = 100;
        selectedFalseGround = 0;

        selectedMethod = "Full-reference fallback";

    end

    %% Record frame decision

    row = table();

    row.FrameIndex = frameID;
    row.ROIPoints = F.ROIPoints(1);

    row.SelectedMethod = selectedMethod;
    row.SelectedVoxelSizeM = selectedSize;

    row.SelectedLatencyMs = selectedLatency;
    row.FullReferenceLatencyMs = F.FullMedianMs(1);

    row.SelectedReferenceAgreementPercent = ...
        selectedAgreement;

    row.SelectedFalseGroundCount = ...
        selectedFalseGround;

    row.SpeedRatioVsFull = ...
        row.FullReferenceLatencyMs/selectedLatency;

    row.EligibleVoxelOptions = sum(eligible);
    row.ParetoVoxelOptions = sum(isPareto);

    decision = [decision;row];

    %% Record every configuration's status

    for i = 1:height(F)

        detail = table();

        detail.FrameIndex = frameID;
        detail.VoxelSizeM = F.VoxelSizeM(i);
        detail.MedianLatencyMs = F.VoxelMedianMs(i);

        detail.MedianAgreementPercent = ...
            F.MedianAgreementPercent(i);

        detail.MedianFalseGround = ...
            F.MedianFalseGround(i);

        detail.IsParetoEfficient = isPareto(i);
        detail.PassesDiagnosticCriteria = eligible(i);

        paretoRows = [paretoRows;detail];

    end

    fprintf("\nFrame %d\n",frameID);

    fprintf("Eligible voxel options: %d / 3\n", ...
        sum(eligible));

    fprintf("Pareto-efficient voxel options: %d / 3\n", ...
        sum(isPareto));

    fprintf("Offline selected method: %s\n",selectedMethod);

    if ~isnan(selectedSize)
        fprintf("Selected voxel size: %.2f m\n", ...
            selectedSize);
    end

    fprintf("Selected median latency: %.4f ms\n", ...
        selectedLatency);

end

%% 4. Save results

decisionFile = fullfile(dataDir, ...
    "task19_10e_offline_configuration_decisions.csv");

paretoFile = fullfile(dataDir, ...
    "task19_10e_pareto_configuration_analysis.csv");

writetable(decision,decisionFile);
writetable(paretoRows,paretoFile);

%% 5. Visualization

fig = figure("Color","w", ...
    "Position",[100 100 1200 740]);

subplot(2,2,1);

plot(decision.FrameIndex, ...
    decision.FullReferenceLatencyMs, ...
    "-o","LineWidth",1.3);

hold on;

plot(decision.FrameIndex, ...
    decision.SelectedLatencyMs, ...
    "-s","LineWidth",1.3);

xlabel("Frame index");
ylabel("Median latency (ms)");
title("Offline Selection vs Full Reference");
legend("Full reference","Offline selection", ...
    "Location","best");
grid on;

subplot(2,2,2);

bar(decision.FrameIndex,decision.SpeedRatioVsFull);

hold on;
yline(1,"k--");

xlabel("Frame index");
ylabel("Latency ratio (full / selected)");
title("Offline Speed Ratio");
grid on;

subplot(2,2,3);

bar(decision.FrameIndex, ...
    decision.EligibleVoxelOptions);

xlabel("Frame index");
ylabel("Eligible configurations");
title("Configurations Passing Diagnostic Criteria");
ylim([0 3.5]);
grid on;

subplot(2,2,4);

hold on;

sizes = unique(paretoRows.VoxelSizeM);

for j = 1:numel(sizes)

    S = paretoRows( ...
        abs(paretoRows.VoxelSizeM-sizes(j))<1e-9,:);

    scatter(S.MedianLatencyMs, ...
        S.MedianAgreementPercent, ...
        55,"filled", ...
        "DisplayName",sprintf("%.2f m",sizes(j)));

end

yline(minAgreement,"k--","Agreement threshold");

xlabel("Median latency (ms)");
ylabel("Reference agreement (%)");

title("Measured Configuration Trade-offs");

legend("Location","best");
grid on;

sgtitle("GEMSTAR - Offline Configuration Selection");

graphFile = fullfile(graphDir, ...
    "task19_10e_offline_configuration_analysis.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 6. Final report

fprintf("\n=== TASK 19.10E SUMMARY ===\n");

disp(decision(:,{ ...
    'FrameIndex', ...
    'SelectedMethod', ...
    'SelectedVoxelSizeM', ...
    'SelectedLatencyMs', ...
    'SelectedReferenceAgreementPercent', ...
    'SpeedRatioVsFull'}));

fprintf("Frames requiring full-reference fallback: %d\n", ...
    sum(decision.SelectedMethod=="Full-reference fallback"));

fprintf("Median offline speed ratio: %.3fx\n", ...
    median(decision.SpeedRatioVsFull));

fprintf("\n=== TASK 19.10E COMPLETE ===\n");

fprintf("Decision CSV saved: %d\n",isfile(decisionFile));
fprintf("Pareto CSV saved: %d\n",isfile(paretoFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nIMPORTANT:\n");
fprintf("This is an offline oracle, NOT a deployable scheduler.\n");
fprintf("Reference agreement is NOT obstacle-detection accuracy.\n");
fprintf("No actual ARM or FPGA energy savings measured.\n");
