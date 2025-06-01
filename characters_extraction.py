# Developed by Elizaveta Mikheeva

import re
import openai

# -------------------------------------------------------------------------#
# Create a dictionary from the identidied characters involved in the story
# -------------------------------------------------------------------------#
def parse_character_data(character_data):
    character_dict = {}

    # Split the data into lines
    lines = character_data.strip().split("\n")

    # Initialize variables to store current character details
    current_name = None
    current_description = []
    current_role = None

    # Iterate through each line and extract character data
    for line in lines:
        line = line.strip()

        # Match the line starting with a number followed by the character's name
        # For example, "1. Coraline: ..."
        name_match = re.match(r"^\d+\.\s*(.*?):\s*(.*)", line)
                
        if name_match is None:
            name_match = re.match(r"^\d+\)\s*(.*?):\s*(.*)", line)
        if name_match:
            # If we have an existing character, save it before starting a new one
            if current_name:
                character_dict[current_name] = {
                    "appearance": " ".join(current_description).strip(),
                    "role": current_role.strip() if current_role else "unknown role"
                }

            # Start a new character, reset variables
            current_name = name_match.group(1).strip()  # Extract name
            current_description = [name_match.group(2).strip()]  # Start description with the first part after the name
            current_role = None  # Reset the role for the new character
            continue

        # Look for the "Role:" keyword to capture the character's role
        if line.startswith("Role:"):
            current_role = line.replace("Role:", "").strip()

        # If the line is not the beginning of a new character, it is part of the description
        if current_name and not line.startswith("Role:"):
            current_description.append(line.strip())

    # After finishing the loop, add the last character to the dictionary
    if current_name:
        character_dict[current_name] = {
            "appearance": " ".join(current_description).strip(),
            "role": current_role.strip() if current_role else "unknown role"
        }
    print("Initial Dictionary: ", character_dict)
    return character_dict
