import pygame
import datetime
import json
import os
import random
import time
import sys

from unidecode import unidecode
from problems import create_problems_dict, format_problem_name
from classes import Record
from sessions import save_session_data, format_score


# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 150, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)

# Removed Unicode symbols - they don't display reliably

# Unicode font support - try multiple fonts for better symbol rendering
def get_unicode_font(size=72):
    """Get a font with good Unicode support"""
    # List of fonts known to have good Unicode support, in order of preference
    font_names = [
        'DejaVu Sans',
        'Arial Unicode MS', 
        'Noto Sans',
        'Liberation Sans',
        'FreeSans',
        'Arial',
        'Helvetica',
    ]
    
    for font_name in font_names:
        try:
            font = pygame.font.SysFont(font_name, size)
            if font:
                # Test if this font can render our Unicode characters
                test_chars = ['←', '→', '↑', '↓', '■', '□', '▲', '△', '●', '○']
                can_render = True
                for char in test_chars:
                    try:
                        surface = font.render(char, True, (0, 0, 0))
                        # Check if the character actually rendered (not just a box/missing glyph)
                        if surface.get_width() < 5:  # Too narrow suggests missing glyph
                            can_render = False
                            break
                    except (UnicodeError, pygame.error):
                        can_render = False
                        break
                
                if can_render:
                    return font
        except (pygame.error, OSError):
            continue
    
    # Fallback to default font if none work
    print(f"Warning: No Unicode font found, using default font (size {size})")
    return pygame.font.Font(None, size)

# Initialize pygame fonts
pygame.font.init()

# Use Unicode fonts for ALL text to ensure consistent alignment
font_huge = get_unicode_font(72)
font_large = get_unicode_font(48)
font_medium = get_unicode_font(36)
font_small = get_unicode_font(24)

# Create window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Memory Trainer - Pygame Version")




def draw_text(surface, text, font, color, x, y, center=False):
    """Draw text on surface with consistent Unicode font"""
    try:
        # All fonts are now Unicode-capable, so just render directly
        text_surface = font.render(text, True, color)
        
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            surface.blit(text_surface, text_rect)
        else:
            surface.blit(text_surface, (x, y))
        return text_surface.get_height()
        
    except (UnicodeError, pygame.error):
        # Ultimate fallback: replace problematic characters
        fallback_text = text
        char_replacements = {
            '←': '<', '→': '>', '↑': '^', '↓': 'v',
            '■': '[B]', '□': '[W]', '▪': '[b]', '▫': '[w]',
            '▲': '[T]', '△': '[t]', '▼': '[V]', '▽': '[v]',
            '●': '[O]', '○': '[o]', '◉': '[O]', '◯': '[o]'
        }
        for unicode_char, replacement in char_replacements.items():
            fallback_text = fallback_text.replace(unicode_char, replacement)
        
        text_surface = font.render(fallback_text, True, color)
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            surface.blit(text_surface, text_rect)
        else:
            surface.blit(text_surface, (x, y))
        return text_surface.get_height()


