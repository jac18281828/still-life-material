// SPDX-License-Identifier: MIT

#include <algorithm>
#include <string>

#include <gman/gmanbsdf.h>
#include <gman/gmanloadable.h>
#include <gman/gmanshaderparams.h>
#include <gman/gmansurfaceshader.h>

#include "gildednormal.h"

/*
 * surface gilded(float Ka=1, Ks=1, roughness=.1, bump=0, normalgreendown=0; string texturename="", normalname="")
 *
 * Gold leaf: shinymetal's Cs-tinted specular metal with a surface texture.
 *
 *   texturename  an image read as colour at (s, t); it tints the metal, scales its roughness and, through its
 *                luminance, bumps its normal. Empty, the texture is white and the shader is shinymetal without its
 *                environment term.
 *   roughness    the lobe's roughness at a white texel; it is multiplied by clamp(3 - 2L, 0.3, 2), L the texel's
 *                Rec. 709 luminance, so darker texels are rougher.
 *   bump         how far the luminance gradient bends the shading normal along the surface tangents dPdu and dPdv;
 *                0 leaves the normal alone. Declare it, or pass it inline as "float bump" [6].
 *   normalname   a tangent-space normal map read at (s, t): each channel c in [0, 1] decodes to 2c - 1 along the
 * tangent dPdu, the bitangent and N, as in paintedplastic. It gives the foil edges the colour texture cannot, and wins
 * over bump. Declare it, or pass it inline as "string normalname" ["build/foilnormal.tif"]. normalgreendown  nonzero
 * reads a DirectX map, green along +dPdv; zero, the default, an OpenGL map, along -dPdv. Ka, Ks       ambient and
 * specular weights, as in shinymetal.
 *
 * The path tracer samples one GGX lobe of Ks * Cs * texture; the ray tracer shades the same colour, roughness and
 * bent normal with specular(). The normal stays unbent where a tangent is zero, as at a sphere's poles.
 */
namespace gmanshader {

namespace {

constexpr RtFloat kBumpStep = 1.0f / 2048.0f;
constexpr double kRoughnessScaleMin = 0.3;
constexpr double kRoughnessScaleMax = 2.0;

double luminance(GMANColor const& c) { return 0.2126 * c.getRed() + 0.7152 * c.getGreen() + 0.0722 * c.getBlue(); }

} // namespace

class gilded : public GMANSurfaceShader {
public:
  explicit gilded(GMANParameterList const& parameters)
      : ka(getFloatParam(parameters, RI_KA, 1.0f)), ks(getFloatParam(parameters, RI_KS, 1.0f)),
        roughness(getFloatParam(parameters, RI_ROUGHNESS, 0.1f)),
        texturename(getStringParam(parameters, RI_TEXTURENAME, std::string())),
        bump(getFloatParam(parameters, "bump", 0.0f)),
        normalname(getStringParam(parameters, "normalname", std::string())),
        normalgreendown(getFloatParam(parameters, "normalgreendown", 0.0f) != 0.0f) {}

  GMANColor computeCi(GMANSurfaceEnv const& se) const override;
  GMANColor computeOi(GMANSurfaceEnv const& se) const override;
  gman::BSDF bsdf(GMANSurfaceEnv const& se) const override;

private:
  GMANColor tint(GMANSurfaceEnv const& se) const;
  RtFloat texturedRoughness(GMANColor const& tinted) const;
  GMANVector shadingNormal(GMANSurfaceEnv const& se) const;
  GMANVector mappedShadingNormal(GMANSurfaceEnv const& se) const;
  double luminanceAt(GMANSurfaceEnv const& se, RtFloat s, RtFloat t) const;

