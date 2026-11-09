/*
 * Copyright (c) 2026 DLR e.V.
 *
 * This program and the accompanying materials are made
 * available under the terms of the Eclipse Public License 2.0
 * which is available at https://www.eclipse.org/legal/epl-2.0/
 *
 * SPDX-License-Identifier: EPL-2.0
 */

#include "SimpleLidar.h"

#include "Effects/LidarWeatherEffectModel.h"
#include "PhysicsPublic.h"
#include "Materials/Material.h"

// Sets default values
ASimpleLidar::ASimpleLidar()
{
}

// Called when the game starts or when spawned
void ASimpleLidar::BeginPlay()
{
	Super::BeginPlay();
	CreateTestConfig();

	// complex collisions: true
	TraceParams = FCollisionQueryParams(TEXT("LaserTrace"), true, GetOwner());
	TraceParams.bReturnPhysicalMaterial = true;
	TraceParams.bTraceComplex = true;
	TraceParams.bReturnFaceIndex = true;
}

void ASimpleLidar::Tick(float time) {
	if (!TickActive) return;
	GetScanData();
	if (bDebugRayTraces || bDebugReflections || bDebugNormals)
		ShowSensorDebugInformation();
	if (PublishingActive)
	{
		GenerateOSIMessage();
		SendData(*Sensor.SensorView);
	}
}

void ASimpleLidar::GetScanData() {

	// Get owner's location and rotation
	const FVector LidarPosition = this->GetActorLocation();
	const FRotator LidarRotation = this->GetActorRotation();

	// Initialize array for raycast result
	Sensor.RecordedHits.Init(FHitResultAndIntesity(), Sensor.Number_of_rays_horizontal * Sensor.Number_of_rays_vertical);

	// Calculate batch size for 'ParallelFor' based on workable thread
	const int32 ThreadNum = FPlatformMisc::NumberOfWorkerThreadsToSpawn();
	const int32 DivideEnd = FMath::FloorToInt((float)(Sensor.RecordedHits.Num() / ThreadNum));

	ParallelFor(
		ThreadNum,
		[&](int32 PFIndex)
		{
			int32 StartAt = PFIndex * DivideEnd;
			if (StartAt >= Sensor.RecordedHits.Num()) {
				return;
			}

			int32 EndAt = StartAt + DivideEnd;
			if (PFIndex == (ThreadNum - 1)) {
				EndAt = Sensor.RecordedHits.Num();
			}

			for (int32 Index = StartAt; Index < EndAt; ++Index) {
				const float HAngle = Sensor.AzimuthAngles[Index % Sensor.Number_of_rays_horizontal];
				const float VAngle = Sensor.ElevationAngles[Index / Sensor.Number_of_rays_horizontal];

				FRotator LaserRotation(FMath::RadiansToDegrees(VAngle), FMath::RadiansToDegrees(HAngle), 0.f);
				FRotator Rotation = UKismetMathLibrary::ComposeRotators(LaserRotation, LidarRotation);

				FVector EndPoint = LidarPosition + Sensor.SensorViewConfig->range() * 100 * UKismetMathLibrary::GetForwardVector(Rotation);

				GetWorld()->LineTraceSingleByChannel(
					Sensor.RecordedHits[Index].HitResult, LidarPosition, EndPoint, ECC_Visibility, TraceParams, FCollisionResponseParams::DefaultResponseParam);
				if (Sensor.RecordedHits[Index].HitResult.bBlockingHit) {
					Sensor.RecordedHits[Index].Intesity = ComputeLidarSignalStrength(Sensor.RecordedHits[Index].HitResult);
				}
			}
		},
		!SupportMultithread
	);

}

