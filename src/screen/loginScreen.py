import pygame
import os
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
        self.remember_username = False  # Checkbox to save username
        self._last_remember_state = False  # Track state changes
        
        # Button rectangles for click detection
        self.toggle_mode_button_rect = None
        self.toggle_password_button_rect = None
        self.submit_button_rect = None
        
        # Load saved username if it exists
        self._load_saved_username()
        
    def handleEvents(self):
        """Handle keyboard input for login form."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check button clicks
                if self.toggle_mode_button_rect and self.toggle_mode_button_rect.collidepoint(mouse_pos):
                    self.show_registration = not self.show_registration
                    self.error_message = ""
                    self.email_input = ""
                
                elif self.toggle_password_button_rect and self.toggle_password_button_rect.collidepoint(mouse_pos):
                    self.show_password = not self.show_password
                
                elif self.submit_button_rect and self.submit_button_rect.collidepoint(mouse_pos):
                    self.submit()
            
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
                
                # 'S' key to toggle remember username (Shift+S to avoid conflict)
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.remember_username = not self.remember_username
                
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
                
                # Save username if remember is checked
                if self.remember_username:
                    self._save_username(self.username_input)
                
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
                
                # Save username if remember is checked
                if self.remember_username:
                    self._save_username(self.username_input)
                
                # Proceed to world screen
                self.nextScreen = ScreenType.WORLD_SCREEN
                self.changeScreen = True
        
        except Exception as e:
            error_str = str(e)
            # Provide user-friendly error messages
            if "connection" in error_str.lower() or "failed to establish" in error_str.lower():
                self.error_message = "Couldn't connect to server"
            elif "401" in error_str or "Invalid" in error_str:
                self.error_message = "That user wasn't found or password is incorrect"
            elif "404" in error_str:
                self.error_message = "That user wasn't found"
            elif "400" in error_str:
                self.error_message = "Please check your input"
            elif "already" in error_str.lower():
                self.error_message = "Username or email already exists"
            elif "timeout" in error_str.lower():
                self.error_message = "Server is taking too long to respond"
            else:
                self.error_message = f"An error occurred: {error_str}"
    
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
        # Center text in field
        text_font = pygame.font.Font("freesansbold.ttf", 20)
        text_surface = text_font.render(self.username_input or "", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(field_x + field_width / 2, username_y + field_height / 2))
        self.graphik.getGameDisplay().blit(text_surface, text_rect)
        
        # Password field
        password_y = username_y + spacing
        password_color = (255, 255, 100) if self.active_field == "password" else (200, 200, 200)
        # Draw label above field to avoid overlap
        self.graphik.drawText("Password:", field_x + field_width / 2, password_y - 20, 18, (200, 200, 200))
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
        # Center text in field
        text_font = pygame.font.Font("freesansbold.ttf", 20)
        text_surface = text_font.render(display_password, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(field_x + field_width / 2, password_y + field_height / 2))
        self.graphik.getGameDisplay().blit(text_surface, text_rect)
        
        # Show/Hide password button
        button_width = 80
        button_height = 30
        password_button_x = field_x + field_width + 10
        password_button_y = password_y + field_height / 2 - button_height / 2
        self.toggle_password_button_rect = pygame.Rect(password_button_x, password_button_y, button_width, button_height)
        pygame.draw.rect(self.graphik.getGameDisplay(), (70, 70, 120), self.toggle_password_button_rect)
        pygame.draw.rect(self.graphik.getGameDisplay(), (150, 150, 200), self.toggle_password_button_rect, 2)
        button_text = "Hide" if self.show_password else "Show"
        self.graphik.drawText(button_text, password_button_x + button_width / 2, password_button_y + button_height / 2, 16, (255, 255, 255))
        
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
            # Center text in field
            text_font = pygame.font.Font("freesansbold.ttf", 20)
            text_surface = text_font.render(self.email_input or "", True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(field_x + field_width / 2, email_y + field_height / 2))
            self.graphik.getGameDisplay().blit(text_surface, text_rect)
        
        # Messages
        message_y = y * 2 / 3
        if self.error_message:
            self.graphik.drawText(self.error_message, x / 2, message_y, 18, (255, 50, 50))
        if self.success_message:
            self.graphik.drawText(self.success_message, x / 2, message_y, 18, (50, 255, 50))
        
        # Remember username checkbox
        checkbox_y = message_y + 40
        checkbox_size = 20
        checkbox_x = x / 2 - 100
        checkbox_color = (100, 255, 100) if self.remember_username else (200, 200, 200)
        pygame.draw.rect(
            self.graphik.getGameDisplay(),
            checkbox_color,
            (checkbox_x, checkbox_y - checkbox_size / 2, checkbox_size, checkbox_size),
            2 if not self.remember_username else 0
        )
        if self.remember_username:
            # Draw checkmark
            pygame.draw.line(
                self.graphik.getGameDisplay(),
                (0, 0, 0),
                (checkbox_x + 5, checkbox_y),
                (checkbox_x + 8, checkbox_y + 5),
                3
            )
            pygame.draw.line(
                self.graphik.getGameDisplay(),
                (0, 0, 0),
                (checkbox_x + 8, checkbox_y + 5),
                (checkbox_x + 15, checkbox_y - 5),
                3
            )
        # Draw label next to checkbox
        label_font = pygame.font.Font("freesansbold.ttf", 16)
        label_surface = label_font.render("Remember username (Shift+S)", True, (200, 200, 200))
        self.graphik.getGameDisplay().blit(label_surface, (checkbox_x + checkbox_size + 10, checkbox_y - checkbox_size / 2))
        
        # Instructions
        instructions_y = y * 4 / 5
        self.graphik.drawText("TAB: Switch field | ENTER: Submit | ESC: Cancel", x / 2, instructions_y, 16, (150, 150, 150))
        
        # Submit button
        submit_button_width = 120
        submit_button_height = 40
        submit_button_x = x / 2 - submit_button_width / 2
        submit_button_y = instructions_y + 40
        self.submit_button_rect = pygame.Rect(submit_button_x, submit_button_y, submit_button_width, submit_button_height)
        pygame.draw.rect(self.graphik.getGameDisplay(), (50, 150, 50), self.submit_button_rect)
        pygame.draw.rect(self.graphik.getGameDisplay(), (100, 200, 100), self.submit_button_rect, 2)
        submit_text = "Register" if self.show_registration else "Login"
        self.graphik.drawText(submit_text, submit_button_x + submit_button_width / 2, submit_button_y + submit_button_height / 2, 20, (255, 255, 255))
        
        # Toggle mode button
        toggle_mode_button_width = 200
        toggle_mode_button_height = 35
        toggle_mode_button_x = x / 2 - toggle_mode_button_width / 2
        toggle_mode_button_y = submit_button_y + submit_button_height + 15
        self.toggle_mode_button_rect = pygame.Rect(toggle_mode_button_x, toggle_mode_button_y, toggle_mode_button_width, toggle_mode_button_height)
        pygame.draw.rect(self.graphik.getGameDisplay(), (70, 70, 120), self.toggle_mode_button_rect)
        pygame.draw.rect(self.graphik.getGameDisplay(), (100, 150, 255), self.toggle_mode_button_rect, 2)
        toggle_mode_text = "Switch to Login" if self.show_registration else "Switch to Register"
        self.graphik.drawText(toggle_mode_text, toggle_mode_button_x + toggle_mode_button_width / 2, toggle_mode_button_y + toggle_mode_button_height / 2, 16, (100, 150, 255))
    
    def _load_saved_username(self):
        """Load saved username from file if it exists."""
        try:
            with open('.saved_username', 'r') as f:
                self.username_input = f.read().strip()
                self.remember_username = True
        except FileNotFoundError:
            pass
        except Exception:
            pass
    
    def _save_username(self, username):
        """Save username to file for future logins."""
        try:
            with open('.saved_username', 'w') as f:
                f.write(username)
        except Exception:
            pass
    
    def _clear_saved_username(self):
        """Remove saved username file."""
        try:
            os.remove('.saved_username')
        except Exception:
            pass
    
    def run(self):
        """Main loop for login screen."""
        while self.running:
            self.handleEvents()
            
            # Clear saved username only when state changes from True to False
            if self._last_remember_state and not self.remember_username:
                self._clear_saved_username()
            self._last_remember_state = self.remember_username
            
            # Draw
            self.graphik.getGameDisplay().fill((20, 20, 40))
            self.drawForm()
            pygame.display.update()
            
            if self.changeScreen:
                self.changeScreen = False
                return self.nextScreen
        
        return ScreenType.NONE
