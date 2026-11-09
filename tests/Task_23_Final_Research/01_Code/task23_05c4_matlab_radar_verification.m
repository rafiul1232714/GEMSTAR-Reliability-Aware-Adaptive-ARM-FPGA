%% TASK 23.5C-4: INDEPENDENT MATLAB RADAR VERIFICATION
clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root, 'tests', 'Task_23_Final_Research');

csvDir = fullfile(task, '02_CSV_Data');
graphDir = fullfile(task, '03_Graphs');
findingsDir = fullfile(task, '06_Research_Findings');

rawPath = fullfile(csvDir, ...
    'task23_05c1_radar_measurements.csv');

pythonPath = fullfile(csvDir, ...
    'task23_05c3_radar_3d_points.csv');

summaryPath = fullfile(csvDir, ...
    'task23_05c1_radar_frame_summary.csv');

assert(isfile(rawPath), 'Raw Radar CSV missing');
assert(isfile(pythonPath), 'Python 3D CSV missing');
assert(isfile(summaryPath), 'Radar summary CSV missing');

raw = readtable(rawPath);
python = readtable(pythonPath);
summary = readtable(summaryPath);

c = 299792458.0;

tolRange = 1e-8;
tolVelocity = 1e-8;
tolXYZ = 1e-8;

fprintf('\n=== TASK 23.5C-4 MATLAB VERIFICATION ===\n');

results = struct( ...
    'PairID', {}, ...
    'Frame', {}, ...
    'PositivePoints', {}, ...
    'MaxRangeErrorM', {}, ...
    'MaxRadialVelocityErrorMps', {}, ...
    'MaxSensorCoordinateErrorM', {}, ...
    'MaxVehicleCoordinateErrorM', {}, ...
    'ValidationPass', {} ...
);

allPass = true;
totalPoints = 0;
steadyPoints = 0;

for pair = 1:4
    for frame = [0 1 25 99]

        group = raw( ...
            raw.PairID == pair & raw.Frame == frame, :);

        saved = python( ...
            python.PairID == pair & python.Frame == frame, :);

        config = summary( ...
            summary.PairID == pair & ...
            summary.Frame == frame, :);

        assert(height(group) == 100, ...
            'Expected 100 Radar slots');

        assert(height(config) == 1, ...
            'Expected one Radar configuration');

        % Derive validity independently from raw measurements.
        valid = ...
            isfinite(group.TimeOfFlightS) & ...
            group.TimeOfFlightS > 0 & ...
            isfinite(group.SignalStrength) & ...
            group.SignalStrength > 0;

        group = group(valid, :);

        group = sortrows(group, 'RayIndex');
        saved = sortrows(saved, 'RayIndex');

        count = height(group);

        assert(height(saved) == count, ...
            'Python/MATLAB point-count mismatch');

        assert(isequal(group.RayIndex, saved.RayIndex), ...
            'Radar ray indices do not match');

        frequency = config.EmitterFrequencyHz;

        assert(isfinite(frequency) && frequency > 0, ...
            'Invalid emitter frequency');

        % Independent range and Doppler calculations.
        ranges = c .* group.TimeOfFlightS ./ 2;

        velocities = ...
            group.DopplerShiftHz .* c ./ (2 * frequency);

        az = group.HorizontalAngleRad;
        el = group.VerticalAngleRad;

        % Unreal-local sensor coordinates.
        x = ranges .* cos(el) .* cos(az);
        yUE = ranges .* cos(el) .* sin(az);
        z = ranges .* sin(el);

        % GEMSTAR ToOSI convention: reverse Y.
        sensorOSI = [x, -yUE, z];

        mounting = [
            config.MountX, ...
            config.MountY, ...
            config.MountZ
        ];

        vehicleOSI = sensorOSI + mounting;

        if count > 0
            pythonSensor = [
                saved.SensorOSI_X, ...
                saved.SensorOSI_Y, ...
                saved.SensorOSI_Z
            ];

            pythonVehicle = [
                saved.VehicleOSI_X, ...
                saved.VehicleOSI_Y, ...
                saved.VehicleOSI_Z
            ];

            rangeError = max(abs( ...
                ranges - saved.RangeM));

            velocityError = max(abs( ...
                velocities - ...
                saved.EquivalentRadialVelocityMps));

            sensorError = max(abs( ...
                sensorOSI(:) - pythonSensor(:)));

            vehicleError = max(abs( ...
                vehicleOSI(:) - pythonVehicle(:)));
        else
            rangeError = 0;
            velocityError = 0;
            sensorError = 0;
            vehicleError = 0;
        end

        passed = ...
            rangeError <= tolRange && ...
            velocityError <= tolVelocity && ...
            sensorError <= tolXYZ && ...
            vehicleError <= tolXYZ;

        allPass = allPass && passed;
        totalPoints = totalPoints + count;

        if frame >= 25
            steadyPoints = steadyPoints + count;
        end

        result.PairID = pair;
        result.Frame = frame;
        result.PositivePoints = count;
        result.MaxRangeErrorM = rangeError;
        result.MaxRadialVelocityErrorMps = velocityError;
        result.MaxSensorCoordinateErrorM = sensorError;
        result.MaxVehicleCoordinateErrorM = vehicleError;
        result.ValidationPass = passed;

        results(end+1) = result;

        fprintf( ...
            ['Pair %d | Frame %02d | Points=%3d | ' ...
             'RangeErr=%.3e | XYZErr=%.3e | PASS=%d\n'], ...
            pair, frame, count, rangeError, ...
            vehicleError, passed);
    end
