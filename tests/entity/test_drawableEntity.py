import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest

from src.entity.drawableEntity import DrawableEntity


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def test_initialization():
    drawableEntity = DrawableEntity("test", "myimagepath.png")

    assert drawableEntity.getName() == "test"
    assert drawableEntity.getImagePath() == "myimagepath.png"


def test_get_image_returns_placeholder_for_missing_asset():
    missingPath = "assets/images/__does_not_exist__.png"
    DrawableEntity._imageCache.pop(missingPath, None)
    entity = DrawableEntity("missing", missingPath)

    # A missing asset must not propagate out of the render path
    image = entity.getImage()

    assert isinstance(image, pygame.Surface)
    assert image.get_size() == (
        DrawableEntity._FALLBACK_SIZE,
        DrawableEntity._FALLBACK_SIZE,
    )
    DrawableEntity._imageCache.pop(missingPath, None)


def test_get_image_caches_fallback_without_retry():
    missingPath = "assets/images/__also_missing__.png"
    DrawableEntity._imageCache.pop(missingPath, None)
    entity = DrawableEntity("missing", missingPath)

    first = entity.getImage()
    second = entity.getImage()

    # Same cached surface returned — the failing load is not retried each frame
    assert first is second
    assert missingPath in DrawableEntity._imageCache
    DrawableEntity._imageCache.pop(missingPath, None)
