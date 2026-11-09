
%% TASK 19.8H - LiDAR Sensor-to-World Alignment
% GEMSTAR - Frame 150
% Uses SensorView embedded host pose
% Initial alignment: must be checked against simulation geometry

clear;
clc;
close all;

%% 1. Paths

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

cloudDir = fullfile(base, "08_Extracted_PointClouds");
dataDir  = fullfile(base, "02_CSV_Data");
graphDir = fullfile(base, "01_Graphs");

lidarFile = fullfile(cloudDir, ...
    "task19_2a_frame150_candidate_xyz.csv");

gtFile = fullfile(dataDir, ...
    "task19_8e_gt_frame150_objects.csv");

assert(isfile(lidarFile), "LiDAR CSV missing.");
assert(isfile(gtFile), "Ground-truth CSV missing.");

%% 2. Load data

T = readtable(lidarFile);
GT = readtable(gtFile);

P = [T.X,T.Y,T.Z];

%% 3. Recorded host pose (SensorView frame 150)

hostPosition = [ ...
    43.1051134868421, ...
   -16.284652960526316, ...
     0.0 ...
];

hostYaw = 0.5720295371638123;

%% 4. LiDAR mounting offset

lidarMount = [2.6, 0.0, 0.7];

% Rotation in OSI right-handed XY coordinates
R = [
    cos(hostYaw), -sin(hostYaw), 0;
    sin(hostYaw),  cos(hostYaw), 0;
    0,             0,            1
];

%% 5. Convert sensor-local points to world coordinates

Pvehicle = P + lidarMount;

Pworld = (R * Pvehicle')' + hostPosition;

%% 6. Export world-coordinate point cloud

World = T;

World.WorldX = Pworld(:,1);
World.WorldY = Pworld(:,2);
World.WorldZ = Pworld(:,3);

worldFile = fullfile(cloudDir, ...
    "task19_8h_frame150_world_xyz.csv");

writetable(World,worldFile);

%% 7. Compare with ground-truth object centers

fig = figure("Color","w", ...
    "Position",[100 100 1050 650], ...
    "Name","GEMSTAR LiDAR World Alignment");

scatter(Pworld(:,1),Pworld(:,2), ...
    10,T.RangeM,"filled");

hold on;

scatter(GT.X,GT.Y, ...
    90,"r","x","LineWidth",2);

for k = 1:height(GT)
    text(GT.X(k),GT.Y(k), ...
        sprintf("  GT %d",GT.ObjectID(k)), ...
        "FontSize",9);
end

xlabel("World X (m)");
ylabel("World Y (m)");
title("GEMSTAR - LiDAR Point Cloud and Ground-Truth Centers");

axis equal;
grid on;

legend("LiDAR points","GT moving-object centers", ...
    "Location","best");

colorbar;

graphFile = fullfile(graphDir, ...
    "task19_8h_world_alignment.png");

exportgraphics(fig,graphFile,"Resolution",200);

%% 8. Report distances to nearest ground-truth center
% These are distances between centers only, not object-level matches.

fprintf("\n=== TASK 19.8H WORLD ALIGNMENT ===\n");

for k = 1:height(GT)

    delta = Pworld(:,1:2) - [GT.X(k), GT.Y(k)];

    distance = sqrt(sum(delta.^2,2));

    fprintf("GT ID %d: nearest LiDAR point XY distance = %.3f m\n", ...
        GT.ObjectID(k),min(distance));
end

%% 9. Verification

fprintf("\n=== TASK 19.8H COMPLETE ===\n");

fprintf("World XYZ CSV saved: %d\n",isfile(worldFile));
fprintf("Alignment graph saved: %d\n",isfile(graphFile));
fprintf("Transformed LiDAR points: %d\n",size(Pworld,1));

fprintf("\nNote: This is an initial coordinate transformation.");
fprintf("\nGround-truth association is not yet validated.\n");
