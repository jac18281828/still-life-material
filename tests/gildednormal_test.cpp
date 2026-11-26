// SPDX-License-Identifier: MIT

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <random>

#include "gildednormal.h"

namespace {

int failures = 0;

void check(bool ok, char const* what) {
  if (!ok) {
    std::fprintf(stderr, "FAIL: %s\n", what);
    ++failures;
  }
}

double lengthOf(GMANVector const& v) {
  return std::sqrt(static_cast<double>(v.getX()) * v.getX() + static_cast<double>(v.getY()) * v.getY() +
                   static_cast<double>(v.getZ()) * v.getZ());
}

bool finite(GMANVector const& v) {
  return std::isfinite(v.getX()) && std::isfinite(v.getY()) && std::isfinite(v.getZ());
}

bool near(GMANVector const& a, GMANVector const& b, double tolerance = 1e-6) {
  return std::fabs(a.getX() - b.getX()) <= tolerance && std::fabs(a.getY() - b.getY()) <= tolerance &&
         std::fabs(a.getZ() - b.getZ()) <= tolerance;
}

double dotOf(GMANVector const& a, GMANVector const& b) {
  return static_cast<double>(a.getX()) * b.getX() + static_cast<double>(a.getY()) * b.getY() +
         static_cast<double>(a.getZ()) * b.getZ();
}

GMANVector const kNormal(0, 0, 1);
GMANVector const kDPdu(1, 0, 0);
GMANVector const kDPdv(0, 1, 0);

void identityWhenNothingBends() {
  using gmanshader::bentNormal;
  check(near(bentNormal(kNormal, kDPdu, kDPdv, 0.5f, -0.25f, 0.0f), kNormal), "bump 0 returns the unit normal");
  check(near(bentNormal(kNormal, kDPdu, kDPdv, 0.0f, 0.0f, 6.0f), kNormal), "no gradient returns the unit normal");
  GMANVector const scaledNormal(0, 0, 4);
  GMANVector const bent = bentNormal(scaledNormal, kDPdu, kDPdv, 0.0f, 0.0f, 6.0f);
  check(near(bent, kNormal), "an unbent normal comes back unit length");
}

void zeroTangentLeavesNormalUnbent() {
  using gmanshader::bentNormal;
  GMANVector const zero(0, 0, 0);
  check(near(bentNormal(kNormal, zero, kDPdv, 0.5f, 0.5f, 6.0f), kNormal), "a zero dPdu leaves the normal unbent");
  check(near(bentNormal(kNormal, kDPdu, zero, 0.5f, 0.5f, 6.0f), kNormal), "a zero dPdv leaves the normal unbent");
  check(near(bentNormal(kNormal, zero, zero, -3.0f, 2.0f, 10.0f), kNormal),
        "two zero tangents leave the normal unbent");
}

void parallelTangentLeavesNormalUnbent() {
  using gmanshader::bentNormal;
  GMANVector const alongNormal(0, 0, 2);
  check(near(bentNormal(kNormal, alongNormal, kDPdv, 0.5f, 0.5f, 6.0f), kNormal), "dPdu along the normal is unbent");
  check(near(bentNormal(kNormal, kDPdu, alongNormal, 0.5f, 0.5f, 6.0f), kNormal), "dPdv along the normal is unbent");
  GMANVector const diagonal(1, 1, 1);
  GMANVector const alongDiagonal(2, 2, 2);
  check(near(bentNormal(diagonal, alongDiagonal, kDPdv, 1.0f, 1.0f, 1.0f),
             bentNormal(diagonal, kDPdu, kDPdu, 0.0f, 0.0f, 1.0f)),
        "a tangent parallel to a skew normal is unbent");
}

void positiveGradientTiltsAwayFromTangent() {
  using gmanshader::bentNormal;
  GMANVector const bent = bentNormal(kNormal, kDPdu, kDPdv, 0.5f, 0.0f, 1.0f);
  check(bent.getX() < -0.4, "a positive dLs tilts away from dPdu");
  check(std::fabs(bent.getY()) < 1e-6, "dLs alone leaves the dPdv axis alone");
  check(std::fabs(lengthOf(bent) - 1.0) < 1e-6, "the bent normal has unit length");

  GMANVector const along(1, 0, 0.5);
  GMANVector const tilted = bentNormal(kNormal, along, kDPdv, 0.5f, 0.0f, 1.0f);
  check(tilted.getX() < -0.4, "a skewed tangent projects before it bends");
  check(std::fabs(lengthOf(tilted) - 1.0) < 1e-6, "a skewed bend has unit length");

  GMANVector const flipped = bentNormal(kNormal, kDPdu, kDPdv, 0.0f, 0.5f, 1.0f);
  check(flipped.getY() < -0.4, "a positive dLt tilts away from dPdv");
  check(dotOf(bentNormal(kNormal, kDPdu, kDPdv, 0.5f, 0.0f, -1.0f), kDPdu) > 0.4, "a negative bump tilts toward dPdu");
}

void everyFiniteInputGivesFiniteOutput() {
  using gmanshader::bentNormal;
  std::mt19937_64 rng(20261117);
  std::uniform_real_distribution<double> exponent(-30.0, 18.0);
  std::uniform_int_distribution<int> pick(0, 5);
  auto component = [&]() -> RtFloat {
    switch (pick(rng)) {
    case 0:
      return 0.0f;
    case 1:
      return 1e-30f;
    case 2:
      return -1e-30f;
    case 3:
      return 1e18f;
    case 4:
      return -1e18f;
    default:
      return static_cast<RtFloat>((pick(rng) % 2 == 0 ? 1.0 : -1.0) * std::pow(10.0, exponent(rng)));
    }
  };
  int notFinite = 0;
  for (int i = 0; i < 200000; ++i) {
    GMANVector const n(component(), component(), component());
    GMANVector const du(component(), component(), component());
    GMANVector const dv(component(), component(), component());
    GMANVector const bent = bentNormal(n, du, dv, component(), component(), component());
    if (!finite(bent)) {
      ++notFinite;
    }
  }
  check(notFinite == 0, "every finite input gives a finite normal");
}

void flatTexelLeavesNormalUnbent() {
  using gmanshader::mappedNormal;
  check(near(mappedNormal(kNormal, kDPdu, kDPdv, 0.5f, 0.5f, 1.0f, false), kNormal), "a flat texel returns the normal");
  GMANVector const scaledNormal(0, 0, 4);
  check(near(mappedNormal(scaledNormal, kDPdu, kDPdv, 0.5f, 0.5f, 1.0f, false), kNormal),
        "a flat texel returns a unit normal");
}

void texelBendsAlongTheFrame() {
  using gmanshader::mappedNormal;
  GMANVector const right = mappedNormal(kNormal, kDPdu, kDPdv, 1.0f, 0.5f, 0.5f, false);
  check(near(right, GMANVector(1, 0, 0)), "full red bends along dPdu");
  GMANVector const openGl = mappedNormal(kNormal, kDPdu, kDPdv, 0.5f, 1.0f, 0.5f, false);
  check(near(openGl, GMANVector(0, -1, 0)), "an OpenGL map's green runs along -dPdv");
  GMANVector const directX = mappedNormal(kNormal, kDPdu, kDPdv, 0.5f, 1.0f, 0.5f, true);
  check(near(directX, GMANVector(0, 1, 0)), "a DirectX map's green runs along +dPdv");
  GMANVector const skewed =
      mappedNormal(kNormal, GMANVector(1, 0, 0.5f), GMANVector(0.3f, 1, 0.2f), 0.9f, 0.7f, 0.8f, true);
  check(std::fabs(lengthOf(skewed) - 1.0) < 1e-6, "a skewed frame gives a unit normal");
}

void degenerateFrameLeavesNormalUnbent() {
  using gmanshader::mappedNormal;
  GMANVector const zero(0, 0, 0);
  GMANVector const alongNormal(0, 0, 2);
  check(near(mappedNormal(kNormal, zero, kDPdv, 1.0f, 1.0f, 0.5f, false), kNormal), "a zero dPdu leaves it unbent");
  check(near(mappedNormal(kNormal, kDPdu, zero, 1.0f, 1.0f, 0.5f, false), kNormal), "a zero dPdv leaves it unbent");
  check(near(mappedNormal(kNormal, kDPdu, kDPdu, 1.0f, 1.0f, 0.5f, false), kNormal),
        "a dPdv parallel to dPdu leaves it unbent");
  check(near(mappedNormal(kNormal, alongNormal, kDPdv, 1.0f, 1.0f, 0.5f, false), kNormal),
        "a dPdu along the normal leaves it unbent");
  check(near(mappedNormal(kNormal, kDPdu, kDPdv, 0.5f, 0.5f, 0.5f, false), kNormal),
        "a zero decoded vector leaves it unbent");
  check(near(mappedNormal(zero, kDPdu, kDPdv, 1.0f, 1.0f, 1.0f, false), zero), "a zero normal comes back as is");
}

void everyFiniteTexelGivesFiniteNormal() {
  using gmanshader::mappedNormal;
  std::mt19937_64 rng(20261125);
  std::uniform_real_distribution<double> exponent(-30.0, 18.0);
  std::uniform_int_distribution<int> pick(0, 5);
  auto component = [&]() -> RtFloat {
    switch (pick(rng)) {
    case 0:
      return 0.0f;
    case 1:
      return 1e-30f;
    case 2:
      return -1e18f;
    default:
      return static_cast<RtFloat>((pick(rng) % 2 == 0 ? 1.0 : -1.0) * std::pow(10.0, exponent(rng)));
    }
  };
  int notFinite = 0;
  for (int i = 0; i < 200000; ++i) {
    GMANVector const n(component(), component(), component());
    GMANVector const du(component(), component(), component());
    GMANVector const dv(component(), component(), component());
    GMANVector const bent = mappedNormal(n, du, dv, component(), component(), component(), i % 2 == 0);
    if (!finite(bent)) {
      ++notFinite;
    }
  }
  check(notFinite == 0, "every finite input gives a finite mapped normal");
}

} // namespace

int main() {
  identityWhenNothingBends();
  zeroTangentLeavesNormalUnbent();
  parallelTangentLeavesNormalUnbent();
  positiveGradientTiltsAwayFromTangent();
  everyFiniteInputGivesFiniteOutput();
  flatTexelLeavesNormalUnbent();
  texelBendsAlongTheFrame();
  degenerateFrameLeavesNormalUnbent();
  everyFiniteTexelGivesFiniteNormal();
  if (failures != 0) {
    std::fprintf(stderr, "%d check(s) failed\n", failures);
    return EXIT_FAILURE;
  }
  std::puts("gildednormal: all checks passed");
  return EXIT_SUCCESS;
}
