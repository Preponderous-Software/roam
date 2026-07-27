from entity.goldenLantern import GoldenLantern
from entity.torch import Torch


def test_initialization():
    lantern = GoldenLantern()
    assert lantern.getName() == "Golden Lantern"
    assert lantern.getImagePath() == "assets/images/goldenLantern.png"
    assert not lantern.isSolid()


def test_is_a_torch():
    # worldScreen's lighting logic uses hasattr(entity, "getLightRadius")
    # generically, but GoldenLantern still mirrors Torch's inheritance chain.
    assert isinstance(GoldenLantern(), Torch)


def test_light_radius_brighter_than_torch():
    lantern = GoldenLantern()
    torch = Torch()
    assert lantern.getLightRadius() == 10
    assert lantern.getLightRadius() > torch.getLightRadius()
