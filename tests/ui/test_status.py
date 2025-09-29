import pygame
from src.ui.status import Status
from src.lib.graphik.src.graphik import Graphik
from src.world.tickCounter import TickCounter
from src.config.config import Config


def test_initialization():
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    config = Config()
    tickCounter = TickCounter(config)
    
    status = Status(graphik, tickCounter)
    
    assert status.text == -1
    assert status.textSize == 18
    assert status.textColor == (0, 0, 0)
    assert status.tickLastSet == -1
    assert status.durationInTicks == 20
    
    pygame.quit()


def test_set_and_clear():
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    config = Config()
    tickCounter = TickCounter(config)
    
    status = Status(graphik, tickCounter)
    
    # Test setting status
    status.set("Test message")
    assert status.text == "Test message"
    assert status.tickLastSet == tickCounter.getTick()
    
    # Test clearing status
    status.clear()
    assert status.text == -1
    
    pygame.quit()


def test_get_tick_last_set():
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    config = Config()
    tickCounter = TickCounter(config)
    
    status = Status(graphik, tickCounter)
    
    assert status.getTickLastSet() == -1
    
    status.set("Test")
    assert status.getTickLastSet() == tickCounter.getTick()
    
    pygame.quit()


def test_check_for_expiration():
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    config = Config()
    tickCounter = TickCounter(config)
    
    status = Status(graphik, tickCounter)
    
    # Set status at tick 0
    status.set("Test message")
    initial_tick = tickCounter.getTick()
    
    # Should not expire yet
    status.checkForExpiration(initial_tick + 10)
    assert status.text == "Test message"
    
    # Should expire after duration
    status.checkForExpiration(initial_tick + status.durationInTicks + 1)
    assert status.text == -1
    
    pygame.quit()


def test_draw_with_no_text():
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    config = Config()
    tickCounter = TickCounter(config)
    
    status = Status(graphik, tickCounter)
    
    # Should return early when text is -1
    result = status.draw()
    assert result is None
    
    pygame.quit()