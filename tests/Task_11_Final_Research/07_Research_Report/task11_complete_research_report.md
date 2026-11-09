# Task 11 - Complete Research Documentation

**Project:** GEMSTAR Multi-Sensor Perception
**Scenario:** MOR100 Fog
**Reference frame:** 150
**Camera timestamp:** 4.902842 s
**Report generated:** 2026-10-28 19:06

## Scope

This report documents the Task 11 research baseline. It distinguishes verified results from provisional geometric interpretations.

## Task 11.1 - Sensor data and experiment identification

**What we did:** Established the recorded GEMSTAR experiment, ego vehicle, SensorView messages, Ground Truth objects, and the relationship between recorded frame numbers and timestamps.

**Results:** Identified the MOR100 recording and established a common data source for Camera, LiDAR and Radar.

**Limitations:** Sensor identification alone does not prove calibration.

## Task 11.2 - Common sensor-frame reconstruction

**What we did:** Examined sensor mounting positions and orientations. Reconstructed LiDAR and Radar observations in a provisional ego-vehicle coordinate system.

**Results:** Produced coordinate-based measurement tables usable for MATLAB plotting and geometric diagnostics.

**Limitations:** Lateral-axis signs and the full coordinate transformation were not independently validated.

## Task 11.3 - LiDAR point-cloud reconstruction

**What we did:** Decoded LiDAR ranges and ray indices, reconstructed 3D positions, and inspected point-cloud distributions.

**Results:** Generated reusable LiDAR measurement CSVs and geometric visualizations.

**Limitations:** The underlying LiDAR return geometry requires calibration and simulator-surface interpretation.

## Task 11.4 - Ground filtering and obstacle clustering

**What we did:** Separated low ground-like returns from elevated candidates and applied geometric clustering to selected frames.

**Results:** Established a reproducible clustering workflow and identified candidate non-ground structures.

**Limitations:** A geometric cluster is not automatically a vehicle.

## Task 11.5 - Ground Truth and LiDAR visibility investigation

**What we did:** Investigated vehicle Ground Truth positions, forward-field candidates, LiDAR ray geometry, ray indices, scan layers and diagnostic simulator object IDs.

**Results:** Found that available raycast reflections could not reliably be identified with the predicted nearby vehicle.

**Limitations:** Simulator diagnostic surface IDs must not be confused with OSI Ground Truth vehicle IDs.

## Task 11.6 - Independent LiDAR object clustering

**What we did:** Performed a separate height-filtered clustering experiment on frame 150, without depending on a successful vehicle detection.

**Results:** A cluster of 190 points was obtained. Its measured dimensions were approximately 7.548 m by 0.992 m, with a vertical extent of 0.270 m.

**Limitations:** The long, low cluster is more consistent with roadside geometry than a verified complete vehicle.

## Task 11.7 - Radar processing and LiDAR-Radar association

**What we did:** Reconstructed Radar reflections and compared their distances with LiDAR points and the selected cluster.

**Results:** Frame 150 contained 31 valid Radar reflections. Nine were within 1 metre of the selected cluster in the provisional XY geometry.

**Limitations:** Spatial proximity is not sufficient evidence that both sensors detected the same physical object.

## Task 11.8A-D - Camera extraction and synchronized dashboard

**What we did:** Extracted the exact Camera image from OSI frame 150 and displayed Camera, LiDAR and Radar observations together in MATLAB.

**Results:** Successfully generated a synchronized three-sensor inspection dashboard. Camera timestamp: 4.902842 s.

**Limitations:** Simultaneous display does not establish object-level fusion.

## Task 11.8E-F - YOLO vehicle detection

**What we did:** Tested pretrained YOLO11n and YOLO11s models on the recorded Camera image and compared the classifications.

**Results:** YOLO11n missed the car and classified an object as an airplane. YOLO11s detected the white car with confidence 0.9306 and visually plausible bounding box (45.70,244.30)-(281.22,380.37). One YOLO11s CPU prediction took 70.419 ms.

**Limitations:** The additional person prediction was unverified. Single-image CPU timings are preliminary.

## Task 11.8G-J - Camera calibration and 3D projection

**What we did:** Read GEMSTAR Camera C++ code and sensor configuration. Used a provisional perspective camera model and projected LiDAR and Radar points onto the image.

**Results:** Confirmed 640x480 resolution and 90-degree horizontal capture FOV. Projection showed zero selected-cluster points in the car box for one lateral convention, versus 190 for the other.

