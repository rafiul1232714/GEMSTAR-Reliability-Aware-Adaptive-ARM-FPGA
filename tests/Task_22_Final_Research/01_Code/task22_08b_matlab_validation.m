%% TASK 22.8B - INDEPENDENT MATLAB VALIDATION
% GEMSTAR multi-recording dataset standardization
% MATLAB R2026b
%
% Purpose:
% 1. Import Python-exported standardized CSV datasets.
% 2. Independently recompute preliminary fusion eligibility.
% 3. Compare MATLAB results against Python's export.
% 4. Create plots, a MAT dataset, and research findings.
%
% This task does NOT validate sensor-fusion accuracy
% or measure hardware electrical energy.

clearvars;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';
task = fullfile(root,'tests','Task_22_Final_Research');

dataDir = fullfile(task,'08_Processed_Data');
graphDir = fullfile(task,'03_Graphs');
csvDir = fullfile(task,'02_CSV_Data');
findingDir = fullfile(task,'06_Research_Findings');

if ~isfolder(graphDir), mkdir(graphDir); end
if ~isfolder(csvDir), mkdir(csvDir); end
if ~isfolder(findingDir), mkdir(findingDir); end

fprintf('\n=== TASK 22.8B MATLAB VALIDATION ===\n');

%% STEP 1 - Read Python outputs

allPath = fullfile(dataDir,'task22_08_all_frames.csv');
candidatePath = fullfile(dataDir, ...
    'task22_08_fusion_ready_candidates.csv');
summaryPath = fullfile(dataDir, ...
    'task22_08_dataset_summary.csv');

assert(isfile(allPath), 'All-frame CSV missing');
assert(isfile(candidatePath), 'Candidate CSV missing');
assert(isfile(summaryPath), 'Dataset summary CSV missing');

allFrames = readtable(allPath, ...
    'VariableNamingRule','preserve');

candidates = readtable(candidatePath, ...
    'VariableNamingRule','preserve');

summary = readtable(summaryPath, ...
    'VariableNamingRule','preserve');

fprintf('All imported frames: %d\n',height(allFrames));
fprintf('Imported candidates: %d\n',height(candidates));
fprintf('Unique recording summaries: %d\n',height(summary));

%% STEP 2 - Convert columns to numerical values

frame = str2double(string(allFrames.Frame));
pairID = str2double(string(allFrames.PairID));

structural = str2double(string(allFrames.StructuralPass));
timestamp = str2double(string(allFrames.TimestampMatched));

camera = str2double(string(allFrames.CameraAvailable));
lidar = str2double(string(allFrames.LiDARAvailable));
radar = str2double(string(allFrames.RadarAvailable));

startup = str2double(string( ...
    allFrames.StartupFrameExcluded));

pythonCandidate = str2double(string( ...
    allFrames.FusionCandidate));

requiredValues = [frame pairID structural timestamp ...
    camera lidar radar startup pythonCandidate];

assert(all(isfinite(requiredValues),'all'), ...
    'A required numerical field contains NaN or Inf');

%% STEP 3 - Independently recalculate eligibility

matlabCandidate = ...
    structural == 1 & ...
    timestamp == 1 & ...
    camera == 1 & ...
    lidar == 1 & ...
    radar == 1 & ...
    frame > 0 & ...
    startup == 0;

matches = matlabCandidate == (pythonCandidate == 1);

mismatchCount = sum(~matches);
recalculatedCount = sum(matlabCandidate);

fprintf('\n=== INDEPENDENT ELIGIBILITY CHECK ===\n');
fprintf('MATLAB candidates: %d\n',recalculatedCount);
fprintf('Python candidates: %d\n',height(candidates));
fprintf('Frame-level disagreements: %d\n',mismatchCount);

assert(mismatchCount == 0, ...
    'MATLAB and Python frame eligibility disagree');

assert(recalculatedCount == height(candidates), ...
    'Candidate row count differs between languages');

assert(numel(unique(pairID)) == height(summary), ...
    'Recording count mismatch');

%% STEP 4 - Validate candidate identities

candidatePair = str2double(string(candidates.PairID));
candidateFrame = str2double(string(candidates.Frame));

pythonKeys = sortrows([candidatePair candidateFrame]);
matlabKeys = sortrows([pairID(matlabCandidate) ...
                       frame(matlabCandidate)]);

assert(isequal(pythonKeys,matlabKeys), ...
    'Candidate recording/frame identities differ');

fprintf('Candidate record identities: MATCH\n');

%% STEP 5 - Per-recording independent statistics

ids = unique(pairID);
n = numel(ids);

recordingID = zeros(n,1);
totalFrames = zeros(n,1);
matlabEligible = zeros(n,1);
pythonEligible = zeros(n,1);

cameraFrames = zeros(n,1);
lidarFrames = zeros(n,1);
radarFrames = zeros(n,1);
startupExcluded = zeros(n,1);

for k = 1:n
    id = ids(k);
    idx = pairID == id;

    recordingID(k) = id;
    totalFrames(k) = sum(idx);

    matlabEligible(k) = sum(matlabCandidate(idx));
    pythonEligible(k) = sum(pythonCandidate(idx));

    cameraFrames(k) = sum(camera(idx));
    lidarFrames(k) = sum(lidar(idx));
    radarFrames(k) = sum(radar(idx));
    startupExcluded(k) = sum(startup(idx));

    fprintf('Pair %d: %d / %d candidate frames\n', ...
        id,matlabEligible(k),totalFrames(k));
end

