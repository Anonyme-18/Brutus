import os
import pygame
import time
from typing import Tuple
from core import ZipCracker

class AppInterface:
    """
    Modern Pygame interface for Brutus.
    """
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Brutus | ZIP Password Recovery")
        
        # Colors
        self.bg_color = (20, 24, 30)
        self.accent_color = (0, 150, 255)
        self.text_color = (220, 230, 240)
        self.input_bg = (40, 45, 55)
        self.btn_color = (0, 100, 200)
        self.btn_hover = (0, 130, 255)
        self.success_color = (0, 255, 120)
        self.error_color = (255, 70, 70)
        
        # Fonts
        self.font_main = pygame.font.SysFont('Segoe UI', 24)
        self.font_small = pygame.font.SysFont('Segoe UI', 18)
        self.font_title = pygame.font.SysFont('Segoe UI', 36, bold=True)
        
        self.cracker = ZipCracker()
        self.file_input = ""
        self.dict_input = ""
        self.active_input = "file" # "file" or "dict"
        self.message = "Welcome to Brutus. Enter ZIP file path to begin."
        self.is_file_loaded = False
        self.running = True

    def draw_text(self, text: str, pos: Tuple[int, int], font=None, color=None, center=True):
        font = font or self.font_main
        color = color or self.text_color
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
        self.screen.blit(surf, rect)

    def draw_button(self, rect: pygame.Rect, text: str, enabled: bool = True) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)
        
        color = self.btn_hover if is_hover and enabled else self.btn_color
        if not enabled:
            color = (60, 60, 60)
            
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        self.draw_text(text, rect.center)
        
        return is_hover and pygame.mouse.get_pressed()[0]

    def main_loop(self):
        clock = pygame.time.Clock()
        
        # UI Elements
        input_zip = pygame.Rect(150, 120, 500, 40)
        input_dict = pygame.Rect(150, 200, 500, 40)
        btn_brute = pygame.Rect(150, 280, 240, 50)
        btn_dict = pygame.Rect(410, 280, 240, 50)
        btn_stop = pygame.Rect(300, 350, 200, 50)
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if input_zip.collidepoint(event.pos):
                        self.active_input = "file"
                    elif input_dict.collidepoint(event.pos):
                        self.active_input = "dict"
                    
                    if btn_brute.collidepoint(event.pos) and self.is_file_loaded:
                        self.cracker.start_cracking(mode="brute")
                    elif btn_dict.collidepoint(event.pos) and self.is_file_loaded:
                        if self.dict_input:
                            self.cracker.start_cracking(mode="dictionary", dictionary_path=self.dict_input)
                        else:
                            self.message = "Error: Dictionary file required for this mode."
                    elif btn_stop.collidepoint(event.pos):
                        self.cracker.stop_cracking()

                if event.type == pygame.KEYDOWN:
                    target = "file" if self.active_input == "file" else "dict"
                    if event.key == pygame.K_BACKSPACE:
                        if target == "file": self.file_input = self.file_input[:-1]
                        else: self.dict_input = self.dict_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if target == "file":
                            if self.cracker.load_file(self.file_input):
                                self.is_file_loaded = True
                                self.message = f"Loaded: {os.path.basename(self.file_input)}"
                            else:
                                self.is_file_loaded = False
                                self.message = "Invalid ZIP file."
                    else:
                        if target == "file": self.file_input += event.unicode
                        else: self.dict_input += event.unicode

            # Update state
            if self.cracker.is_running:
                self.cracker.elapsed_time = time.time() - self.cracker.start_time

            # Rendering
            self.screen.fill(self.bg_color)
            
            # Header
            self.draw_text("BRUTUS", (self.width // 2, 50), self.font_title, self.accent_color)
            self.draw_text(self.message, (self.width // 2, 90), self.font_small)

            # ZIP Input
            self.draw_text("Target ZIP Path:", (150, 115), self.font_small, center=False)
            pygame.draw.rect(self.screen, self.input_bg, input_zip, border_radius=5)
            if self.active_input == "file":
                pygame.draw.rect(self.screen, self.accent_color, input_zip, 2, border_radius=5)
            self.draw_text(self.file_input, input_zip.center)

            # Dictionary Input
            self.draw_text("Wordlist Path (Optional):", (150, 195), self.font_small, center=False)
            pygame.draw.rect(self.screen, self.input_bg, input_dict, border_radius=5)
            if self.active_input == "dict":
                pygame.draw.rect(self.screen, self.accent_color, input_dict, 2, border_radius=5)
            self.draw_text(self.dict_input, input_dict.center)

            # Buttons
            self.draw_button(btn_brute, "Start Brute Force", self.is_file_loaded and not self.cracker.is_running)
            self.draw_button(btn_dict, "Start Dictionary", self.is_file_loaded and not self.cracker.is_running)
            self.draw_button(btn_stop, "Stop", self.cracker.is_running)

            # Stats Area
            if self.is_file_loaded:
                y = 430
                status_color = self.success_color if self.cracker.found_password else (self.accent_color if self.cracker.is_running else self.text_color)
                status_text = "CRACKING..." if self.cracker.is_running else ("FOUND!" if self.cracker.found_password else "READY")
                
                self.draw_text(f"STATUS: {status_text}", (self.width // 2, y), self.font_main, status_color)
                y += 40
                
                if self.cracker.found_password:
                    self.draw_text(f"PASSWORD: {self.cracker.found_password}", (self.width // 2, y), self.font_title, self.success_color)
                    y += 50
                
                stats = [
                    f"Attempts: {self.cracker.attempts}",
                    f"Speed: {self.cracker.attempts_per_second:.1f} p/s",
                    f"Time: {self.cracker.elapsed_time:.1f}s"
                ]
                if self.cracker.mode == "brute":
                    stats.append(f"Length: {self.cracker.current_length}")
                
                stat_x = 150
                for stat in stats:
                    self.draw_text(stat, (stat_x, y), self.font_small, center=False)
                    stat_x += 180

            pygame.display.flip()
            clock.tick(60)

        self.cracker.cleanup()
        pygame.quit()

if __name__ == "__main__":
    app = AppInterface()
    try:
        app.main_loop()
    except KeyboardInterrupt:
        pass
