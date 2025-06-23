# -----------------------------------------------------------------
# Code inspired by Hughes, J., Price, S., Lynch, A., Schaeffer, R., Barez, F., Koyejo, S., Sleight, H., Jones, E., Perez, E., & Sharma, M. (2024). 
# Best-of-N Jailbreaking (No. arXiv:2412.03556). arXiv. 
# https://doi.org/10.48550/arXiv.2412.03556
# -----------------------------------------------------------------

import csv
import random

file_path = "ClickBrick_Prompting_table_v2.csv"  # Change to your actual file path
sigma_value = 0.5  # Adjust this value as needed

# Read the file:
with open(file_path, "r", newline="", encoding="utf-8") as infile:
    reader = csv.reader(infile)
    rows = list(reader)

def apply_word_scrambling(text: str, sigma: float) -> str:
    """
    Scrambles the middle characters of words longer than 3 characters in the input text.
    The probability of scrambling is determined by sigma.

    Example:
    Input: "The quick brown fox jumps"
    Output: "The qiuck bwron fox jpums"
    """
    words = text.split()
    scrambled_words = []
    for word in words:
        if len(word) > 3 and random.random() < sigma ** (1 / 2):
            chars = list(word)
            middle_chars = chars[1:-1]
            random.shuffle(middle_chars)
            scrambled_word = chars[0] + "".join(middle_chars) + chars[-1]
            scrambled_words.append(scrambled_word)
        else:
            scrambled_words.append(word)
    return " ".join(scrambled_words)


def apply_random_capitalization(text: str, sigma: float) -> str:
    """
    Randomly capitalizes letters in the input text.

    Input: "The quick brown fox jumps"
    Output: "The qUick bRoWn fOx jUmps"
    """
    new_text = []
    for c in text:
        if c.isalpha() and random.random() < sigma ** (1 / 2):
            if "a" <= c <= "z":
                new_text.append(chr(ord(c) - 32))  # Convert to uppercase
            elif "A" <= c <= "Z":
                new_text.append(chr(ord(c) + 32))  # Convert to lowercase
        else:
            new_text.append(c)
    return "".join(new_text)


def apply_ascii_noising(text: str, sigma: float) -> str:
    """
    Perturbs the ASCII characters of the input text.

    Example:
    Input: "The quick brown fox jumps"
    Output: "Tge quick brown fox junps"
    """
    new_text = []
    for c in text:
        if c.isprintable() and random.random() < sigma**3:
            perturbation = random.choice([-1, 1])
            new_char_code = ord(c) + perturbation
            # Ensure new character is printable ASCII
            if 32 <= new_char_code <= 126:
                new_text.append(chr(new_char_code))
            else:
                new_text.append(c)
        else:
            new_text.append(c)
    return "".join(new_text)

# Write back to the file with additional modified rows
with open(file_path, "w", newline="", encoding="utf-8") as outfile:
    writer = csv.writer(outfile)

    # Write header row first (unchanged)
    writer.writerow(rows[0])

    for row in rows[1:]: # Skip first row (headers)
        writer.writerow(row)  # Write the original row

        # Use the first column value as the base name for new rows
        base_name = row[0]

        # scrambled_row = [f"{base_name}_Scrambled"] + [apply_word_scrambling(cell, sigma_value) for cell in row[1:]]
        # writer.writerow(scrambled_row)  # Write scrambled row with label
        
        # capitalized_row = [f"{base_name}_Capitalized"] + [apply_random_capitalization(cell, sigma_value) for cell in row[1:]]
        # writer.writerow(capitalized_row)  # Write capitalized row with label
        
        both_modified_row = [f"{base_name}_Scrambled"] + [
            apply_random_capitalization(apply_word_scrambling(cell, sigma_value), sigma_value) for cell in row[1:]
        ]
        writer.writerow(both_modified_row)  # Write row with both transformations and label
        

print("Scrambled content added as a new line for each row in the file!")
