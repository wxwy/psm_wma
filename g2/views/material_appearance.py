"""Material-driven display-only optical response for translucent surfaces.

This is a documented studio-light *preview*, not measured illumination or
color evidence. The inputs are source albedo, alpha, a surface normal and
projection ray. All values are independent of semantic identity, category,
Geom name and scene-specific texture coordinates.

Transparent shells with alpha=0 are invisible; their presence must not be
inferred by a default glass label. RGB evidence retains original albedo.
"""
import numpy as np


def preview_optics(rgb_linear, alpha, known, cosine, *,
                   ior=1.5, environment_linear=(0.20, 0.26, 0.32)):
    """Return (preview_linear_RGB, preview_alpha, approximation_mask).

    A dielectric interface reflects Fresnel fraction F and transmits (1-F).
    Historical source alpha represents the residual non-refracted surface
    appearance; this preview blends F*environment and (1-F)*alpha*albedo.
    It deliberately does NOT modify numeric source RGB, alpha or validity.
    A material/texture with zero alpha remains exactly absent.
    """
    rgb=np.asarray(rgb_linear,dtype=np.float64)
    a=np.asarray(alpha,dtype=np.float64)
    valid=np.asarray(known,dtype=bool)
    mu=np.asarray(cosine,dtype=np.float64)
    if rgb.shape!=(*a.shape,3) or valid.shape!=a.shape or mu.shape!=a.shape:
        raise ValueError("optical appearance arrays must share pixel shape")
    if not np.isfinite(ior) or ior<=1.0 or ior>4.0:
        raise ValueError("invalid dielectric IOR")
    env=np.asarray(environment_linear,dtype=np.float64)
    if env.shape!=(3,) or not np.isfinite(env).all() or (env<0).any():
        raise ValueError("invalid studio environment")
    active=valid & np.isfinite(a) & (a>0) & (a<1) & np.isfinite(mu) & (mu>=0) & (mu<=1)
    reflectance=((ior-1)/(ior+1))**2
    fresnel=reflectance + (1-reflectance)*(1-np.clip(mu,0,1))**5
    f=np.where(active, fresnel, 0.0)
    opacity=np.where(active,a*(1-f)+f,a)
    radiance=np.where(active[...,None],
                      (a*(1-f))[...,None]*rgb + f[...,None]*env, rgb*opacity[...,None])
    result=np.divide(radiance, opacity[...,None],out=np.zeros_like(radiance),
                     where=opacity[...,None]>0)
    # Unknown source must remain UNKNOWN to the separate source compositor.
    return result,opacity,active
