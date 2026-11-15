%% GEMSTAR TASK 27.3D
% LiDAR nominal data transfer and hypothetical FPGA break-even.
% NO hardware bandwidth or energy has been measured.

clear; clc; close all;

root = 'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_27_Final_Research';

csvDir = fullfile(root,'02_CSV_Data');
plotDir = fullfile(root,'04_Plots');
reportDir = fullfile(root,'06_Research_Findings');

fprintf('=== TASK 27.3D MATLAB TRANSFER ANALYSIS ===\n');

%% 1. Load archived research data

T = readtable(fullfile(csvDir, ...
    'task27_3C_lidar_memory_model.csv'), ...
    'VariableNamingRule','preserve');

assert(height(T)==53,'Expected 53 LiDAR frames');

[frame,idx] = sort(double(T.frame));
T = T(idx,:);

inputB = double(T.nominal_input_xyz_bytes);
outputB = double(T.nominal_output_xyz_bytes);
roundtripB = double(T.model_roundtrip_payload_bytes);

cpu = double(T.archived_cpu_filter_median_ms);
requiredBW = double(T.required_transfer_bw_MBps_zero_compute);

assert(sum(inputB)==2074068,'Input byte count mismatch');
assert(sum(outputB)==195540,'Output byte count mismatch');
assert(sum(roundtripB)==2269608,'Round-trip byte count mismatch');
assert(all(cpu>0),'Invalid CPU timing');
assert(all(roundtripB==inputB+outputB),'Payload mismatch');

% Decimal MB/s, not MiB/s.
bandwidths = [100 500 1000];

% Only nominal payload transfer time, no overhead.
transfer = zeros(height(T),numel(bandwidths));

for k = 1:numel(bandwidths)
    transfer(:,k) = roundtripB ./ (bandwidths(k)*1e6)*1000;
end

assert(max(abs(transfer(:,1) - ...
    double(T.hypothetical_transfer_ms_100MBps)))<1e-9, ...
    '100 MB/s transfer model mismatch');

assert(max(abs(transfer(:,2) - ...
    double(T.hypothetical_transfer_ms_500MBps)))<1e-9, ...
    '500 MB/s transfer model mismatch');

assert(max(abs(transfer(:,3) - ...
    double(T.hypothetical_transfer_ms_1000MBps)))<1e-9, ...
    '1000 MB/s transfer model mismatch');

%% 2. Preflight outputs: preserve existing research

names = {
    'Task27_Fig09_LiDAR_Transfer_Payload'
    'Task27_Fig10_LiDAR_CPU_vs_Transfer'
    'Task27_Fig11_LiDAR_Required_Bandwidth'
    'Task27_Fig12_LiDAR_BreakEven_Map'
};

for k = 1:numel(names)
    assert(~isfile(fullfile(plotDir,[names{k} '.png'])), ...
        'Existing PNG preserved');
    assert(~isfile(fullfile(plotDir,[names{k} '.fig'])), ...
        'Existing FIG preserved');
end

summaryPath = fullfile(csvDir, ...
    'task27_3D_lidar_transfer_summary.csv');

reportPath = fullfile(reportDir, ...
    'task27_3D_matlab_transfer_findings.txt');

assert(~isfile(summaryPath),'Existing summary preserved');
assert(~isfile(reportPath),'Existing report preserved');

%% 3. Figure 09: Nominal data volumes

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1150 550]);

plot(frame,inputB/1024,'LineWidth',1.5);
hold on;
plot(frame,outputB/1024,'LineWidth',1.5);
plot(frame,roundtripB/1024,'LineWidth',1.5);

xlabel('Recorded Frame ID');
ylabel('Nominal XYZ Payload (KiB)');
title('LiDAR Data Movement Model per Frame');
legend('Input','Filtered output','Round trip', ...
    'Location','best');
grid on;

savefig(f,fullfile(plotDir,[names{1} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{1} '.png']), ...
    'Resolution',300);
close(f);

%% 4. Figure 10: CPU versus hypothetical transfer

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1150 550]);

plot(frame,cpu,'k-','LineWidth',1.8);
hold on;

plot(frame,transfer(:,1),'LineWidth',1.4);
plot(frame,transfer(:,2),'LineWidth',1.4);
plot(frame,transfer(:,3),'LineWidth',1.4);

xlabel('Recorded Frame ID');
ylabel('Time (ms)');
title('Archived CPU Filtering vs Hypothetical Transfer-Only Time');
legend('CPU filter median','100 MB/s','500 MB/s', ...
    '1000 MB/s','Location','best');
grid on;

savefig(f,fullfile(plotDir,[names{2} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{2} '.png']), ...
    'Resolution',300);
close(f);

%% 5. Figure 11: Bandwidth threshold

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1150 550]);

plot(frame,requiredBW,'-o','LineWidth',1.3);
hold on;
yline(median(requiredBW),'--', ...
    'Median threshold','LineWidth',1.2);

xlabel('Recorded Frame ID');
ylabel('Required Transfer Bandwidth (MB/s)');
title('Zero-Compute LiDAR Transfer Break-Even Threshold');
grid on;