void ASimpleLidar::GenerateOSIMessage() {
	delete Sensor.SensorView;
	Sensor.SensorView = new osi3::SensorView();
	auto* lidarSensorView = Sensor.SensorView->add_lidar_sensor_view();
	auto* viewConfiguration = lidarSensorView->mutable_view_configuration();
	if (Sensor.SensorViewConfig != nullptr && Sensor.SensorViewConfig->lidar_sensor_view_configuration_size())
		viewConfiguration->CopyFrom(Sensor.SensorViewConfig->lidar_sensor_view_configuration(0));

	for (auto& hit : Sensor.RecordedHits) {
		auto* reflection = lidarSensorView->add_reflection();
		reflection->set_time_of_flight(2 * 0.01 * hit.HitResult.Distance / SPEED_OF_LIGHT);

		osi3::Vector3d* normal_to_surface = reflection->mutable_normal_to_surface();
		normal_to_surface->set_x(hit.HitResult.ImpactNormal.X);
		normal_to_surface->set_y(-hit.HitResult.ImpactNormal.Y);
		normal_to_surface->set_z(hit.HitResult.ImpactNormal.Z);
		reflection->set_doppler_shift(0);
		if (hit.HitResult.bBlockingHit) {
			reflection->mutable_object_id()->set_value(hit.HitResult.GetActor()->GetUniqueID());
			reflection->set_signal_strength(hit.Intesity);
		}
		else {
			reflection->mutable_object_id()->set_value(UINT64_MAX);
			reflection->set_signal_strength(0.0);
		}
	}

	Parent = GetAttachParentActor();

	if (Parent != nullptr) {
		auto* moving_object = Sensor.SensorView->mutable_global_ground_truth()->add_moving_object();
		uint32_t uniqueID = Parent->GetUniqueID();
		moving_object->mutable_id()->set_value(uniqueID);
		moving_object->mutable_base()->set_allocated_position(ToOSI::Position(Parent->GetActorLocation()));
		moving_object->mutable_base()->set_allocated_orientation(ToOSI::Orientation3d(Parent->GetActorQuat()));
		Sensor.SensorView->mutable_global_ground_truth()->mutable_host_vehicle_id()->set_value(uniqueID);
	}

	//apply weathereffect
	if (HasWeatherData && Sensor.SensorView) {
		LidarWeatherEffectModel LidarWeatherEffectModel;
		LidarWeatherEffectModel.ApplyLidarWeatherEffect(*Sensor.SensorView, LatestWeatherData);
	}
}

float ASimpleLidar::ComputeLidarSignalStrength(const FHitResult& Hit)
{
	// Surface normal from hit result
	FVector Normal = Hit.ImpactNormal.GetSafeNormal();

	// Vector from hit point back to lidar (return direction)
	FVector ToLidar = (Hit.TraceStart - Hit.ImpactPoint).GetSafeNormal();

	// Angle factor: cos^2(theta), clamped to [0,1]
	float CosTheta = FVector::DotProduct(Normal, ToLidar);
	CosTheta = FMath::Clamp(CosTheta, 0.0f, 1.0f);
	float AngleFactor = FMath::Square(CosTheta);
	AngleFactor = FMath::Clamp(AngleFactor, 0.0f, 1.0f);

	// Distance attenuation: 1 / (1 + (d/d0)^2)
	float DistanceFactor = 1.0f / (1.0f + FMath::Square(Hit.Distance / DistanceHalfFalloff));

	float Rho = 1.0f; // default backscatter coefficient
	if (Hit.Component.IsValid() && Hit.Component.Get())
	{
		UMaterialInterface* HitMaterial = GetHitMaterial(Hit);
		Rho = GetReflectivity(HitMaterial);
	}
	float Signal = Rho * AngleFactor * DistanceFactor;
	return FMath::Clamp(Signal, 0.0f, 1.0f);
}

UMaterialInterface* ASimpleLidar::GetHitMaterial(const FHitResult& Hit) const {

	UMaterialInterface* HitMat = nullptr;
	UPrimitiveComponent* PrimComp = Cast<UPrimitiveComponent>(Hit.Component.Get());
	if (!PrimComp)
	{
		return nullptr;
	}
	if (PrimComp && Hit.FaceIndex != INDEX_NONE)
	{
		int32 SectionIndex = INDEX_NONE;
		HitMat = PrimComp->GetMaterialFromCollisionFaceIndex(Hit.FaceIndex, SectionIndex);
		if (HitMat)
		{
			return HitMat;
		}
	}
	if (!HitMat && PrimComp->GetNumMaterials() > 0)
	{
		return PrimComp->GetMaterial(0);
	}
	return nullptr;
}

