%% TASK 24.10.5.3D.3 - FIGURE 27
% Observed sensor support and EKF update decisions.
% Descriptive measurement availability, NOT calibrated reliability.
% Original Task 24 data remains read-only.

clear; clc; close all;

base = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget';
data = fullfile(base,'C02_V2_EKF_Input_53Frames_V1');
out = fullfile(base,'MATLAB_Task24_Analysis');

figdir = fullfile(out,'01_Graphs');
csvdir = fullfile(out,'02_CSV_Data');

if ~isfolder(figdir), mkdir(figdir); end
if ~isfolder(csvdir), mkdir(csvdir); end

figpath = fullfile(figdir,'Task24_Figure_27.png');
csvpath = fullfile(csvdir, ...
    'Task24_Figure27_SensorSupport_Timeline_V1.csv');

assert(~isfile(figpath),'Figure exists. No overwrite.');
assert(~isfile(csvpath),'CSV exists. No overwrite.');

%% Load measurement and estimator evidence

S = readtable(fullfile(data,'selected_frames.csv'));
T = readtable(fullfile(data,'lidar_temporal_tracks_v1.csv'));
M = readtable(fullfile(data,'radar_track_matches_v1.csv'));
E = readtable(fullfile(data,'lidar_radar_ekf_track2_v1.csv'));
F = readtable(fullfile(data, ...
    'three_estimator_matched_comparison_v1.csv'));

assert(height(S)==53,'Expected 53 sampled frames');
assert(height(E)==24,'Expected 24 EKF observations');
assert(height(F)==24,'Expected 24 estimator comparisons');
assert(isequal(E.frame,F.frame), ...
    'EKF and three-estimator frames do not match');

assert(numel(unique(S.frame))==53, ...
    'Duplicate selected frame');
assert(numel(unique(E.frame))==24, ...
    'Duplicate EKF frame');

frames = S.frame;
time = S.time_s;

n = height(S);
lidarPoints = zeros(n,1);
radarMatches = zeros(n,1);
nonzeroDoppler = zeros(n,1);

trackPresent = false(n,1);
radarAccepted = false(n,1);
cameraObserved = false(n,1);
cameraAccepted = false(n,1);

matched2 = M(M.track_id==2,:);
track2 = T(T.track_id==2,:);

for k=1:n
    fr = frames(k);

    tp = track2(track2.frame==fr,:);
    if height(tp)>1
        error('Duplicate Track 2 at frame %d',fr);
    end

    if height(tp)==1
        trackPresent(k)=true;
        lidarPoints(k)=tp.point_count(1);
    end

    mp = matched2(matched2.frame==fr,:);
    radarMatches(k)=height(mp);
    nonzeroDoppler(k)=sum(double(mp.nonzero_doppler)~=0);

    ep = E(E.frame==fr,:);
    if height(ep)==1
        radarAccepted(k) = ...
            string(ep.radar_status(1))=="ACCEPTED";
    end

    fp = F(F.frame==fr,:);
    if height(fp)==1
        cameraAccepted(k) = ...
            string(fp.camera_status(1))=="EXPERIMENTAL_ACCEPTED";
    end

    % The only observed Camera bearing hypothesis
    % in this development sequence was at frame 530.
    cameraObserved(k) = fr==530;
end

assert(sum(trackPresent)==24, ...
    'Expected 24 Track 2 observations');
assert(sum(radarAccepted)==4, ...
    'Expected four accepted Radar updates');
assert(sum(cameraObserved)==1, ...
    'Expected one Camera observation');

% Earlier Task 24.9.6B recorded one accepted Camera
% update at frame 530. Verify the saved status.
if sum(cameraAccepted)~=1
    fprintf(['WARNING: Camera status field does not report ', ...
             'exactly one accepted update.\n']);
    disp(unique(string(F.camera_status)));
end

%% Figure: four linked timelines

f = figure('Color','w', ...
    'Position',[80 60 1350 1100]);

