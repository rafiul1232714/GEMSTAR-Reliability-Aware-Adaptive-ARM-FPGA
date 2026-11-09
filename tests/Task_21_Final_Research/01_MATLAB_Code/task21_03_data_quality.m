%% TASK 21.3 - RADAR DATA QUALITY VALIDATION

clear;
clc;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_21_Final_Research');

inputDir = fullfile(task,'02_Imported_Data');
outputDir = fullfile(task,'04_CSV_Results');
findingDir = fullfile(task,'06_Research_Findings');

if ~isfolder(outputDir), mkdir(outputDir); end
if ~isfolder(findingDir), mkdir(findingDir); end

files = {
    'task20_28_radar_world_points.mat'
    'task20_49_50m_radar_returns.mat'
    'task20_55_ray_alignment.mat'
    'task20_57_ray_box_intersections.mat'
};

fprintf('\n=== TASK 21.3 RADAR DATA QUALITY ===\n');

results = table();

for k = 1:numel(files)

    name = files{k};
    path = fullfile(inputDir,name);

    if ~isfile(path)
        error('Missing MAT dataset: %s',path);
    end

    S = load(path,'T');
    T = S.T;

    names = string(T.Properties.VariableNames);
    normalized = lower(names);

    fprintf('\nDataset: %s\n',name);

    fprintf('Rows: %d\n',height(T));
    fprintf('Columns: %d\n',width(T));

    % Missing entries across all table columns.
    missingCells = 0;

    for j = 1:width(T)
        col = T.(T.Properties.VariableNames{j});

        try
            missingCells = missingCells + ...
                nnz(ismissing(col),'all');
        catch
            fprintf('Missing-value check unavailable: %s\n', ...
                T.Properties.VariableNames{j});
        end
    end

    % Find frame index column if present.
    frameIndex = find( ...
        normalized == "frame" | ...
        normalized == "frameindex",1);

    startupRows = NaN;
    uniqueFrames = NaN;

    if ~isempty(frameIndex)
        frames = str2double( ...
            string(T.(T.Properties.VariableNames{frameIndex})));

        startupRows = nnz(frames == 0);
        uniqueFrames = numel(unique(frames(~isnan(frames))));

        fprintf('Frame-zero rows: %d\n',startupRows);
        fprintf('Unique frames: %d\n',uniqueFrames);
    else
        fprintf('Frame column not found.\n');
    end

    % Examine available range-related columns.
    rangeColumns = find(contains(normalized,'range'));

    for j = rangeColumns

        columnName = T.Properties.VariableNames{j};
        column = T.(columnName);

        values = str2double(string(column));

        valid = isfinite(values);

        fprintf('\nRange-like column: %s\n',columnName);
        fprintf('Finite values: %d\n',nnz(valid));
        fprintf('Missing/non-numeric: %d\n',nnz(~valid));

        if any(valid)
            fprintf('Minimum: %.6f\n',min(values(valid)));
            fprintf('Median: %.6f\n',median(values(valid)));
            fprintf('Maximum: %.6f\n',max(values(valid)));
        end
    end

    fprintf('Missing table entries: %d\n',missingCells);

    [~,datasetName] = fileparts(name);

    row = table( ...
        string(datasetName), ...
        height(T),width(T), ...
        missingCells,startupRows,uniqueFrames, ...
        'VariableNames', ...
        {'Dataset','Rows','Columns', ...
         'MissingCells','FrameZeroRows','UniqueFrames'});

    results = [results;row];

end

summaryPath = fullfile( ...
    outputDir,'task21_03_quality_summary.csv');

writetable(results,summaryPath);

notesPath = fullfile( ...
    findingDir,'task21_03_quality_findings.txt');

fid = fopen(notesPath,'w');

if fid < 0
    error('Cannot create findings report.');
end

fprintf(fid,'TASK 21.3 - MATLAB RADAR QUALITY AUDIT\n\n');
fprintf(fid,'Original Task 20 files were not modified.\n');
fprintf(fid,'Missing values and frame-zero rows were audited.\n');
fprintf(fid,'Range-like fields were inspected when present.\n');
fprintf(fid,'Per-frame multiple reflections are not duplicates.\n');
fprintf(fid,'Unverified object associations remain unverified.\n');
fprintf(fid,'Energy measurements have not been performed.\n');

fclose(fid);

fprintf('\n=== DATA QUALITY SUMMARY ===\n');
disp(results);

fprintf('CSV saved: %d\n',isfile(summaryPath));
fprintf('Findings saved: %d\n',isfile(notesPath));

fprintf('\n=== TASK 21.3 COMPLETE ===\n');
