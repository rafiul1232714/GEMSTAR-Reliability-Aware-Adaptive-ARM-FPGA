%% TASK 17.7A — MATLAB TIMESTAMP AND SENSOR GEOMETRY VALIDATION
clear; clc; close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_17_Final_Research";

csvDir = fullfile(base, "02_CSV_Data");
graphDir = fullfile(base, "01_Graphs");

sv = readtable(fullfile(csvDir, "task17_sensor_timestamps.csv"));
gt = readtable(fullfile(csvDir, "task17_groundtruth_timestamps.csv"));
mounts = readtable(fullfile(csvDir, "task17_sensor_mounting_positions.csv"));

%% 1. Timestamp validation
assert(height(sv) == height(gt), "Frame count mismatch");
assert(all(sv.Frame == gt.Frame), "Frame indices mismatch");

dt_ms = (sv.TimestampSeconds - gt.TimestampSeconds) * 1000;

maxError = max(abs(dt_ms));
meanError = mean(abs(dt_ms));
exactMatches = sum(abs(dt_ms) < 1e-6);

intervals_ms = diff(sv.TimestampSeconds) * 1000;
medianInterval = median(intervals_ms);
longThreshold = 2 * medianInterval;
longIntervals = sum(intervals_ms > longThreshold);

fprintf("\n=== TASK 17 MATLAB TIMESTAMP VALIDATION ===\n");
fprintf("Frames: %d\n", height(sv));
fprintf("Exact matches: %d\n", exactMatches);
fprintf("Maximum difference: %.9f ms\n", maxError);
fprintf("Mean difference: %.9f ms\n", meanError);
fprintf("Median interval: %.4f ms\n", medianInterval);
fprintf("Long intervals: %d\n", longIntervals);

%% 2. Sensor geometry
fprintf("\n=== SENSOR MOUNTING GEOMETRY ===\n");

positions = [mounts.X_m, mounts.Y_m, mounts.Z_m];

for i = 1:height(mounts)
    fprintf("%s: (%.3f, %.3f, %.3f) m\n", ...
        string(mounts.Sensor(i)), ...
        positions(i,1), positions(i,2), positions(i,3));
end

for i = 1:height(mounts)
    for j = i+1:height(mounts)
        distance = norm(positions(i,:) - positions(j,:));

        fprintf("%s <-> %s: %.4f m\n", ...
            string(mounts.Sensor(i)), ...
            string(mounts.Sensor(j)), distance);
    end
end

%% 3. Reconstruct transformation matrices
for i = 1:height(mounts)
    r = mounts.Roll_rad(i);
    p = mounts.Pitch_rad(i);
    y = mounts.Yaw_rad(i);

    Rx = [1 0 0; 0 cos(r) -sin(r); 0 sin(r) cos(r)];
    Ry = [cos(p) 0 sin(p); 0 1 0; -sin(p) 0 cos(p)];
    Rz = [cos(y) -sin(y) 0; sin(y) cos(y) 0; 0 0 1];

    T = eye(4);
    T(1:3,1:3) = Rz * Ry * Rx;
    T(1:3,4) = positions(i,:)';

    fprintf("\n%s transformation matrix:\n", string(mounts.Sensor(i)));
    disp(T);

    assert(norm(T(1:3,4) - positions(i,:)') < 1e-9);
    assert(norm(inv(T)*T - eye(4), "fro") < 1e-9);
end

%% 4. Generate plots
figure("Color", "w", "Position", [100 100 1000 650]);

tiledlayout(2,1);

nexttile;
plot(sv.Frame, dt_ms, "LineWidth", 1.2);
grid on;
xlabel("Frame");
ylabel("SV - GT (ms)");
title("GEMSTAR GroundTruth / SensorView Timestamp Alignment");

nexttile;
plot(sv.Frame(2:end), intervals_ms, "LineWidth", 1);
hold on;
yline(longThreshold, "--r", "2x median threshold");
grid on;
xlabel("Frame");
ylabel("Interval (ms)");
title("SensorView Message Timing Irregularities");

exportgraphics(gcf, ...
    fullfile(graphDir, "task17_matlab_timestamp_validation.png"), ...
    "Resolution", 200);

%% 5. Save validation summary
metrics = [
    "Frames"
    "ExactMatches"
    "MaximumErrorMs"
    "MeanErrorMs"
    "MedianIntervalMs"
    "LongIntervals"
];

values = [
    height(sv)
    exactMatches
    maxError
    meanError
    medianInterval
    longIntervals
];

results = table(metrics, values, ...
    "VariableNames", {"Metric", "Value"});

writetable(results, ...
    fullfile(csvDir, "task17_matlab_validation_results.csv"));

fprintf("\n=== MATLAB VALIDATION COMPLETE ===\n");
fprintf("Graph saved: task17_matlab_timestamp_validation.png\n");
fprintf("CSV saved: task17_matlab_validation_results.csv\n");