  RtFloat const ka;
  RtFloat const ks;
  RtFloat const roughness;
  std::string const texturename;
  RtFloat const bump;
  std::string const normalname;
  bool const normalgreendown;
};

GMANColor gilded::tint(GMANSurfaceEnv const& se) const {
  return texturename.empty() ? GMANColor(1.0f, 1.0f, 1.0f) : se.texture(texturename, se.s, se.t);
}

RtFloat gilded::texturedRoughness(GMANColor const& tinted) const {
  double const scale = std::clamp(3.0 - 2.0 * luminance(tinted), kRoughnessScaleMin, kRoughnessScaleMax);
  return static_cast<RtFloat>(roughness * scale);
}

double gilded::luminanceAt(GMANSurfaceEnv const& se, RtFloat s, RtFloat t) const {
  return luminance(se.texture(texturename, s, t));
}

GMANVector gilded::mappedShadingNormal(GMANSurfaceEnv const& se) const {
  GMANColor const texel = se.texture(normalname, se.s, se.t);
  GMANVector const bent =
      mappedNormal(se.N, se.dPdu, se.dPdv, texel.getRed(), texel.getGreen(), texel.getBlue(), normalgreendown);
  return gman::ensureValidReflection(se.Ng, -se.I, bent);
}

GMANVector gilded::shadingNormal(GMANSurfaceEnv const& se) const {
  if (!normalname.empty()) {
    return mappedShadingNormal(se);
  }
  if (texturename.empty() || bump == 0.0f) {
    return se.N;
  }
  auto const dLs =
      static_cast<RtFloat>(luminanceAt(se, se.s + kBumpStep, se.t) - luminanceAt(se, se.s - kBumpStep, se.t));
  auto const dLt =
      static_cast<RtFloat>(luminanceAt(se, se.s, se.t + kBumpStep) - luminanceAt(se, se.s, se.t - kBumpStep));
  return bentNormal(se.N, se.dPdu, se.dPdv, dLs, dLt, bump);
}

GMANColor gilded::computeCi(GMANSurfaceEnv const& se) const {
  GMANColor const tinted = tint(se);
  GMANVector nf = se.faceforward(shadingNormal(se), se.I, se.Ng);
  GMANVector vf(-se.I.getX(), -se.I.getY(), -se.I.getZ());
  vf.normalize();

  GMANColor lit = se.ambient();
  lit.scale(ka);

  GMANColor specularTerm = se.specular(nf, vf, texturedRoughness(tinted));
  specularTerm.scale(ks);
  lit += specularTerm;

  return GMANColor(se.Os.getRed() * se.Cs.getRed() * tinted.getRed() * lit.getRed(),
                   se.Os.getGreen() * se.Cs.getGreen() * tinted.getGreen() * lit.getGreen(),
                   se.Os.getBlue() * se.Cs.getBlue() * tinted.getBlue() * lit.getBlue());
}

GMANColor gilded::computeOi(GMANSurfaceEnv const& se) const { return se.Os; }

gman::BSDF gilded::bsdf(GMANSurfaceEnv const& se) const {
  GMANColor const tinted = tint(se);
  gman::BSDF closure(shadingNormal(se));
  GMANColor const weight =
      clampAlbedo(GMANColor(ks * se.Cs.getRed() * tinted.getRed(), ks * se.Cs.getGreen() * tinted.getGreen(),
                            ks * se.Cs.getBlue() * tinted.getBlue()));
  closure.addGGX(weight, alphaFromRoughness(texturedRoughness(tinted)));
  return closure;
}

} // namespace gmanshader

static GMANLoadableObjectInfo loadableInfo = {
    "Gilded surface shader",
    "still-life-material",
    "A GMAN SurfaceShader for gold leaf: Cs-tinted specular metal with a surface texture that tints it, roughens it "
    "and bumps its normal.",
};

extern "C" GMAN_EXPORT GMANLoadableObjectInfo* GMANGetLoadableInfo(void) { return &loadableInfo; }

extern "C" GMAN_EXPORT GMANShader* GMANLoadShader(GMANParameterList const& parameters) {
  return new gmanshader::gilded(parameters);
}

extern "C" GMAN_EXPORT void GMANDestroyShader(GMANShader* shader) { delete shader; }
