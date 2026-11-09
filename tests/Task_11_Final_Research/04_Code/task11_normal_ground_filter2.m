fprintf("Total points: %d\n", height(T));

fprintf("Ground-like points: %d\n", ...
    sum(T.groundCandidate));

fprintf("Other points: %d\n", ...
    sum(T.otherCandidate));

C = T(T.otherCandidate, :);

fprintf("\nOther-point coordinate ranges:\n");

fprintf("X: %.2f to %.2f m\n", ...
    min(C.x_ego_m), max(C.x_ego_m));

fprintf("Y: %.2f to %.2f m\n", ...
    min(C.y_ego_m), max(C.y_ego_m));

fprintf("Z: %.2f to %.2f m\n", ...
    min(C.z_ego_m), max(C.z_ego_m));