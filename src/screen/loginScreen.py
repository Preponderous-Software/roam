import pygame
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui.status import Status

# @author Daniel McCoy Stephenson
class LoginScreen:
    """Login/Registration screen for user authentication."""
    
    def __init__(self, graphik: Graphik, config: Config, status: Status, api_client):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.api_client = api_client
        self.running = True
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        
        # Input fields
        self.username_input = ""
        self.password_input = ""
        self.email_input = ""
        self.active_field = "username"  # username, password, or email
        self.show_registration = False  # Toggle between login and registration
        self.show_password = False  # Toggle password visibility
        self.error_message = ""
        self.success_message = ""
        
    def handleEvents(self):
        """Handle keyboard input for login form."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            
            if event.type == pygame.KEYDOWN:
                # Tab to switch fields
                if event.key == pygame.K_TAB:
                    if self.show_registration:
                        if self.active_field == "username":
                            self.active_field = "password"
                        elif self.active_field == "password":
                            self.active_field = "email"
                        else:
                            self.active_field = "username"
                    else:
                        self.active_field = "password" if self.active_field == "username" else "username"
                
                # Enter to submit
                elif event.key == pygame.K_RETURN:
                    self.submit()
                
                # Backspace to delete
                elif event.key == pygame.K_BACKSPACE:
                    if self.active_field == "username":
                        self.username_input = self.username_input[:-1]
                    elif self.active_field == "password":
                        self.password_input = self.password_input[:-1]
                    elif self.active_field == "email":
                        self.email_input = self.email_input[:-1]
                
                # Escape to toggle between login/register or go back
                elif event.key == pygame.K_ESCAPE:
                    if self.show_registration:
                        self.show_registration = False
                        self.email_input = ""
                        self.error_message = ""
                    else:
                        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
                        self.changeScreen = True
                
                # Type characters
                elif event.unicode.isprintable():
                    if self.active_field == "username":
                        self.username_input += event.unicode
                    elif self.active_field == "password":
                        self.password_input += event.unicode
                    elif self.active_field == "email":
                        self.email_input += event.unicode
    
    def submit(self):
        """Submit login or registration form."""
        self.error_message = ""
        self.success_message = ""
        
        try:
            if self.show_registration:
                # Register
                if not self.email_input:
                    self.error_message = "Email is required for registration"
                    return
                
                response = self.api_client.register(
                    self.username_input,
                    self.password_input,
                    self.email_input
                )
                self.success_message = f"Welcome, {response['username']}!"
                self.status.set(f"Logged in as {response['username']}")
                # Proceed to world screen
                self.nextScreen = ScreenType.WORLD_SCREEN
                self.changeScreen = True
            else:
                # Login
                response = self.api_client.login(
                    self.username_input,
                    self.password_input
                )
                self.success_message = f"Welcome back, {response['username']}!"
                self.status.set(f"Logged in as {response['username']}")
                # Proceed to world screen
                self.nextScreen = ScreenType.WORLD_SCREEN
                self.changeScreen = True
        
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "Invalid" in error_str:
                self.error_message = "Invalid username or password"
            elif "400" in error_str:
                self.error_message = "Please check your input"
            elif "already" in error_str.lower():
                self.error_message = "Username or email already exists"
            else:
                self.error_message = f"Error: {error_str}"
    
    def drawForm(self):
        """Draw the login/registration form."""
        x, y = self.graphik.getGameDisplay().get_size()
        
        # Title
        title = "Register New Account" if self.show_registration else "Login"
        self.graphik.drawText(title, x / 2, y / 6, 48, (255, 255, 255))
        
        # Input fields
        field_width = x / 3
        field_height = 50
        field_x = x / 2 - field_width / 2
        label_x = field_x - 15  # Position labels to the left of fields
        start_y = y / 3
        spacing = 80  # Increased spacing to prevent overlap
        
        # Username field
        username_y = start_y
        username_color = (255, 255, 100) if self.active_field == "username" else (200, 200, 200)
        # Draw label above field to avoid overlap
        self.graphik.drawText("Username:", field_x + field_width / 2, username_y - 20, 18, (200, 200, 200))
        pygame.draw.rect(
            self.graphik.getGameDisplay(),
            username_color,
            (field_x, username_y, field_width, field_height),
            2
        )
        self.graphik.drawText(self.username_input or "", field_x + 10, username_y + 25, 20, (255, 255, 255), align="left")
        
        # Password field
        password_y = username_y + spacing
        password_color = (255, 255, 100) if self.active_field == "password" else (200, 200, 200)
        # Draw label above field to avoid overlap
        password_label = "Password: (Press P to show)" if not self.show_password else "Password: (Press P to hide)"
        self.graphik.drawText(password_label, field_x + field_width / 2, password_y - 20, 18, (200, 200, 200))
        pygame.draw.rect(
            self.graphik.getGameDisplay(),
            password_color,
            (field_x, password_y, field_width, field_height),
            2
        )
        # Show password or asterisks based on toggle
        if self.show_password:
            display_password = self.password_input or ""
        else:
            display_password = "*" * len(self.password_input) if self.password_input else ""
        self.graphik.drawText(display_password, field_x + 10, password_y + 25, 20, (255, 255, 255), align="left")
        
        # Email field (only for registration)
        if self.show_registration:
            email_y = password_y + spacing
            email_color = (255, 255, 100) if self.active_field == "email" else (200, 200, 200)
            # Draw label above field to avoid overlap
            self.graphik.drawText("Email:", field_x + field_width / 2, email_y - 20, 18, (200, 200, 200))
            pygame.draw.rect(
                self.graphik.getGameDisplay(),
                email_color,
                (field_x, email_y, field_width, field_height),
                2
            )
            self.graphik.drawText(self.email_input or "", field_x + 10, email_y + 25, 20, (255, 255, 255), align="left")
        
        # Messages
        message_y = y * 2 / 3
        if self.error_message:
            self.graphik.drawText(self.error_message, x / 2, message_y, 18, (255, 50, 50))
        if self.success_message:
            self.graphik.drawText(self.success_message, x / 2, message_y, 18, (50, 255, 50))
        
        # Instructions
        instructions_y = y * 4 / 5
        self.graphik.drawText("TAB: Switch field | ENTER: Submit | ESC: Cancel", x / 2, instructions_y, 16, (150, 150, 150))
        
        # Toggle link
        toggle_y = instructions_y + 30
        toggle_text = "Already have an account? Press R to Login" if self.show_registration else "Don't have an account? Press R to Register"
        self.graphik.drawText(toggle_text, x / 2, toggle_y, 16, (100, 150, 255))
    
    def run(self):
        """Main loop for login screen."""
        while self.running:
            self.handleEvents()
            
            # Check for 'R' key to toggle registration
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                self.show_registration = not self.show_registration
                self.error_message = ""
                self.email_input = ""
                pygame.time.wait(200)  # Debounce
            
            # Check for 'P' key to toggle password visibility
            if keys[pygame.K_p]:
                self.show_password = not self.show_password
                pygame.time.wait(200)  # Debounce
            
            # Draw
            self.graphik.getGameDisplay().fill((20, 20, 40))
            self.drawForm()
            pygame.display.update()
            
            if self.changeScreen:
                self.changeScreen = False
                return self.nextScreen
        
        return ScreenType.NONE