def show_problems_screen(problems_dict):
    """Show available problems and wait for user to start"""
    screen.fill(WHITE)
    
    # Title
    draw_text(screen, "Memory Trainer - Available Problems", font_large, BLACK, 
              WINDOW_WIDTH//2, 60, center=True)
    
    # Problems list
    y_offset = 120
    for func, prob in sorted(problems_dict.items(), key=lambda x: x[0].__name__):
        formatted_name = format_problem_name(func.__name__)
        draw_text(screen, formatted_name, font_medium, DARK_GRAY, 50, y_offset)
        y_offset += 35
    
    # Instructions
    draw_text(screen, f"Total: {len(problems_dict)} problems", font_medium, BLACK, 
              50, y_offset + 20)
    draw_text(screen, "Press SPACE to start training or ESC to quit", font_medium, BLUE,
              WINDOW_WIDTH//2, WINDOW_HEIGHT - 50, center=True)
    
    pygame.display.flip()
    
    # Wait for input
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False


def show_memorize_phase(memorize_text, exposure_ms, current_question, total_questions, correct_count, elapsed_time, problem_func=None):
    """Show the memorization phase"""
    screen.fill(WHITE)
    
    # Stats
    minutes, seconds = divmod(int(elapsed_time), 60)
    stats_text = f"Question {current_question}/{total_questions} | Perfect: {correct_count}/{current_question-1 if current_question > 1 else 0} | Time: {minutes}:{seconds:02d}"
    draw_text(screen, stats_text, font_small, GRAY, 10, 10)
    
    # Progress bar
    progress_width = 800
    progress_height = 20
    progress_x = (WINDOW_WIDTH - progress_width) // 2
    progress_y = 50
    
    pygame.draw.rect(screen, LIGHT_GRAY, (progress_x, progress_y, progress_width, progress_height))
    if total_questions > 0:
        filled_width = int((current_question - 1) / total_questions * progress_width)
        pygame.draw.rect(screen, BLUE, (progress_x, progress_y, filled_width, progress_height))
    
    # Main content area
    content_y = 150
    
    # Memorize instruction
    draw_text(screen, "", font_medium, DARK_GRAY, WINDOW_WIDTH//2, content_y, center=True)
    
    # The content to memorize (larger, centered)
    # Check if this is a pair problem by examining the function name
    is_pair_problem = problem_func and 'pair' in problem_func.__name__.lower()
    
    if is_pair_problem and ':' in memorize_text:
        # For pair problems, split by spaces and display each pair on its own line
        pairs = memorize_text.split(' ')
        # Filter to only include items that contain ':'
        pair_items = [item for item in pairs if ':' in item]
        
        if pair_items:
            line_height = 60
            start_y = content_y + 80
            
            for i, pair in enumerate(pair_items):
                draw_text(screen, pair, font_huge, BLACK, WINDOW_WIDTH//2, start_y + i * line_height, center=True)
        else:
            # Fallback to normal display if no pairs found
            lines = memorize_text.split('\n')
            line_height = 80
            start_y = content_y + 80
            
            for i, line in enumerate(lines):
                draw_text(screen, line, font_huge, BLACK, WINDOW_WIDTH//2, start_y + i * line_height, center=True)
    elif '\n' in memorize_text:
        # Handle multiline problems (like flight plans)
        lines = memorize_text.split('\n')
        line_height = 60  # Slightly smaller for multiline content
        start_y = content_y + 80
        
        for i, line in enumerate(lines):
            draw_text(screen, line, font_huge, BLACK, WINDOW_WIDTH//2, start_y + i * line_height, center=True)
    else:
        # Normal display for non-pair problems
        lines = memorize_text.split('\n')
        line_height = 80
        start_y = content_y + 80
        
        for i, line in enumerate(lines):
            draw_text(screen, line, font_huge, BLACK, WINDOW_WIDTH//2, start_y + i * line_height, center=True)
    
    # Timer bar showing remaining time
    timer_width = 600
    timer_height = 10
    timer_x = (WINDOW_WIDTH - timer_width) // 2
    timer_y = WINDOW_HEIGHT - 100
    
    pygame.draw.rect(screen, LIGHT_GRAY, (timer_x, timer_y, timer_width, timer_height))
    
    pygame.display.flip()
    
    # Handle the timing - use pygame's more precise timing
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()  # Get milliseconds since pygame.init()
    
    while True:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        
        # Check if exposure time is complete
        if elapsed >= exposure_ms:
            break
            
        # Update timer bar
        remaining_ratio = max(0, (exposure_ms - elapsed) / exposure_ms)
        filled_width = int(remaining_ratio * timer_width)
        
        # Redraw only the timer area
        pygame.draw.rect(screen, LIGHT_GRAY, (timer_x, timer_y, timer_width, timer_height))
        pygame.draw.rect(screen, GREEN, (timer_x, timer_y, filled_width, timer_height))
        pygame.display.update((timer_x, timer_y, timer_width, timer_height))
        
        # Handle events to prevent freezing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Use clock to maintain consistent frame rate and precise timing
        clock.tick(60)  # 60 FPS for smooth timer updates


def get_user_input(problem):
    """Get text input from user"""
    input_text = ""
    input_active = True
    
    while input_active:
        screen.fill(WHITE)
        
        # Prompt (replace > with right arrow, < with left arrow)
        display_prompt = problem.prompt.replace('>', '→').replace('<', '←')
        draw_text(screen, f"{display_prompt}", font_large, BLACK, WINDOW_WIDTH//2, 200, center=True)
        
        # User input text (no box, just centered text)
        draw_text(screen, input_text, font_medium, BLACK, WINDOW_WIDTH//2, 300, center=True)
        
        # Instructions
        draw_text(screen, "Type your answer and press ENTER", font_small, GRAY, 
                  WINDOW_WIDTH//2, 400, center=True)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
    
    return input_text.strip().lower()


def show_feedback(score, user_answer, correct_answer, response_time, exposure_time):
    """Show feedback for the answer"""
    screen.fill(WHITE)
    
    # Result - score-based feedback
    if score == 1.0:
        text = "PERFECT!"
        result_color = GREEN
    elif score >= 0.7:
        text = "CLOSE!"
        result_color = BLUE
    else:
        text = "INCORRECT"
        result_color = RED
    
    # Draw the result text centered
    draw_text(screen, text, font_huge, result_color, WINDOW_WIDTH//2, 200, center=True)
    
    # Details
    y_offset = 300
    draw_text(screen, f"Your answer: {user_answer}", font_medium, BLACK, WINDOW_WIDTH//2, y_offset, center=True)
    
    y_offset += 40
    draw_text(screen, f"Score: {score:.1%}", font_medium, result_color, WINDOW_WIDTH//2, y_offset, center=True)
    
    if score < 1.0:
        y_offset += 40
        draw_text(screen, f"Correct answer: {correct_answer}", font_medium, DARK_GRAY, 
                  WINDOW_WIDTH//2, y_offset, center=True)
    
    y_offset += 40
    draw_text(screen, f"Response time: {response_time}ms (Shown for: {exposure_time}ms)", 
              font_small, GRAY, WINDOW_WIDTH//2, y_offset, center=True)
    
    pygame.display.flip()
    
    # Show feedback for exactly 1 second
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    
    while True:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        
        # Check if 1 second has passed
        if elapsed >= 1000:  # 1000 milliseconds = 1 second
            break
            
        # Handle events to prevent freezing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Use clock to maintain consistent frame rate
        clock.tick(60)  # 60 FPS


def show_final_statistics(total_questions, total_correct, records, total_score=None, avg_score=None):
    """Show final statistics"""
    screen.fill(WHITE)
    
    # Use format_score function for consistent formatting
    if avg_score is not None and total_score is not None:
        formatted_text = format_score(total_questions, total_correct, records, total_score, avg_score)
    else:
        formatted_text = format_score(total_questions, total_correct, records)
    
    # Display the formatted text with appropriate styling
    lines = formatted_text.split('\n')
    y_offset = 60
    line_height = 35
    
    for i, line in enumerate(lines):
        if not line.strip():  # Skip empty lines
            y_offset += line_height // 2
            continue
            
        # Determine text size and color based on content
        if i == 0:  # "Training session completed!"
            font = font_large
            color = BLACK
        elif line.startswith("Final score:") or line.startswith("Average Score:"):
            font = font_medium
            color = BLUE
        elif line.startswith("Perfect answers:") or line.startswith("Total:"):
            font = font_small
            color = DARK_GRAY
        elif line.startswith("Results by problem type:"):
            font = font_medium
            color = BLACK
        elif line.startswith("  "):  # Problem type results (indented)
            font = font_small
            # Extract percentage for color coding
            if "100.0%" in line:
                color = GREEN
            elif any(pct in line for pct in ["80.", "90."]):
                color = GREEN
            elif any(pct in line for pct in ["60.", "70."]):
                color = BLUE
            else:
                color = RED
        else:
            font = font_small
            color = BLACK
        
        draw_text(screen, line.strip(), font, color, WINDOW_WIDTH//2, y_offset, center=True)
        y_offset += line_height
    
    # Instructions
    draw_text(screen, "Press ESC to exit", font_medium, GRAY, 
              WINDOW_WIDTH//2, WINDOW_HEIGHT - 50, center=True)
    
    pygame.display.flip()
    
    # Wait for exit
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                waiting = False


def main():
    """Main training function"""
    # Setup
    test_date = datetime.datetime.now()
    start_time = time.time()
    max_questions = 10  # Configurable
    records = []
    
    # Get problems
    problems_dict = create_problems_dict()
    
    if not problems_dict:
        print("No problems found!")
        return
    
    # Show problems and wait for start
    show_problems_screen(problems_dict)
    
    # Training loop
    for question_num in range(1, max_questions + 1):
        # Select random problem
        problem_func = random.choices(list(problems_dict.keys()), list(problems_dict.values()))[0]
        problem = problem_func()
        
        # Show memorization phase
        elapsed_time = time.time() - start_time
        correct_count = sum(1 for r in records if r.correct)  # Uses .correct property for perfect scores
        show_memorize_phase(problem.memorize, problem.exposure_ms, question_num, max_questions, 
                           correct_count, elapsed_time, problem_func)
        
        # Get user input
        input_start_time = time.time()
        user_input = get_user_input(problem)
        response_time = int((time.time() - input_start_time) * 1000)
        
        # Calculate fractional score
        score = problem.evaluate_solution(user_input)
        
        # Create record
        record = Record(problem, user_input, response_time, score)
        records.append(record)
        
        # Show feedback
        show_feedback(score, user_input, problem.solution, response_time, problem.exposure_ms)
    
    # Show final statistics
    total_correct = sum(1 for r in records if r.correct)  # Perfect scores count
    total_score = sum(r.score for r in records)  # Sum of all fractional scores
    avg_score = (total_score / max_questions * 100) if max_questions > 0 else 0
    show_final_statistics(max_questions, total_correct, records, total_score, avg_score)
    
    # Save session data
    save_session_data(test_date, start_time, max_questions, total_correct, records)
    
    pygame.quit()


if __name__ == '__main__':
    main()