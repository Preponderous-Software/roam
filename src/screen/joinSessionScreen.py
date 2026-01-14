import pygame
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui.status import Status

# @author Daniel McCoy Stephenson
class JoinSessionScreen:
    """Screen to join an existing game session by entering session ID."""
    
    def __init__(self, graphik: Graphik, config: Config, status: Status, api_client):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.api_client = api_client
        self.running = True
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = False
        
        # Input field
        self.session_id_input = ""
        self.error_message = ""
        self.is_loading = False
        self.joined_session_id = None
    
    def handleEvents(self):
        """Handle keyboard input for join session form."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.nextScreen = ScreenType.NONE
                self.changeScreen = True
            
            if event.type == pygame.KEYDOWN:
                # Don't handle input if loading
                if self.is_loading:
                    continue
                
                # Enter to submit
                if event.key == pygame.K_RETURN:
                    self.submitJoin()
                
                # Backspace to delete
                elif event.key == pygame.K_BACKSPACE:
                    self.session_id_input = self.session_id_input[:-1]
                
                # Escape to go back
                elif event.key == pygame.K_ESCAPE:
                    self.nextScreen = ScreenType.MAIN_MENU_SCREEN
                    self.changeScreen = True
                
                # Type characters (alphanumeric and hyphens for UUIDs)
                elif event.unicode.isprintable():
                    self.session_id_input += event.unicode
    
    def submitJoin(self):
        """Submit join session request."""
        self.error_message = ""
        
        if not self.session_id_input.strip():
            self.error_message = "Please enter a session ID"
            return
        
        self.is_loading = True
        
        try:
            # Join the session
            session_data = self.api_client.join_session(self.session_id_input.strip())
            self.joined_session_id = session_data.get('sessionId', self.session_id_input.strip())
            self.status.set(f"Joined session: {self.joined_session_id}")
            
            # Proceed to world screen
            self.nextScreen = ScreenType.WORLD_SCREEN
            self.changeScreen = True
        
        except Exception as e:
            error_str = str(e)
            if "404" in error_str:
                self.error_message = "Session not found"
            elif "403" in error_str or "full" in error_str.lower():
                self.error_message = "Session is full (max 10 players)"
            elif "400" in error_str or "invalid" in error_str.lower():
                self.error_message = "Invalid session ID format"
            else:
                self.error_message = f"Error: {error_str}"
            
            self.is_loading = False
    
    def drawTitle(self):
        """Draw the title."""
        x, y = self.graphik.getGameDisplay().get_size()
        self.graphik.drawText("Join Session", x / 2, y / 6, 48, (255, 255, 255))
    
    def drawForm(self):
        """Draw the join session form."""
        x, y = self.graphik.getGameDisplay().get_size()
        
        # Input field label
        label_y = y / 3
        self.graphik.drawText("Enter Session ID:", x / 2, label_y, 24, (200, 200, 200))
        
        # Input field
        field_width = x / 2
        field_height = 60
        field_x = x / 2 - field_width / 2
        field_y = label_y + 50
        
        # Draw input box
        input_color = (255, 255, 100) if not self.is_loading else (150, 150, 150)
        pygame.draw.rect(
            self.graphik.getGameDisplay(),
            input_color,
            (field_x, field_y, field_width, field_height),
            3
        )
        
        # Draw input text
        display_text = self.session_id_input if not self.is_loading else "Loading..."
        self.graphik.drawText(display_text or "", field_x + field_width / 2, field_y + 30, 20, (255, 255, 255))
        
        # Error message
        if self.error_message:
            error_y = field_y + field_height + 40
            self.graphik.drawText(self.error_message, x / 2, error_y, 18, (255, 50, 50))
    
    def drawButtons(self):
        """Draw action buttons."""
        x, y = self.graphik.getGameDisplay().get_size()
        button_width = x / 5
        button_height = y / 12
        button_y = y / 2 + 40
        
        # Join button
        join_button_x = x / 2 - button_width - 10
        join_color = (100, 255, 100) if not self.is_loading else (100, 150, 100)
        self.graphik.drawButton(
            join_button_x,
            button_y,
            button_width,
            button_height,
            join_color,
            (0, 0, 0),
            24,
            "Join" if not self.is_loading else "Joining...",
            self.submitJoin if not self.is_loading else lambda: None,
        )
        
        # Cancel button
        cancel_button_x = x / 2 + 10
        if not self.is_loading:
            self.graphik.drawButton(
                cancel_button_x,
                button_y,
                button_width,
                button_height,
                (255, 100, 100),
                (0, 0, 0),
                24,
                "Cancel",
                lambda: self.setScreen(ScreenType.MAIN_MENU_SCREEN),
            )
    
    def setScreen(self, screen_type):
        """Set next screen."""
        self.nextScreen = screen_type
        self.changeScreen = True
    
    def drawInstructions(self):
        """Draw instructions."""
        x, y = self.graphik.getGameDisplay().get_size()
        instructions_y = y * 3 / 4
        self.graphik.drawText("ENTER: Join | ESC: Cancel", x / 2, instructions_y, 16, (150, 150, 150))
    
    def run(self):
        """Main loop for join session screen."""
        while not self.changeScreen:
            self.handleEvents()
            
            # Draw
            self.graphik.getGameDisplay().fill((20, 40, 60))
            self.drawTitle()
            self.drawForm()
            self.drawButtons()
            self.drawInstructions()
            pygame.display.update()
        
        self.changeScreen = False
        return self.nextScreen
