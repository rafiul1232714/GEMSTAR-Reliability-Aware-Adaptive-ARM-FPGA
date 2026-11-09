%% TASK 24.10.5.4A — MATLAB RESEARCH REPORT
% Read-only access to original experiment data.
% Produces a structured Markdown research report and figure index.
% No filtering, GT association or EKF states are modified.

clear; clc;

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';

analysis = fullfile(base,'MATLAB_Task24_Analysis');
dataDir = fullfile(base,'C02_V2_EKF_Input_53Frames_V1');
figDir = fullfile(analysis,'01_Graphs');
reportDir = fullfile(analysis,'04_Research_Findings');
csvDir = fullfile(analysis,'02_CSV_Data');

if ~isfolder(reportDir), mkdir(reportDir); end
if ~isfolder(csvDir), mkdir(csvDir); end

reportPath = fullfile(reportDir, ...
    'Task24_Complete_MATLAB_Research_Report_V1.md');

indexPath = fullfile(csvDir, ...
    'Task24_MATLAB_30_Figure_Index_V1.csv');

assert(~isfile(reportPath),'Report already exists');
assert(~isfile(indexPath),'Figure index already exists');

%% Verify numerical evidence

G = readtable(fullfile(dataDir, ...
    'gt_center_comparison_track2_v1.csv'));

R = readtable(fullfile(dataDir, ...
    'gt_robustness_per_frame_v1.csv'));

V = readtable(fullfile(dataDir, ...
    'gt_ekf_velocity_comparison_v1.csv'));

F = readtable(fullfile(dataDir, ...
    'gt_fullrate_velocity_audit_v1.csv'));

assert(height(G)==23,'GT center table row count mismatch');
assert(height(R)==23,'Robustness table row count mismatch');
assert(height(V)==23,'Velocity table row count mismatch');
assert(height(F)==2122,'Full-rate GT target row count mismatch');

assert(isequal(G.frame,R.frame,V.frame), ...
    'Evaluation frames do not align');

%% Complete Figure Index
% Scientific interpretation is descriptive and conditional.

titles = {
'Raw sensor measurement availability'
'LiDAR filtering and clustering'
'LiDAR temporal track trajectories'
'Radar association coverage'
'Radar and LiDAR velocity consistency'
'Matched three-estimator position errors'
'GT center and EKF trajectories'
'Signed longitudinal and lateral bias'
'Radar position-error contribution'
'Camera update contribution'
'Position-error empirical distributions'
'GT bounding-box dimensions and reference effects'
'3D LiDAR point cloud'
'3D Radar return geometry'
'Nominal Camera-LiDAR projection'
'Combined LiDAR-Radar scene'
'Track 2 position through space and time'
'Three-frame LiDAR-Radar comparison'
'EKF velocity state comparison'
'Radar measured versus predicted velocity'
'Radar innovation NIS gating'
'EKF reported X uncertainty'
'Estimator position separation'
'Radar update effectiveness'
'Local target LiDAR-Radar association'
'Camera-LiDAR target depth compatibility'
'Sensor support and update timeline'
'GT-center residual versus X uncertainty'
'GT actor velocity versus EKF states'
'Velocity-error and GT-reference disagreement'
};

findings = {
'Both LiDAR and Radar return data throughout the sampled recording; startup counts differ.'
'Filtering reduces LiDAR points substantially; candidate count changes over time.'
'Track 2 is moving while Track 7 is approximately stationary in the selected scene.'
'Provisional Radar associations are concentrated early for Track 2.'
'Five Doppler and LiDAR velocity comparisons have substantial magnitude disagreement.'
'Radar gives a small average center-reference improvement; Camera does not.'
'Three estimators follow similar trajectories with a systematic GT-center displacement.'
'Longitudinal reference-point bias dominates much of the position error.'
'Radar improvements are concentrated around particular updates and are not universal.'
'One Camera bearing update changes position only slightly.'
'Radar slightly reduces the upper portion of the observed error distribution.'
'Reported GT dimensions vary with target yaw; exporter uses AABB half-extents.'
'Measured LiDAR geometry is visible; object identity is not proven by the plot.'
'Radar returns exist at frame 530 but do not associate with Track 2.'
'56 nominally projected LiDAR points overlap a low-confidence Camera hypothesis.'
'Frame 530 supports LiDAR and Track 7 Radar matches, not a full three-sensor match for Track 2.'
'Track 2 Radar support varies substantially over time.'
'Scene geometry changes across frames 245, 530 and 816.'
'Radar updates noticeably influence the early longitudinal velocity state.'
'Measured Radar velocity and EKF prediction disagree in magnitude.'
'Four accepted Radar updates meet the exploratory NIS gate.'
'Reported uncertainty decreases after initialization but is not calibrated against object-center GT.'
'Radar shifts position by at most about 17 cm; Camera by about 1.74 cm.'
'Four accepted Radar updates reduce center-reference error at their update frames.'
'Local 3D views show 14, 0 and 2 Track 2 Radar matches at frames 245, 530 and 816.'
'Depth clustering supports Camera-LiDAR geometric compatibility, not confirmed class or identity.'
'Track 2 availability is distinct from sensor-wide availability; one Camera hypothesis is accepted experimentally.'
'GT-center X residual exceeds reported X sigma, but these refer to different target points.'
'Exported GT actor velocity switches between zero and values above position-derived speed.'
'GT velocity-reference disagreement limits physical interpretation of EKF velocity RMSE.'
};

