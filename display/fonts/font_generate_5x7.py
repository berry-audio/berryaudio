#!/usr/bin/env python3
"""
Create a custom dot matrix font with fixed-width blocks
Each character occupies the same width block for consistent spacing
"""

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
import sys

# 5x7 dot matrix character definitions
# Each character is defined as a list of rows (top to bottom)
# 1 = dot filled, 0 = empty
DOT_MATRIX_CHARS = {
    "0": [
        "01110",
        "10001",
        "10011",
        "10101",
        "11001",
        "10001",
        "01110",
    ],
    "1": [
        "00010",
        "00110",
        "00010",
        "00010",
        "00010",
        "00010",
        "00111",
    ],
    "2": [
        "01110",
        "10001",
        "00001",
        "00010",
        "00100",
        "01000",
        "11111",
    ],
    "3": [
        "11111",
        "00010",
        "00100",
        "00010",
        "00001",
        "10001",
        "01110",
    ],
    "4": [
        "00010",
        "00110",
        "01010",
        "10010",
        "11111",
        "00010",
        "00010",
    ],
    "5": [
        "11111",
        "10000",
        "11110",
        "00001",
        "00001",
        "10001",
        "01110",
    ],
    "6": [
        "00110",
        "01000",
        "10000",
        "11110",
        "10001",
        "10001",
        "01110",
    ],
    "7": [
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
        "01000",
        "01000",
    ],
    "8": [
        "01110",
        "10001",
        "10001",
        "01110",
        "10001",
        "10001",
        "01110",
    ],
    "9": [
        "01110",
        "10001",
        "10001",
        "01111",
        "00001",
        "00010",
        "01100",
    ],
    "A": [
        "01110",
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
    ],
    "B": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10001",
        "10001",
        "11110",
    ],
    "C": [
        "01110",
        "10001",
        "10000",
        "10000",
        "10000",
        "10001",
        "01110",
    ],
    "D": [
        "11110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "11110",
    ],
    "E": [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "11111",
    ],
    "F": [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "10000",
    ],
    "G": [
        "01110",
        "10001",
        "10000",
        "10111",
        "10001",
        "10001",
        "01111",
    ],
    "H": [
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "I": [
        "01110",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "01110",
    ],
    "J": [
        "00111",
        "00010",
        "00010",
        "00010",
        "00010",
        "10010",
        "01100",
    ],
    "K": [
        "10001",
        "10010",
        "10100",
        "11000",
        "10100",
        "10010",
        "10001",
    ],
    "L": [
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "11111",
    ],
    "M": [
        "10001",
        "11011",
        "10101",
        "10101",
        "10001",
        "10001",
        "10001",
    ],
    "N": [
        "10001",
        "10001",
        "11001",
        "10101",
        "10011",
        "10001",
        "10001",
    ],
    "O": [
        "01110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    "P": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10000",
        "10000",
        "10000",
    ],
    "Q": [
        "01110",
        "10001",
        "10001",
        "10001",
        "10101",
        "10010",
        "01101",
    ],
    "R": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10100",
        "10010",
        "10001",
    ],
    "S": [
        "01111",
        "10000",
        "10000",
        "01110",
        "00001",
        "00001",
        "11110",
    ],
    "T": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    "U": [
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    "V": [
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01010",
        "00100",
    ],
    "W": [
        "10001",
        "10001",
        "10001",
        "10101",
        "10101",
        "10101",
        "01010",
    ],
    "X": [
        "10001",
        "10001",
        "01010",
        "00100",
        "01010",
        "10001",
        "10001",
    ],
    "Y": [
        "10001",
        "10001",
        "10001",
        "01010",
        "00100",
        "00100",
        "00100",
    ],
    "Z": [
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
        "10000",
        "11111",
    ],
    " ": [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
    ],
    ":": [
        "00000",
        "00000",
        "00001",
        "00000",
        "00001",
        "00000",
        "00000",
    ],
    ".": [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00001",
    ],
    ",": [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "01000",
        "10000",
    ],
    "'": [
        "00100",
        "00100",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
    ],
    "]": [
        "01110",
        "00010",
        "00010",
        "00010",
        "00010",
        "00010",
        "01110",
    ],
    "[": [
        "01110",
        "01000",
        "01000",
        "01000",
        "01000",
        "01000",
        "01110",
    ],
    "!": [
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00000",
        "00100",
    ],
    "?": [
        "01110",
        "10001",
        "00001",
        "00010",
        "00100",
        "00000",
        "00100",
    ],
    "-": [
        "00000",
        "00000",
        "00000",
        "11111",
        "00000",
        "00000",
        "00000",
    ],
    "_": [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "11111",
    ],
    "+": [
        "00000",
        "00100",
        "00100",
        "11111",
        "00100",
        "00100",
        "00000",
    ],
    "=": [
        "00000",
        "00000",
        "11111",
        "00000",
        "11111",
        "00000",
        "00000",
    ],
    "&": [
        "01100",
        "10010",
        "10100",
        "01000",
        "10101",
        "10010",
        "01101",
    ],
    "ü": [
        "01010",
        "00000",
        "10001",
        "10001",
        "10001",
        "10011",
        "01101",
    ],
    "/": [
        "00000",
        "00001",
        "00010",
        "00100",
        "01000",
        "10000",
        "00000",
    ],
    "(": [
        "00010",
        "00100",
        "01000",
        "01000",
        "01000",
        "00100",
        "00010",
    ],
    ")": [
        "01000",
        "00100",
        "00010",
        "00010",
        "00010",
        "00100",
        "01000",
    ],
    "a": [
        "00000",
        "00000",
        "01110",
        "00001",
        "01111",
        "10001",
        "01111",
    ],
    "b": [
        "10000",
        "10000",
        "10110",
        "11001",
        "10001",
        "10001",
        "11110",
    ],
    "c": [
        "00000",
        "00000",
        "01110",
        "10000",
        "10000",
        "10001",
        "01110",
    ],
    "d": [
        "00001",
        "00001",
        "01101",
        "10011",
        "10001",
        "10001",
        "01111",
    ],
    "e": [
        "00000",
        "00000",
        "01110",
        "10001",
        "11111",
        "10000",
        "01110",
    ],
    "f": [
        "00110",
        "01001",
        "01000",
        "11110",
        "01000",
        "01000",
        "01000",
    ],
    "g": [
        "00000",
        "00000",
        "01111",
        "10001",
        "01111",
        "00001",
        "01110",
    ],
    "h": [
        "10000",
        "10000",
        "10110",
        "11001",
        "10001",
        "10001",
        "10001",
    ],
    "i": [
        "00100",
        "00000",
        "01100",
        "00100",
        "00100",
        "00100",
        "01110",
    ],
    "j": [
        "00010",
        "00000",
        "00110",
        "00010",
        "00010",
        "10010",
        "01100",
    ],
    "k": [
        "10000",
        "10000",
        "10010",
        "10100",
        "11000",
        "10100",
        "10010",
    ],
    "l": [
        "01100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "01110",
    ],
    "m": [
        "00000",
        "00000",
        "11010",
        "10101",
        "10101",
        "10101",
        "10101",
    ],
    "n": [
        "00000",
        "00000",
        "10110",
        "11001",
        "10001",
        "10001",
        "10001",
    ],
    "o": [
        "00000",
        "00000",
        "01110",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    "p": [
        "00000",
        "00000",
        "11110",
        "10001",
        "11110",
        "10000",
        "10000",
    ],
    "q": [
        "00000",
        "00000",
        "01101",
        "10011",
        "01111",
        "00001",
        "00001",
    ],
    "r": [
        "00000",
        "00000",
        "10110",
        "11001",
        "10000",
        "10000",
        "10000",
    ],
    "s": [
        "00000",
        "00000",
        "01110",
        "10000",
        "01110",
        "00001",
        "11110",
    ],
    "t": [
        "01000",
        "01000",
        "11110",
        "01000",
        "01000",
        "01001",
        "00110",
    ],
    "u": [
        "00000",
        "00000",
        "10001",
        "10001",
        "10001",
        "10011",
        "01101",
    ],
    "v": [
        "00000",
        "00000",
        "10001",
        "10001",
        "10001",
        "01010",
        "00100",
    ],
    "w": [
        "00000",
        "00000",
        "10001",
        "10101",
        "10101",
        "10101",
        "01010",
    ],
    "x": [
        "00000",
        "00000",
        "10001",
        "01010",
        "00100",
        "01010",
        "10001",
    ],
    "y": [
        "00000",
        "00000",
        "10001",
        "10001",
        "01111",
        "00001",
        "01110",
    ],
    "z": [
        "00000",
        "00000",
        "11111",
        "00010",
        "00100",
        "01000",
        "11111",
    ],
}


def create_glyph_from_matrix(matrix, dot_size=100, gap=20, left_padding=0):
    """
    Create a glyph outline from a dot matrix pattern.
    Characters maintain their full 5-column block width.

    Args:
        matrix: List of strings representing the dot matrix
        dot_size: Size of each dot in font units
        gap: Gap between dots in font units
        left_padding: Left padding to prevent cutoff (default: 0)
    """
    pen = TTGlyphPen(glyphSet={})

    for row_idx, row in enumerate(matrix):
        for col_idx, pixel in enumerate(row):
            if pixel == "1":
                x = left_padding + (col_idx * (dot_size + gap))
                y = 600 - (row_idx * (dot_size + gap))  # Flip Y axis

                # Draw a square dot
                pen.moveTo((x, y))
                pen.lineTo((x + dot_size, y))
                pen.lineTo((x + dot_size, y + dot_size))
                pen.lineTo((x, y + dot_size))
                pen.closePath()

    return pen.glyph()


def create_dot_matrix_font(
    output_path="DotMatrix.ttf", dot_size=80, gap=30, block_spacing=0, left_padding=50
):
    """
    Create a complete dot matrix font with fixed-width blocks.
    Each character occupies its full 5-column width, creating a continuous grid.

    Args:
        output_path: Where to save the .ttf file
        dot_size: Size of each dot
        gap: Gap between dots within a character
        block_spacing: Additional spacing between character blocks (default: 0)
                      This adds extra space AFTER each character block
        left_padding: Left padding to prevent column 0 from being cut off (default: 50)
    """
    fb = FontBuilder(1000, isTTF=True)

    # Calculate fixed block width based on the 5-column matrix
    # This ensures all characters occupy the same width
    matrix_cols = 5
    char_content_width = matrix_cols * (dot_size + gap) - gap
    # Add left padding to the total width
    block_width = left_padding + char_content_width + block_spacing

    # Set font metadata
    fb.setupHead(unitsPerEm=1000)
    fb.setupGlyphOrder([".notdef"] + list(DOT_MATRIX_CHARS.keys()))

    # Create character map
    cmap = {}
    for char in DOT_MATRIX_CHARS:
        cmap[ord(char)] = char
    fb.setupCharacterMap(cmap)

    # Setup font names
    fb.setupNameTable(
        {
            "familyName": "Dot Matrix Block",
            "styleName": "Regular",
            "uniqueFontIdentifier": "DotMatrixBlock-Regular",
            "fullName": "Dot Matrix Block Regular",
            "psName": "DotMatrixBlock-Regular",
            "version": "Version 1.0",
        }
    )

    # Create glyphs
    glyphs = {}
    metrics = {}

    # Create .notdef (missing glyph)
    pen = TTGlyphPen(glyphSet={})
    pen.moveTo((left_padding + 50, 0))
    pen.lineTo((block_width - 50, 0))
    pen.lineTo((block_width - 50, 700))
    pen.lineTo((left_padding + 50, 700))
    pen.closePath()
    glyphs[".notdef"] = pen.glyph()
    metrics[".notdef"] = (block_width, left_padding)

    # Create character glyphs - ALL use the same block width
    for char, matrix in DOT_MATRIX_CHARS.items():
        glyphs[char] = create_glyph_from_matrix(matrix, dot_size, gap, left_padding)
        # Use left_padding as the left side bearing to prevent cutoff
        metrics[char] = (
            block_width,
            left_padding,
        )  # (advance_width, left_side_bearing)

    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupOS2(
        sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200
    )
    fb.setupPost()

    # Save the font
    fb.save(output_path)
    print(f"Font created successfully: {output_path}")
    print(f"Block width: {block_width} units (includes left padding)")
    print(f"Left padding: {left_padding} units")
    print(f"Character content width: {char_content_width} units")
    print(f"Dot size: {dot_size} units")
    print(f"Gap between dots: {gap} units")
    print(f"Block spacing: {block_spacing} units")


if __name__ == "__main__":
    # Configuration parameters:
    # - dot_size: Size of each individual dot
    # - gap: Space between dots within a character
    # - block_spacing: Additional space between character blocks
    #
    # Examples:
    # No spacing between blocks:
    #   create_dot_matrix_font("tight.ttf", dot_size=80, gap=30, block_spacing=0)
    #
    # Add spacing between blocks:
    #   create_dot_matrix_font("spaced.ttf", dot_size=80, gap=30, block_spacing=50)
    #
    # Larger dots with more spacing:
    #   create_dot_matrix_font("large.ttf", dot_size=100, gap=40, block_spacing=60)

    output = "DotMatrix-Custom-5x7.ttf"
    if len(sys.argv) > 1:
        output = sys.argv[1]

    # Default configuration - adjust these values as needed
    create_dot_matrix_font(
        output_path=output,
        dot_size=60,  # Size of each dot #60, 30
        gap=30,  # Space between dots in a character
        block_spacing=10,  # Extra space between character blocks (0 = no gap)
        left_padding=100,  # Left padding to prevent column 0 cutoff
    )
    # 60, 30, 10, 100 for 21
    # 60, 30, 0, 80 for 45

    print(f"\nFont saved to: {output}")
    print("Supported characters: 0-9, A-Z, a-z, space, and common punctuation")
    print("\nTo use in your code:")
    print(f'font = ImageFont.truetype("{output}", 24)')
    print("\nTo adjust spacing:")
    print("- Increase block_spacing to add gaps between characters")
    print("- Increase gap to spread dots within characters")
    print("- Increase dot_size for larger dots")
