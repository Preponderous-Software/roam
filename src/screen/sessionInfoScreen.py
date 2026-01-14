import pygame
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui.status import Status

# @author Daniel McCoy Stephenson
class SessionInfoScreen:
    """Screen to display session ID and allow copying to clipboard."""
    
    def __init__(self, graphik: Graphik, config: Config, status: Status, session_id: str):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.session_id = session_id
        self.running = True
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        self.copy_confirmation = False
        self.copy_confirmation_time = 0
    
    def copyToClipboard(self):
        """Copy session ID to clipboard."""
        try:
            # Use pygame's scrap module for clipboard operations
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, self.session_id.encode('utf-8'))
            self.copy_confirmation = True
            self.copy_confirmation_time = pygame.time.get_ticks()
            self.status.set("Session ID copied to clipboard!")
        except Exception as e:
            self.status.set(f"Could not copy to clipboard: {e}")
    
    def continueToGame(self):
        """Continue to the game world."""
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True
    
    def drawTitle(self):
        """Draw the title."""
        x, y = self.graphik.getGameDisplay().get_size()
        self.graphik.drawText("Session Created!", x / 2, y / 6, 48, (255, 255, 255))
    
    def drawSessionId(self):
        """Draw the session ID."""
        x, y = self.graphik.getGameDisplay().get_size()
        
        # Label
        self.graphik.drawText("Share this Session ID with friends:", x / 2, y / 3, 24, (200, 200, 200))
        
        # Session ID in a box
        session_id_y = y / 3 + 60
        # Use font metrics for proper width calculation
        font = pygame.font.Font(None, 20)
        session_text_width = font.size(self.session_id)[0]
        box_width = session_text_width + 20  # Add padding
        box_height = 60
        box_x = x / 2 - box_width / 2
        
        # Draw box
        pygame.draw.rect(
            self.graphik.getGameDisplay(),
            (255, 255, 100),
            (box_x, session_id_y - 30, box_width, box_height),
            3
        )
        
        # Draw session ID text
        self.graphik.drawText(self.session_id, x / 2, session_id_y, 20, (255, 255, 255))
    
    def drawButtons(self):
        """Draw action buttons."""
        x, y = self.graphik.getGameDisplay().get_size()
        button_width = x / 4
        button_height = y / 12
        button_y = y / 2 + 40
        
        # Copy button
        copy_button_x = x / 2 - button_width - 10
        self.graphik.drawButton(
            copy_button_x,
            button_y,
            button_width,
            button_height,
            (100, 200, 255),
            (0, 0, 0),
            24,
            "Copy to Clipboard",
            self.copyToClipboard,
        )
        
        # Continue button
        continue_button_x = x / 2 + 10
        self.graphik.drawButton(
            continue_button_x,
            button_y,
            button_width,
            button_height,
            (100, 255, 100),
            (0, 0, 0),
            24,
            "Continue to Game",
            self.continueToGame,
        )
        
        # Copy confirmation message
        if self.copy_confirmation:
            current_time = pygame.time.get_ticks()
            if current_time - self.copy_confirmation_time < 2000:  # Show for 2 seconds
                self.graphik.drawText("✓ Copied to clipboard!", x / 2, button_y + button_height + 30, 18, (100, 255, 100))
            else:
                self.copy_confirmation = False
    
    def drawInstructions(self):
        """Draw instructions."""
        x, y = self.graphik.getGameDisplay().get_size()
        instructions_y = y * 3 / 4
        self.graphik.drawText("Press ENTER to continue or ESC to go back", x / 2, instructions_y, 16, (150, 150, 150))
    
    def handleEvents(self):
        """Handle keyboard input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.nextScreen = ScreenType.NONE
                self.changeScreen = True
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.continueToGame()
                elif event.key == pygame.K_ESCAPE:
                    self.continueToGame()
    
    def run(self):
        """Main loop for session info screen."""
        while not self.changeScreen:
            self.handleEvents()
            
            # Draw
            self.graphik.getGameDisplay().fill((20, 40, 60))
            self.drawTitle()
            self.drawSessionId()
            self.drawButtons()
            self.drawInstructions()
            pygame.display.update()
        
        self.changeScreen = False
        return self.nextScreen