float ASimpleLidar::GetReflectivity(const UMaterialInterface* Material) const {

	float Rho = 1.0f; // default backscatter coefficient
	if (Material) {
		float Reflectivity = 1.0f; // Lidar Unreal Material Reflectivity
		float Roughness = 1.0f;
		float Metallic = 1.0f;
		if (Material->GetScalarParameterValue(TEXT("LidarReflectivity"), Reflectivity)) {
			return  FMath::Clamp(Reflectivity, 0.0f, 1.0f);
		}
		else if (Material->GetScalarParameterValue(TEXT("Roughness"), Roughness) && Material->GetScalarParameterValue(TEXT("Metallic"), Metallic)) {
			Rho = FMath::Clamp(0.1f + (1.0f - Roughness) * 0.6f - Metallic * 0.3f, 0.05f, 1.0f);
		}
	}
	return  FMath::Clamp(Rho, 0.0f, 1.0f);
}

void ASimpleLidar::SetSensorConfiguration(FSensorConfigData NewSensorConfiguration)
{
	Super::SetSensorConfiguration(NewSensorConfiguration);
	Sensor.SensorViewConfig->clear_lidar_sensor_view_configuration();
	auto* conf = Sensor.SensorViewConfig->add_lidar_sensor_view_configuration();
	conf->set_field_of_view_horizontal(SensorConfiguration.Lidar.FieldOfViewHorizontal);
	conf->set_field_of_view_vertical(SensorConfiguration.Lidar.FieldOfViewVertical);
	conf->set_number_of_rays_horizontal(SensorConfiguration.Lidar.NumberOfRaysHorizontal);
	conf->set_number_of_rays_vertical(SensorConfiguration.Lidar.NumberOfRaysVertical);
	conf->mutable_mounting_position()->set_allocated_position(
		ToOSI::Position(SensorConfiguration.Offset.GetLocation()));
	conf->mutable_mounting_position()->set_allocated_orientation(
		ToOSI::Orientation3d(SensorConfiguration.Offset.GetRotation()));
	Sensor.SensorViewConfig->set_range(NewSensorConfiguration.Lidar.Range);

	//calculate angles
	Sensor.AzimuthAngles.Empty();
	Sensor.ElevationAngles.Empty();
	Sensor.Number_of_rays_horizontal = Sensor.SensorViewConfig->lidar_sensor_view_configuration(0).number_of_rays_horizontal();
	for (uint32_t i = 0; i < Sensor.Number_of_rays_horizontal; i++) {
		Sensor.AzimuthAngles.Add(-0.5 * Sensor.SensorViewConfig->lidar_sensor_view_configuration(0).field_of_view_horizontal()
			+ Sensor.SensorViewConfig->lidar_sensor_view_configuration(0).field_of_view_horizontal() / (Sensor.Number_of_rays_horizontal - 1) * i);
	}
	Sensor.Number_of_rays_vertical = Sensor.SensorViewConfig->lidar_sensor_view_configuration(0).number_of_rays_vertical();
	for (uint32_t i = 0; i < Sensor.Number_of_rays_vertical; i++) {
		Sensor.ElevationAngles.Add(-0.5 * Sensor.SensorViewConfig->lidar_sensor_view_configuration(0).field_of_view_vertical()
			+ Sensor.SensorViewConfig->lidar_sensor_view_configuration(0).field_of_view_vertical() / (Sensor.Number_of_rays_vertical - 1) * i);
	}
}

void ASimpleLidar::CreateTestConfig() {
	Sensor.SensorViewConfig = new osi3::SensorViewConfiguration();
	Sensor.SensorViewConfig->set_range(Range);
}

void ASimpleLidar::ShowSensorDebugInformation() {
	int noHitCounter = 0;
	for (auto& hit : Sensor.RecordedHits) {
		if (hit.HitResult.bBlockingHit) {
			if (bDebugRayTraces)
				DrawDebugLine(GetWorld(), hit.HitResult.TraceStart, hit.HitResult.ImpactPoint, FColor::Green, false, 0.0f, 0, 1.0f);
			if (bDebugReflections)
				DrawDebugPoint(GetWorld(), hit.HitResult.ImpactPoint, 10.0f, FColor::Red, false, 0.0f);
			if (bDebugNormals)
				DrawDebugLine(GetWorld(), hit.HitResult.ImpactPoint, hit.HitResult.ImpactPoint + hit.HitResult.ImpactNormal * 10, FColor::Blue, false, 0.0f, 0, 1.0f);
		}
		else {
			noHitCounter++;
		}
	}
	UE_LOG(Lidar, Log, TEXT("No reflection from lidar: %d of %d"), noHitCounter, Sensor.RecordedHits.Num());
}