import random
import os
import hashlib
import qrcode
from PIL import Image, ImageDraw, ImageFont
import textwrap

class UrbanAICardGenerator:
    def __init__(self):
        # Card dimensions - using standard playing card ratio (2.5 x 3.5 inches)
        # At 200 DPI this would be 500 x 700 pixels
        self.card_width = 500
        self.card_height = 700
        
        # Define color schemes (background, text)
        self.color_schemes = {
            'green': ('#1a4d4d', 'white'),  # Teal/green
            'blue': ('#224f66', 'white'),   # Dark blue
            'red': ('#a83232', 'white'),    # Red
            'light_blue': ('#3e7b99', 'white'),  # Light blue
            'gray': ('#667788', 'white'),   # Gray
        }
        
        # Define timing labels
        self.timing_labels = ["NOW", "NEAR", "NEXT"]
        
        # Sample card data
        self.sample_cards = [
            {
                "title": "Increasing urbanisation of data centres",
                "content": "Digitalisation of life has seen data centres urbanise to provide low latency and real-time responsiveness to consumers. Their energy, water and space needs, as well as waste heat, are some of the issues urban planners need to consider.",
                "source": "CIDOB, 2023",
                "timing": "NOW",
                "id": "card_test_001",
                "color": "green"
            },
            {
                "title": "Rapid concept generation",
                "content": "Generative AI adoption is allowing designers to explore new ideas, including previously unimagined ones, much faster than traditional methods. Here, designers are increasingly using text prompts to generate unique visuals within minutes, supporting rapid ideation and explore design concepts more efficiently.",
                "source": "Forbes, 2024",
                "timing": "NOW",
                "id": "card_test_002",
                "color": "blue"
            },
            {
                "title": "Biased data influencing decisions",
                "content": "AI is only as good as the data it is trained on. Poor data in models can perpetuate bias, causing unintended and discriminative consequences in solution designs/plans.",
                "source": "OCHR, 2024",
                "timing": "NEAR",
                "id": "card_test_003",
                "color": "red"
            },
            {
                "title": "AI for urban resilience",
                "content": "Using AI to create higher fidelity and more accessible digital twins, this can help planners better analyze, prepare and respond to potential climate events and population shocks, aiding greater levels of urban resilience.",
                "source": "Frontiers Policy Labs, 2024",
                "timing": "NEAR",
                "id": "card_test_004",
                "color": "red"
            },
            {
                "title": "AI in the design lifecycle",
                "content": "AI has the potential to make projects more efficient, inclusive and creative but carries risks due to bias, privacy issues, and over-reliance on technology. Balancing regulation and human insight will be crucial.",
                "source": "Archdaily, 2024",
                "timing": "NEAR",
                "id": "card_test_005",
                "color": "blue"
            },
            {
                "title": "Tackling housing shortages",
                "content": "With interventions across the construction lifecycle, AI can improve location selection, pre-building, accelerate planning by generating multiple design proposals with the latest building codes and regulations as well as optimise construction sites and processes.",
                "source": "UN OHCHR, 2023",
                "timing": "NEAR",
                "id": "card_test_006",
                "color": "red"
            },
            {
                "title": "Interconnected infrastructure systems",
                "content": "Using AI to break silos and integrate our systems and infrastructure could allow for vastly improved and responsive urban services and infrastructure.",
                "source": "Wired, 2023",
                "timing": "NEXT",
                "id": "card_test_007",
                "color": "gray"
            },
            {
                "title": "Citizen-driven design",
                "content": "New highly iterative methods of urban planning could emerge by converting text prompts into photorealistic designs for public feedback, bringing citizens early in the design process to shape their city.",
                "source": "Forbes, 2024",
                "timing": "NEXT",
                "id": "card_test_008",
                "color": "light_blue"
            },
            {
                "title": "Growing public spending pressures",
                "content": "Public spending pressures are universal around the globe and increasing. Delivering more with limited resources creates the need for resource and time efficiency across the design and planning lifecycle.",
                "source": "UNCTAD, 2024",
                "timing": "NOW",
                "id": "card_test_009",
                "color": "green"
            },
            {
                "title": "Immersive and personalised urban experiences",
                "content": "Immersive and personalised urban experiences such as 3D billboards are increasingly prevalent. AI can help this infrastructure adapt in real time to environmental conditions and user preferences.",
                "source": "Artist, Warm & Fuzzy, 2023",
                "timing": "NEXT",
                "id": "card_test_010",
                "color": "gray"
            }
        ]
        
        # Load fonts with proportionally larger sizes for better readability
        try:
            # Using Arial Bold for all text elements for better readability
            self.title_font = ImageFont.truetype("arialbd.ttf", 40)
            self.body_font = ImageFont.truetype("arialbd.ttf", 28)
            self.source_font = ImageFont.truetype("arialbd.ttf", 24)
            self.timing_font = ImageFont.truetype("arialbd.ttf", 32)
            self.hash_font = ImageFont.truetype("arialbd.ttf", 18)  # Smaller font for hash
        except IOError:
            # Try alternative font paths
            try:
                self.title_font = ImageFont.truetype("Arial Bold.ttf", 40)
                self.body_font = ImageFont.truetype("Arial Bold.ttf", 28)
                self.source_font = ImageFont.truetype("Arial Bold.ttf", 24)
                self.timing_font = ImageFont.truetype("Arial Bold.ttf", 32)
                self.hash_font = ImageFont.truetype("Arial Bold.ttf", 18)  # Smaller font for hash
            except IOError:
                # Fallback to default font if custom fonts not available
                self.title_font = ImageFont.load_default()
                self.body_font = ImageFont.load_default()
                self.source_font = ImageFont.load_default()
                self.timing_font = ImageFont.load_default()
                self.hash_font = ImageFont.load_default()

    def create_card(self, card_data, id=None):
        """Create a single card based on provided data"""
        # Get color values
        bg_color_hex, text_color = self.color_schemes[card_data["color"]]
        
        # Convert hex color to RGBA tuple
        r = int(bg_color_hex[1:3], 16)
        g = int(bg_color_hex[3:5], 16)
        b = int(bg_color_hex[5:7], 16)
        bg_color_rgba = (r, g, b, 255)
        
        # Create a transparent base image
        img = Image.new('RGBA', (self.card_width, self.card_height), (0, 0, 0, 0))
        
        # Create a colored rectangle with rounded corners
        mask = Image.new('L', (self.card_width, self.card_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        
        # Draw a rounded rectangle on the mask
        radius = int(self.card_width * 0.05)  # Corner radius as 5% of card width
        mask_draw.rounded_rectangle([(0, 0), (self.card_width, self.card_height)], radius=radius, fill=255)
        
        # Create colored overlay
        colored_overlay = Image.new('RGBA', (self.card_width, self.card_height), bg_color_rgba)
        
        # Apply the mask to the colored overlay
        colored_overlay.putalpha(mask)
        
        # Paste the colored overlay onto the transparent base
        img.paste(colored_overlay, (0, 0), colored_overlay)
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        # Generate MD5 hash (8 characters) from the title
        title_hash = hashlib.md5(card_data["title"].encode()).hexdigest()#[:8]  # First 8 characters
        URL = card_data["ID"]
        # Generate QR code that points to a URL with the hash
        qr_url = f"https://futures.kghosh.me/{URL}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=1
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # Create QR code image with white background
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize QR code to match approximately 2 lines of title height
        title_line_height = 44  # Approximate height of a line of title text
        qr_size = title_line_height * 2
        qr_img = qr_img.resize((qr_size, qr_size))
        
        # Calculate position for QR code (left of title)
        qr_x = 35  # Left margin for QR code
        qr_y = 35  # Top margin for QR code
        
        # Convert QR code to RGBA if it isn't already
        if qr_img.mode != 'RGBA':
            qr_img = qr_img.convert('RGBA')
        
        # Paste QR code onto card
        img.paste(qr_img, (qr_x, qr_y), qr_img)
        
        # Calculate title position (to the right of QR code)
        title_x = qr_x + qr_size + 15  # Spacing between QR and title
        title_y = 35  # Top margin for title
        
        # Calculate available width for title
        available_width = self.card_width - title_x - 35  # 35px margin on the right side
        
        # Draw title - calculate characters per line based on available width
        title_text = card_data["title"]
        # Estimate characters per line based on average character width
        avg_char_width = self.title_font.getbbox("W")[2]  # Width of a wide character
        chars_per_line = max(10, int(available_width / (avg_char_width * 0.6)))  # 0.6 factor for mixed character widths
        
        wrapped_title = textwrap.fill(title_text, width=chars_per_line)
        draw.text((title_x, title_y), wrapped_title, font=self.title_font, fill=text_color)
        
        # Calculate the height of the wrapped title text to ensure content doesn't overlap
        title_lines = wrapped_title.count('\n') + 1  # Number of lines in wrapped title
        title_height = title_lines * (self.title_font.getbbox("Wy")[3] * 1.2)  # Height of title text with line spacing
        
        # Ensure content starts after title with adequate spacing
        content_y = max(180, title_y + title_height + 30)  # At least 30px spacing between title end and content start
        
        # Draw content text with dynamic spacing based on title height
        content_text = card_data["content"]
        wrapped_content = textwrap.fill(content_text, width=28)  # Adjusted width for the playing card ratio
        draw.text((35, content_y), wrapped_content, font=self.body_font, fill=text_color)
        
        # Draw source at bottom left
        source_text = card_data["source"]
        draw.text((35, self.card_height - 70), source_text, font=self.source_font, fill=text_color)
        
        # Draw MD5 hash below the source
        draw.text((35, self.card_height - 35), title_hash, font=self.hash_font, fill=text_color)
        
        # Draw timing label at bottom right
        timing_text = card_data["timing"]
        # Use font.getbbox() instead of draw.textsize
        timing_bbox = self.timing_font.getbbox(timing_text)
        timing_width = timing_bbox[2] - timing_bbox[0]
        draw.text(
            (self.card_width - timing_width - 35, self.card_height - 70),
            timing_text,
            font=self.timing_font,
            fill=text_color
        )
        
        return img
    
    def generate_cards(self, cards_to_generate=None, output_dir="docs/imgs", debug = False):
        """Generate multiple cards and save to output directory"""
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # If num_cards is not specified, generate all sample cards
        if cards_to_generate is None:
            cards_to_generate = self.sample_cards
        
        # Generate and save each card
        ids = []
        for i, card_data in enumerate(cards_to_generate):
            id = hashlib.md5(str(card_data).encode()).hexdigest()
            ids.append(id)
            card_img = self.create_card(card_data)
            # Create filename using hash of title for uniqueness
            #title_hash = hashlib.md5(card_data["title"].encode()).hexdigest()[:8]
            #safe_title = card_data["title"].replace(" ", "_")[:20]  # Truncate and make filename safe
            filename = f"{output_dir}/card_{id}.png"
            # Save with transparency
            card_img.save(filename, format="png")
            if debug:
                print(f"Generated card: {filename}")
        return ids

    def generate_grid(self, selected_cards, rows=2, cols=3, output_file="urban_ai_cards_grid.png",debug=False):
        """Generate a grid of cards and save as a single image"""
        num_cards = rows * cols
        
        if not len(selected_cards):
            selected_cards = self.sample_cards
            
        selected_cards = selected_cards[:]
        
        # Create grid image with transparent background
        grid_width = cols * self.card_width
        grid_height = rows * self.card_height
        grid_img = Image.new('RGBA', (grid_width, grid_height), (0, 0, 0, 0))
        
        # Generate and place each card on the grid
        for i, card_data in enumerate(selected_cards):
            row = i // cols
            col = i % cols
            card_img = self.create_card(card_data)
            # Use paste with alpha channel for proper transparency
            grid_img.paste(card_img, (col * self.card_width, row * self.card_height), card_img)
        
        # Save the grid image with transparency
        grid_img.save(output_file, format="PNG")
        if debug:
            print(f"Generated grid image: {output_file}")
        
        return output_file

    def generate_custom_card(self, title, content, source, timing, color, ID, debug = False):
        """Generate a custom card with user-provided content"""
        custom_card_data = {
            "title": title,
            "content": content,
            "source": source,
            "timing": timing,
            "color": color,
            "id": ID
        }
        
        card_img = self.create_card(custom_card_data)
        safe_title = title.replace(" ", "_")[:20]  # Use part of title for filename
        filename = f"custom_card_{safe_title}.png"
        # Save with transparency
        card_img.save(filename, format="PNG")
        if debug:
            print(f"Generated custom card: {filename}")
        
        return filename

# Example usage:
if __name__ == "__main__":
    generator = UrbanAICardGenerator()
    
    # Generate all sample cards
    generator.generate_cards(debug=True)
    
    # Generate a 3x3 grid of cards
    generator.generate_grid(rows=3, cols=3, debug=True)
    
    # Create a custom card
    generator.generate_custom_card(
        title="Smart City Integration",
        content="AI-powered urban systems are enabling cities to optimize resource usage, improve traffic flow, and enhance citizen services through intelligent data analysis and predictive modeling.",
        source="Smart Cities Journal, 2024",
        timing="NEAR",
        color="blue",
        debug = True
    )