
%% TASK 19.8M - Robust LiDAR Geometry Analysis with SVD
% GEMSTAR Frame 150
% Compare IDs 83185 and 83265.
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
    "task19_8h_frame150_world_xyz.csv");

assert(isfile(inputFile), "World-coordinate point cloud missing.");

T = readtable(inputFile);

targetIDs = [83185;83265];

stats = table();

fig = figure("Color","w", ...
    "Position",[100 100 1200 720]);

fprintf("\n=== TASK 19.8M SVD GEOMETRY ===\n");

%% 2. Analyze each actor

for k = 1:numel(targetIDs)

    id = targetIDs(k);

    mask = T.ObjectID == id;

    P = [T.WorldX(mask), ...
         T.WorldY(mask), ...
         T.WorldZ(mask)];

    assert(size(P,1)>=3, "Insufficient points.");
    assert(all(isfinite(P(:))), "Nonfinite XYZ detected.");

    %% Center coordinates to improve numerical stability

    centroid = mean(P,1);
    Q = P-centroid;

    %% SVD of the centered 3D coordinates

    [~,S,V] = svd(Q,0);

    singularValues = diag(S);

    s1 = singularValues(1);
    s2 = singularValues(2);
    s3 = singularValues(3);

    relativeS2 = s2/max(s1,eps);
    relativeS3 = s3/max(s1,eps);

    %% PCA shape descriptors

    lambda = singularValues.^2;

    if lambda(1)>0
        linearity = (lambda(1)-lambda(2))/lambda(1);
        planarity = (lambda(2)-lambda(3))/lambda(1);
        scattering = lambda(3)/lambda(1);
    else
        linearity = NaN;
        planarity = NaN;
        scattering = NaN;
    end

    %% Orthogonal distance to best-fit 3D line

    mainDirection = V(:,1);

    projectedLine = ...
        (Q*mainDirection)*mainDirection';

    lineResidual = ...
        sqrt(sum((Q-projectedLine).^2,2));

    lineRMSE = sqrt(mean(lineResidual.^2));

    %% Orthogonal distance to best-fit 3D plane

    normal = V(:,3);

    planeResidual = Q*normal;
    planeRMSE = sqrt(mean(planeResidual.^2));

    %% Determine numerical 3D rank
    % Relative threshold is only a diagnostic setting.

    rankTolerance = 1e-6;
    numericalRank = sum( ...
        singularValues > rankTolerance*max(s1,eps));

    %% Evaluate XY footprint separately

    XY = P(:,1:2);
    XY = XY-mean(XY,1);

    [~,Sxy,~] = svd(XY,0);

    singularXY = diag(Sxy);

    xyWidthRatio = ...
        singularXY(2)/max(singularXY(1),eps);

    %% Output statistics

    row = table();

    row.ObjectID = id;
    row.PointCount = size(P,1);

    row.SingularValue1 = s1;
    row.SingularValue2 = s2;
    row.SingularValue3 = s3;

    row.RelativeS2 = relativeS2;
    row.RelativeS3 = relativeS3;

    row.Linearity = linearity;
    row.Planarity = planarity;
    row.Scattering = scattering;

    row.LineRMSE_M = lineRMSE;
    row.PlaneRMSE_M = planeRMSE;

    row.NumericalRank = numericalRank;
    row.XYWidthRatio = xyWidthRatio;

    stats = [stats;row];

    fprintf("\n--- Object ID %.0f ---\n",id);
    fprintf("Points: %d\n",size(P,1));
    fprintf("Singular values: %.6g, %.6g, %.6g\n", ...
        s1,s2,s3);
    fprintf("Relative S2/S1: %.8f\n",relativeS2);
    fprintf("Relative S3/S1: %.8f\n",relativeS3);
    fprintf("Linearity score: %.6f\n",linearity);
    fprintf("Planarity score: %.6f\n",planarity);
    fprintf("Scattering score: %.6f\n",scattering);
    fprintf("Best-fit line RMSE: %.6f m\n",lineRMSE);
    fprintf("Best-fit plane RMSE: %.6f m\n",planeRMSE);
    fprintf("Numerical rank: %d\n",numericalRank);
    fprintf("XY footprint width ratio: %.8f\n", ...
        xyWidthRatio);

    %% Plot singular value ratios

    subplot(2,2,k);

    bar([1,relativeS2,relativeS3]);

    set(gca,"YScale","log");
    ylim([1e-12 2]);

    grid on;

    xticks(1:3);
    xticklabels(["S1/S1","S2/S1","S3/S1"]);

    ylabel("Relative singular value");
    title(sprintf("ID %.0f - SVD Spectrum",id));

    %% Plot point coordinates in PCA axes

    PCAcoordinates = Q*V;

    subplot(2,2,k+2);

    scatter(PCAcoordinates(:,1), ...
        PCAcoordinates(:,2), ...
        12,PCAcoordinates(:,3),"filled");

    xlabel("Principal direction 1 (m)");
    ylabel("Principal direction 2 (m)");

    title(sprintf("ID %.0f - PCA Projection",id));

    grid on;
    colorbar;

end

%% 3. Save outputs

summaryFile = fullfile(dataDir, ...
    "task19_8m_svd_geometry_summary.csv");

writetable(stats,summaryFile);

sgtitle("GEMSTAR LiDAR - SVD Geometry Validation");

graphFile = fullfile(graphDir, ...
    "task19_8m_svd_geometry.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 4. Finish

fprintf("\n=== TASK 19.8M COMPLETE ===\n");

fprintf("Statistics CSV saved: %d\n", ...
    isfile(summaryFile));

fprintf("SVD graph saved: %d\n", ...
    isfile(graphFile));

disp(stats);

fprintf("\nInterpret geometry using singular values");
fprintf(" AND residuals, not plane RMSE alone.\n");
