
%% TASK 19.8N - Final DBSCAN Cluster Quality Assessment
% GEMSTAR frame 150
% Geometric screening only, not semantic classification.
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir  = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inputFile = fullfile(cloudDir, ...
    "task19_7a_frame150_clustered_points.csv");

assert(isfile(inputFile),"DBSCAN point cloud missing.");

T = readtable(inputFile);

required = ["X","Y","Z","ClusterID","ObjectID"];

assert(all(ismember(required, ...
    string(T.Properties.VariableNames))), ...
    "Required CSV columns missing.");

%% 2. Extract valid cluster IDs

clusterIDs = unique(T.ClusterID);
clusterIDs = clusterIDs(clusterIDs > 0);

stats = table();

fig = figure("Color","w", ...
    "Position",[100 100 1150 550]);

fprintf("\n=== TASK 19.8N CLUSTER QUALITY ===\n");

%% 3. Analyze each cluster

for k = 1:numel(clusterIDs)

    cid = clusterIDs(k);

    A = T(T.ClusterID == cid,:);

    P = [A.X,A.Y,A.Z];

    assert(size(P,1)>=3, ...
        "Too few points for SVD.");

    Q = P-mean(P,1);

    [~,S,V] = svd(Q,0);

    s = diag(S);

    s1 = s(1);
    s2 = s(2);
    s3 = s(3);

    ratio21 = s2/max(s1,eps);
    ratio31 = s3/max(s1,eps);

    lambda = s.^2;

    linearity = (lambda(1)-lambda(2)) ...
        /max(lambda(1),eps);

    planarity = (lambda(2)-lambda(3)) ...
        /max(lambda(1),eps);

    lineRMSE = sqrt(mean( ...
        sum((Q-(Q*V(:,1))*V(:,1)').^2,2)));

    planeRMSE = sqrt(mean((Q*V(:,3)).^2));

    span = max(P,[],1)-min(P,[],1);

    %% Actor-ID consistency

    [ids,~,g] = unique(A.ObjectID);
    counts = accumarray(g,1);

    [dominantCount,index] = max(counts);

    dominantID = ids(index);
    dominantPercent = ...
        100*dominantCount/height(A);

    %% Screening flags
    % These are exploratory thresholds, not validated
    % obstacle / non-obstacle classification rules.

    lowPointCount = height(A)<10;
    elongated = ratio21<0.10;
    thinVertical = span(3)<0.05;
    mixedActors = numel(ids)>1;

    %% Save results

    row = table();

    row.ClusterID = cid;
    row.PointCount = height(A);

    row.DominantObjectID = dominantID;
    row.DominantIDPercent = dominantPercent;
    row.UniqueObjectIDs = numel(ids);

    row.S2OverS1 = ratio21;
    row.S3OverS1 = ratio31;

    row.Linearity = linearity;
    row.Planarity = planarity;

    row.LineRMSE_M = lineRMSE;
    row.PlaneRMSE_M = planeRMSE;

    row.XSpan_M = span(1);
    row.YSpan_M = span(2);
    row.ZSpan_M = span(3);

    row.LowPointCountFlag = lowPointCount;
    row.ElongatedFlag = elongated;
    row.ThinVerticalFlag = thinVertical;
    row.MixedActorFlag = mixedActors;

    row.NeedsFurtherValidation = ...
        lowPointCount || elongated || ...
        thinVertical || mixedActors;

    stats = [stats;row];

    fprintf("\n--- Cluster %d ---\n",cid);

    fprintf("Points: %d\n",height(A));
    fprintf("Dominant actor ID: %.0f\n",dominantID);
    fprintf("Dominant ID fraction: %.2f%%\n",dominantPercent);

    fprintf("S2/S1: %.6f\n",ratio21);
    fprintf("S3/S1: %.6f\n",ratio31);

    fprintf("Line RMSE: %.6f m\n",lineRMSE);
    fprintf("Plane RMSE: %.6f m\n",planeRMSE);

    fprintf("Dimensions: %.3f x %.3f x %.3f m\n",span);

    fprintf("Low point count flag: %d\n",lowPointCount);
    fprintf("Elongated flag: %d\n",elongated);
    fprintf("Thin vertical flag: %d\n",thinVertical);
    fprintf("Mixed actor flag: %d\n",mixedActors);

    fprintf("Needs further validation: %d\n", ...
        row.NeedsFurtherValidation);

    %% Plot the cluster in PCA coordinates

    subplot(1,numel(clusterIDs),k);

    principalCoords = Q*V;

    scatter(principalCoords(:,1), ...
        principalCoords(:,2), ...
        20,principalCoords(:,3),"filled");

    xlabel("PCA direction 1 (m)");
    ylabel("PCA direction 2 (m)");

    title(sprintf( ...
        "Cluster %d - %d points",cid,height(A)));

    grid on;
    axis equal;
    colorbar;

end

%% 4. Save results

summaryFile = fullfile(dataDir, ...
    "task19_8n_final_cluster_quality.csv");

writetable(stats,summaryFile);

sgtitle("GEMSTAR - Final DBSCAN Cluster Geometry Assessment");

graphFile = fullfile(graphDir, ...
    "task19_8n_cluster_quality.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 5. Completion

fprintf("\n=== TASK 19.8N COMPLETE ===\n");

fprintf("Quality CSV saved: %d\n",isfile(summaryFile));
fprintf("Graph saved: %d\n",isfile(graphFile));

disp(stats);

fprintf("\nScreening flags are NOT ground-truth labels.\n");
fprintf("Detection precision and recall remain unmeasured.\n");
