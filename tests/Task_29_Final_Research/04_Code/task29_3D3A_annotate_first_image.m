%% GEMSTAR Task 29.3D.3A - Manual annotation of Frame 0
clearvars;
clc;
close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor';

task28 = fullfile(root,'tests','Task_28_Final_Research');
task29 = fullfile(root,'tests','Task_29_Final_Research');

manifestPath = fullfile(task28,'02_CSV_Data', ...
    'task28_3D4B2_camera_image_manifest.csv');

T = readtable(manifestPath,'TextType','string');

frames = str2double(string(T.Frame));

idx = find(T.Scenario=="baseline_clear" & frames==0);

assert(numel(idx)==1,'Expected exactly one baseline-clear Frame 0');

imagePath = char(T.OutputPNG(idx));
assert(isfile(imagePath),'Original image not found');

img = imread(imagePath);

assert(size(img,1)==480 && size(img,2)==640, ...
    'Unexpected Camera image resolution');

outDir = fullfile(task29,'03_Configurations', ...
    'Camera_GroundTruth_Annotations');

if ~exist(outDir,'dir')
    mkdir(outDir);
end

outPath = fullfile(outDir, ...
    'task29_labels_baseline_clear_frame00000.json');

if isfile(outPath)
    fprintf('Existing annotation preserved:\n%s\n',outPath);
    return;
end

fprintf('\n=== TASK 29.3D.3A ===\n');
fprintf('Scenario: baseline_clear\n');
fprintf('Frame: 0\n');

fig = figure('Color','w', ...
    'Name','GEMSTAR Manual Ground Truth - Frame 0', ...
    'Position',[100 100 1000 750]);

ax = axes(fig);
image(ax,img);
axis(ax,'image');
axis(ax,'on');

title(ax,'Inspect original Frame 0 - Ground Truth');

fprintf('\nAllowed classes: car, truck, bus, person, bicycle, motorcycle\n');
fprintf('Inspect the ORIGINAL image, not YOLO predictions.\n');
fprintf('Enter 0 only if no identifiable target objects are visible.\n');

count = input('Number of visible target objects: ');

assert(isnumeric(count) && isscalar(count) && ...
    isfinite(count) && count>=0 && ...
    count==floor(count), ...
    'Enter a nonnegative integer');

allowed = ["car","truck","bus","person","bicycle","motorcycle"];

objects = struct('class',{},'x1',{},'y1',{}, ...
    'x2',{},'y2',{});

for k = 1:count

    fprintf('\nObject %d of %d\n',k,count);

    cls = lower(strtrim(string(input( ...
        'Object class: ','s'))));

    assert(any(cls==allowed),'Unsupported object class');

    fprintf('Click top-left corner, then bottom-right corner.\n');

    figure(fig);
    [x,y] = ginput(2);

    x1 = max(0,min(x));
    x2 = min(size(img,2),max(x));
    y1 = max(0,min(y));
    y2 = min(size(img,1),max(y));

    assert(x2>x1 && y2>y1,'Invalid bounding box');

    rectangle(ax,'Position',[x1 y1 x2-x1 y2-y1], ...
        'EdgeColor','g','LineWidth',2);

    objects(k).class = char(cls);
    objects(k).x1 = x1;
    objects(k).y1 = y1;
    objects(k).x2 = x2;
    objects(k).y2 = y2;
end

answer = lower(strtrim(string(input( ...
    'Annotation complete and correct? (yes/no): ','s'))));

if answer ~= "yes"
    fprintf('Annotation not saved.\n');
    return;
end

record = struct();
record.task = '29.3D.3A';
record.scenario = 'baseline_clear';
record.frame = 0;
record.image = imagePath;
record.image_sha256 = char(T.ImageSHA256(idx));
record.reviewed = true;
record.annotation_source = 'manual_visual_review';
record.independently_verified = false;
record.objects = objects;

jsonText = jsonencode(record,'PrettyPrint',true);

fid = fopen(outPath,'w');
assert(fid~=-1,'Could not create annotation file');

fprintf(fid,'%s\n',jsonText);
fclose(fid);

fprintf('\n=== ANNOTATION SAVED ===\n');
fprintf('Objects: %d\n',count);
fprintf('File: %s\n',outPath);
fprintf('Independent verification: PENDING\n');
fprintf('\nTASK 29.3D.3A: PASS\n');

