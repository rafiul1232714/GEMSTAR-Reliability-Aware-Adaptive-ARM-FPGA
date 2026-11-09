/*
 * Copyright (c) 2026 DLR e.V.
 *
 * This program and the accompanying materials are made
 * available under the terms of the Eclipse Public License 2.0
 * which is available at https://www.eclipse.org/legal/epl-2.0/
 *
 * SPDX-License-Identifier: EPL-2.0
 */

#include "WeatherVisualController.h"
#include "WeatherEffectLog.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/SceneComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraFunctionLibrary.h"
#include "Engine/ExponentialHeightFog.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Kismet/GameplayStatics.h"

 // Sets default values
AWeatherVisualController::AWeatherVisualController() {

	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostUpdateWork;

	WeatherAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("WeatherAnchor"));
	RootComponent = WeatherAnchor;

	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> RainSytemFinder(TEXT("/ue_weather_effect_feature/ns_rain.ns_rain"));
	if (RainSytemFinder.Succeeded()) {
		RainSytemAsset = RainSytemFinder.Object;
		UE_LOG(WeatherEffect, Log, TEXT("Rain Niagara system loaded."));
	}
	else {
		UE_LOG(WeatherEffect, Error, TEXT("Failed to load Rain Niagara system."));
	}

	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> SnowSytemFinder(TEXT("/ue_weather_effect_feature/ns_snow.ns_snow"));
	if (SnowSytemFinder.Succeeded()) {
		SnowSytemAsset = SnowSytemFinder.Object;
		UE_LOG(WeatherEffect, Log, TEXT("Snow Niagara system loaded."));
	}
	else {
		UE_LOG(WeatherEffect, Error, TEXT("Failed to load Snow Niagara system."));
	}
}

void AWeatherVisualController::BeginPlay() {

	Super::BeginPlay();
	SpawnFogActor();
}

void AWeatherVisualController::SetWeatherState(const FGEMSTARWeatherState& NewWeatherState) {

	CurrentWeatherState = NewWeatherState;
	ApplyWeatherState();
}

void AWeatherVisualController::WeatherDataUpdate_Implementation(FWeatherData& data, int32 targetIndex) {

	SetWeatherState(data.WeatherState);
}

void AWeatherVisualController::Tick(float DeltaTime) {

	Super::Tick(DeltaTime);

	APlayerCameraManager* CameraManager = UGameplayStatics::GetPlayerCameraManager(GetWorld(), 0);

	if (!IsValid(CameraManager)) {
		return;
	}

	SetActorLocation(CameraManager->GetCameraLocation());
}

void AWeatherVisualController::ApplyWeatherState() {

	if (!CurrentWeatherState.bWeatherEffectEnabled) {
		if (IsValid(RainComponent)) {
			RainComponent->Deactivate();
		}
		if (IsValid(SnowComponent)) {
			SnowComponent->Deactivate();
		}
		if (IsValid(FogActor)) {
			if (UExponentialHeightFogComponent* FogComponent = FogActor->GetComponent()) {
				FogComponent->SetFogDensity(ClearAtmosphere);
			}
		}

		return;
	}

	ApplyFog();
	ApplyRain();
	ApplySnow();
}

void AWeatherVisualController::SpawnFogActor() {

	for (TActorIterator<AExponentialHeightFog> It(GetWorld()); It; ++It) {
		FogActor = *It;
		UE_LOG(WeatherEffect, Log, TEXT("WeatherVisualController: ExponentialHeightFog found."));
		return;
	}

	FActorSpawnParameters SpawnParams;
	FogActor = GetWorld()->SpawnActor<AExponentialHeightFog>(
		AExponentialHeightFog::StaticClass(),
		FVector::ZeroVector,
		FRotator::ZeroRotator,
		SpawnParams
	);

	if (FogActor) {
		UE_LOG(WeatherEffect, Log, TEXT("ExponentialHeightFog spawned!"));
	}
	else {
		UE_LOG(WeatherEffect, Log, TEXT("Failed to spawne ExponentialHeightFog!"));
	}
}

