"""Source-independent dielectric appearance: never a glass-object special case."""
import numpy as np
import pytest

from g2.views.material_appearance import preview_optics
from g2.views.surface_composer import compose_surface_layers


def test_nonzero_translucent_white_shell_is_visible_against_white_background():
    src=np.ones((1,3,3),float)
    alpha=np.full((1,3),.2)
    cos=np.asarray([[1.,.5,.1]])
    out,ao,mask=preview_optics(src,alpha,np.ones((1,3),bool),cos)
    assert mask.all()
    # Higher Fresnel reflectance at grazing incidence gives the source-bound
    # transparent interface a visible, display-only optical boundary.
    visible=out*ao[...,None]+(1-ao[...,None])*1.0
    assert np.all(visible[0,0]>visible[0,1])
    assert np.all(visible[0,1]>visible[0,2])
    assert np.all((visible>=0)&(visible<=1))
    np.testing.assert_array_equal(src,np.ones((1,3,3)))
    np.testing.assert_array_equal(alpha,np.full((1,3),.2))


def test_alpha_zero_is_not_resurrected_as_fake_glass():
    rgb=np.ones((1,2,3))
    alpha=np.asarray([[0.,1.]])
    out,ao,mask=preview_optics(rgb,alpha,np.asarray([[True,True]]),
                              np.asarray([[0.,0.]]))
    assert not mask.any()
    np.testing.assert_allclose(ao,alpha)
    assert out.shape==(1,2,3)


def test_unknown_or_invalid_incidence_has_no_appearance_evidence():
    rgb=np.ones((1,3,3))
    alpha=np.full((1,3),.2)
    out,ao,mask=preview_optics(rgb,alpha,np.asarray([[False,True,True]]),
                              np.asarray([[.1,np.nan,2.]]))
    assert not mask.any()
    np.testing.assert_allclose(ao,alpha)


def test_source_linear_color_and_display_appearance_remain_independent():
    source={"depth":np.ones((1,1)), "rgb_linear":np.ones((1,1,3)),
            "geometry_valid":np.ones((1,1),bool),"color_valid":True,
            "alpha":.2,"alpha_valid":True,"geom_id":7}
    background={**source,"depth":np.full((1,1),2.),"rgb_linear":np.zeros((1,1,3)),
                "alpha":1.,"geom_id":12}
    baseline=compose_surface_layers(background,[source])
    disp_rgb,disp_alpha,mask=preview_optics(source["rgb_linear"],np.full((1,1),.2),
                                         np.ones((1,1),bool),np.full((1,1),.1))
    preview=compose_surface_layers(background,[dict(source,rgb_linear=disp_rgb,
                                                   alpha=disp_alpha)])
    np.testing.assert_allclose(baseline["composite_rgb_linear"],[[[.2,.2,.2]]])
    assert mask.all()
    assert not np.array_equal(baseline["composite_rgb_linear"],preview["composite_rgb_linear"])


@pytest.mark.parametrize("bad", [0.,1.,float("nan"),5.])
def test_unsupported_ior_fail_closed(bad):
    with pytest.raises(ValueError,match="IOR"):
        preview_optics(np.ones((1,1,3)),np.full((1,1),.2),
                       np.ones((1,1),bool),np.ones((1,1)),ior=bad)
