from src.entity.campfire import Campfire


def test_light_radius():
    campfire = Campfire()
    assert campfire.getLightRadius() == 8
