
%% TASK 19.8L - LiDAR Actor Planarity Analysis
% GEMSTAR - Frame 150
% Compare actor 83185 and actor 83265.
% No additional toolbox required.
%
% Plane: z = ax + by + c
% Small residuals suggest a planar surface.
% Planarity alone does not establish semantic object identity.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base,"08_Extracted_PointClouds");
dataDir = fullfile(base,"02_CSV_Data");
graphDir = fullfile(base,"01_Graphs");

inputFile = fullfile(cloudDir, ...
    "task19_8h_frame150_world_xyz.csv");

assert(isfile(inputFile),"World-coordinate LiDAR CSV missing.");

T = readtable(inputFile);

targetIDs = [83185;83265];

stats = table();

fig = figure("Color","w", ...
    "Position",[100 100 1200 770]);

fprintf("\n=== TASK 19.8L PLANARITY ANALYSIS ===\n");

%% 2. Analyze each actor

for k = 1:numel(targetIDs)

    id = targetIDs(k);

    A = T(T.ObjectID == id,:);

    x = A.WorldX;
    y = A.WorldY;
    z = A.WorldZ;

    assert(numel(z)>=3,"Too few points for plane fitting.");

    %% Least-squares plane fitting
    % Fit world Z as a linear function of world X,Y.

    M = [x,y,ones(size(x))];

    coefficient = M\z;

    a = coefficient(1);
    b = coefficient(2);
    c = coefficient(3);

    zPredicted = M*coefficient;
    verticalResidual = z-zPredicted;

    % Orthogonal distance to fitted plane
    normalScale = sqrt(a*a+b*b+1);
    planeResidual = verticalResidual/normalScale;

    rmse = sqrt(mean(planeResidual.^2));
    medianError = median(abs(planeResidual));
    p95 = prctileLocal(abs(planeResidual),0.95);

    slopeDeg = atan(hypot(a,b))*180/pi;

    %% PCA shape analysis, using basic MATLAB eig()

    P = [x,y,z];
    centered = P-mean(P,1);

    covariance = (centered'*centered)/max(size(P,1)-1,1);

    eigenvalues = sort(real(eig(covariance)),"descend");
    eigenvalues = max(eigenvalues,0);

    totalVariance = sum(eigenvalues);

    if totalVariance>0
        planarityScore = (eigenvalues(2)-eigenvalues(3)) ...
            /totalVariance;
        surfaceVarianceFraction = eigenvalues(3)/totalVariance;
    else
        planarityScore = NaN;
        surfaceVarianceFraction = NaN;
    end

    %% Save statistics

    row = table();

    row.ObjectID = id;
    row.PointCount = numel(z);

    row.PlaneA = a;
    row.PlaneB = b;
    row.PlaneC = c;

    row.SlopeDegrees = slopeDeg;
    row.OrthogonalRMSE_M = rmse;
    row.MedianAbsResidual_M = medianError;
    row.P95AbsResidual_M = p95;

    row.PlanarityScore = planarityScore;
    row.SmallestVarianceFraction = surfaceVarianceFraction;

    stats = [stats;row];

    fprintf("\n--- Object ID %.0f ---\n",id);
    fprintf("Points: %d\n",numel(z));
    fprintf("Fitted plane: z = %.6fx + %.6fy + %.6f\n",a,b,c);
    fprintf("Plane slope: %.3f degrees\n",slopeDeg);
    fprintf("Orthogonal RMSE: %.5f m\n",rmse);
    fprintf("95%% absolute residual: %.5f m\n",p95);
    fprintf("PCA planarity score: %.5f\n",planarityScore);

    %% Plot: XY map colored by plane residual

    subplot(2,2,k);

    scatter(x,y,12,planeResidual,"filled");
    axis equal;
    grid on;

    xlabel("World X (m)");
    ylabel("World Y (m)");
    title(sprintf("ID %.0f - Plane Residuals",id));
    colorbar;

    %% Plot: observed height versus fitted height

    subplot(2,2,k+2);

    scatter(zPredicted,z,12,x,"filled");

    hold on;

    lo = min([z;zPredicted]);
    hi = max([z;zPredicted]);

    if hi-lo<0.01
        lo = lo-0.01;
        hi = hi+0.01;
    end

    plot([lo hi],[lo hi],"k--","LineWidth",1.3);

    xlim([lo hi]);
    ylim([lo hi]);

    axis square;
    grid on;

    xlabel("Predicted World Z (m)");
    ylabel("Measured World Z (m)");

    title(sprintf("ID %.0f - RMSE %.4f m",id,rmse));
    colorbar;

end

%% 3. Save statistics and graph

statsFile = fullfile(dataDir, ...
    "task19_8l_actor_planarity_statistics.csv");

writetable(stats,statsFile);

sgtitle("GEMSTAR - LiDAR Actor Planarity Comparison");

graphFile = fullfile(graphDir, ...
    "task19_8l_actor_planarity_analysis.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 4. Finish

fprintf("\n=== TASK 19.8L COMPLETE ===\n");
fprintf("Statistics CSV saved: %d\n",isfile(statsFile));
fprintf("Planarity graph saved: %d\n",isfile(graphFile));

disp(stats);

fprintf("\nReminder: A good plane fit does not");
fprintf(" prove that an actor is a road surface.\n");

%% Local function - percentile without Statistics Toolbox

function v = prctileLocal(values,fraction)

    values = sort(values(:));
    n = numel(values);

    if n==1
        v = values(1);
        return;
    end

    position = 1+(n-1)*fraction;

    low = floor(position);
    high = ceil(position);

    weight = position-low;

    v = values(low)*(1-weight)+values(high)*weight;

end
