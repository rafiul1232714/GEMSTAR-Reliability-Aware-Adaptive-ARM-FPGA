%% TASK 24.10.5.3C — EKF DIAGNOSTICS
% Uses saved results from the clean C02 V2 recording.
% No model parameters or original EKF states are changed.
% This analysis is descriptive, not a calibration.

clear; clc; close all;

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';

data = fullfile(base,'C02_V2_EKF_Input_53Frames_V1');
out = fullfile(base,'MATLAB_Task24_Analysis');

figdir = fullfile(out,'01_Graphs');
csvdir = fullfile(out,'02_CSV_Data');
finddir = fullfile(out,'04_Research_Findings');

dirs = {figdir,csvdir,finddir};

for k = 1:numel(dirs)
    if ~isfolder(dirs{k})
        mkdir(dirs{k});
    end
end

%% INPUT FILES

ekfPath = fullfile(data,'lidar_radar_ekf_track2_v1.csv');
comparisonPath = fullfile(data, ...
    'three_estimator_matched_comparison_v1.csv');
gtPath = fullfile(data,'gt_center_comparison_track2_v1.csv');

assert(isfile(ekfPath),'Missing EKF input');
assert(isfile(comparisonPath),'Missing estimator comparison');
assert(isfile(gtPath),'Missing GT evaluation input');

%% OUTPUT CHECKS

for k = 19:24
    output = fullfile(figdir, ...
        sprintf('Task24_Figure_%02d.png',k));

    assert(~isfile(output), ...
        'Existing plot. No overwrite: %s',output);
end

csvOutput = fullfile(csvdir, ...
    'Task24_EKF_Diagnostics_V1.csv');

reportOutput = fullfile(finddir, ...
    'Task24_EKF_Diagnostics_Report_V1.txt');

assert(~isfile(csvOutput),'Existing diagnostics CSV');
assert(~isfile(reportOutput),'Existing diagnostics report');

%% LOAD DATA

E = readtable(ekfPath);
F = readtable(comparisonPath);
G = readtable(gtPath);

assert(height(E)==24,'Expected 24 EKF observations');
assert(height(F)==24,'Expected 24 estimator comparisons');
assert(height(G)==23,'Expected 23 GT evaluations');

assert(isequal(E.frame,F.frame), ...
    'EKF and comparison frames differ');

% Explicitly align GT rows by frame, not row position.
[hasGT,gtIndex] = ismember(E.frame,G.frame);

assert(sum(hasGT)==23, ...
    'Expected 23 matching GT frames');

t = E.time_s;
frames = E.frame;

radarStatus = string(E.radar_status);
accepted = radarStatus == "ACCEPTED";

fprintf('\n=== TASK 24 MATLAB EKF DIAGNOSTICS ===\n');
fprintf('EKF observations: %d\n',height(E));
fprintf('Accepted Radar updates: %d\n',sum(accepted));

%% FIGURE 19 — EKF VELOCITY COMPONENTS

f = figure('Color','w','Position',[100 100 1150 730]);

tiledlayout(2,1);

nexttile;

plot(t,E.lidar_only_vx_mps,'-o', ...
    'LineWidth',1.6,'MarkerSize',4);

hold on;

plot(t,E.radar_ekf_vx_mps,'-s', ...
    'LineWidth',1.6,'MarkerSize',4);

scatter(t(accepted), ...
    E.radar_ekf_vx_mps(accepted), ...
    75,'filled');

ylabel('Estimated Vx (m/s)');
title('Longitudinal velocity');

legend('LiDAR-only','LiDAR-Radar', ...
    'Accepted Radar update','Location','best');

grid on;

nexttile;

plot(t,E.lidar_only_vy_mps,'-o', ...
    'LineWidth',1.6,'MarkerSize',4);

hold on;

plot(t,E.radar_ekf_vy_mps,'-s', ...
    'LineWidth',1.6,'MarkerSize',4);