tiledlayout(4,1,'TileSpacing','compact', ...
    'Padding','compact');

nexttile;
stem(time,lidarPoints,'filled','LineWidth',1.2);
ylabel('Cluster points');
title('A. LiDAR support for provisional Track 2');
grid on;

nexttile;
stem(time,radarMatches,'filled','LineWidth',1.2);
ylabel('Radar matches');
title('B. Provisional Radar returns associated with Track 2');
grid on;

nexttile;
stem(time,nonzeroDoppler, ...
    'filled','LineWidth',1.2);
hold on;
scatter(time(radarAccepted), ...
    nonzeroDoppler(radarAccepted), ...
    90,'r','filled', ...
    'DisplayName','Radar EKF update accepted');
ylabel('Nonzero Doppler');
title('C. Doppler availability and accepted Radar updates');
legend('Matched nonzero Doppler','Accepted update', ...
    'Location','best');
grid on;

nexttile;
stem(time,double(cameraObserved), ...
    'LineWidth',1.5);
hold on;
scatter(time(cameraAccepted), ...
    double(cameraAccepted(cameraAccepted)), ...
    100,'r','filled');
ylim([-0.1 1.4]);
yticks([0 1]);
yticklabels({'None','Observed'});
xlabel('Recording time (s)');
ylabel('Camera');
title('D. Camera hypothesis and experimental EKF update');
legend('Camera hypothesis','Experimental accepted update', ...
    'Location','best');
grid on;

sgtitle(['Figure 27 — Track 2 sensor support ', ...
    'and exploratory fusion decisions']);

exportgraphics(f,figpath,'Resolution',220);
close(f);

%% Export aligned 53-frame evidence

Evidence = table(frames,time, ...
    trackPresent,lidarPoints, ...
    radarMatches,nonzeroDoppler, ...
    radarAccepted,cameraObserved,cameraAccepted, ...
    'VariableNames',{ ...
    'Frame','Time_s','Track2Present', ...
    'LiDARClusterPoints', ...
    'RadarMatchedReturns', ...
    'RadarMatchedNonzeroDoppler', ...
    'RadarEKFUpdateAccepted', ...
    'CameraHypothesisPresent', ...
    'CameraExperimentalUpdateAccepted'});

writetable(Evidence,csvpath);

%% Results

fprintf('\n=== TASK 24 FIGURE 27 RESULTS ===\n');
fprintf('SAMPLED_FRAMES=%d\n',n);
fprintf('TRACK2_OBSERVATIONS=%d\n',sum(trackPresent));
fprintf('TOTAL_RADAR_MATCHES=%d\n',sum(radarMatches));
fprintf('TOTAL_NONZERO_MATCHED_DOPPLER=%d\n', ...
    sum(nonzeroDoppler));
fprintf('RADAR_EKF_ACCEPTED_UPDATES=%d\n', ...
    sum(radarAccepted));
fprintf('CAMERA_HYPOTHESES=%d\n',sum(cameraObserved));
fprintf('CAMERA_EXPERIMENTAL_UPDATES=%d\n', ...
    sum(cameraAccepted));

fprintf('FRAMES_WITH_TRACK2_AND_RADAR=%d\n', ...
    sum(trackPresent & radarMatches>0));

fprintf('FRAMES_WITH_TRACK2_AND_NONZERO_DOPPLER=%d\n', ...
    sum(trackPresent & nonzeroDoppler>0));

fprintf('FIGURE=%s\n',figpath);
fprintf('EVIDENCE_CSV=%s\n',csvpath);
fprintf('RELIABILITY_CALIBRATED=NO\n');
fprintf('ASSOCIATIONS_PROVISIONAL=YES\n');
fprintf('GROUND_TRUTH_USED_FOR_ASSOCIATION=NO\n');
fprintf('ORIGINAL_FILES_MODIFIED=NO\n');
fprintf('TASK24_MATLAB_FIGURE27_COMPLETE\n');