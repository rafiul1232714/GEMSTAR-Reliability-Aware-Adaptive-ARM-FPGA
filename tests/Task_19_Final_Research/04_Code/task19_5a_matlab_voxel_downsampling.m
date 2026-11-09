%% TASK 19.5A - LiDAR Voxel Downsampling
clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base, "08_Extracted_PointClouds");
graphDir = fullfile(base, "01_Graphs");
dataDir = fullfile(base, "02_CSV_Data");

T = readtable(fullfile(cloudDir, ...
    "task19_4a_frame150_roi_xyz.csv"));

P = [T.X, T.Y, T.Z];
voxelSizes = [0.10, 0.25, 0.50];

originalCount = size(P,1);
remainingCounts = zeros(3,1);
reductions = zeros(3,1);
meanErrors = zeros(3,1);

fig = figure("Color","w", ...
    "Position",[100 100 1100 750]);

subplot(2,2,1);
scatter3(P(:,1),P(:,2),P(:,3),8,T.RangeM,"filled");
axis equal; grid on; view(40,20);
title(sprintf("Original ROI: %d points",originalCount));
xlabel("X (m)"); ylabel("Y (m)"); zlabel("Z (m)");

for k = 1:numel(voxelSizes)

    s = voxelSizes(k);

    % Map each point to an integer voxel coordinate.
    voxelIndex = floor(P ./ s);

    % Group points occupying the same voxel.
    [~,~,groupID] = unique(voxelIndex,"rows");

    nGroups = max(groupID);
    Q = zeros(nGroups,3);

    % Each output point is a voxel centroid.
    for j = 1:nGroups
        members = P(groupID == j,:);
        Q(j,:) = mean(members,1);
    end

    remainingCounts(k) = size(Q,1);
    reductions(k) = 100 * (1-size(Q,1)/originalCount);

    % Mean distance from each original point
    % to its own voxel's centroid.
    reconstructed = Q(groupID,:);
    error = sqrt(sum((P-reconstructed).^2,2));
    meanErrors(k) = mean(error);

    % Save centroid points. Original per-ray metadata is
    % not copied because a centroid combines multiple rays.
    voxelCloud = table(Q(:,1),Q(:,2),Q(:,3), ...
        'VariableNames',{'X','Y','Z'});

    filename = sprintf( ...
        "task19_5a_frame150_voxel_%dmm.csv",round(s*1000));

    writetable(voxelCloud,fullfile(cloudDir,filename));

    subplot(2,2,k+1);
    scatter3(Q(:,1),Q(:,2),Q(:,3),12,Q(:,1),"filled");
    axis equal; grid on; view(40,20);
    xlabel("X (m)"); ylabel("Y (m)"); zlabel("Z (m)");
    title(sprintf("%.2f m: %d points",s,size(Q,1)));

    fprintf("Voxel %.2f m: %d points, reduction %.2f%%, " + ...
        "mean displacement %.5f m\n", ...
        s,remainingCounts(k),reductions(k),meanErrors(k));
end

exportgraphics(fig,fullfile(graphDir, ...
    "task19_5a_voxel_comparison.png"),"Resolution",200);

summary = table(voxelSizes(:),remainingCounts,reductions, ...
    meanErrors,'VariableNames', ...
    {'VoxelSizeM','RemainingPoints','ReductionPercent', ...
    'MeanWithinVoxelDisplacementM'});

summaryFile = fullfile(dataDir, ...
    "task19_5a_voxel_comparison.csv");

writetable(summary,summaryFile);

fprintf("\n=== TASK 19.5A COMPLETE ===\n");
fprintf("Original ROI points: %d\n",originalCount);
disp(summary);
fprintf("Summary CSV saved: %d\n",isfile(summaryFile));
fprintf("Comparison graph saved: %d\n", ...
    isfile(fullfile(graphDir,"task19_5a_voxel_comparison.png")));