limits = {
'Counts do not measure probability of detection or accuracy.'
'Clustering depends on selected filtering and grid parameters.'
'Tracks are provisional and not full-rate validated.'
'Geometric associations are not independently calibrated.'
'Radar and LiDAR may observe different surfaces.'
'One development sequence with 23 matched GT comparisons.'
'GT center differs from the LiDAR observation reference.'
'Reference-point effect is unresolved.'
'The improvement is descriptive, not a causal guarantee.'
'One low-confidence Camera hypothesis; uncalibrated projection.'
'Temporal samples are correlated.'
'GT exporter does not supply physical heading-aligned full dimensions.'
'LiDAR data is a sparse sampled subset.'
'No Track 2 Radar association at the displayed frame.'
'Nominal camera intrinsics and extrinsics only.'
'Associations remain provisional.'
'Time is the vertical axis, not physical elevation.'
'Only three snapshots are presented.'
'Velocity states are not validated by the figure alone.'
'Measurement-model uncertainty remains uncalibrated.'
'Exploratory NIS gate 9; no full consistency test.'
'Only reported X marginal standard deviation is available.'
'Estimator separation is not an accuracy metric.'
'Radar measurements are not consistently beneficial.'
'LiDAR bounding boxes are not verified physical vehicle boxes.'
'Low detector confidence; mixed object/background depths possible.'
'Absence of Track 2 is not evidence of sensor failure.'
'Not an NEES or valid covariance coverage test.'
'GT velocity export exhibits systematic inconsistencies.'
'Actor velocity, AABB center and time sampling references are not reconciled.'
};

assert(numel(titles)==30 && numel(findings)==30 ...
    && numel(limits)==30,'Figure metadata mismatch');

%% Locate figures without changing existing files

figurePath = strings(30,1);
exists = false(30,1);

for i=1:30
    if i==26
        candidate = fullfile(figDir,'Task24_Figure_26_V2.png');
    else
        candidate = fullfile(figDir, ...
            sprintf('Task24_Figure_%02d.png',i));
    end

    figurePath(i) = string(candidate);
    exists(i) = isfile(candidate);
end

FigureNumber = (1:30)';
FigureTitle = string(titles);
MainFinding = string(findings);
Limitation = string(limits);
FilePath = figurePath;
FileExists = exists;

Index = table(FigureNumber,FigureTitle, ...
    MainFinding,Limitation,FilePath,FileExists);

%% Numeric summary

meanL = mean(G.lidar_center_error_m);
meanR = mean(G.radar_center_error_m);
meanC = mean(G.camera_center_error_m);

meanVL = mean(V.lidar_velocity_error_mps);
meanVR = mean(V.radar_velocity_error_mps);

improvement = G.lidar_center_error_m ...
    - G.radar_center_error_m;

zeroFlags = F.zero_actor_during_center_motion;

if ~islogical(zeroFlags)
    if isnumeric(zeroFlags)
        zeroFlags = zeroFlags ~= 0;
    else
        zeroFlags = strcmpi(string(zeroFlags),"true");
    end
end

%% Create report

fid = fopen(reportPath,'w');
assert(fid>=0,'Unable to create report');

fprintf(fid,'# Task 24 — Complete MATLAB Research Findings\n\n');
fprintf(fid,'## 1. Research scope\n\n');
fprintf(fid,['Exploratory Camera-LiDAR-Radar association and EKF ', ...
    'tracking using one clean V2 GEMSTAR recording. ', ...
    'Ground Truth is evaluation-only.\n\n']);

fprintf(fid,'## 2. Experimental evidence\n\n');

fprintf(fid,'- Ground Truth recording: 2122 frames.\n');
fprintf(fid,'- Sampled measurement frames: 53.\n');
fprintf(fid,'- Provisional Track 2 observations: 24.\n');
fprintf(fid,'- Valid GT-center comparisons: 23.\n');
fprintf(fid,'- Radar EKF accepted updates: 4.\n');
fprintf(fid,'- Experimental Camera-bearing updates: 1.\n');
fprintf(fid,'- Generated MATLAB figures: %d of 30 found.\n\n', ...
    sum(exists));

fprintf(fid,'## 3. Position accuracy\n\n');

fprintf(fid,'| Estimator | Mean GT-center error (m) |\n');
fprintf(fid,'|---|---:|\n');
fprintf(fid,'| LiDAR-only | %.6f |\n',meanL);
fprintf(fid,'| LiDAR-Radar | %.6f |\n',meanR);
fprintf(fid,'| Three-sensor | %.6f |\n\n',meanC);

fprintf(fid,'Mean Radar error reduction: %.6f m (%.3f%%).\n\n', ...
    meanL-meanR,100*(meanL-meanR)/meanL);

