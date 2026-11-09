%% TASK 21.3B - CORRECTED MISSING-DATA AUDIT
clear; clc;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_21_Final_Research');

inputDir = fullfile(task,'02_Imported_Data');
outputDir = fullfile(task,'04_CSV_Results');
findingsDir = fullfile(task,'06_Research_Findings');

files = {
    'task20_28_radar_world_points.mat'
    'task20_49_50m_radar_returns.mat'
    'task20_55_ray_alignment.mat'
    'task20_57_ray_box_intersections.mat'
};

fprintf('\n=== TASK 21.3B CORRECTED QUALITY AUDIT ===\n');

records = cell(0,7);

for k = 1:numel(files)
    S = load(fullfile(inputDir,files{k}),'T');
    T = S.T;

    missingCount = 0;
    nonfiniteCount = 0;

    for j = 1:width(T)
        name = T.Properties.VariableNames{j};
        column = T.(name);

        if isnumeric(column)
            missingCount = missingCount + nnz(isnan(column(:)));
            nonfiniteCount = nonfiniteCount + ...
                nnz(isinf(column(:)));

        elseif islogical(column)
            % Logical values are always present.

        else
            % Convert textual, categorical and cell fields
            % to strings for consistent blank checks.
            values = string(column);
            blanks = ismissing(values) | ...
                strlength(strtrim(values)) == 0;

            missingCount = missingCount + nnz(blanks(:));
        end
    end

    names = T.Properties.VariableNames;
    frameColumn = find(strcmpi(names,'Frame'),1);

    frameZeroRows = 0;
    uniqueFrames = NaN;

    if ~isempty(frameColumn)
        frames = double(T.(names{frameColumn}));
        frameZeroRows = nnz(frames == 0);
        uniqueFrames = numel(unique(frames(isfinite(frames))));
    end

    [~,shortName] = fileparts(files{k});

    records(end+1,:) = {
        shortName,height(T),width(T), ...
        missingCount,nonfiniteCount, ...
        frameZeroRows,uniqueFrames
    };

    fprintf('%s | Missing=%d | Inf=%d | Frame0=%d\n', ...
        shortName,missingCount,nonfiniteCount, ...
        frameZeroRows);
end

summary = cell2table(records, ...
    'VariableNames', ...
    {'Dataset','Rows','Columns','MissingValues', ...
     'InfiniteValues','FrameZeroRows','UniqueFrames'});

% Additional inspection of the corrected 50 m recording.
S = load(fullfile(inputDir, ...
    'task20_49_50m_radar_returns.mat'),'T');

R = S.T;

frames = double(R.Frame);
ranges = double(R.RangeM);

frameZero = frames == 0;
nearZero = ranges < 0.001;

fprintf('\n=== FRAME ZERO VALIDATION ===\n');
fprintf('All candidate returns: %d\n',height(R));
fprintf('Frame-zero returns: %d\n',nnz(frameZero));
fprintf('Near-zero returns (<1 mm): %d\n',nnz(nearZero));
fprintf('Near-zero returns in frame zero: %d\n', ...
    nnz(nearZero & frameZero));
fprintf('Returns excluding frame zero: %d\n', ...
    nnz(~frameZero));

csvPath = fullfile(outputDir, ...
    'task21_03b_corrected_quality.csv');

writetable(summary,csvPath);

notesPath = fullfile(findingsDir, ...
    'task21_03b_quality_validation.txt');

fid = fopen(notesPath,'w');
if fid < 0
    error('Could not create research findings file.');
end

fprintf(fid,'TASK 21.3B - CORRECTED DATA QUALITY\n\n');
fprintf(fid,'50m candidate returns: %d\n',height(R));
fprintf(fid,'Frame-zero returns: %d\n',nnz(frameZero));
fprintf(fid,'Near-zero returns: %d\n',nnz(nearZero));
fprintf(fid,'Near-zero in frame zero: %d\n', ...
    nnz(nearZero & frameZero));
fprintf(fid,'Returns excluding frame zero: %d\n', ...
    nnz(~frameZero));
fprintf(fid,'\nMissing fields and invalid numeric values');
fprintf(fid,' were audited separately.\n');
fprintf(fid,'Empty radar returns are not automatically');
fprintf(fid,' corrupted data.\n');
fprintf(fid,'Original datasets remain unchanged.\n');
fprintf(fid,'No detection accuracy or energy claims.\n');

fclose(fid);

fprintf('\n=== CORRECTED QUALITY SUMMARY ===\n');
disp(summary);

fprintf('CSV saved: %d\n',isfile(csvPath));
fprintf('Findings saved: %d\n',isfile(notesPath));

fprintf('\n=== TASK 21.3B COMPLETE ===\n');
