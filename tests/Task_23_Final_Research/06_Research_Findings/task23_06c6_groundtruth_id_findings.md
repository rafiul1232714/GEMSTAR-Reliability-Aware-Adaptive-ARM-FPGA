# Task 23.6C-6 — GroundTruth Actor-ID Investigation

Status: SOURCE-CODE FINDING; STATIC EXPORT NOT YET VERIFIED

## Confirmed from inspected source

1. LiDAR hit metadata uses Unreal actor GetUniqueID().
2. Dynamic vehicle GroundTruth uses actor GetUniqueID().
3. The dynamic GroundTruth logic uses class-path filtering.
4. Stationary GroundTruth uses GetTypeHash(actor->GetName()).
5. Consequently, stationary GroundTruth IDs cannot be directly
   assumed equal to LiDAR reflection actor IDs.

## Evidence from earlier recordings

- 20,032 sampled valid LiDAR reflections had usable actor IDs.
- Zero matched the moving-object GroundTruth IDs.
- Five reflection actor IDs were observed.
- No stationary objects appeared in the sampled dynamic
  GroundTruth frames.

## Still unverified

- Whether static-map GroundTruth is exported separately.
- Whether the five observed LiDAR actors are stationary.
- Whether a stable crosswalk between actor-name hashes
  and Unreal runtime unique IDs is available.
- Which maps contain controllable, reference-labeled targets.

## Research policy

Do not report the earlier geometric association fraction
as detection accuracy or fusion accuracy.

Do not alter the original GEMSTAR logger before verifying
the reference-data export pathway.
