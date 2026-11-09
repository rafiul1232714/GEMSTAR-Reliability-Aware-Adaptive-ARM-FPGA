
%% TASK 19.10F - Input-Observable Scheduler Features
% GEMSTAR fog_mor100, eight frames
%
% Extract features available before RANSAC processing.
% Join offline oracle decisions for ANALYSIS ONLY.
% Oracle results must never become runtime input features.
%
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

decisionFile = fullfile(dataDir, ...
    "task19_10e_offline_configuration_decisions.csv");

assert(isfile(decisionFile), ...
    "Task 19.10E decision CSV missing.");

D = readtable(decisionFile);

frames = [0 50 100 150 200 250 350 450];

features = table();

%% 2. Extract input-only features

fprintf("\n=== TASK 19.10F FEATURE EXTRACTION ===\n");

for k = 1:numel(frames)

    frameID = frames(k);

    filename = sprintf( ...
        "task19_10b_frame%03d_candidate_xyz.csv",frameID);

    path = fullfile(cloudDir,filename);

    assert(isfile(path),"Missing file: %s",path);

    T = readtable(path);

    P = double([T.X,T.Y,T.Z]);

    assert(all(isfinite(P(:))), ...
        "Nonfinite XYZ points detected.");

    %% Consistent ROI

    roiMask = ...
        P(:,1)>=0 & P(:,1)<=20 & ...
        P(:,2)>=-6 & P(:,2)<=6;

    R = P(roiMask,:);

    assert(~isempty(R),"Empty ROI at frame %d",frameID);

    %% Voxel occupancy at 0.25 m

    voxelSize = 0.25;

    voxelIndex = floor(R./voxelSize);

    [~,~,group] = unique(voxelIndex,"rows");

    voxelCount = max(group);

    %% Spatial distribution

    rangeM = sqrt(sum(R.^2,2));

    %% Extract feature row

    row = table();

    row.FrameIndex = frameID;

    row.ValidCandidatePoints = size(P,1);
    row.ValidCandidateFractionPercent = ...
        100*size(P,1)/5271;

    row.ROIPoints = size(R,1);

    row.ROIFractionPercent = ...
        100*size(R,1)/max(size(P,1),1);

    row.VoxelCount025 = voxelCount;

    row.VoxelCompressionPercent = ...
        100*(1-voxelCount/size(R,1));

    row.MedianROIRangeM = median(rangeM);

    row.ROIWidthXM = max(R(:,1))-min(R(:,1));
    row.ROIWidthYM = max(R(:,2))-min(R(:,2));

    row.ROIHeightZM = max(R(:,3))-min(R(:,3));

    features = [features;row];

    fprintf( ...
        "Frame %3d | candidates=%4d | ROI=%4d | voxels=%4d | compression=%.2f%%\n", ...
        frameID, ...
        row.ValidCandidatePoints, ...
        row.ROIPoints, ...
        row.VoxelCount025, ...
        row.VoxelCompressionPercent);

end

%% 3. Save runtime-eligible feature table
% This CSV contains NO offline decisions or RANSAC labels.

featureFile = fullfile(dataDir, ...
    "task19_10f_runtime_observable_features.csv");

writetable(features,featureFile);

%% 4. Join offline decisions ONLY for research analysis

[found,position] = ismember( ...
    features.FrameIndex,D.FrameIndex);

assert(all(found),"An offline decision is missing.");

analysis = features;

analysis.OfflineSelectedMethod = ...
    string(D.SelectedMethod(position));

analysis.OfflineSelectedVoxelSizeM = ...
    D.SelectedVoxelSizeM(position);

analysis.OfflineSpeedRatioVsFull = ...
    D.SpeedRatioVsFull(position);

analysis.NeedsReferenceFallback = ...
    analysis.OfflineSelectedMethod=="Full-reference fallback";

analysisFile = fullfile(dataDir, ...
    "task19_10f_features_vs_offline_oracle.csv");

writetable(analysis,analysisFile);

%% 5. Visualization

fig = figure("Color","w", ...
    "Position",[100 100 1150 760]);

subplot(2,2,1);

plot(frames,features.ValidCandidatePoints, ...
    "-o","LineWidth",1.4);

hold on;

plot(frames,features.ROIPoints, ...
    "-s","LineWidth",1.4);

xlabel("Frame index");
ylabel("Number of points");

title("Observable Workload Across Frames");

legend("Valid candidates","ROI points", ...
    "Location","best");

grid on;

subplot(2,2,2);

plot(frames,features.VoxelCompressionPercent, ...
    "-o","LineWidth",1.4);

xlabel("Frame index");
ylabel("Voxel compression (%)");

title("0.25 m Voxel Compression");
grid on;

subplot(2,2,3);

scatter( ...
    features.ROIPoints, ...
    features.VoxelCompressionPercent, ...
    90,double(analysis.NeedsReferenceFallback), ...
    "filled");

xlabel("ROI points");
ylabel("Voxel compression (%)");

title("Input Features vs Offline Fallback");

grid on;
colormap(gca,parula(2));
clim([-0.5 1.5]);

cb = colorbar;
cb.Ticks = [0 1];
cb.TickLabels = {"Voxel accepted","Full fallback"};

subplot(2,2,4);

scatter( ...
    features.VoxelCount025, ...
    analysis.OfflineSpeedRatioVsFull, ...
    90,double(analysis.NeedsReferenceFallback), ...
    "filled");

hold on;
yline(1,"k--","Equal latency");

xlabel("0.25 m occupied voxels");
ylabel("Offline speed ratio");

title("Input Workload vs Offline Selection");

grid on;
clim([-0.5 1.5]);

sgtitle("GEMSTAR - Scheduler Feature Feasibility");

graphFile = fullfile(graphDir, ...
    "task19_10f_scheduler_feature_analysis.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 6. Final outputs

fprintf("\n=== FEATURE / OFFLINE DECISION COMPARISON ===\n");

disp(analysis(:,{ ...
    'FrameIndex', ...
    'ValidCandidatePoints', ...
    'ROIPoints', ...
    'VoxelCount025', ...
    'VoxelCompressionPercent', ...
    'OfflineSelectedMethod', ...
    'OfflineSelectedVoxelSizeM'}));

fprintf("\n=== TASK 19.10F COMPLETE ===\n");

fprintf("Feature CSV saved: %d\n",isfile(featureFile));
fprintf("Research analysis CSV saved: %d\n",isfile(analysisFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

fprintf("\nWARNING:\n");
fprintf("Offline labels are included for analysis only.\n");
fprintf("No adaptive policy has been validated.\n");
fprintf("Feature extraction overhead is not benchmarked yet.\n");
