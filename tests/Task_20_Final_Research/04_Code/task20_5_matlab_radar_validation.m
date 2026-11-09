clear;
clc;
close all;

base = "E:\GEMSTAR_Project\sensor-health-monitor" + ...
       "\tests\Task_20_Final_Research";

dataDir = fullfile(base, "02_CSV_Data");
graphDir = fullfile(base, "01_Graphs");
findingsDir = fullfile(base, "06_Research_Findings");

if ~isfolder(graphDir)
    mkdir(graphDir);
end

if ~isfolder(findingsDir)
    mkdir(findingsDir);
end

rawFile = fullfile(dataDir, ...
    "task20_2_radar_reflection_samples.csv");

pythonFile = fullfile(dataDir, ...
    "task20_4_radar_reconstructed_returns.csv");

assert(isfile(rawFile), "Task 20.2 CSV missing");
assert(isfile(pythonFile), "Task 20.4 CSV missing");

fprintf("\n=== TASK 20.5 MATLAB RADAR VALIDATION ===\n");

raw = readtable(rawFile, "TextType", "string");
py = readtable(pythonFile, "TextType", "string");

% Same simulator constants established in Task 20.3.
c = 299705543.0;
frequency = 77000000000.0;

% Select exactly the candidates used by Python.
valid = raw.CandidateReturn == 1;
selected = raw(valid, :);

assert(height(selected) == height(py), ...
    "Python and MATLAB row counts disagree");

% Verify that both datasets are in the same order.
sameRows = all( ...
    selected.Recording == py.Recording & ...
    selected.FrameIndex == py.FrameIndex & ...
    selected.RadarIndex == py.RadarIndex & ...
    selected.ReflectionIndex == py.ReflectionIndex);

assert(sameRows, ...
    "Input row identity or order mismatch");

tof = selected.TimeOfFlightRaw;
doppler = selected.DopplerShiftRaw;

azimuth = selected.AzimuthRad;
elevation = selected.ElevationRad;

% Reconstruct from source measurements.
rangeM = (tof .* c) ./ 2.0;
velocityMps = (doppler .* c) ./ (2.0 .* frequency);

localX = rangeM .* cos(elevation) .* cos(azimuth);
localY = rangeM .* cos(elevation) .* sin(azimuth);
localZ = rangeM .* sin(elevation);

% Compare with Python CSV.
errorRange = abs(rangeM - py.DistanceM);
errorVelocity = abs(velocityMps - py.RadialVelocityMps);
errorX = abs(localX - py.LocalX);
errorY = abs(localY - py.LocalY);
errorZ = abs(localZ - py.LocalZ);

maxErrors = [
    max(errorRange);
    max(errorVelocity);
    max(errorX);
    max(errorY);
    max(errorZ)
];

names = [
    "Range";
    "RadialVelocity";
    "LocalX";
    "LocalY";
    "LocalZ"
];

tolerances = [
    1e-9;
    1e-9;
    1e-9;
    1e-9;
    1e-9
];

passed = isfinite(maxErrors) & ...
         (maxErrors <= tolerances);

verification = table( ...
    names, maxErrors, tolerances, passed, ...
    'VariableNames', ...
    {'Quantity','MaxAbsoluteError', ...
     'Tolerance','Pass'});

summaryFile = fullfile( ...
    dataDir, "task20_5_matlab_validation_summary.csv");

writetable(verification, summaryFile);

% Full independent-calculation export.
matlabResults = table( ...
    selected.Recording, ...
    selected.FrameIndex, ...
    selected.ReflectionIndex, ...
    rangeM, velocityMps, ...
    localX, localY, localZ, ...
    errorRange, errorVelocity, ...
    errorX, errorY, errorZ, ...
    'VariableNames', { ...
    'Recording','FrameIndex','ReflectionIndex', ...
    'MATLABRangeM','MATLABRadialVelocityMps', ...
    'MATLABX','MATLABY','MATLABZ', ...
    'ErrorRangeM','ErrorVelocityMps', ...
    'ErrorX','ErrorY','ErrorZ'});

outputFile = fullfile( ...
    dataDir, "task20_5_matlab_reconstruction.csv");

writetable(matlabResults, outputFile);

fprintf("Reconstructed returns: %d\n", height(py));

fprintf("\n=== NUMERICAL COMPARISON ===\n");
disp(verification);

% Visualize a real baseline_clear radar frame.
mask = selected.Recording == "baseline_clear";

if any(mask)
    firstFrame = min(selected.FrameIndex(mask));

    sample = mask & ...
        selected.FrameIndex == firstFrame;

    fig = figure( ...
        'Visible', 'off', ...
        'Color', 'w', ...
        'Position', [100 100 1200 500]);

    subplot(1, 2, 1);
    scatter(localX(sample), localY(sample), ...
        40, rangeM(sample), 'filled');
    hold on;
    plot(0, 0, 'kx', 'MarkerSize', 12, ...
        'LineWidth', 2);
    axis equal;
    grid on;
    xlabel('Provisional local X (m)');
    ylabel('Provisional local Y (m)');
    title('MATLAB Radar Reconstruction');
    colorbar;

    subplot(1, 2, 2);
    scatter(rangeM(sample), ...
        velocityMps(sample), 40, 'filled');
    grid on;
    xlabel('Range (m)');
    ylabel('Signed radial velocity (m/s)');
    title('Range-Doppler Visualization');

    sgtitle( ...
        'GEMSTAR Radar - MATLAB Numerical Validation');

    graphFile = fullfile(graphDir, ...
        "task20_5_matlab_radar_visualization.png");

    exportgraphics(fig, graphFile, ...
        'Resolution', 180);

    close(fig);
else
    graphFile = "";
end

allPassed = all(passed);

reportFile = fullfile(findingsDir, ...
    "task20_5_matlab_validation_notes.txt");

fid = fopen(reportFile, 'w');

assert(fid > 0, "Cannot write findings report");

fprintf(fid, "TASK 20.5 MATLAB VALIDATION\n");
fprintf(fid, "Candidate returns: %d\n", height(py));
fprintf(fid, "All numeric checks pass: %d\n", allPassed);
fprintf(fid, "Coordinate convention verified: NO\n");
fprintf(fid, "Ground-truth accuracy verified: NO\n");
fprintf(fid, "FPGA energy measured: NO\n");
fprintf(fid, "This is cross-language numerical consistency.\n");

fclose(fid);

fprintf("\n=== TASK 20.5 COMPLETE ===\n");
fprintf("Candidate returns: %d\n", height(py));
fprintf("All numerical checks passed: %d\n", allPassed);
fprintf("Summary CSV saved: %d\n", isfile(summaryFile));
fprintf("MATLAB CSV saved: %d\n", isfile(outputFile));
fprintf("Graph saved: %d\n", isfile(graphFile));
fprintf("Research notes saved: %d\n", isfile(reportFile));

fprintf("\nLIMITATION:\n");
fprintf("Matching Python does not establish ground truth.\n");
fprintf("Coordinate convention still requires validation.\n");
fprintf("No energy measurement has been performed.\n");

if ~allPassed
    error("MATLAB/Python numerical comparison failed");
end
