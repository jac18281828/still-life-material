// SPDX-License-Identifier: MIT
#pragma once

#include <cmath>

#include <gman/gmanvector.h>
#include <gman/ri.h>

namespace gmanshader {

namespace gildedframe {

constexpr double kMinTangentLength = 1e-6;

struct Vec3 {
  double x;
  double y;
  double z;
};

inline Vec3 widen(GMANVector const& v) { return {v.getX(), v.getY(), v.getZ()}; }

inline double dot(Vec3 const& a, Vec3 const& b) { return a.x * b.x + a.y * b.y + a.z * b.z; }

inline double length(Vec3 const& v) { return std::sqrt(dot(v, v)); }

inline Vec3 scaled(Vec3 const& v, double f) { return {v.x * f, v.y * f, v.z * f}; }

inline Vec3 difference(Vec3 const& a, Vec3 const& b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }

inline Vec3 sum(Vec3 const& a, Vec3 const& b) { return {a.x + b.x, a.y + b.y, a.z + b.z}; }

inline GMANVector narrow(Vec3 const& v) {
  return GMANVector(static_cast<RtFloat>(v.x), static_cast<RtFloat>(v.y), static_cast<RtFloat>(v.z));
}

inline Vec3 unit(Vec3 const& v) { return scaled(v, 1.0 / length(v)); }

// The unit tangent of `tangent` in the plane perpendicular to the unit `normal`, or false when the projection is
// shorter than kMinTangentLength.
inline bool tangentInPlane(Vec3 const& tangent, Vec3 const& normal, Vec3& out) {
  Vec3 const projected = difference(tangent, scaled(normal, dot(tangent, normal)));
  if (!(length(projected) >= kMinTangentLength)) {
    return false;
  }
  out = unit(projected);
  return true;
}

} // namespace gildedframe

// The unit shading normal `n` bent by a luminance gradient (dLs, dLt) along the surface tangents dPdu and dPdv:
// normalize(n - bump * (tu * dLs + tv * dLt)), tu and tv being the tangents projected onto the plane of `n` and
// normalized. The normal stays unbent, and unit length, when bump or both gradients are zero, when either tangent
// projects to under 1e-6, or when `n` is itself zero, which is returned as is. Arithmetic runs in double, so any
// finite RtFloat inputs give a finite result.
inline GMANVector bentNormal(GMANVector const& n, GMANVector const& dPdu, GMANVector const& dPdv, RtFloat dLs,
                             RtFloat dLt, RtFloat bump) {
  using namespace gildedframe;
  Vec3 const raw = widen(n);
  if (!(length(raw) > 0.0)) {
    return n;
  }
  Vec3 const normal = unit(raw);
  if (bump == 0.0f || (dLs == 0.0f && dLt == 0.0f)) {
    return narrow(normal);
  }
  Vec3 tu{};
  Vec3 tv{};
  if (!tangentInPlane(widen(dPdu), normal, tu) || !tangentInPlane(widen(dPdv), normal, tv)) {
    return narrow(normal);
  }
  Vec3 const gradient = sum(scaled(tu, dLs), scaled(tv, dLt));
  return narrow(unit(difference(normal, scaled(gradient, bump))));
}

} // namespace gmanshader