savefig(f,fullfile(plotDir,[names{3} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{3} '.png']), ...
    'Resolution',300);
close(f);

%% 6. Figure 12: Hypothetical break-even feasibility

% X: hypothetical effective transfer bandwidth
% Y: FPGA compute + scheduling overhead (combined)
% Value: fraction of archived frames where the modeled
% total would be faster than CPU filtering.
%
% These are model scenarios, NOT measured FPGA results.

bwSweep = 25:25:1000;
computeSweep = 0:0.025:1.0;

fractionFaster = zeros(numel(computeSweep),numel(bwSweep));

for i = 1:numel(computeSweep)
    for j = 1:numel(bwSweep)

        transferTime = roundtripB ./ ...
            (bwSweep(j)*1e6)*1000;

        modeledTotal = transferTime + computeSweep(i);

        fractionFaster(i,j) = 100*mean(modeledTotal < cpu);
    end
end

f = figure('Visible','off','Color','w', ...
    'Position',[100 100 1150 600]);

imagesc(bwSweep,computeSweep,fractionFaster);
axis xy;
xlabel('Hypothetical Effective Transfer Bandwidth (MB/s)');
ylabel('Assumed FPGA Compute + Other Overhead (ms)');
title('Modeled Fraction of Frames Faster than Archived CPU');
cb = colorbar;
cb.Label.String = 'Frames Meeting Modeled Break-Even (%)';
caxis([0 100]);

savefig(f,fullfile(plotDir,[names{4} '.fig']));
exportgraphics(f,fullfile(plotDir,[names{4} '.png']), ...
    'Resolution',300);
close(f);

%% 7. Save per-frame numerical summary

S = table( ...
    frame, ...
    inputB, ...
    outputB, ...
    roundtripB, ...
    cpu, ...
    requiredBW, ...
    transfer(:,1), ...
    transfer(:,2), ...
    transfer(:,3), ...
    'VariableNames', { ...
        'Frame', ...
        'InputBytes', ...
        'OutputBytes', ...
        'RoundtripBytes', ...
        'ArchivedCPUMedianMs', ...
        'RequiredBandwidthMBps', ...
        'Transfer100MBpsMs', ...
        'Transfer500MBpsMs', ...
        'Transfer1000MBpsMs' ...
    });

writetable(S,summaryPath);

%% 8. Save thesis research findings

reduction = 100*(1-sum(outputB)/sum(inputB));

fid = fopen(reportPath,'w');
assert(fid>0,'Could not create findings report');

fprintf(fid,'GEMSTAR TASK 27.3D\n');
fprintf(fid,'LiDAR Transfer Model and Break-Even Analysis\n');
fprintf(fid,'============================================\n\n');

fprintf(fid,'Frames: %d\n',height(T));
fprintf(fid,'Input payload: %.0f bytes\n',sum(inputB));
fprintf(fid,'Filtered payload: %.0f bytes\n',sum(outputB));
fprintf(fid,'Round-trip payload: %.0f bytes\n',sum(roundtripB));
fprintf(fid,'Output reduction: %.4f percent\n',reduction);
fprintf(fid,'Median required bandwidth: %.4f MB/s\n', ...
    median(requiredBW));
fprintf(fid,'Maximum required bandwidth: %.4f MB/s\n', ...
    max(requiredBW));
fprintf(fid,'Median archived CPU filter time: %.6f ms\n', ...
    median(cpu));

fprintf(fid,'\nMODEL ASSUMPTIONS:\n');
fprintf(fid,'XYZ payload: 3 float32 values per point.\n');
fprintf(fid,'Host sends raw points and receives filtered points.\n');
fprintf(fid,'Bandwidth scenarios: 100, 500, 1000 MB/s.\n');
fprintf(fid,'No measured DMA or FPGA hardware results.\n');
fprintf(fid,'Transfer-only comparison excludes execution and overhead.\n');
fprintf(fid,'Feasibility map adds hypothetical compute/overhead.\n');
fprintf(fid,'No FPGA speedup or energy savings demonstrated.\n');
fprintf(fid,'CPU timings originate from the development workstation.\n');

fclose(fid);

%% 9. Print completion

fprintf('FRAMES_ANALYZED: %d\n',height(T));
fprintf('INPUT_BYTES: %.0f\n',sum(inputB));
fprintf('OUTPUT_BYTES: %.0f\n',sum(outputB));
fprintf('ROUNDTRIP_BYTES: %.0f\n',sum(roundtripB));
fprintf('MEDIAN_REQUIRED_BW_MBPS: %.4f\n',median(requiredBW));
fprintf('MAX_REQUIRED_BW_MBPS: %.4f\n',max(requiredBW));
fprintf('FIGURES_CREATED: 4 PNG + 4 FIG\n');
fprintf('SUMMARY_CSV_CREATED: YES\n');
fprintf('FINDINGS_CREATED: YES\n');
fprintf('MEASURED_FPGA_RESULTS: NO\n');
fprintf('TASK27_3D_MATLAB_TRANSFER_ANALYSIS_DONE\n');