end

%% Save MATLAB verification table
resultTable = struct2table(results);

outputCSV = fullfile(csvDir, ...
    'task23_05c4_matlab_python_comparison.csv');

writetable(resultTable, outputCSV);

%% Independent MATLAB plot
figure('Color', 'w', 'Position', [100 100 900 500]);

hold on;

for pair = 1:4
    subset = resultTable(resultTable.PairID == pair, :);

    plot(subset.Frame, subset.PositivePoints, ...
        '-o', 'LineWidth', 1.5, ...
        'DisplayName', sprintf('Pair %d', pair));
end

xlabel('Sampled frame');
ylabel('Positive Radar returns');
title('MATLAB: Radar point availability');
legend('Location', 'best');
grid on;

graphPath = fullfile(graphDir, ...
    'task23_05c4_matlab_radar_point_counts.png');

saveas(gcf, graphPath);
close(gcf);

%% Save research findings
findings.Task = '23.5C-4';
findings.Method = 'Independent MATLAB calculation';
findings.FramesVerified = height(resultTable);
findings.TotalPoints = totalPoints;
findings.SteadyStateCandidatePoints = steadyPoints;
findings.AllChecksPassed = allPass;
findings.ToleranceM = tolXYZ;
findings.ValidationType = ...
    'Cross-language numerical consistency';
findings.Limitation = ...
    ['This does not establish independent target accuracy ' ...
     'or physical Doppler validity.'];

jsonPath = fullfile(findingsDir, ...
    'task23_05c4_matlab_verification_findings.json');

fid = fopen(jsonPath, 'w');
assert(fid ~= -1, 'Cannot write MATLAB findings JSON');
fprintf(fid, '%s', jsonencode(findings));
fclose(fid);

fprintf('\n=== TASK 23.5C-4 FINAL VERIFICATION ===\n');
fprintf('Frames verified: %d\n', height(resultTable));
fprintf('Radar points verified: %d\n', totalPoints);
fprintf('Steady-state candidate points: %d\n', steadyPoints);
fprintf('All MATLAB checks passed: %d\n', allPass);
fprintf('Comparison CSV saved: %d\n', isfile(outputCSV));
fprintf('Graph saved: %d\n', isfile(graphPath));
fprintf('Findings JSON saved: %d\n', isfile(jsonPath));

assert(height(resultTable) == 16, ...
    'Unexpected number of Radar frames');
assert(totalPoints == 544, ...
    'Unexpected total Radar point count');
assert(steadyPoints == 237, ...
    'Unexpected steady-state point count');
assert(allPass, ...
    'MATLAB/Python numerical consistency failed');

fprintf('\n=== TASK 23.5C-4 COMPLETE ===\n');
