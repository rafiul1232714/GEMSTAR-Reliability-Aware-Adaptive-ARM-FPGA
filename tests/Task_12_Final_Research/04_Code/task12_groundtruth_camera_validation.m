
%% TASK 12.2 - GROUND TRUTH TO CAMERA VALIDATION
% GEMSTAR MOR100, frame 150
% Tests whether GT vehicle 76865 aligns with YOLO car detection.
% Uses actual recorded coordinates and provisional camera geometry.

clc;
clear;
close all;

%% 1. PROJECT AND ARCHIVE

root = "E:\GEMSTAR_Project\sensor-health-monitor";

task11 = fullfile(root, ...
    "tests","Task_11_Final_Research");

task12 = fullfile(root, ...
    "tests","Task_12_Final_Research");

graphDir = fullfile(task12,"01_Graphs");
dataDir = fullfile(task12,"02_CSV_Data");
codeDir = fullfile(task12,"04_Code");
findingDir = fullfile(task12,"06_Research_Findings");

for folder = [graphDir,dataDir,codeDir,findingDir]
    if ~isfolder(folder)
        mkdir(folder);
    end
end

%% 2. LOAD SOURCE DATA FROM TASK 11

G = readtable(fullfile(task11, ...
    "02_CSV_Data","task11_groundtruth_objects.csv"));

D = readtable(fullfile(task11, ...
    "02_CSV_Data","task11_yolo11s_frame150.csv"));

imageFile = fullfile(task11, ...
    "01_Graphs","task11_mor100_frame0150_camera_0.ppm");

I = imread(imageFile);

frame = 150;
egoID = 76895;
targetID = 76865;

ego = G(G.frame == frame & G.object_id == egoID,:);
target = G(G.frame == frame & G.object_id == targetID,:);

assert(height(ego)==1, "Ego GT row missing.");
assert(height(target)==1, "Target GT row missing.");

car = D(D.frame==frame & ...
    strcmpi(string(D.class_name),"car"),:);

assert(~isempty(car), "YOLO car detection missing.");

% Use highest confidence car detection.
[~,idx] = max(car.confidence);
car = car(idx,:);

bbox = [car.x1,car.y1,car.x2,car.y2];

%% 3. WORLD COORDINATES TO EGO COORDINATES

dx = target.x_m - ego.x_m;
dy = target.y_m - ego.y_m;

yaw = ego.yaw_rad;

forward =  cos(yaw)*dx + sin(yaw)*dy;
lateral = -sin(yaw)*dx + cos(yaw)*dy;

relativeZ = target.z_m - ego.z_m;

fprintf('\n===== TASK 12.2 GT CAMERA VALIDATION =====\n');
fprintf('Frame: %d\n',frame);
fprintf('Ego ID: %d\n',egoID);
fprintf('Target ID: %d\n',targetID);
fprintf('Forward: %.3f m\n',forward);
fprintf('Lateral: %.3f m\n',lateral);
fprintf('GT vertical difference: %.3f m\n',relativeZ);

%% 4. CAMERA INTRINSICS

W = size(I,2);
H = size(I,1);

horizontalFOV = 90;

fx = W/(2*tand(horizontalFOV/2));
fy = fx;

cx = W/2;
cy = H/2;

% Camera mount relative to ego reference frame.
cameraX = 0.70;
cameraY = 0;
cameraZ = 1.60;

% GT object Z is assumed to be given relative to
% the vehicle's ground reference. This assumption
% requires confirmation from GEMSTAR transformations.
Xcam = forward - cameraX;
Ycam = lateral - cameraY;
Zcam = relativeZ - cameraZ;

assert(Xcam>0,"Target behind camera.");

%% 5. TEST BOTH IMAGE LATERAL CONVENTIONS

uMinus = cx - fx*Ycam/Xcam;
uPlus  = cx + fx*Ycam/Xcam;

v = cy - fy*Zcam/Xcam;

boxCenterU = (bbox(1)+bbox(3))/2;
boxCenterV = (bbox(2)+bbox(4))/2;

insideMinus = ...
    uMinus>=bbox(1) && uMinus<=bbox(3) && ...
    v>=bbox(2) && v<=bbox(4);

insidePlus = ...
    uPlus>=bbox(1) && uPlus<=bbox(3) && ...
    v>=bbox(2) && v<=bbox(4);

distanceMinus = hypot( ...
    uMinus-boxCenterU, v-boxCenterV);

distancePlus = hypot( ...
    uPlus-boxCenterU, v-boxCenterV);

fprintf('\nYOLO box center: (%.2f, %.2f)\n', ...
    boxCenterU,boxCenterV);

