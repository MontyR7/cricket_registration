from PIL import Image, ImageDraw, ImageFont
import os
import logging
import sys
from typing import Optional, Tuple
from pathlib import Path

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('card_generator.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants for card generation
CARD_WIDTH = 800
CARD_HEIGHT = 400
PHOTO_SIZE = (300, 360)
PHOTO_POSITION = (20, 20)
TEXT_START_X = 340
BACKGROUND_COLOR = '#1a237e'
FALLBACK_PHOTO_COLOR = '#4a5568'
TEXT_COLORS = {
    'name': 'white',
    'nickname': '#ffd700',
    'role': '#90caf9'
}
FONT_SIZES = {
    'name': 48,
    'nickname': 32,
    'role': 36
}

def load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font with fallbacks"""
    try:
        # Try system font paths
        system_fonts = [
            "arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "C:/Windows/Fonts/arial.ttf"  # Windows
        ]
        
        for font_path in system_fonts:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
                
        logger.warning(f"Could not find system fonts, using default")
        return ImageFont.load_default()
        
    except Exception as e:
        logger.error(f"Error loading font: {str(e)}")
        return ImageFont.load_default()

def validate_inputs(player_name: str, nickname: Optional[str], role: str, 
                  photo_path: Optional[str], output_path: str) -> Tuple[bool, str]:
    """Validate all input parameters before card generation"""
    if not player_name or not player_name.strip():
        return False, "Player name is required"
    if not role or not role.strip():
        return False, "Role is required"
    if not output_path or not output_path.strip():
        return False, "Output path is required"
    
    # Check output directory permissions
    try:
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        # Test write permissions with a temporary file
        test_file = os.path.join(output_dir, '.test_write')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception as e:
        return False, f"Output directory is not writable: {str(e)}"
    
    # Validate photo path if provided
    if photo_path:
        if not os.path.exists(photo_path):
            return False, f"Photo file not found: {photo_path}"
        try:
            with Image.open(photo_path) as img:
                img.verify()
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    return True, ""

def create_player_card(player_name: str, nickname: Optional[str], role: str, 
                      photo_path: Optional[str], output_path: str) -> bool:
    """Create a player card using Pillow"""
    try:
        logger.info(f"Starting card generation for player: {player_name}")
        logger.debug(f"Parameters: nickname='{nickname}', role='{role}', "
                    f"photo_path='{photo_path}', output_path='{output_path}'")
        
        # Validate inputs
        valid, error_msg = validate_inputs(player_name, nickname, role, photo_path, output_path)
        if not valid:
            logger.error(f"Input validation failed: {error_msg}")
            return False
        
        # Create a new image with background
        image = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)
        
        # Load fonts
        fonts = {
            'name': load_font('arial.ttf', FONT_SIZES['name']),
            'nickname': load_font('arial.ttf', FONT_SIZES['nickname']),
            'role': load_font('arial.ttf', FONT_SIZES['role'])
        }
        
        # Process photo
        photo_box = [PHOTO_POSITION[0], PHOTO_POSITION[1],
                    PHOTO_POSITION[0] + PHOTO_SIZE[0],
                    PHOTO_POSITION[1] + PHOTO_SIZE[1]]
                    
        if photo_path and os.path.exists(photo_path):
            try:
                with Image.open(photo_path) as photo:
                    # Convert to RGB if necessary
                    if photo.mode not in ('RGB', 'RGBA'):
                        photo = photo.convert('RGB')
                    
                    # Handle RGBA images
                    if photo.mode == 'RGBA':
                        # Create white background
                        bg = Image.new('RGB', photo.size, 'white')
                        bg.paste(photo, mask=photo.split()[3])  # Use alpha channel as mask
                        photo = bg
                    
                    # Resize maintaining aspect ratio
                    photo.thumbnail(PHOTO_SIZE, Image.Resampling.LANCZOS)
                    
                    # Center the photo in the designated area
                    paste_x = PHOTO_POSITION[0] + (PHOTO_SIZE[0] - photo.size[0]) // 2
                    paste_y = PHOTO_POSITION[1] + (PHOTO_SIZE[1] - photo.size[1]) // 2
                    
                    image.paste(photo, (paste_x, paste_y))
                    logger.info("Successfully processed and pasted player photo")
            except Exception as e:
                logger.error(f"Error processing photo: {str(e)}", exc_info=True)
                draw.rectangle(photo_box, fill=FALLBACK_PHOTO_COLOR)
        else:
            logger.warning("No photo provided or not found, using fallback")
            draw.rectangle(photo_box, fill=FALLBACK_PHOTO_COLOR)
        
        # Draw text
        try:
            # Draw name with shadow effect for better visibility
            shadow_offset = 2
            draw.text((TEXT_START_X + shadow_offset, 50 + shadow_offset), 
                     player_name, font=fonts['name'], fill='black')
            draw.text((TEXT_START_X, 50), player_name, 
                     font=fonts['name'], fill=TEXT_COLORS['name'])
            
            if nickname:
                draw.text((TEXT_START_X, 120), f"({nickname})", 
                         font=fonts['nickname'], fill=TEXT_COLORS['nickname'])
            
            # Draw role with multi-line support if needed
            role_y = 200
            max_width = CARD_WIDTH - TEXT_START_X - 20
            role_parts = role.split(' | ')
            for part in role_parts:
                draw.text((TEXT_START_X, role_y), part, 
                         font=fonts['role'], fill=TEXT_COLORS['role'])
                role_y += fonts['role'].size + 5
            
            logger.info("Successfully added text to card")
            
        except Exception as e:
            logger.error(f"Error drawing text: {str(e)}", exc_info=True)
            return False
        
        # Save the image with error handling
        try:
            image.save(output_path, format='PNG', quality=95, optimize=True)
            
            # Verify file was created and is valid
            if os.path.exists(output_path):
                with Image.open(output_path) as verify_img:
                    verify_img.verify()
                logger.info(f"Card successfully saved to: {output_path}")
                return True
            else:
                logger.error("Card file was not created")
                return False
                
        except Exception as e:
            logger.error(f"Error saving card: {str(e)}", exc_info=True)
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in card generation: {str(e)}", exc_info=True)
        return False