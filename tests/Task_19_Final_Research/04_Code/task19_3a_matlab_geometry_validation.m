%% TASK 19.3A - LiDAR Geometry Validation

clear;
clc;
close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_19_Final_Research";

csvFile = fullfile(base, ...
    "08_Extracted_PointClouds", ...
    "task19_2a_frame150_candidate_xyz.csv");

graphDir = fullfile(base, "01_Graphs");
dataDir = fullfile(base, "02_CSV_Data");

T = readtable(csvFile);

x = T.X;
y = T.Y;
z = T.Z;

%% 1. Check reconstructed range consistency

calculatedRange = sqrt(x.^2 + y.^2 + z.^2);
rangeError = abs(calculatedRange - T.RangeM);

fprintf("\n=== TASK 19.3A GEOMETRY VALIDATION ===\n");
fprintf("Points: %d\n", height(T));
fprintf("Maximum range reconstruction error: %.12f m\n", ...
    max(rangeError));

%% 2. Examine vertical scan rows

fig1 = figure("Color", "w");

scatter(x, z, 14, T.VerticalIndex, "filled");

xlabel("X - Forward (m)");
ylabel("Z - Sensor-local height (m)");
title("LiDAR vertical scan-row geometry");

grid on;
axis equal;

cb = colorbar;
cb.Label.String = "Vertical scan index";

exportgraphics(fig1, ...
    fullfile(graphDir, "task19_3a_vertical_geometry.png"), ...
    "Resolution", 200);

%% 3. Examine horizontal scan columns

fig2 = figure("Color", "w");

scatter(x, y, 14, T.HorizontalIndex, "filled");

xlabel("X - Forward (m)");
ylabel("Y - Lateral (m)");
title("LiDAR horizontal scan-column geometry");

grid on;
axis equal;

cb = colorbar;
cb.Label.String = "Horizontal scan index";

exportgraphics(fig2, ...
    fullfile(graphDir, "task19_3a_horizontal_geometry.png"), ...
    "Resolution", 200);

%% 4. Reconstructed height distribution

fig3 = figure("Color", "w");

histogram(z, 40);

xlabel("Sensor-local Z (m)");
ylabel("Number of points");
title("LiDAR reconstructed height distribution");

grid on;

exportgraphics(fig3, ...
    fullfile(graphDir, "task19_3a_height_histogram.png"), ...
    "Resolution", 200);

%% 5. Summary by vertical scan row

[G, rowIDs] = findgroups(T.VerticalIndex);

pointCount = splitapply(@numel, z, G);
meanZ = splitapply(@mean, z, G);
medianRange = splitapply(@median, T.RangeM, G);

rowStats = table(rowIDs, pointCount, meanZ, medianRange, ...
    "VariableNames", { ...
    "VerticalIndex", "PointCount", "MeanZ", "MedianRangeM"});

outCSV = fullfile(dataDir, ...
    "task19_3a_vertical_row_statistics.csv");

writetable(rowStats, outCSV);

%% 6. Final results

fprintf("Minimum sensor-local Z: %.3f m\n", min(z));
fprintf("Maximum sensor-local Z: %.3f m\n", max(z));
fprintf("Mean sensor-local Z: %.3f m\n", mean(z));
fprintf("Vertical scan rows represented: %d\n", height(rowStats));

fprintf("\n=== TASK 19.3A COMPLETE ===\n");
fprintf("Statistics CSV saved: %d\n", isfile(outCSV));
fprintf("Vertical geometry graph saved: %d\n", ...
    isfile(fullfile(graphDir, "task19_3a_vertical_geometry.png")));
fprintf("Horizontal geometry graph saved: %d\n", ...
    isfile(fullfile(graphDir, "task19_3a_horizontal_geometry.png")));
fprintf("Height histogram saved: %d\n", ...
    isfile(fullfile(graphDir, "task19_3a_height_histogram.png")));