fprintf(fid,['Radar-improved frames: %d; worsened: %d; ', ...
    'approximately unchanged: %d.\n\n'], ...
    sum(improvement>1e-6),sum(improvement<(-1e-6)), ...
    sum(abs(improvement)<=1e-6));

fprintf(fid,'## 4. Velocity comparison — provisional\n\n');

fprintf(fid,'LiDAR mean 2D velocity error: %.6f m/s.\n\n',meanVL);
fprintf(fid,'LiDAR-Radar mean 2D velocity error: %.6f m/s.\n\n',meanVR);

fprintf(fid,['These errors use the exported actor velocity ', ...
    'and must not be presented as validated physical ', ...
    'velocity performance.\n\n']);

fprintf(fid,'## 5. Ground Truth exporter findings\n\n');

fprintf(fid,['- Reported dimensions use world-axis-aligned ', ...
    'bounding-box half-extents rather than full physical dimensions.\n']);
fprintf(fid,['- Exported actor velocity components were not ', ...
    'converted from Unreal cm/s to OSI m/s in the examined source.\n']);
fprintf(fid,['- Nonzero actor speeds are approximately twice ', ...
    'position-derived speeds during many active-motion samples.\n']);
fprintf(fid,['- Full-rate audit found %d zero-actor-velocity ', ...
    'samples despite finite-difference center motion.\n'], ...
    sum(zeroFlags));
fprintf(fid,['- The root cause of the velocity discrepancy ', ...
    'is unresolved; no correction factor is authorized.\n\n']);

fprintf(fid,'## 6. Figure-by-figure interpretation\n\n');

for i=1:30
    fprintf(fid,'### Figure %02d — %s\n\n',i,titles{i});
    fprintf(fid,'**Finding:** %s\n\n',findings{i});
    fprintf(fid,'**Limitation:** %s\n\n',limits{i});
    fprintf(fid,'**File:** `%s`\n\n',figurePath(i));
    fprintf(fid,'**Present:** %s\n\n',string(exists(i)));
end

fprintf(fid,'## 7. Research validity and limitations\n\n');

fprintf(fid,['- Single development recording; no independent ', ...
    'scenario replication.\n']);
fprintf(fid,'- 23 evaluated frames are temporally correlated.\n');
fprintf(fid,['- Track 2 matched GT object 76897 as nearest ', ...
    'candidate in all 23 audited frames; physical ', ...
    'correspondence remains subject to observation bias.\n']);
fprintf(fid,['- LiDAR cluster position and GT geometric ', ...
    'center are different measurement references.\n']);
fprintf(fid,['- Camera projection and sensor noise are ', ...
    'not independently calibrated.\n']);
fprintf(fid,['- No three-sensor Camera-LiDAR-Radar association ', ...
    'was confirmed at frame 530.\n']);
fprintf(fid,['- Full-state covariance consistency and ', ...
    'NEES were not established.\n']);
fprintf(fid,['- No energy, latency, FPGA acceleration, ', ...
    'or full-rate deployment performance is established.\n\n']);

fprintf(fid,'## 8. Implications for Task 25\n\n');

fprintf(fid,['Task 25 should distinguish sensor availability, ', ...
    'target observability, association confidence, ', ...
    'measurement validity, and estimator uncertainty. ', ...
    'Reliability thresholds need independent validation ', ...
    'rather than tuning to this development recording.\n\n']);

fprintf(fid,'## 9. Conclusions\n\n');

fprintf(fid,['An experimental three-sensor fusion workflow ', ...
    'has been demonstrated. Radar provides a small ', ...
    'mean improvement in GT-center position error ', ...
    'for this recording. Camera produced one accepted ', ...
    'exploratory update without demonstrated accuracy benefit. ', ...
    'Geometry and velocity-export issues must be ', ...
    'accounted for in subsequent validation.\n']);

fclose(fid);

writetable(Index,indexPath);

%% Output

fprintf('\n=== TASK 24 MATLAB RESEARCH REPORT ===\n');
fprintf('FIGURES_EXPECTED=30\n');
fprintf('FIGURES_PRESENT=%d\n',sum(exists));

if any(~exists)
    fprintf('MISSING_FIGURE_NUMBERS=');
    fprintf('%d ',find(~exists));
    fprintf('\n');
end

fprintf('GT_CENTER_MEAN_LIDAR_M=%.6f\n',meanL);
fprintf('GT_CENTER_MEAN_RADAR_M=%.6f\n',meanR);
fprintf('GT_CENTER_MEAN_CAMERA_M=%.6f\n',meanC);

fprintf('GT_VELOCITY_REFERENCE_STATUS=PROVISIONAL\n');
fprintf('GT_VELOCITY_ROOT_CAUSE=UNRESOLVED\n');

fprintf('REPORT=%s\n',reportPath);
fprintf('FIGURE_INDEX=%s\n',indexPath);
fprintf('ORIGINAL_INPUTS_MODIFIED=NO\n');
fprintf('TASK24_MATLAB_FINAL_REPORT_COMPLETE\n');