validation = table( ...
    recordingID,totalFrames, ...
    matlabEligible,pythonEligible, ...
    cameraFrames,lidarFrames,radarFrames, ...
    startupExcluded, ...
    'VariableNames',{ ...
    'PairID','TotalFrames', ...
    'MATLABCandidates','PythonCandidates', ...
    'CameraFrames','LiDARFrames','RadarFrames', ...
    'StartupExcluded'});

assert(all(validation.MATLABCandidates == ...
    validation.PythonCandidates), ...
    'Per-recording eligibility mismatch');

assert(sum(validation.TotalFrames) == height(allFrames), ...
    'Total frame count mismatch');

%% STEP 6 - Figure 1: Sensor coverage

fig1 = figure('Color','w', ...
    'Position',[100 100 1050 550]);

bar(categorical(string(recordingID)), ...
    [cameraFrames lidarFrames radarFrames], ...
    'grouped');

xlabel('Recording pair');
ylabel('Frames with populated sensor data');
title('Task 22.8B - MATLAB Sensor Availability');
legend('Camera','LiDAR','Radar', ...
    'Location','southoutside', ...
    'Orientation','horizontal');
ylim([0 110]);
grid on;

graph1 = fullfile(graphDir, ...
    'task22_08b_matlab_sensor_coverage.png');

exportgraphics(fig1,graph1,'Resolution',200);
close(fig1);

%% STEP 7 - Figure 2: Candidate eligibility

fig2 = figure('Color','w', ...
    'Position',[100 100 1050 550]);

bar(categorical(string(recordingID)), ...
    [matlabEligible totalFrames-matlabEligible], ...
    'stacked');

xlabel('Recording pair');
ylabel('Number of frames');
title('Task 22.8B - Preliminary Fusion Candidate Selection');
legend('Eligible candidates','Excluded frames', ...
    'Location','southoutside', ...
    'Orientation','horizontal');
ylim([0 110]);
grid on;

graph2 = fullfile(graphDir, ...
    'task22_08b_candidate_comparison.png');

exportgraphics(fig2,graph2,'Resolution',200);
close(fig2);

%% STEP 8 - Figure 3: Frame-level eligibility

eligibility = NaN(n,100);

for k = 1:n
    idx = pairID == ids(k);
    localFrames = frame(idx);

    validIndex = localFrames >= 0 & localFrames < 100;

    eligibility(k,localFrames(validIndex)+1) = ...
        double(matlabCandidate(idx & ...
        frame >= 0 & frame < 100));
end

fig3 = figure('Color','w', ...
    'Position',[100 100 1100 440]);

imagesc(0:99,1:n,eligibility);
colormap([0.85 0.85 0.85; 0.15 0.55 0.85]);
clim([0 1]);

yticks(1:n);
yticklabels("Pair " + string(ids));
xlabel('Frame index');
ylabel('Recording pair');
title('Task 22.8B - Frame-Level Candidate Availability');

cb = colorbar;
cb.Ticks = [0 1];
cb.TickLabels = {'Excluded','Candidate'};

graph3 = fullfile(graphDir, ...
    'task22_08b_frame_eligibility.png');

exportgraphics(fig3,graph3,'Resolution',200);
close(fig3);

%% STEP 9 - Save MATLAB dataset and verification CSV

matPath = fullfile(dataDir, ...
    'task22_08b_standardized_dataset.mat');

csvPath = fullfile(csvDir, ...
    'task22_08b_matlab_cross_validation.csv');

save(matPath, ...
    'allFrames','candidates','summary', ...
    'validation','matlabCandidate');

writetable(validation,csvPath);

%% STEP 10 - Save research findings

findingsPath = fullfile(findingDir, ...
    'task22_08b_matlab_findings.txt');

fid = fopen(findingsPath,'w');

assert(fid ~= -1,'Cannot create MATLAB findings file');

fprintf(fid,'TASK 22.8B - MATLAB CROSS VALIDATION\n\n');
fprintf(fid,'All frame rows: %d\n',height(allFrames));
fprintf(fid,'Python candidate rows: %d\n',height(candidates));
fprintf(fid,'MATLAB candidate rows: %d\n',recalculatedCount);
fprintf(fid,'Eligibility disagreements: %d\n',mismatchCount);
fprintf(fid,'Unique recordings: %d\n\n',n);

for k = 1:n
    fprintf(fid,'Pair %d: %d / %d candidates\n', ...
        ids(k),matlabEligible(k),totalFrames(k));
end

fprintf(fid,'\nSCIENTIFIC LIMITATIONS\n');
fprintf(fid, ...
    '- Frame-zero exclusion is a conservative policy.\n');
fprintf(fid, ...
    '- Availability is not proof of sensor accuracy.\n');
fprintf(fid, ...
    '- No image or point-cloud geometry was validated.\n');
fprintf(fid, ...
    '- No sensor-to-GT object association was measured.\n');
fprintf(fid, ...
    '- Runtime scenario conditions remain unverified.\n');
fprintf(fid, ...
    '- No CPU/FPGA electrical energy was measured.\n');

fclose(fid);

%% STEP 11 - Final verification

fprintf('\n=== TASK 22.8B FILE VERIFICATION ===\n');

fprintf('MAT file saved: %d\n',isfile(matPath));
fprintf('Validation CSV saved: %d\n',isfile(csvPath));
fprintf('Figure 1 saved: %d\n',isfile(graph1));
fprintf('Figure 2 saved: %d\n',isfile(graph2));
fprintf('Figure 3 saved: %d\n',isfile(graph3));
fprintf('Findings TXT saved: %d\n',isfile(findingsPath));

fprintf('\n=== TASK 22.8B COMPLETE ===\n');
