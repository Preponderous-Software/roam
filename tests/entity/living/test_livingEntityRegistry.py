import os

from codex.codex import ALL_LIVING_ENTITY_TYPES, ENTITY_IMAGE_PATHS
from entity.living.livingEntity import LivingEntity
from entity.living.livingEntityRegistry import LIVING_ENTITY_TYPES


def test_registry_contains_the_known_creatures():
    assert set(LIVING_ENTITY_TYPES) == {
        "Bear",
        "Chicken",
        "Deer",
        "Rabbit",
        "Snake",
        "Wolf",
    }


def test_every_constructor_takes_tick_created_and_returns_living_entity():
    for name, constructor in LIVING_ENTITY_TYPES.items():
        creature = constructor(42)
        assert isinstance(creature, LivingEntity)
        assert creature.name == name
        assert creature.getTickCreated() == 42


def test_registry_matches_codex_entity_types():
    # The codex must advertise exactly the creatures the round-trip can rebuild.
    assert set(LIVING_ENTITY_TYPES) == set(ALL_LIVING_ENTITY_TYPES)


def test_every_creature_sprite_exists_on_disk():
    repoRoot = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    for name in LIVING_ENTITY_TYPES:
        imagePath = ENTITY_IMAGE_PATHS[name]
        assert os.path.isfile(
            os.path.join(repoRoot, imagePath)
        ), f"missing sprite for {name}: {imagePath}"
