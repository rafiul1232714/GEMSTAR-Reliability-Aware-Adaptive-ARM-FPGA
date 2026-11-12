%% Task 26.4E - LiDAR CPU Benchmark Visualization
% Uses actual Task 26.4D timing results.
% Does not modify Task 24 source data.
% Timings are isolated CPU stage measurements, not energy.

clear; clc; close all;

root = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_26_Final_Research";

csvDir = fullfile(root, "02_CSV_Data");
plotDir = fullfile(root, "04_Plots");

rawFile = fullfile(csvDir, "task26_4D_lidar_cpu_timing.csv");
summaryFile = fullfile(csvDir, "task26_4D_lidar_cpu_summary.csv");

if ~isfile(rawFile) || ~isfile(summaryFile)
    error("Task 26.4D benchmark CSV files are missing.");
end

T = readtable(rawFile, "TextType", "string");
S = readtable(summaryFile, "TextType", "string");

if height(T) ~= 2650 || height(S) ~= 106
    error("Unexpected benchmark CSV dimensions.");
end

frames = sort(unique(S.frame));

if numel(frames) ~= 53
    error("Expected 53 unique frames.");
end

n = numel(frames);

filterMedian = zeros(n,1);
clusterMedian = zeros(n,1);
filterP99 = zeros(n,1);
clusterP99 = zeros(n,1);

inputPoints = zeros(n,1);
filteredPoints = zeros(n,1);
clusters = zeros(n,1);

for i = 1:n
    f = frames(i);

    a = S(S.frame == f & S.stage == "filter",:);
    b = S(S.frame == f & S.stage == "cluster",:);

    if height(a) ~= 1 || height(b) ~= 1
        error("Missing or duplicate stage at frame %d.",f);
    end

    filterMedian(i) = a.median_ms;
    clusterMedian(i) = b.median_ms;

    filterP99(i) = a.p99_ms;
    clusterP99(i) = b.p99_ms;

    inputPoints(i) = a.input_points;
    filteredPoints(i) = a.filtered_points;
    clusters(i) = a.clusters_found;
end

outputFiles = [
    "task26_4E_lidar_filter_vs_cluster.png"
    "task26_4E_lidar_scaling.png"
    "task26_4E_lidar_p99.png"
    "task26_4E_lidar_points_clusters.png"
];

for k = 1:numel(outputFiles)
    if isfile(fullfile(plotDir,outputFiles(k)))
        error("Existing plot preserved: %s",outputFiles(k));
    end
end

if ~isfolder(plotDir)
    mkdir(plotDir);
end

%% Figure 1 - Filtering versus clustering latency

f1 = figure("Color","w","Position",[100 100 1050 480]);

plot(frames,filterMedian,"-o","LineWidth",1.4);
hold on;
plot(frames,clusterMedian,"-s","LineWidth",1.4);
hold off;

xlabel("GEMSTAR frame number");
ylabel("Median CPU time per stage (ms)");
title("Task 26 - LiDAR filtering versus clustering");
legend("Spatial filtering","Grid clustering", ...
    "Location","best");
grid on;

saveas(f1,fullfile(plotDir,outputFiles(1)));

%% Figure 2 - Workload scaling

f2 = figure("Color","w","Position",[100 100 1050 480]);

scatter(inputPoints,filterMedian,45,"filled");
hold on;
scatter(filteredPoints,clusterMedian,45,"filled");
hold off;

xlabel("Points processed by stage");
ylabel("Median stage execution time (ms)");
title("Task 26 - LiDAR processing cost versus point count");

legend("Filtering: raw input points", ...
       "Clustering: filtered points", ...
       "Location","best");

grid on;
saveas(f2,fullfile(plotDir,outputFiles(2)));

%% Figure 3 - p99 latency

f3 = figure("Color","w","Position",[100 100 1050 480]);

plot(frames,filterP99,"-o","LineWidth",1.4);
hold on;
plot(frames,clusterP99,"-s","LineWidth",1.4);
hold off;

xlabel("GEMSTAR frame number");
ylabel("p99 CPU stage duration (ms)");
title("Task 26 - LiDAR p99 stage latency");

legend("Filtering p99","Clustering p99", ...
    "Location","best");

grid on;
saveas(f3,fullfile(plotDir,outputFiles(3)));

%% Figure 4 - Retained points and clusters

f4 = figure("Color","w","Position",[100 100 1050 480]);

yyaxis left;
plot(frames,inputPoints,"--","LineWidth",1.5);
hold on;
plot(frames,filteredPoints,"-","LineWidth",2);
ylabel("LiDAR point count");

yyaxis right;
stairs(frames,clusters,"LineWidth",1.8);
ylabel("Candidate clusters per frame");

xlabel("GEMSTAR frame number");
title("Task 26 - LiDAR point retention and clusters");

legend("Raw input points","Filtered points", ...
    "Candidate clusters","Location","best");

grid on;
saveas(f4,fullfile(plotDir,outputFiles(4)));

%% Results summary

disp("=== TASK 26.4E MATLAB ANALYSIS ===");

fprintf("FRAMES: %d\n",n);
fprintf("TIMED_MEASUREMENTS: %d\n",height(T));

fprintf("MEDIAN_OF_FRAME_FILTER_MEDIANS_MS: %.6f\n", ...
    median(filterMedian));

fprintf("MEDIAN_OF_FRAME_CLUSTER_MEDIANS_MS: %.6f\n", ...
    median(clusterMedian));

fprintf("MAX_FRAME_FILTER_P99_MS: %.6f\n", ...
    max(filterP99));

fprintf("MAX_FRAME_CLUSTER_P99_MS: %.6f\n", ...
    max(clusterP99));

fprintf("TOTAL_RAW_POINTS_ACROSS_FRAMES: %d\n", ...
    sum(inputPoints));

fprintf("TOTAL_FILTERED_POINTS_ACROSS_FRAMES: %d\n", ...
    sum(filteredPoints));

fprintf("OVERALL_POINT_RETENTION_PERCENT: %.2f\n", ...
    100 * sum(filteredPoints)/sum(inputPoints));

disp("NOTE: No OSI parsing, tracking or energy measured.");
disp("NOTE: These are exploratory geometric clusters.");
disp("NOTE: Per-frame p99 estimates use only 25 runs.");
disp("TASK26_4E_LIDAR_MATLAB_ANALYSIS_PASS");
