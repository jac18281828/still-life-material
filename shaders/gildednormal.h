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

// The unit shading normal of a tangent-space normal-map texel (red, green, blue), each in [0, 1] and decoded to
// 2c - 1 along the tangent, the bitangent and `n`. The tangent is dPdu projected onto the plane of the unit `n`; the
// bitangent is dPdv made perpendicular to `n` and the tangent. Green runs along -dPdv, or along +dPdv when `greenDown`
// reads a DirectX map. The normal stays unbent, and unit length, when either tangent degenerates to under 1e-6 or the
// decoded vector is zero; a zero `n` is returned as is. Arithmetic runs in double, so any finite RtFloat inputs give
// a finite result.
inline GMANVector mappedNormal(GMANVector const& n, GMANVector const& dPdu, GMANVector const& dPdv, RtFloat red,
                               RtFloat green, RtFloat blue, bool greenDown) {
  using namespace gildedframe;
  Vec3 const raw = widen(n);
  if (!(length(raw) > 0.0)) {
    return n;
  }
  Vec3 const normal = unit(raw);
  Vec3 tangent{};
  Vec3 bitangent{};
  if (!tangentInPlane(widen(dPdu), normal, tangent)) {
    return narrow(normal);
  }
  Vec3 const flattened = difference(widen(dPdv), scaled(normal, dot(widen(dPdv), normal)));
  if (!tangentInPlane(flattened, tangent, bitangent)) {
    return narrow(normal);
  }
  double const alongGreen = 2.0 * static_cast<double>(green) - 1.0;
  Vec3 const bent = sum(sum(scaled(tangent, 2.0 * static_cast<double>(red) - 1.0),
                            scaled(bitangent, greenDown ? alongGreen : -alongGreen)),
                        scaled(normal, 2.0 * static_cast<double>(blue) - 1.0));
  if (!(length(bent) > 0.0)) {
    return narrow(normal);
  }
  return narrow(unit(bent));
}

} // namespace gmanshader
