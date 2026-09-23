#include <vector>
#include <cmath>

double mean(const std::vector<double>& values) {
    double sum = 0.0;
    for (double v : values) sum += v;
    return sum / values.size();
}

double rms(const std::vector<double>& values) {
    double m = mean(values);
    return std::sqrt(m * m);
}