**Limitations:** Choosing a coordinate sign because it increases overlap would be invalid calibration.

## Task 11.8K - Cluster physical-geometry validation

**What we did:** Compared the projected cluster with its actual 3D shape, vertical distribution, and diagnostic ID.

**Results:** All 190 cluster points had reconstructed Z below 0.5 m; measured Z ranged from 0.152 to 0.422 m. Diagnostic surface ID: 83265.

**Limitations:** Image-box overlap did not verify a common vehicle.

## Task 11.9 - Validation and research archiving

**What we did:** Audited the saved figures, CSVs, scripts and research findings, and documented successful and unsuccessful experiments.

**Results:** The previous focused audit confirmed 11 of 11 selected files were present.

**Limitations:** Full object-level Camera-LiDAR-Radar fusion remains unverified. Further Ground Truth calibration and multi-frame evaluation are required.

## Research conclusion

The study established an end-to-end recorded-data inspection pipeline for Camera, LiDAR and Radar. A 2D car detection was visually confirmed, but the selected LiDAR and Radar measurements could not be reliably attributed to that vehicle.

This is a valid and useful baseline result. Object-level fusion remains future work.

## Complete file inventory

- `01_Graphs\task11_camera_yolo_frame150.png` (332,708 bytes)
- `01_Graphs\task11_common_sensor_3d.fig` (44,217 bytes)
- `01_Graphs\task11_common_sensor_3d.png` (214,270 bytes)
- `01_Graphs\task11_common_sensor_topview.fig` (37,808 bytes)
- `01_Graphs\task11_common_sensor_topview.png` (124,945 bytes)
- `01_Graphs\task11_frame150_association_validation.fig` (14,528 bytes)
- `01_Graphs\task11_frame150_association_validation.png` (107,933 bytes)
- `01_Graphs\task11_frame150_cluster_geometry_validation.fig` (2,093,513 bytes)
- `01_Graphs\task11_frame150_cluster_geometry_validation.png` (666,176 bytes)
- `01_Graphs\task11_frame150_independent_clusters_3d.fig` (43,226 bytes)
- `01_Graphs\task11_frame150_independent_clusters_3d.png` (142,099 bytes)
- `01_Graphs\task11_frame150_independent_clusters_top.fig` (41,285 bytes)
- `01_Graphs\task11_frame150_independent_clusters_top.png` (120,581 bytes)
- `01_Graphs\task11_frame150_lidar_3d.fig` (53,460 bytes)
- `01_Graphs\task11_frame150_lidar_3d.png` (224,993 bytes)
- `01_Graphs\task11_frame150_lidar_radar_3d.fig` (13,472 bytes)
- `01_Graphs\task11_frame150_lidar_radar_3d.png` (150,222 bytes)
- `01_Graphs\task11_frame150_lidar_radar_overlay.fig` (14,275 bytes)
- `01_Graphs\task11_frame150_lidar_radar_overlay.png` (95,976 bytes)
- `01_Graphs\task11_frame150_projection_comparison.fig` (2,110,173 bytes)
- `01_Graphs\task11_frame150_projection_comparison.png` (589,235 bytes)
- `01_Graphs\task11_frame150_three_sensor_dashboard.fig` (1,078,099 bytes)
- `01_Graphs\task11_frame150_three_sensor_dashboard.png` (777,657 bytes)
- `01_Graphs\task11_frame150_vehicle_closeup.fig` (53,016 bytes)
- `01_Graphs\task11_frame150_vehicle_closeup.png` (149,807 bytes)
- `01_Graphs\task11_frame150_vehicle_topview.fig` (46,014 bytes)
- `01_Graphs\task11_frame150_vehicle_topview.png` (149,919 bytes)
- `01_Graphs\task11_frame150_yolo_original_lowconf.png` (334,715 bytes)
- `01_Graphs\task11_frame150_yolo_swapped_rb_lowconf.png` (335,711 bytes)
- `01_Graphs\task11_frame431_3d.fig` (50,693 bytes)
- `01_Graphs\task11_frame431_3d.png` (162,986 bytes)
- `01_Graphs\task11_frame431_topview.fig` (43,836 bytes)
- `01_Graphs\task11_frame431_topview.png` (134,109 bytes)
- `01_Graphs\task11_groundtruth_ego_frame431.fig` (12,265 bytes)
- `01_Graphs\task11_groundtruth_ego_frame431.png` (83,722 bytes)
- `01_Graphs\task11_lidar_3d_frame101.fig` (52,863 bytes)
- `01_Graphs\task11_lidar_3d_frame101.png` (201,493 bytes)
- `01_Graphs\task11_lidar_dbscan_clusters.fig` (17,216 bytes)
- `01_Graphs\task11_lidar_dbscan_clusters.png` (72,312 bytes)
- `01_Graphs\task11_lidar_dbscan_clusters_3d.fig` (20,992 bytes)
- `01_Graphs\task11_lidar_dbscan_clusters_3d.png` (164,059 bytes)
- `01_Graphs\task11_lidar_ground_filter_exploration.fig` (38,517 bytes)
- `01_Graphs\task11_lidar_ground_filter_exploration.png` (121,596 bytes)
- `01_Graphs\task11_lidar_gt_forward_frame431.fig` (46,722 bytes)
- `01_Graphs\task11_lidar_gt_forward_frame431.png` (102,483 bytes)
- `01_Graphs\task11_lidar_gt_overlay_frame431.fig` (48,999 bytes)
- `01_Graphs\task11_lidar_gt_overlay_frame431.png` (114,885 bytes)
- `01_Graphs\task11_lidar_height_distribution.fig` (17,205 bytes)
- `01_Graphs\task11_lidar_height_distribution.png` (56,476 bytes)
- `01_Graphs\task11_lidar_radar_alignment_check.fig` (73,355 bytes)
- `01_Graphs\task11_lidar_radar_alignment_check.png` (162,799 bytes)
- `01_Graphs\task11_lidar_topview_frame101.fig` (49,578 bytes)
- `01_Graphs\task11_lidar_topview_frame101.png` (134,117 bytes)
- `01_Graphs\task11_mor100_frame0150_camera_0.ppm` (921,615 bytes)
- `01_Graphs\task11_normal_surface_classification_3d.fig` (43,068 bytes)
- `01_Graphs\task11_normal_surface_classification_3d.png` (189,818 bytes)
- `01_Graphs\task11_normal_surface_classification_topview.fig` (37,326 bytes)
- `01_Graphs\task11_normal_surface_classification_topview.png` (115,234 bytes)
- `01_Graphs\task11_radar_3d_frame101.fig` (18,511 bytes)
- `01_Graphs\task11_radar_3d_frame101.png` (189,970 bytes)
- `01_Graphs\task11_radar_topview_frame101.fig` (20,271 bytes)
- `01_Graphs\task11_radar_topview_frame101.png` (89,299 bytes)
- `01_Graphs\task11_yolo11s_frame150.png` (334,378 bytes)
- `02_CSV_Data\task11_camera_frame150_metadata.csv` (165 bytes)
- `02_CSV_Data\task11_camera_yolo_detections_frame150.csv` (50 bytes)
- `02_CSV_Data\task11_cluster_objectid_validation.csv` (94 bytes)
- `02_CSV_Data\task11_common_lidar_radar_frame101.csv` (236,593 bytes)
- `02_CSV_Data\task11_final_archive_audit.csv` (634 bytes)
- `02_CSV_Data\task11_forward_vehicle_frames.csv` (4,213 bytes)
- `02_CSV_Data\task11_frame150_association_summary.csv` (254 bytes)
- `02_CSV_Data\task11_frame150_cluster_geometry_validation.csv` (346 bytes)
- `02_CSV_Data\task11_frame150_independent_cluster_labels.csv` (22,093 bytes)
- `02_CSV_Data\task11_frame150_independent_cluster_summary.csv` (191 bytes)
- `02_CSV_Data\task11_frame150_nearby_radar_returns.csv` (2,010 bytes)
- `02_CSV_Data\task11_frame150_negative_y_window.csv` (56,009 bytes)
- `02_CSV_Data\task11_frame150_positive_y_window.csv` (46,555 bytes)
- `02_CSV_Data\task11_frame150_projection_comparison.csv` (192 bytes)
- `02_CSV_Data\task11_frame150_radar_cluster_association.csv` (6,367 bytes)
- `02_CSV_Data\task11_frame150_surface_audit.csv` (880 bytes)
- `02_CSV_Data\task11_geometric_frame_candidates.csv` (220,786 bytes)
- `02_CSV_Data\task11_ground_threshold_exploration.csv` (87 bytes)
- `02_CSV_Data\task11_groundtruth_ego_frame431.csv` (1,182 bytes)
- `02_CSV_Data\task11_groundtruth_frame431.csv` (3,135 bytes)
- `02_CSV_Data\task11_groundtruth_objects.csv` (669,085 bytes)
- `02_CSV_Data\task11_lidar_cluster_labels_frame101.csv` (93,616 bytes)
- `02_CSV_Data\task11_lidar_cluster_summary_frame101.csv` (181 bytes)
- `02_CSV_Data\task11_lidar_frame150_geometry.csv` (234,304 bytes)
- `02_CSV_Data\task11_lidar_frame431_geometry.csv` (306,125 bytes)
- `02_CSV_Data\task11_lidar_height_candidates_frame101.csv` (234,150 bytes)
- `02_CSV_Data\task11_lidar_measurements.csv` (100,947,070 bytes)
- `02_CSV_Data\task11_lidar_normal_classification_frame101.csv` (362,759 bytes)
- `02_CSV_Data\task11_lidar_normals_frame101.csv` (158,542 bytes)
- `02_CSV_Data\task11_lidar_points_frame101.csv` (230,056 bytes)
- `02_CSV_Data\task11_lidar_ray_diagnostics_frame150.csv` (838 bytes)
- `02_CSV_Data\task11_measurement_validation.csv` (384 bytes)
- `02_CSV_Data\task11_nearby_vehicles_frame431.csv` (133 bytes)
- `02_CSV_Data\task11_normal_filter_summary.csv` (57 bytes)
- `02_CSV_Data\task11_radar_coordinate_candidates.csv` (2,494 bytes)
- `02_CSV_Data\task11_radar_frame150_points.csv` (5,159 bytes)
- `02_CSV_Data\task11_radar_lidar_distance_frame150.csv` (5,718 bytes)
- `02_CSV_Data\task11_radar_measurements.csv` (1,757,556 bytes)
- `02_CSV_Data\task11_radar_points_frame101.csv` (3,924 bytes)
- `02_CSV_Data\task11_vehicle_frame_candidates.csv` (228,493 bytes)
- `02_CSV_Data\task11_yolo11s_frame150.csv` (304 bytes)
- `02_CSV_Data\task11_yolo_diagnostic_frame150.csv` (664 bytes)
- `02_CSV_Data\task11_yolo_diagnostic_summary.csv` (70 bytes)
- `03_Configurations\DefaultGemstar_Task11_snapshot.ini` (5,007 bytes)
- `03_Configurations\task11_dbscan_parameters.txt` (239 bytes)
- `03_Configurations\task11_frame150_independent_clustering_config.txt` (196 bytes)
- `03_Configurations\task11_lidar_mount_config.txt` (1,058 bytes)
- `04_Code\task09_extract_mor100_camera.py` (3,800 bytes)
- `04_Code\task11_build_research_report.py` (16,490 bytes)
- `04_Code\task11_camera_lidar_radar_projection.m` (6,161 bytes)
- `04_Code\task11_check_ai_libraries.py` (984 bytes)
- `04_Code\task11_check_lidar_directions.py` (1,915 bytes)
- `04_Code\task11_common_sensor_frame.m` (3,927 bytes)
- `04_Code\task11_dbscan_clustering.m` (8,638 bytes)
- `04_Code\task11_extract_camera_frame150.py` (4,221 bytes)
- `04_Code\task11_extract_lidar_normals.py` (2,352 bytes)
- `04_Code\task11_extract_measurements.py` (5,297 bytes)
- `04_Code\task11_find_forward_vehicle_frames.py` (3,578 bytes)
- `04_Code\task11_find_object_candidates.py` (3,073 bytes)
- `04_Code\task11_find_vehicle_frames.py` (2,168 bytes)
- `04_Code\task11_frame150_surface_audit.py` (3,346 bytes)
- `04_Code\task11_frame150_vehicle_inspection.m` (5,656 bytes)
- `04_Code\task11_ground_filter_exploration.m` (3,084 bytes)
- `04_Code\task11_independent_obstacle_clustering.m` (6,098 bytes)
- `04_Code\task11_inspect_frame150.py` (3,746 bytes)
- `04_Code\task11_inspect_frame431.py` (2,644 bytes)
- `04_Code\task11_inspect_osi.py` (5,362 bytes)
- `04_Code\task11_lidar_geometry_check.py` (1,615 bytes)
- `04_Code\task11_lidar_gt_alignment.m` (4,888 bytes)
- `04_Code\task11_lidar_pointcloud.m` (4,536 bytes)
- `04_Code\task11_lidar_radar_alignment.m` (2,958 bytes)
- `04_Code\task11_lidar_radar_frame150.m` (5,290 bytes)
- `04_Code\task11_lidar_radar_frame150extra.m` (1,779 bytes)
- `04_Code\task11_lidar_ray_diagnostics.py` (3,613 bytes)
- `04_Code\task11_normal_ground_filter.m` (3,911 bytes)
- `04_Code\task11_normal_ground_filter2.m` (489 bytes)
- `04_Code\task11_normal_ground_filter3.m` (465 bytes)
- `04_Code\task11_radar_reconstruction.m` (3,941 bytes)
- `04_Code\task11_three_sensor_dashboard.m` (6,697 bytes)
- `04_Code\task11_validate_camera_lidar_geometry.m` (6,671 bytes)
- `04_Code\task11_validate_clusters.py` (2,178 bytes)
- `04_Code\task11_validate_lidar_radar_association.m` (5,232 bytes)
- `04_Code\task11_validate_measurements.py` (2,634 bytes)
- `04_Code\task11_verify_vehicle_visibility.py` (3,496 bytes)
- `04_Code\task11_visualize_frame431.m` (2,380 bytes)
- `04_Code\task11_world_to_ego.m` (3,556 bytes)
- `04_Code\task11_yolo11s_test.py` (3,243 bytes)
- `04_Code\task11_yolo_diagnostic.py` (4,586 bytes)
- `04_Code\task11_yolo_vehicle_detection.py` (3,471 bytes)
- `05_Raw_Data_References\task11_original_osi_references.txt` (363 bytes)
- `06_Research_Findings\task11_camera_yolo_frame150_findings.txt` (288 bytes)
- `06_Research_Findings\task11_cluster_geometry_findings.txt` (468 bytes)
- `06_Research_Findings\task11_final_research_summary.txt` (1,658 bytes)
- `06_Research_Findings\task11_forward_vehicle_search.txt` (2,108 bytes)
- `06_Research_Findings\task11_frame150_association_validation.txt` (312 bytes)
- `06_Research_Findings\task11_frame150_initial_inspection.txt` (454 bytes)
- `06_Research_Findings\task11_frame150_lidar_radar_comparison.txt` (212 bytes)
- `06_Research_Findings\task11_frame150_surface_audit.txt` (852 bytes)
- `06_Research_Findings\task11_frame150_visibility_diagnostic.txt` (2,235 bytes)
- `06_Research_Findings\task11_frame150_visual_inspection.txt` (280 bytes)
- `06_Research_Findings\task11_frame431_alignment_notes.txt` (290 bytes)
- `06_Research_Findings\task11_lidar_cpp_ray_generation.txt` (60,570 bytes)
- `06_Research_Findings\task11_lidar_direction_implementation.txt` (2,705 bytes)
- `06_Research_Findings\task11_lidar_directions.txt` (576 bytes)
- `06_Research_Findings\task11_lidar_geometry_check.txt` (2,388 bytes)
- `06_Research_Findings\task11_lidar_mount_source.txt` (4,372 bytes)
- `06_Research_Findings\task11_lidar_ray_diagnostics.txt` (1,713 bytes)
- `06_Research_Findings\task11_lidar_ray_order.txt` (34,568 bytes)
- `06_Research_Findings\task11_osi_inspection.txt` (13,648 bytes)
- `06_Research_Findings\task11_projection_limitations.txt` (417 bytes)
- `06_Research_Findings\task11_radar_coordinate_cpp.txt` (27,208 bytes)
- `06_Research_Findings\task11_sensor_vehicle_config_inspection.txt` (10,343 bytes)
- `06_Research_Findings\task11_three_sensor_dashboard_findings.txt` (491 bytes)
- `06_Research_Findings\task11_vehicle_platform_source_analysis.txt` (19,668 bytes)
- `06_Research_Findings\task11_yolo11s_findings.txt` (266 bytes)
- `06_Research_Findings\task11_yolo_missed_detection_diagnostic.txt` (391 bytes)
- `06_Research_Findings\task11_yolo_model_comparison.txt` (669 bytes)