ylabel('Estimated Vy (m/s)');
xlabel('Recording time (s)');
title('Lateral velocity');

grid on;

sgtitle('Figure 19 — EKF velocity state comparison');

saveas(f,fullfile(figdir,'Task24_Figure_19.png'));
close(f);

%% FIGURE 20 — RADAR PREDICTED VS MEASURED VELOCITY

valid = isfinite(E.radar_measured_mps) & ...
        isfinite(E.radar_predicted_mps);

f = figure('Color','w','Position',[100 100 1100 570]);

if any(valid)

    plot(t(valid),E.radar_measured_mps(valid), ...
        'o-','LineWidth',1.5);

    hold on;

    plot(t(valid),E.radar_predicted_mps(valid), ...
        's-','LineWidth',1.5);

    ylabel('Radial velocity (m/s)');
    xlabel('Recording time (s)');

    legend('Radar measurement','EKF prediction', ...
        'Location','best');

else
    text(0.5,0.5,'No finite Radar measurements', ...
        'Units','normalized', ...
        'HorizontalAlignment','center');
end

title('Figure 20 — Radar velocity innovation inputs');
grid on;

saveas(f,fullfile(figdir,'Task24_Figure_20.png'));
close(f);

%% FIGURE 21 — RADAR NIS

validNIS = isfinite(E.radar_nis);

f = figure('Color','w','Position',[100 100 1050 530]);

if any(validNIS)

    stem(t(validNIS),E.radar_nis(validNIS), ...
        'filled','LineWidth',1.7);

    hold on;

    yline(9,'r--','Exploratory NIS gate = 9', ...
        'LineWidth',1.4);

    xlabel('Recording time (s)');
    ylabel('Normalized innovation squared');

    title('Figure 21 — Radar NIS and update gating');

else
    text(0.5,0.5,'No finite Radar NIS values', ...
        'Units','normalized', ...
        'HorizontalAlignment','center');

    title('Figure 21 — Radar NIS unavailable');
end

grid on;

saveas(f,fullfile(figdir,'Task24_Figure_21.png'));
close(f);

%% FIGURE 22 — EKF REPORTED POSITION UNCERTAINTY

% Only X standard deviations are present in the saved CSV.
% No complete covariance consistency claim is made.

f = figure('Color','w','Position',[100 100 1100 550]);

plot(t,E.lidar_only_std_x_m,'-o', ...
    'LineWidth',1.7);

hold on;

plot(t,E.radar_ekf_std_x_m,'-s', ...
    'LineWidth',1.7);

if any(accepted)
    scatter(t(accepted), ...
        E.radar_ekf_std_x_m(accepted), ...
        65,'filled');
end

xlabel('Recording time (s)');
ylabel('Reported standard deviation in X (m)');

title('Figure 22 — EKF reported X uncertainty');

legend('LiDAR-only','LiDAR-Radar', ...
    'Accepted Radar update','Location','best');

grid on;

saveas(f,fullfile(figdir,'Task24_Figure_22.png'));
close(f);

%% FIGURE 23 — DISTANCE BETWEEN ESTIMATORS

f = figure('Color','w','Position',[100 100 1100 550]);

plot(F.time_s, ...
    100*F.lidar_vs_radar_difference_m, ...
    '-o','LineWidth',1.7);

hold on;

plot(F.time_s, ...
    100*F.radar_vs_camera_aided_difference_m, ...
    '-s','LineWidth',1.7);

xline(F.time_s(F.frame==530),'k--', ...
    'Camera update');

xlabel('Recording time (s)');
ylabel('Estimator position separation (cm)');

title('Figure 23 — How much fusion changes position');

legend('LiDAR vs. LiDAR-Radar', ...
    'LiDAR-Radar vs. three-sensor', ...
    'Location','best');

grid on;

saveas(f,fullfile(figdir,'Task24_Figure_23.png'));
close(f);

%% FIGURE 24 — RADAR UPDATE EFFECTIVENESS

