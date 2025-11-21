from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from PIL import Image as PILImage
import os

def generate_players_pdf(players, app):
    """Generate a PDF document containing the list of players with their details and pictures."""
    buffer = BytesIO()
    
    # Create the PDF document with optimized margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20,  # Reduced right margin
        leftMargin=20,   # Reduced left margin
        topMargin=30,    # Slightly reduced top margin
        bottomMargin=30  # Slightly reduced bottom margin
    )
    
    # Initialize flowable elements list
    elements = []
    styles = getSampleStyleSheet()
    
    # Create custom styles
    custom_style = ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        alignment=1  # Center alignment
    )
    
    sno_style = ParagraphStyle(
        'SNOStyle',
        parent=styles['Normal'],
        fontSize=14,
        leading=16,
        alignment=1,
        textColor=colors.black,
        backColor=colors.white,
        borderColor=colors.black,
        borderWidth=1,
        borderPadding=5,
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    # Add title
    title = Paragraph(
        f"Cricket Tournament Registered Players List - {datetime.now().strftime('%Y-%m-%d')}",
        ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1
        )
    )
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Create header style
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.whitesmoke,
        alignment=1
    )
    
    # Create headers with styled paragraphs
    headers = [
        Paragraph('<b>S.No</b>', header_style),
        Paragraph('Picture', header_style),
        Paragraph('Player Name', header_style),
        Paragraph('Nickname', header_style),
        Paragraph('Role', header_style),
        Paragraph('Mobile Number', header_style),
        Paragraph('Address', header_style)
    ]
    
    # Initialize table data with headers
    data = [headers]
    
    # Helper function to get player role text
    def get_player_role(player):
        roles = []
        if player.is_all_rounder:
            roles.append("All-Rounder")
        if player.is_left_hand_batter or player.is_right_hand_batter:
            bat_style = []
            if player.is_left_hand_batter:
                bat_style.append("Left-Hand")
            if player.is_right_hand_batter:
                bat_style.append("Right-Hand")
            roles.append(f"{' & '.join(bat_style)} Batter")
        if player.is_left_arm_bowler or player.is_right_arm_bowler:
            bowl_style = []
            if player.is_left_arm_bowler:
                bowl_style.append("Left-Arm")
            if player.is_right_arm_bowler:
                bowl_style.append("Right-Arm")
            roles.append(f"{' & '.join(bowl_style)} Bowler")
        return " | ".join(roles) if roles else "Not Specified"
    
    # Process each player
    for idx, player in enumerate(players, 1):
        # Process player picture
        pic_cell = None
        try:
            def process_image(image_path):
                """Process an image file for PDF inclusion"""
                img = PILImage.open(image_path)
                # Convert RGBA to RGB by pasting on white background
                if img.mode == 'RGBA':
                    background = PILImage.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize image maintaining aspect ratio
                img.thumbnail((100, 100))
                
                # Convert to PDF-compatible format
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG', quality=95)
                img_buffer.seek(0)
                
                # Create ReportLab Image
                img_rl = Image(img_buffer)
                img_rl.drawHeight = 80
                img_rl.drawWidth = 80
                return img_rl
            
            # Try player's profile picture first
            if player.profile_picture:
                try:
                    pic_path = os.path.join(app.config['UPLOAD_FOLDER'], player.profile_picture)
                    if os.path.exists(pic_path):
                        pic_cell = process_image(pic_path)
                except Exception as e:
                    app.logger.error(f'Error processing profile picture: {str(e)}')
            
            # If no profile picture, try generated card
            if not pic_cell:
                try:
                    card_name = f"{player.id}_{player.full_name.replace(' ', '_')}_card.png"
                    role_dir = '1_All_Rounders' if player.is_all_rounder else \
                              '2_Batters' if (player.is_left_hand_batter or player.is_right_hand_batter) else \
                              '3_Bowlers'
                    
                    card_path = os.path.join(app.root_path, 'Player_Event_Assets', role_dir, 
                                             str(player.id) + '_' + player.full_name.replace(' ', '_'), 
                                             card_name)
                    
                    if os.path.exists(card_path):
                        pic_cell = process_image(card_path)
                except Exception as e:
                    app.logger.error(f'Error processing player card: {str(e)}')
            
        except Exception as e:
            app.logger.error(f'Error in image search process: {str(e)}')
        except Exception as e:
            app.logger.error(f'Error processing player image: {str(e)}')
        
        if not pic_cell:
            pic_cell = Paragraph('No Image', ParagraphStyle(
                'NoImage',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=1
            ))
        
        # Create row data with enhanced S.No formatting
        row = [
            Paragraph(f'<b>{idx}</b>', ParagraphStyle(
                'SNO',
                parent=styles['Normal'],
                fontSize=12,
                alignment=1,  # Center alignment
                textColor=colors.black,
                spaceAfter=0,
                spaceBefore=0,
                leading=14
            )),
            pic_cell or Paragraph('No Image', custom_style),  # Picture or placeholder
            Paragraph(player.full_name, styles['Normal']),
            Paragraph(player.nickname or "N/A", styles['Normal']),
            Paragraph(get_player_role(player), styles['Normal']),
            Paragraph(player.mobile_number, styles['Normal']),
            Paragraph(player.address, ParagraphStyle(
                'Address',
                parent=styles['Normal'],
                alignment=0,
                leftIndent=5,
                rightIndent=5
            ))
        ]
        data.append(row)
    
    # Create and style table
    table = Table(
        data,
        colWidths=[
            0.5*inch,     # S.No - compact but visible
            1.5*inch,     # Picture - adjusted for images
            1.6*inch,     # Player Name - slightly reduced
            1.1*inch,     # Nickname - compact
            2.6*inch,     # Role - optimized for content
            1.3*inch,     # Mobile Number - compact
            2.4*inch,     # Address - optimized
        ],
        rowHeights=[0.7*inch] + [1.4*inch] * (len(data)-1)  # Slightly reduced height
    )
    
    # Define table style
    table_style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        # S.No column styling - maximized visibility
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e3f2fd')),  # Light blue background
        ('GRID', (0, 0), (0, -1), 1.5, colors.black),  # Thicker grid lines
        ('BOX', (0, 0), (0, -1), 2, colors.black),  # Bold outer border
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Center alignment
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # Bold font
        ('FONTSIZE', (0, 1), (0, -1), 14),  # Clear font size
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),  # Black text
        ('TOPPADDING', (0, 0), (0, -1), 15),  # More top padding
        ('BOTTOMPADDING', (0, 0), (0, -1), 15),  # More bottom padding
        ('LEFTPADDING', (0, 0), (0, -1), 5),  # Less left padding for numbers
        ('RIGHTPADDING', (0, 0), (0, -1), 5),  # Less right padding for numbers
        
        # Column alignments
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),    # Picture
        ('ALIGN', (2, 1), (4, -1), 'LEFT'),      # Name, Nickname, Role
        ('ALIGN', (5, 1), (5, -1), 'CENTER'),    # Mobile
        ('ALIGN', (6, 1), (6, -1), 'LEFT'),      # Address
        
        # Borders and grid
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#1a237e')),
        
        # Row styling
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # General formatting
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5)
    ])
    
    # Apply style to table
    table.setStyle(table_style)
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer