from src.entity.torch import Torch


def test_initialization():
    torch = Torch()
    assert torch.getName() == "Torch"
    assert torch.getImagePath() == "assets/images/torch.png"
    assert not torch.isSolid()


def test_light_radius():
    torch = Torch()
    assert torch.getLightRadius() == 3
