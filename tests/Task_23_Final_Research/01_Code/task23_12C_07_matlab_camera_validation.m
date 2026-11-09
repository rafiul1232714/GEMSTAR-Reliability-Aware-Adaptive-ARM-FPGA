% Task 23.12.C.7 - Independent MATLAB Camera validation
% Validate OpenCV Camera ROI luminance and contrast.

clear;
clc;

task = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research';

imageDir = fullfile(task, '08_Processed_Data', ...
    'Camera_Weather_Comparison');

outCsv = fullfile(task, '02_CSV_Data', ...
    'task23_12C_07_matlab_camera_validation.csv');

if isfile(outCsv)
    error('Output CSV already exists. Refusing to overwrite.');
end

scenarios = {'CLEAR'; 'FOG100'; 'FOG20'};

filenames = {
    'CLEAR_t0200ms.png';
    'FOG100_t0200ms.png';
    'FOG20_t0200ms.png'
};

% Reference values from Task 23.12.C.6 Python results
refLuminance = [169.41; 178.88; 194.90];
refContrast = [45.9824; 43.6135; 31.0490];

n = numel(scenarios);

matlabLuminance = zeros(n,1);
matlabContrast = zeros(n,1);

fprintf('\n=== MATLAB CAMERA VALIDATION ===\n');

for i = 1:n

    path = fullfile(imageDir, filenames{i});

    if ~isfile(path)
        error('Missing image: %s', path);
    end

    rgb = imread(path);

    if ~isa(rgb, 'uint8') || ...
       ~isequal(size(rgb), [480 640 3])
        error('Invalid RGB image: %s', filenames{i});
    end

    % Python ROI=(128,96,384,288), zero-based indexing.
    % MATLAB uses one-based indexing.
    roi = rgb(97:384, 129:512, :);

    gray = rgb2gray(roi);

    matlabLuminance(i) = mean(double(gray(:)));

    % Population standard deviation, matching numpy.std().
    matlabContrast(i) = std(double(gray(:)), 1);

    fprintf('%s LUMA=%.4f CONTRAST=%.4f\n', ...
        scenarios{i}, ...
        matlabLuminance(i), ...
        matlabContrast(i));

end

lumaDifference = abs(matlabLuminance - refLuminance);
contrastDifference = abs(matlabContrast - refContrast);

% Small tolerance allows different uint8 conversion rounding.
tolerance = 0.5;

passed = ...
    all(lumaDifference <= tolerance) && ...
    all(contrastDifference <= tolerance);

results = table( ...
    scenarios, ...
    matlabLuminance, ...
    refLuminance, ...
    lumaDifference, ...
    matlabContrast, ...
    refContrast, ...
    contrastDifference, ...
    'VariableNames', { ...
        'Scenario', ...
        'MATLAB_Luminance', ...
        'Python_Luminance', ...
        'Luminance_Difference', ...
        'MATLAB_Contrast', ...
        'Python_Contrast', ...
        'Contrast_Difference' ...
    });

writetable(results, outCsv);

disp(results);

fprintf('CSV_SAVED=%s\n', outCsv);
fprintf('TOLERANCE=%.4f\n', tolerance);

if ~passed
    error('TASK23_12C_07_MATLAB_VALIDATION_FAILED');
end

fprintf('TASK23_12C_07_MATLAB_VALIDATION_PASS\n');