fprintf('Negative-Y projection: (%.2f, %.2f)\n', ...
    uMinus,v);

fprintf('Positive-Y projection: (%.2f, %.2f)\n', ...
    uPlus,v);

fprintf('Negative-Y in box: %d\n',insideMinus);
fprintf('Positive-Y in box: %d\n',insidePlus);

fprintf('Negative-Y center error: %.2f px\n', ...
    distanceMinus);

fprintf('Positive-Y center error: %.2f px\n', ...
    distancePlus);

%% 6. PLOT THE ACTUAL CAMERA IMAGE

fig = figure( ...
    'Color','w', ...
    'Position',[100 100 1050 720]);

image(I);
axis image;
hold on;

rectangle( ...
    'Position',[ ...
    bbox(1),bbox(2), ...
    bbox(3)-bbox(1),bbox(4)-bbox(2)], ...
    'EdgeColor','g', ...
    'LineWidth',2.5);

plot(boxCenterU,boxCenterV, ...
    'g+','MarkerSize',15,'LineWidth',2);

plot(uMinus,v, ...
    'ro','MarkerSize',12,'LineWidth',2);

plot(uPlus,v, ...
    'bx','MarkerSize',12,'LineWidth',2);

legend({ ...
    'YOLO box center', ...
    'GT negative-Y', ...
    'GT positive-Y'}, ...
    'Location','northoutside', ...
    'Orientation','horizontal');

title('Task 12.2 - GT Vehicle 76865 vs YOLO Car');

xlabel('Image column (pixels)');
ylabel('Image row (pixels)');

%% 7. SAVE GRAPH

pngFile = fullfile(graphDir, ...
    "task12_2_groundtruth_camera_projection.png");

figFile = fullfile(graphDir, ...
    "task12_2_groundtruth_camera_projection.fig");

exportgraphics(fig,pngFile,'Resolution',250);
savefig(fig,figFile);

%% 8. SAVE NUMERICAL CSV

result = table( ...
    frame,egoID,targetID, ...
    forward,lateral,relativeZ, ...
    uMinus,uPlus,v, ...
    boxCenterU,boxCenterV, ...
    distanceMinus,distancePlus, ...
    insideMinus,insidePlus, ...
    'VariableNames',{ ...
    'frame','ego_id','target_id', ...
    'forward_m','lateral_m','relative_z_m', ...
    'u_negative','u_positive','v_pixel', ...
    'yolo_center_u','yolo_center_v', ...
    'error_negative_px','error_positive_px', ...
    'inside_negative','inside_positive'});

csvFile = fullfile(dataDir, ...
    "task12_2_groundtruth_camera_validation.csv");

writetable(result,csvFile);

%% 9. SAVE RESEARCH FINDINGS

reportFile = fullfile(findingDir, ...
    "task12_2_groundtruth_camera_findings.txt");

fid = fopen(reportFile,'w');
assert(fid~=-1, "Unable to write findings.");

fprintf(fid,'TASK 12.2 - GT TO CAMERA VALIDATION\n');
fprintf(fid,'Scenario: GEMSTAR MOR100\n');
fprintf(fid,'Frame: 150\n');
fprintf(fid,'Ego ID: 76895\n');
fprintf(fid,'Target candidate ID: 76865\n\n');

fprintf(fid,'Forward: %.4f m\n',forward);
fprintf(fid,'Lateral: %.4f m\n',lateral);
fprintf(fid,'Relative Z: %.4f m\n',relativeZ);

fprintf(fid,'Negative sign pixel error: %.3f\n', ...
    distanceMinus);

fprintf(fid,'Positive sign pixel error: %.3f\n', ...
    distancePlus);

fprintf(fid,'Negative sign inside box: %d\n',insideMinus);
fprintf(fid,'Positive sign inside box: %d\n',insidePlus);

fprintf(fid,'\nLIMITATIONS\n');
fprintf(fid,'GT reference point is not fully calibrated.\n');
fprintf(fid,'Camera extrinsic and optical axis are provisional.\n');
fprintf(fid,'Pixel overlap does not prove identity.\n');
fprintf(fid,'GT object association remains a candidate.\n');
fprintf(fid,'No LiDAR/Radar fusion has been validated.\n');

fclose(fid);

%% 10. ARCHIVE SOURCE CODE

sourceFile = fullfile(root,"matlab", ...
    "task12_groundtruth_camera_validation.m");

if isfile(sourceFile)
    copyfile(sourceFile,codeDir,'f');
end

%% 11. FINAL OUTPUT

disp(result);

fprintf('\nGraph saved: %s\n',pngFile);
fprintf('CSV saved: %s\n',csvFile);
fprintf('\nTASK 12.2 COMPLETED\n');
