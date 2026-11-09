
%% TASK 19.8I - LiDAR Proximity to Ground Truth Object 76865
% GEMSTAR - Frame 150
% Diagnostic spatial association, not validated object detection.
% No additional toolbox required.

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base, "08_Extracted_PointClouds");
dataDir = fullfile(base, "02_CSV_Data");
graphDir = fullfile(base, "01_Graphs");

lidarFile = fullfile(cloudDir, ...
    "task19_8h_frame150_world_xyz.csv");

gtFile = fullfile(dataDir, ...
    "task19_8e_gt_frame150_objects.csv");

assert(isfile(lidarFile), "World-coordinate LiDAR CSV missing.");
assert(isfile(gtFile), "Ground-truth object CSV missing.");

%% 2. Load data

T = readtable(lidarFile);
GT = readtable(gtFile);

requiredColumns = ["WorldX","WorldY","WorldZ","ObjectID"];

assert(all(ismember(requiredColumns, ...
    string(T.Properties.VariableNames))), ...
    "A required LiDAR column is missing.");

%% 3. Select ground-truth object 76865

targetID = 76865;

idx = find(GT.ObjectID == targetID, 1);

assert(~isempty(idx), "Ground-truth object 76865 missing.");

center = [GT.X(idx), GT.Y(idx), GT.Z(idx)];

dimensions = [ ...
    GT.Length(idx), ...
    GT.Width(idx), ...
    GT.Height(idx) ...
];

P = [T.WorldX,T.WorldY,T.WorldZ];

%% 4. Calculate point distances

delta = P - center;

distanceXY = hypot(delta(:,1),delta(:,2));

distance3D = sqrt(sum(delta.^2,2));

[nearestXY,nearestIndex] = min(distanceXY);

fprintf("\n=== TASK 19.8I GT OBJECT PROXIMITY ===\n");

fprintf("Ground-truth object ID: %d\n",targetID);

fprintf("Center: X=%.3f Y=%.3f Z=%.3f m\n",center);

fprintf("Dimensions: %.3f x %.3f x %.3f m\n",dimensions);

fprintf("\nNearest point (horizontal distance):\n");
fprintf("XY distance: %.3f m\n",nearestXY);
fprintf("3D distance: %.3f m\n",distance3D(nearestIndex));

fprintf("Point position: %.3f, %.3f, %.3f\n", ...
    P(nearestIndex,:));

fprintf("Point simulator ObjectID: %.0f\n", ...
    T.ObjectID(nearestIndex));

%% 5. Count points in nearby areas

radii = [1;2;3];

nearbyCounts = zeros(size(radii));

for k = 1:numel(radii)
    nearbyCounts(k) = sum(distanceXY <= radii(k));
end

fprintf("\nNearby points (horizontal distance):\n");

for k = 1:numel(radii)
    fprintf("Within %.1f m: %d points\n", ...
        radii(k),nearbyCounts(k));
end

%% 6. Check a provisional axis-aligned 3D box
% This is NOT a rotated object bounding box.
% Ground-truth orientation and reference-point semantics
% must be verified before interpreting box membership.

halfSize = dimensions / 2;

margin = 0.3;

insideApproxBox = ...
    abs(delta(:,1)) <= halfSize(1) + margin & ...
    abs(delta(:,2)) <= halfSize(2) + margin & ...
    abs(delta(:,3)) <= halfSize(3) + margin;

fprintf("\nProvisional axis-aligned 3D box:\n");
fprintf("Points inside (+0.3 m margin): %d\n", ...
    sum(insideApproxBox));

%% 7. Analyze ObjectIDs near the target

nearMask = distanceXY <= 3;

nearIDs = T.ObjectID(nearMask);

if ~isempty(nearIDs)

    [uniqueIDs,~,group] = unique(nearIDs);
    counts = accumarray(group,1);

    objectSummary = table();
    objectSummary.ObjectID = uniqueIDs;
    objectSummary.PointCount = counts;

    fprintf("\n=== LIDAR OBJECT IDS WITHIN 3 M ===\n");
    disp(objectSummary);

else

    objectSummary = table();
    objectSummary.ObjectID = zeros(0,1);
    objectSummary.PointCount = zeros(0,1);

    fprintf("\nNo points within 3 m.\n");

end

%% 8. Save nearby points

Nearby = T(nearMask,:);

Nearby.DistanceXYToGT = distanceXY(nearMask);
Nearby.Distance3DToGT = distance3D(nearMask);
Nearby.InsideApproxBox = insideApproxBox(nearMask);

nearFile = fullfile(cloudDir, ...
    "task19_8i_gt76865_nearby_points.csv");

writetable(Nearby,nearFile);

summaryFile = fullfile(dataDir, ...
    "task19_8i_gt76865_object_id_distribution.csv");

writetable(objectSummary,summaryFile);

%% 9. Visualize nearby cloud

fig = figure("Color","w", ...
    "Position",[100 100 1150 500]);

subplot(1,2,1);

scatter(P(:,1),P(:,2),9,[0.75 0.75 0.75],"filled");
hold on;

scatter(P(nearMask,1),P(nearMask,2), ...
    18,P(nearMask,3),"filled");

scatter(center(1),center(2), ...
    120,"r","x","LineWidth",2);

rectangle( ...
    "Position",[center(1)-halfSize(1), ...
                center(2)-halfSize(2), ...
                dimensions(1),dimensions(2)], ...
    "EdgeColor","r","LineStyle","--", ...
    "LineWidth",1.5);

xlabel("World X (m)");
ylabel("World Y (m)");

title("GT 76865 - Nearby LiDAR Points");
axis equal;
grid on;

xlim(center(1)+[-5 5]);
ylim(center(2)+[-5 5]);
colorbar;

subplot(1,2,2);

scatter(P(nearMask,1),P(nearMask,3), ...
    20,P(nearMask,2),"filled");

hold on;

scatter(center(1),center(3), ...
    120,"r","x","LineWidth",2);

xlabel("World X (m)");
ylabel("World Z (m)");

title("Nearby Points - Vertical Distribution");

grid on;
colorbar;

graphFile = fullfile(graphDir, ...
    "task19_8i_gt76865_proximity_analysis.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 10. Completion

fprintf("\n=== TASK 19.8I COMPLETE ===\n");

fprintf("Nearby points CSV saved: %d\n",isfile(nearFile));
fprintf("Object-ID summary saved: %d\n",isfile(summaryFile));
fprintf("Analysis graph saved: %d\n",isfile(graphFile));

fprintf("\nIMPORTANT: Spatial proximity is not yet");
fprintf(" proof of ground-truth object association.\n");
