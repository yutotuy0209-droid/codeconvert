function [scaled, count] = analyze_values(values, threshold)
% Normalize values and count samples above threshold.
scaled = normalize_values(values);
count = sum(scaled >= threshold);
end

function scaled = normalize_values(values)
% Normalize by maximum absolute value.
peak = max(abs(values));
scaled = values ./ peak;
end
