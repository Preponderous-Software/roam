import os
import tempfile
import pygame
from src.entity.drawableEntity import DrawableEntity


def test_initialization():
    drawableEntity = DrawableEntity("test", "myimagepath.png")

    assert drawableEntity.getName() == "test"
    assert drawableEntity.getImagePath() == "myimagepath.png"


def test_get_image():
    # Create a temporary PNG file for testing
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        # Create a simple 1x1 pixel PNG image
        temp_surface = pygame.Surface((1, 1))
        temp_surface.fill((255, 255, 255))
        pygame.image.save(temp_surface, temp_file.name)
        temp_path = temp_file.name
    
    try:
        drawableEntity = DrawableEntity("test", temp_path)
        image = drawableEntity.getImage()
        
        # Verify that getImage returns a pygame Surface
        assert isinstance(image, pygame.Surface)
        assert image.get_width() == 1
        assert image.get_height() == 1
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_set_image_path():
    drawableEntity = DrawableEntity("test", "original_path.png")
    
    assert drawableEntity.getImagePath() == "original_path.png"
    
    drawableEntity.setImagePath("new_path.png")
    assert drawableEntity.getImagePath() == "new_path.png"
