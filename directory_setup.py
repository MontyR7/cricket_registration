import os
import logging

logger = logging.getLogger(__name__)

def setup_directories(app):
    """
    Creates all required directories for the application
    """
    try:
        # Create uploads directory
        uploads_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(uploads_dir, exist_ok=True)
        logger.info(f"Created uploads directory: {uploads_dir}")

        # Create player cards directories
        cards_base_dir = os.path.join(app.static_folder, 'player_cards')
        role_dirs = {
            '1_all_rounders': os.path.join(cards_base_dir, '1_all_rounders'),
            '2_batters': os.path.join(cards_base_dir, '2_batters'),
            '3_bowlers': os.path.join(cards_base_dir, '3_bowlers')
        }

        # Create all directories
        for dir_name, dir_path in role_dirs.items():
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created {dir_name} directory: {dir_path}")

        # Create static/images directory for default profile picture
        images_dir = os.path.join(app.static_folder, 'images')
        os.makedirs(images_dir, exist_ok=True)
        logger.info(f"Created images directory: {images_dir}")

        return True
    except Exception as e:
        logger.error(f"Error creating directories: {str(e)}")
        return False