void AWeatherVisualController::ApplyFog() {

	if (!FogActor) {
		UE_LOG(WeatherEffect, Warning, TEXT("WeatherVisualController: Cannot apply Fog. FogActor is null."));
		return;
	}

	UExponentialHeightFogComponent* FogComponent = FogActor->GetComponent();
	if (!FogComponent) {
		return;
	}

	// No Fog selected , or has visibilty rang 
	if (!CurrentWeatherState.bHasMOR || CurrentWeatherState.MOR <= 0.0) {
		FogComponent->SetFogDensity(ClearAtmosphere);
		return;
	}

	const double MOR = CurrentWeatherState.MOR;

	const float FogDensity = FMath::Clamp(static_cast<float>(2.0 / MOR), 0.0f, 0.2f);
	FogComponent->SetFogDensity(FogDensity);
	FogComponent->SetVolumetricFog(true);

	FogComponent->SetFogInscatteringColor(FogInscatteringColor);
	FogComponent->SetVolumetricFogExtinctionScale(VolumetricFogExtinctionScale);

	UE_LOG(WeatherEffect, Warning, TEXT("Fog applied. MOR=%.2f m, FogDensity=%.4f"), MOR, FogDensity);
}

void AWeatherVisualController::SpawnRain() {

	if (IsValid(RainComponent)) {
		return;
	}
	if (!RainSytemAsset) {
		UE_LOG(WeatherEffect, Error, TEXT("RainSytemAsset is null."));
		return;
	}

	RainComponent = UNiagaraFunctionLibrary::SpawnSystemAttached(
		RainSytemAsset,
		WeatherAnchor,
		NAME_None,
		FVector(0.0f, 0.0f, 1000.0f),  // 10 m above camera
		FRotator::ZeroRotator,
		EAttachLocation::KeepRelativeOffset,
		false,   // Auto destroy
		false,  // Auto activate
		ENCPoolMethod::None,
		false
	);

	if (RainComponent) {
		UE_LOG(WeatherEffect, Log, TEXT("Rain effect spawned!"));
	}
}

void AWeatherVisualController::ApplyRain() {

	const bool bIsRain = CurrentWeatherState.bHasPrecipitation &&
		CurrentWeatherState.PrecipitationType == GemstarWeatherTypes::Rain &&
		CurrentWeatherState.PrecipitationIntensity > 0.0;

	if (!bIsRain) {

		if (RainComponent) {
			RainComponent->Deactivate();
		}
		return;
	}

	SpawnRain();
	if (!RainComponent) {
		return;
	}

	const float RainSpawnRate = FMath::Clamp(static_cast<float>(CurrentWeatherState.PrecipitationIntensity * 100.0), 0.0f, 10000.0f);
	RainComponent->SetVariableFloat(TEXT("User.RainSpawnRate"), RainSpawnRate);

	RainComponent->Activate(true);
	UE_LOG(WeatherEffect, Log, TEXT("Rain activated. Rain intensity=%.2f, SpawnRate=%.2f"), CurrentWeatherState.PrecipitationIntensity, RainSpawnRate);
}

void AWeatherVisualController::SpawnSnow() {

	if (IsValid(SnowComponent)) {
		return;
	}
	if (!SnowSytemAsset) {
		UE_LOG(WeatherEffect, Error, TEXT("SnowSytemAsset is null."));
		return;
	}

	SnowComponent = UNiagaraFunctionLibrary::SpawnSystemAttached(
		SnowSytemAsset,
		WeatherAnchor,
		NAME_None,
		FVector(0.0f, 0.0f, 1000.0f),  // 10 m above camera
		FRotator::ZeroRotator,
		EAttachLocation::KeepRelativeOffset,
		false,   // Auto destroy
		false,  // Auto activate
		ENCPoolMethod::None,
		false
	);

	if (SnowSytemAsset) {
		UE_LOG(WeatherEffect, Log, TEXT("Snow effect spawned!"));
	}
}

void AWeatherVisualController::ApplySnow() {

	const bool bIsSnow = CurrentWeatherState.bHasPrecipitation &&
		CurrentWeatherState.PrecipitationType == GemstarWeatherTypes::Snow &&
		CurrentWeatherState.PrecipitationIntensity > 0.0;

	if (!bIsSnow) {

		if (SnowComponent) {
			SnowComponent->Deactivate();
		}
		return;
	}

	SpawnSnow();
	if (!SnowComponent) {
		return;
	}

	const float SnowSpawnRate = FMath::Clamp(static_cast<float>(CurrentWeatherState.PrecipitationIntensity * 50.0), 0.0f, 50000.0f);
	SnowComponent->SetVariableFloat(TEXT("User.SnowSpawnRate"), SnowSpawnRate);

	SnowComponent->Activate(true);
	UE_LOG(WeatherEffect, Log, TEXT("Snow activated. Snow intensity=%.2f, SpawnRate=%.2f"), CurrentWeatherState.PrecipitationIntensity, SnowSpawnRate);
}