% LiDAR vs. LiDAR-Radar center-reference improvement.
% Only reference-aligned frames are evaluated.

evalFrames = E.frame(hasGT);
evalGT = G(gtIndex(hasGT),:);

improvement = ...
    evalGT.lidar_center_error_m ...
    - evalGT.radar_center_error_m;

evalAccepted = accepted(hasGT);
evalTimes = E.time_s(hasGT);

f = figure('Color','w','Position',[100 100 1100 700]);

tiledlayout(2,1);

nexttile;

stem(t,E.radar_nonzero_returns, ...
    'filled','LineWidth',1.4);

hold on;

scatter(t(accepted), ...
    E.radar_nonzero_returns(accepted), ...
    80,'filled');

ylabel('Matched nonzero Radar returns');
title('Radar measurement availability');

legend('Available for Track 2', ...
    'Accepted update','Location','best');

grid on;

nexttile;

stem(evalTimes,100*improvement, ...
    'filled','LineWidth',1.5);

hold on;

yline(0,'k-');

scatter(evalTimes(evalAccepted), ...
    100*improvement(evalAccepted), ...
    85,'filled');

xlabel('Recording time (s)');
ylabel('Center error improvement (cm)');

title('Accepted updates and subsequent EKF impact');

legend('Radar improvement', ...
    'Zero improvement', ...
    'Accepted Radar update', ...
    'Location','best');

grid on;

sgtitle('Figure 24 — Radar update effectiveness');

saveas(f,fullfile(figdir,'Task24_Figure_24.png'));
close(f);

%% DIAGNOSTIC DATA TABLE

% Join GT improvements by matching frame ID.
gtImprovement = nan(height(E),1);
gtImprovement(hasGT) = improvement;

D = table( ...
    E.frame, ...
    E.time_s, ...
    radarStatus, ...
    E.radar_nonzero_returns, ...
    E.radar_measured_mps, ...
    E.radar_predicted_mps, ...
    E.radar_innovation_mps, ...
    E.radar_nis, ...
    E.lidar_only_vx_mps, ...
    E.lidar_only_vy_mps, ...
    E.radar_ekf_vx_mps, ...
    E.radar_ekf_vy_mps, ...
    E.lidar_only_std_x_m, ...
    E.radar_ekf_std_x_m, ...
    F.lidar_vs_radar_difference_m, ...
    F.radar_vs_camera_aided_difference_m, ...
    gtImprovement, ...
    'VariableNames',{ ...
    'Frame', ...
    'Time_s', ...
    'RadarStatus', ...
    'RadarNonzeroReturns', ...
    'RadarMeasured_mps', ...
    'RadarPredicted_mps', ...
    'RadarInnovation_mps', ...
    'RadarNIS', ...
    'LiDAR_Vx_mps', ...
    'LiDAR_Vy_mps', ...
    'RadarEKF_Vx_mps', ...
    'RadarEKF_Vy_mps', ...
    'LiDAR_StdX_m', ...
    'RadarEKF_StdX_m', ...
    'LiDAR_Radar_Separation_m', ...
    'Radar_Camera_Separation_m', ...
    'GT_Center_Improvement_m' ...
    });

writetable(D,csvOutput);

%% NUMERICAL SUMMARY

vxDifference = ...
    E.radar_ekf_vx_mps-E.lidar_only_vx_mps;

vyDifference = ...
    E.radar_ekf_vy_mps-E.lidar_only_vy_mps;

finiteInnovation = ...
    E.radar_innovation_mps( ...
    isfinite(E.radar_innovation_mps));

finiteNIS = E.radar_nis(validNIS);

fprintf('\n=== TASK 24.10.5.3C RESULTS ===\n');

fprintf('MATCHED_EKF_FRAMES=%d\n',height(E));
fprintf('GT_EVALUATED_FRAMES=%d\n',sum(hasGT));
fprintf('RADAR_ACCEPTED_UPDATES=%d\n',sum(accepted));

fprintf('MAX_VX_ESTIMATOR_DIFFERENCE_MPS=%.6f\n', ...
    max(abs(vxDifference)));

fprintf('MAX_VY_ESTIMATOR_DIFFERENCE_MPS=%.6f\n', ...
    max(abs(vyDifference)));

fprintf('MAX_POSITION_ESTIMATOR_DIFFERENCE_M=%.6f\n', ...
    max(F.lidar_vs_radar_difference_m));

fprintf('MAX_CAMERA_POSITION_EFFECT_M=%.6f\n', ...
    max(F.radar_vs_camera_aided_difference_m));

fprintf('MEAN_REPORTED_LIDAR_STD_X_M=%.6f\n', ...
    mean(E.lidar_only_std_x_m));

fprintf('MEAN_REPORTED_RADAR_STD_X_M=%.6f\n', ...
    mean(E.radar_ekf_std_x_m));

if ~isempty(finiteInnovation)
    fprintf('MEAN_ABS_RADAR_INNOVATION_MPS=%.6f\n', ...
        mean(abs(finiteInnovation)));
end

if ~isempty(finiteNIS)
    fprintf('MAX_FINITE_RADAR_NIS=%.6f\n', ...
        max(finiteNIS));
end

fprintf('RADAR_IMPROVED_GT_FRAMES=%d\n', ...
    sum(improvement>1e-6));

fprintf('RADAR_WORSENED_GT_FRAMES=%d\n', ...
    sum(improvement<(-1e-6)));

%% WRITE RESEARCH INTERPRETATION

fid = fopen(reportOutput,'w');

assert(fid>=0,'Cannot create findings report');

fprintf(fid,'TASK 24 MATLAB - EKF DIAGNOSTICS\n');
fprintf(fid,'================================\n\n');

fprintf(fid,'EKF observations: %d\n',height(E));
fprintf(fid,'GT evaluated frames: %d\n',sum(hasGT));
fprintf(fid,'Radar accepted updates: %d\n\n',sum(accepted));

fprintf(fid,'Velocity estimation:\n');
fprintf(fid,'Maximum estimator Vx difference: %.6f m/s\n', ...
    max(abs(vxDifference)));

fprintf(fid,'Maximum estimator Vy difference: %.6f m/s\n\n', ...
    max(abs(vyDifference)));

fprintf(fid,'Radar position influence:\n');
fprintf(fid,'Maximum separation: %.6f m\n\n', ...
    max(F.lidar_vs_radar_difference_m));

fprintf(fid,'Camera position influence:\n');
fprintf(fid,'Maximum separation: %.6f m\n\n', ...
    max(F.radar_vs_camera_aided_difference_m));

fprintf(fid,'IMPORTANT LIMITATIONS:\n');
fprintf(fid,'Only one development recording was evaluated.\n');
fprintf(fid,'Radar noise assumptions were not calibrated.\n');
fprintf(fid,'NIS threshold 9 is an exploratory gate.\n');
fprintf(fid,'Only X position standard deviation is available.\n');
fprintf(fid,'Full covariance and NEES cannot be evaluated.\n');
fprintf(fid,'GT-center errors include surface-reference bias.\n');
fprintf(fid,'Velocity states have not been validated against GT.\n');
fprintf(fid,'No hardware energy or latency evaluation is made.\n');
fprintf(fid,'GT was not used for EKF state updates.\n');

fclose(fid);

fprintf('\nDIAGNOSTICS_CSV=%s\n',csvOutput);
fprintf('RESEARCH_REPORT=%s\n',reportOutput);

fprintf('NEW_FIGURES=6\n');
fprintf('FULL_COVARIANCE_CONSISTENCY_TEST=NO\n');
fprintf('GT_USED_FOR_FILTER_UPDATES=NO\n');
fprintf('ORIGINAL_INPUTS_MODIFIED=NO\n');

fprintf('TASK24_MATLAB_PART3C_COMPLETE\n');