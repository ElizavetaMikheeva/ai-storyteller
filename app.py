# Developed by Elizaveta Mikheeva

from flask import Flask, request, jsonify, render_template, session

import openai
import re
import characters_extraction

app = Flask(__name__)



app.secret_key = "your_secret_key_here"  # Needed for session to work
openai.api_key = 'insert your OpenAI API key here '

# Home route to serve HTML form
@app.route('/') 
def home():
    return render_template('index.html')  # Render the HTML template

# -------------------------------------------------------------------------#
# Initialising dictionaries, lists and variables
# -------------------------------------------------------------------------#

character_appearance_cache = {}
current_chapter = 1  # Initialize the first chapter
user_choices = []  # Store user choices for later reference
chapter_summaries = {}
character_dict = {} 


def get_current_chapter():
    """Retrieve the current chapter from session, defaulting to 1 if not set."""
    return session.get("current_chapter", 1)


def set_current_chapter(chapter):
    """Update the current chapter in session."""
    session["current_chapter"] = chapter


def get_user_choices():
    """Retrieve user choices from session, defaulting to an empty list."""
    return session.get("user_choices", [])


def add_user_choice(choice):
    """Append a choice to the user choices list in session."""
    choices = session.get("user_choices", [])
    choices.append(choice)
    session["user_choices"] = choices


def get_chapter_summaries():
    """Retrieve chapter summaries from session, defaulting to an empty dictionary."""
    return session.get("chapter_summaries", {})


def update_chapter_summary(chapter_number, summary, carryover):

    print(f" update_chapter_summary() called for Chapter {chapter_number}")
    print(f" Summary: {summary}")
    print(f" Carryover: {carryover}")
    """Update the chapter summary and store it in session."""
    if 'chapter_summaries' not in session:
        session['chapter_summaries'] = {}  # Initialize if not exists

    # Store summary and carryover in session
    session['chapter_summaries'][str(chapter_number)] = {
        "summary": summary,
        "carryover": carryover
    }

    # ✅ Print the entire session dictionary for debugging
    print("📜 Full Chapter Summaries Dictionary:")
    print(session['chapter_summaries'])  # Prints all stored chapters
    session.modified = True  # Mark session as modified to save changes


# -------------------------------------------------------------------------#
# Extracting character names that are to be involved in the illustration (scene)
# -------------------------------------------------------------------------#
def extract_character_names_from_scene(scene, character_dict):
    """
    Extract character names mentioned in the scene description by checking against the character dictionary.
    """

    # Initialize an empty set to store the relevant character names mentioned in the scene
    relevant_names = set()

    # Traverse the character dictionary and check if the character's name is mentioned in the scene
    for name in character_dict.keys():
        # Check if the name (case-insensitive) is in the scene
        if name in scene:
            relevant_names.add(name)

    return relevant_names


# -------------------------------------------------------------------------#
# Combining names with the appearance of characters that are to be involved in the illustration (scene)
# -------------------------------------------------------------------------#
def build_character_description_prompt_for_scene(scene, character_dict, relevant_names):
    # Extract character names mentioned in the scene
    
    # Filter the character dictionary to include only characters mentioned in the scene
    relevant_characters = {name: details for name, details in character_dict.items() if name in relevant_names}
    
    # Step 3: Build the character description prompt
    character_description_prompt = ""
    for name, details in relevant_characters.items():
        appearance = details['appearance'] if details['appearance'] else "unknown appearance"
        # We exclude role here, as we're only concerned with appearance
        character_description_prompt += f"{name}: {appearance}. "
    
    print("Dictionary to pass:", character_description_prompt)
    return character_description_prompt

# -------------------------------------------------------------------------#
# Manages the dictionary with the options that the user can make to direct the narrative
# -------------------------------------------------------------------------#
def parse_choices(text):
    choice_dict = {}

    # Use regex to find all choices (e.g., A), B), C)) in the text.
    choice_matches = re.split(r"([A-C]\))", text)

    # Process the splits to populate the dictionary.
    for i in range(1, len(choice_matches) - 1, 2):  # Choices appear at odd indices, descriptions at even indices.
        choice_key = choice_matches[i].strip()  # Extract the choice key (e.g., A), B), C)).
        choice_description = choice_matches[i + 1].strip()  # The following text is its description.

        # Assign the choice and description to the dictionary.
        choice_dict[choice_key] = choice_description
    if len(choice_dict) == 0:
        choice_dict['A)'] = 'Keep Reading...'
    #print(choice_dict)
    return choice_dict

# -------------------------------------------------------------------------#
# Checks the current beat of the stroy
# -------------------------------------------------------------------------#
def get_phase_by_chapter(chapter_number):
    """
    Determines the phase based on the chapter number.
    """
    if chapter_number == 1:
        return "Ordinary World"
    elif chapter_number == 2:
        return "Call to Adventure"
    elif chapter_number == 3:
        return "Refusal of the Call"
    elif chapter_number == 4:
        return "Meeting the Mentor"
    elif chapter_number == 5:
        return "Crossing the First Threshold"
    elif chapter_number == 6:
        return "Tests"
    elif chapter_number == 7:
        return "Allies"
    elif chapter_number == 8:
        return "Enemies"
    elif chapter_number == 9:
        return "Approach to the Inmost Cave"
    elif chapter_number == 10:
        return "Ordeal Part1"
    elif chapter_number == 11:
        return "Ordeal Part2"
    elif chapter_number == 12:
        return "Ordeal Part3"
    elif chapter_number == 13:
        return "Reward"
    elif chapter_number == 14:
        return "The Road Back"
    elif chapter_number == 15:
        return "Resurrection"
    elif chapter_number == 16:
        return "Return with the Elixir Part1"
    elif chapter_number == 17:
        return "Return with the Elixir Part2"
    else:
        return ""

# -------------------------------------------------------------------------#
# Summarise 'previous' chapter
# -------------------------------------------------------------------------#

def summarize_chapter(chapter_text):
    """
    Summarize the given chapter and extract the most relevant part that should be carried over,
    using a single API call to save costs.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an advanced storytelling assistant.\n"
                    "Your task is to:\n"
                    "1. Generate a concise summary of the given chapter in around 200 words.\n"
                    "2. Extract only the **necessary** paragraphs from the end of the chapter to ensure smooth transition, "
                    "without adding any new content.\n"
                    "\n"
                    "**IMPORTANT RULES:**\n"
                    "- ONLY extract existing text. Do NOT generate new sentences, transitions, or foreshadowing.\n"
                    "- Include all ongoing conversations, ensuring no dialogue is cut off in the middle.\n"
                    "- If an important event is unresolved, include all relevant paragraphs leading up to it.\n"
                    "- DO NOT include unnecessary setting descriptions or repeated details unless they are vital for continuity.\n"
                    "- If the chapter ends on a major cliffhanger or mystery, ensure that portion is included.\n"
                    "- Dynamically decide the number of paragraphs to extract—include exactly what is needed for a natural transition (this may be 2, 6, or more).\n"
                    "\n"
                    "FORMAT YOUR RESPONSE STRICTLY AS FOLLOWS:\n"
                    "[SUMMARY]: <Insert concise chapter summary here>\n"
                    "[CARRYOVER]: <Insert only the necessary paragraphs from the end of the chapter>"
                ),
            },
            {
                "role": "user",
                "content": chapter_text,
            },
        ],
        max_tokens=500,  # Limiting for efficiency
        temperature=0.5,
    )

    response_text = response['choices'][0]['message']['content'].strip()

    # Extract summary and carryover text using regex
    summary_match = re.search(r"\[SUMMARY\]: (.*?)\n\[CARRYOVER\]:", response_text, re.DOTALL)
    carryover_match = re.search(r"\[CARRYOVER\]: (.*)", response_text, re.DOTALL)

    summary = summary_match.group(1).strip() if summary_match else "No summary generated."
    carryover_text = carryover_match.group(1).strip() if carryover_match else ""

    #print("SUMMARY FROM FUNCTION: ", summary)
    #print("CARRYOUR FROM FUNCTION: ", carryover_text)
    return summary, carryover_text


@app.route('/reset-session', methods=['POST'])
def reset_session():
    global chapter_summaries, character_dict, user_choices, character_appearance_cache, current_chapter

    # ✅ Empty all dictionaries
    chapter_summaries.clear()
    character_dict.clear()
    character_appearance_cache.clear()
    user_choices.clear()
    session.clear()  # Clears all stored session data
    return jsonify({'message': 'Session reset successfully. You can start a new story.'})

@app.route('/generate-story', methods=['POST'])
def generate_story():
    global chapter_summaries, character_dict, current_chapter, user_choices
    story_response = generate_story2()  # Get story text quickly
    return story_response  # Send story to frontend


@app.route('/generate-summary-and-image', methods=['POST'])
def generate_summary_and_image():

    global character_dict
    data = request.json
    story = data.get('story', '')

    # Process summary
    summary_func(story, current_chapter)

    # Generate image in a separate request
    image_url = generate_picture(story)

    return jsonify({'image': image_url, 'chapter': current_chapter})

# API route to generate the story
def generate_story2():
    global chapter_summaries, character_dict, current_chapter, user_choices
    
    data = request.json
    prompt = data['prompt']

    # SESSION
    current_chapter = get_current_chapter()
    user_choices = get_user_choices()
    chapter_summaries = get_chapter_summaries()


    # Retrieving user's last choice (if any)
    previous_choice = data.get('previous_choice', None)  
    
    # Identifying the current beat the story follows based on the currrent chapter 
    phase = get_phase_by_chapter(current_chapter)

    # Appending previous user's choices to the list 
    if previous_choice is not None:
        user_choices.append(previous_choice)
    print(phase)
    
    # Checking current chapter
    print("CURRENT CHAPTER: ",current_chapter)

    #Checking user's previous choice
    #last_user_choice = user_choices[-1] if user_choices else "No choice made."
    print("LAST_USER_CHOICE", previous_choice)


# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# Based on the current chapter the story is to follow a particular beat of the Hero's Journey Story Structure 
# -------------------------------------------------------------------------------------------------------------------------------------------------------#

    # First beat of the Hero's Journey Story Structure
    # ACT 1
    # Ordinary World
    if phase == "Ordinary World":
        user_content = (
            f"Write the next chapter in the story based on this input: {prompt}. "
            "This chapter is part of the 'Ordinary World' phase, where the reader is introduced to the protagonist’s daily life before any major conflict begins. "
            "Write 500-700 words focusing on the following points: "
            "1. Describe the protagonist’s surroundings with sensory-rich details that highlight the world’s mood, culture, and atmosphere. Include specific sounds, smells, or textures when possible. "
            "2. Highlight the protagonist’s routine or habits, showing what a typical day looks like. Focus on actions that reveal key aspects of their personality. "
            "3. Show subtle hints of the protagonist’s internal conflict or desires. Use interactions with other characters or reflective thoughts to convey what they yearn for or what frustrates them. "
            "4. Include a brief interaction with a secondary character (friend, family member, or rival) that helps deepen the reader’s understanding of the protagonist’s relationships. "
            "5. Describe the stakes of the protagonist’s current life and what they might risk losing if change disrupts their world. "
            "Make sure to expand on descriptions and actions instead of summarizing, providing depth to the setting, characters, and mood. "
        )
        options_start = "In the end of the chapter on a new line wrtie the folowing: A) [Continue]"
        #current_chapter += 1

    # -----------------------------------------------------------------------------------#
    # Second beat of the Hero's Journey Story Structure
    # ACT 1
    # Call to Adventure
    elif phase == "Call to Adventure":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)

        previous_summary = session.get("chapter_summaries", {}).get(str(previous_chapter), {}).get("summary", "")
        carryover_text = session.get("chapter_summaries", {}).get(str(previous_chapter), {}).get("carryover", "")

        print("Previous summary: ", previous_summary)
        print("Carryover Text: ", carryover_text)
       
        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "IMPORTANT INSTRUCTIONS:\n"
            "- Ensure the transition between the last chapter and this chapter is **seamless**. If the last chapter ended with action (e.g., jumping, running, speaking), continue it **fluidly** instead of reintroducing the setting.\n"
            "- If a conversation was unfinished in the last chapter, **continue it immediately** instead of resetting the scene.\n"
            "- Carry over any **lingering emotions, warnings, or thoughts** from the previous chapter. If another character gave advice or a warning, let the protagonist reflect on it **before shifting focus**.\n"
            "- If a new mystery or tension (like an unusual event, magical sign, or enemy presence) was introduced in the last chapter, **connect it naturally to the protagonist’s next steps** instead of making it feel random.\n"
            "- Only introduce a setting description if the scene **physically changes**. Otherwise, continue where the story left off.\n"
            "- If the protagonist is facing a decision (e.g., whether to enter a dangerous place or interact with a mysterious figure), allow **internal conflict** before proceeding.\n"
            "\n"
            "This chapter 2 is part of the 'Call to Adventure' phase. Focus on including a selection of the following points where applicable:\n"
            "1. Present a situation, event, or discovery that disrupts the protagonist’s normal life and demands their attention.\n"
            "2. Highlight how the call reveals a goal or mission that the protagonist cannot ignore, such as a threat, mystery, or opportunity.\n"
            "3. Emphasize the stakes involved, showing the potential consequences of accepting or rejecting the call.\n"
            "4. Incorporate natural dialogue or interactions that highlight the protagonist’s initial reaction to the call.\n"
            "5. Use vivid descriptions to emphasize the emotional impact of the call, whether it evokes fear, excitement, or confusion.\n"
            "6. Include subtle hints that suggest the protagonist’s life will change drastically if they choose to embark on this journey.\n"
            "\n"
            "**Ensure that any ongoing dialogues from the previous chapter are continued fully and not cut off.** If a conversation was started, make sure it is naturally carried over without abrupt resets or unnecessary exposition.\n"
            "\n"
            "End the chapter with 2-3 choices that allow the reader to decide how the protagonist reacts to the call and how the story progresses.\n"
            "Format the choices like this: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]."
            "IMPORTANT!! Make sure to include those choices in the given format and in ONE parapgraph"
        )

        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "
    
    # -----------------------------------------------------------------------------------#
    # Third beat of the Hero's Journey Story Structure
    # ACT 1
    # Refusal of the Call
    elif phase == "Refusal of the Call":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)


        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "IMPORTANT INSTRUCTIONS:\n"
            "- The protagonist **rejects the adventure**, whether out of fear, doubt, or external obstacles.\n"
            "- Show their **internal struggle**—what emotions or risks make them hesitate?\n"
            "- Highlight **how their refusal impacts others** (disappointed allies, frustrated mentors, emboldened enemies, etc.).\n"
            "- Their refusal should feel **real but not final**—there should be **doubt lingering** in their decision.\n"
            "- Introduce **external pressure** (e.g., a growing threat, fate pushing them forward, personal stakes increasing).\n"
            "\n"
            "This chapter 3 is part of the 'Refusal of the Call' pahse of the Hero's Journey Story Structure"
            "**Maintain continuity by naturally carrying over emotions, dialogue, and tensions from the previous chapter.**\n"
            "\n"
            "End the chapter with 2-3 choices reflecting their reluctance and potential reconsideration:\n"
            "Format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]."
        )

        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Fourth beat of the Hero's Journey Story Structure
    # ACT 1
    # Meeting the mentor 
    elif phase == "Meeting the Mentor":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "In this 4 chapter, the protagonist encounters a **mentor figure** who offers wisdom, skills, or guidance.\n"
            "\n"
            "Key elements to include:\n"
            "- The mentor’s **unique personality and teaching style** (kind, strict, mysterious, reluctant, deceptive, etc.).\n"
            "- The protagonist’s **skepticism or curiosity** toward their guidance.\n"
            "- One **important lesson, skill, or tool** the protagonist gains.\n"
            "- A **philosophical or emotional moment** where the protagonist starts shifting their perspective.\n"
            "- Foreshadowing of **greater challenges ahead**, hinting at the dangers of their journey.\n"
            "\n"
            "**Ensure a smooth transition from the last chapter by maintaining any unresolved emotions, dialogue, or conflicts.**\n"
            "\n"
            "End the chapter with 2-3 choices that reflect the protagonist’s response to the mentor’s guidance.\n"
            "Format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]."
        )

        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Fifth beat of the Hero's Journey Story Structure
    # ACT 1
    # Crossing the First Threshold
    elif phase == "Crossing the First Threshold":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "In this 5 chapter, the protagonist reaches the **final moment before stepping into the unknown**.\n"
            "\n"
            "Key elements to include:\n"
            "- **Emphasize hesitation or preparation**: The protagonist must decide whether they are truly ready.\n"
            "- **One last challenge, warning, or obstacle**: Something makes them reconsider (a conversation, an enemy appearing, a vision, etc.).\n"
            "- **Contrast their old world with the unknown ahead**: The safety of what they know vs. the uncertainty of what lies beyond.\n"
            "- **Ominous signs or foreshadowing**: The world hints that they are about to step into something dangerous or life-changing.\n"
            "- **The moment of no return**: The protagonist either takes a **physical action** (e.g., stepping through a portal, crossing a bridge, breaking a law) or an **internal resolution** (deciding they are committed).\n"
            "\n"
            "**Ensure continuity by carrying over emotions, tension, and choices from the previous chapter.**\n"
            "\n"
        )

        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Sixth beat of the Hero's Journey Story Structure
    # ACT 2
    # Tests, Allies, Enemies - Part 1
    elif phase == "Tests":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The protagonist has now stepped further into the **extraordinary world** of their journey. In this chapter, they will experience their **first true test**, one that pushes them to their limits and makes them realize how unprepared they are.\n"
            "\n"
            "**Key elements to include:**\n"
            "- **An Unfamiliar and Dangerous Environment**: The protagonist finds themselves in a setting that feels overwhelming, filled with **hidden dangers, strange rules, or unfamiliar customs**.\n"
            "- **A Challenge They Must Overcome Alone**: This could be a **physical trial (a fight, an escape, an endurance test)**, a **mental test (solving a riddle, navigating a trap)**, or an **emotional/internal struggle (facing a personal fear, dealing with self-doubt, or resisting temptation)**.\n"
            "- **Failure or Near-Failure**: The protagonist **struggles greatly**. They might barely succeed or fail in some way, reinforcing that they are not yet ready for this world.\n"
            "- **A Hint That They Need Help**: Through this test, the protagonist realizes they **can't do this alone**. They need guidance, allies.\n"
            "- **Foreshadowing of Allies and Enemies**: The trial should subtly introduce the presence of **others in this world**—figures watching, unknown forces at play, or hints of future relationships.\n"
            "\n"
            "**Ensure continuity by carrying over the protagonist’s personality, emotions, and choices from the previous chapter. Let this challenge impact them, making them doubt, struggle, or barely survive—so that when help arrives later, it feels meaningful.**\n"
        )


        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "


    # -----------------------------------------------------------------------------------#
    # Sixth beat of the Hero's Journey Story Structure
    # ACT 2
    # Tests, Allies, Enemies - Part 2
    elif phase == "Allies":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "After barely surviving their first major test, the protagonist is left exhausted, vulnerable, and possibly wounded. At this moment, they encounter **someone unexpected**—a figure who offers help but may have their own motives.\n"
            "\n"
            "**Key elements to include:**\n"
            "- **A tense first meeting**: The protagonist and this new character don’t immediately trust each other. There may be suspicion, hesitation, or even hostility at first.\n"
            "- **Hints about the new world**: Through dialogue or actions, the ally provides key insights into this unfamiliar world and what the protagonist is up against.\n"
            "- **A small but meaningful exchange**: Whether it’s **healing a wound, offering shelter, giving advice, or testing the protagonist’s resolve**, something happens to establish a fragile connection.\n"
            "- **A choice to be made**: By the end of the chapter, the protagonist must decide—**do they go with this person, or part ways?**\n"
            "\n"
            "**Ensure continuity by carrying over the protagonist’s emotional and physical state after their first test. They might be too exhausted to argue, too proud to accept help, or too cautious to trust right away. Their personality should shape this first alliance.**\n"
        )


        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Sixth beat of the Hero's Journey Story Structure
    # ACT 2
    # Tests, Allies, Enemies - Part 3
    elif phase == "Enemies":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The protagonist has begun to form a fragile alliance with someone new—but before they can fully decide whether to trust them, **a threat emerges**. This chapter introduces the first major sign of **an enemy, a rival, or an obstacle that stands in their way**.\n"
            "\n"
            "**Key elements to include:**\n"
            "- **A first glimpse of danger**: This could be a **direct confrontation, a warning, or an eerie sign** that someone (or something) is watching them.\n"
            "- **A moment of tension**: The protagonist and their ally may be forced into **a chase, a fight, or a stealthy escape**.\n"
            "- **A lesson in survival**: Whether they win, lose, or run, this experience teaches the protagonist something critical—about their **enemy, the world, or their own weaknesses**.\n"
            "- **Raising the stakes**: By the end of this chapter, the protagonist should feel a **sense of urgency**—they can’t stay in one place forever, and danger is growing closer.\n"
            "\n"
            "**Ensure continuity by making the protagonist's reaction consistent with their past experiences. If they failed their first test, they may hesitate or be afraid. If they succeeded, they may be overconfident and underestimate this new danger. Either way, this encounter should push them forward.**\n"
        )


        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Seventh beat of the Hero's Journey Story Structure
    # ACT 2
    # Approach to the Inmost Cave
    elif phase == "Approach to the Inmost Cave":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The protagonist and their allies have survived their first challenges, but the path ahead is far more dangerous. They now prepare to **enter the most perilous part of the journey**, where their enemy's presence is strongest and the risk of failure is highest.\n"
            "\n"
            "**Key elements to include:**\n"
            "- **A Dangerous Objective**: The protagonist and their allies must decide **how to approach the next major challenge**—a heavily guarded fortress, an ancient ruin, a cursed forest, or another setting that represents deep danger.\n"
            "- **Tension & Doubt**: The protagonist **or their allies may question the plan**—is this really the right move? Someone might want to turn back.\n"
            "- **The Enemy’s Influence Grows**: The group sees **signs of the antagonist’s power**—perhaps a **destroyed village, an ambush, or a supernatural occurrence** that reminds them they are stepping into their enemy’s domain.\n"
            "- **A Personal Moment for the Hero**: Before the final push, the protagonist should have a **moment of introspection**—what fears or doubts still haunt them? Are they truly ready?\n"
            "- **The Plan Is Set**: By the end of the chapter, the protagonist and their allies have **a strategy**, but there should be a sense that **things will not go as expected**.\n"
            "\n"
            "**Ensure continuity by keeping the protagonist’s emotional and mental state in focus. Their fears, doubts, or overconfidence will shape how they approach this moment. Let the world feel ominous—this is the moment where it becomes clear that they are stepping into a place of true danger.**\n"
        )

        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Eight beat of the Hero's Journey Story Structure
    # ACT 2
    # Ordeal - Part 1
    elif phase == "Ordeal Part1":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The protagonist and their allies now step directly into the enemy’s domain, believing they are prepared—but nothing can prepare them for what’s ahead. \n"
            "\n"
            "**Key elements to include:**\n"
            "- **The Plan Begins**: The group follows through on their strategy, whether it’s infiltrating, ambushing, or sneaking past danger.\n"
            "- **An Ominous Feeling**: Something feels wrong. Small signs hint that **this won’t go as planned**—maybe they’re being watched, or an ally is acting strangely.\n"
            "- **The False Victory**: At first, it seems like **they’re succeeding**—they get through the gates, bypass the guards, or make it to their goal.\n"
            "- **The Unexpected Turn**: Just as they think they have the upper hand, something **horribly wrong happens**—an **ambush, a betrayal, or a deadly revelation**.\n"
            "- **The Moment of Despair**: By the end of the chapter, the protagonist and their allies **realize they’re trapped, divided, or in mortal danger**—setting up the true Ordeal.\n"
            "\n"
            "**Ensure continuity by making the protagonist react naturally to this shift. Overconfidence should turn into fear, trust should be tested, and the stakes should feel real. The reader must believe that the protagonist has truly stepped into the abyss.**\n"
        )

        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Eight beat of the Hero's Journey Story Structure
    # ACT 2
    # Ordeal - Part 2
    elif phase == "Ordeal Part2":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The protagonist’s worst fears have come true. They were not ready for what awaited them in the enemy’s domain, and now, everything is falling apart.\n"
            "\n"
            "**Key elements to include:**\n"
            "- **The Trap is Fully Revealed**: The protagonist and their allies are completely overwhelmed—outnumbered, surrounded, or betrayed.\n"
            "- **A Devastating Loss**: Something irreplaceable is taken—an ally, a sacred object, or the protagonist’s faith in themselves.\n"
            "- **The Hero’s Darkest Moment**: They feel truly alone. The world feels colder, and they see no way out.\n"
            "- **A Choice Must Be Made**: When everything is at its worst, the protagonist must decide—**will they give in to fear, or will they fight?**\n"
            "\n"
            "**By the end of this chapter, the protagonist should feel like they have lost everything. Only through this suffering can they be reborn into the hero they were meant to be.**\n"
        )


        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Eight beat of the Hero's Journey Story Structure
    # ACT 2
    # Ordeal - Part 3
    elif phase == "Ordeal Part3":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The protagonist has reached their breaking point—but this time, they refuse to back down. This is the moment they have been preparing for, the moment where everything changes. \n"
            "\n"
            "**Key elements to include:**\n"
            "- **The Enemy’s True Power is Revealed**: The protagonist finally understands the full danger they are up against.\n"
            "- **The Battle is Physical, Emotional, and Psychological**: The fight is not just about strength—it’s about strategy, resilience, and the hero’s growth.\n"
            "- **A Crushing Setback**: The enemy lands a devastating blow—whether physically, emotionally, or through betrayal.\n"
            "- **The Turning Point**: Against all odds, the protagonist finds the key to victory, proving they have changed since the beginning of their journey.\n"
            "- **The Enemy is Defeated—But Not Fully Erased**: The villain is brought down, but **something lingers**—an escape, a dark prophecy, or a foreshadowing that this battle is not the end.\n"
            "- **Victory Comes at a Cost**: The protagonist wins, but they leave something behind—whether it’s an ally, a part of their identity, or the safety they once knew.\n"
            "\n"
            "**This is the moment where the protagonist becomes a true hero. Their journey is far from over, but this battle defines who they will be from now on.**\n"
        )

        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Nine beat of the Hero's Journey Story Structure
    # ACT 2
    # Reward
    elif phase == "Reward":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The battle is over. The dust settles, and for the first time, the protagonist truly grasps what they have been fighting for. They have won—but what have they really gained?\n"
            "\n"
            "**Key elements to include:**\n"
            "- **The Immediate Aftermath**: The battlefield is silent, the enemy is fallen, and the protagonist can finally breathe.\n"
            "- **The True Reward is Revealed**: Whether it’s a powerful object, a hidden truth, or personal growth, it’s not just what they expected—it’s something more.\n"
            "- **An Emotional Moment**: The protagonist processes everything—victory, loss, and what comes next.\n"
            "- **A Quiet Before the Storm**: There’s a moment of relief, but deep down, something **feels unfinished**—the enemy may be gone, but **the journey isn’t truly over.**\n"
            "\n"
            "**Make this moment feel earned. The protagonist should understand the weight of what they’ve gained, and the reader should feel both satisfaction and a hint of what’s to come.**\n"
        )

        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Tenth beat of the Hero's Journey Story Structure
    # ACT 3
    # The Road Back
    elif phase == "The Road Back":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The battle is over. The protagonist and their allies, weary but victorious, begin their journey home. However, the cost of their fight weighs heavily on them, and something feels off—**a shadow still lingers**. As they move forward, they sense that this journey won’t be as easy as they hoped.\n"
            "\n"
            "**Key elements to include:**\n"
            "- **The Journey Begins**: The protagonist and their allies, battered but triumphant, set off toward home.\n"
            "- **The Price of Victory**: The protagonist reflects on the cost of the battle—lives lost, wounds endured, or changes in themselves they can’t undo.\n"
            "- **A Lingering Threat**: Something feels wrong—maybe the enemy **isn’t truly gone**, or the world around them has **shifted in an ominous way**.\n"
            "- **The Pursuit Begins**: Just as they think they are safe, they realize the enemy’s forces **aren’t done yet**—they are being hunted.\n"
            "\n"
            "**The chapter should feel like a transition—giving the protagonist and the reader a moment to breathe before tension rises again. The journey home has begun, but something is waiting in the shadows.**\n"
        )


        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Eleventh beat of the Hero's Journey Story Structure
    # ACT 3
    # Resurrection
    elif phase == "Resurrection":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "This is it. The final battle. The enemy has pushed the protagonist to their breaking point, and now **they must face their greatest test of all**. Everything they have learned, every choice they have made, has led to this moment.\n"
            "\n"
            "**Key elements to include:**\n"
            "- **The True Ordeal Begins**: The protagonist **and the antagonist clash** in their final, most brutal confrontation.\n"
            "- **The Darkest Hour**: The protagonist **is nearly defeated**. Perhaps they are injured, captured, or facing **overwhelming odds**.\n"
            "- **The Moment of Resurrection**: Just when it seems **all hope is lost**, the protagonist **rises again**—transformed by their journey.\n"
            "- **The Final Strike**: Using what they’ve learned, the protagonist **lands the final blow**—but victory **comes at a cost**.\n"
            "- **The Aftermath**: The battle is won, but **something has changed**. The protagonist **is no longer the same person who first set out on this journey**.\n"
            "\n"
            "**The chapter should feel like the true climax of the story. The protagonist must face not only the enemy, but their own deepest fears, proving they have truly earned the title of ‘Hero.’**\n"
        )


        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Twelfth beat of the Hero's Journey Story Structure
    # ACT 3
    # Return with the Elixir - Part 1
    elif phase == "Return with the Elixir Part1":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The battle is over. The protagonist and their allies finally set out on the journey home. But something is different now—the world they left behind no longer feels the same. Victory has come at a cost, and as they retrace their steps, they begin to **feel the weight of all they have lost, and all they have gained.**\n"
            "\n"
            "**Key elements to include:**\n"
            "- **The Aftermath of the Battle**: The dust has settled, and the protagonist sees **the consequences of their fight**—whether it’s the ruins left behind, the scars they now carry, or the memories that haunt them.\n"
            "- **The Journey Feels Different**: What once felt like an adventure now feels like **the closing of a chapter**. They return **not as the person who left, but as someone changed forever**.\n"
            "- **Revisiting Old Places, Now Changed**: As they make their way home, they pass **places that once felt significant**—but now, those places feel smaller, distant, or different.\n"
            "- **The Final Reflection**: The protagonist glances back at where they have been, knowing **they will never see the world the same way again**.\n"
            "\n"
            "**This chapter should focus on the weight of victory and the quiet realization that the journey is truly coming to an end. The protagonist should begin to understand what they will bring back with them—and what they have left behind.**\n"
        )

        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "

    # -----------------------------------------------------------------------------------#
    # Twelfth beat of the Hero's Journey Story Structure
    # ACT 3
    # Return with the Elixir - Part 2
    elif phase == "Return with the Elixir Part2":

        # Getting previous chapter
        previous_chapter = current_chapter-1
        print("CHAPTER - 1", previous_chapter)


        previous_summary = chapter_summaries.get(f"{previous_chapter}", {}).get("summary", "")
        carryover_text = chapter_summaries.get(f"{previous_chapter}", {}).get("carryover", "")

        #print("Previous summary: ", previous_summary)
        #print("Carryover Text: ", carryover_text)

        user_content = (
            f"Write the next chapter in the story based on this input:\n"
            f"Summary of the previous chapter: {previous_summary}.\n"
            f"To ensure continuity, here is the most important passage from the last chapter, including any necessary dialogue for smooth transitions:\n\n{carryover_text}\n\n"
            f"The user's last choice was: {previous_choice}.\n"
            "\n"
            "The journey is over. The protagonist **returns to the world they once called home**—but everything has changed. They bring with them the **Elixir**—the knowledge, power, or object that will forever alter their destiny. But home no longer feels like home, and the person who left is not the one who returns.\n"
            "\n"
            "**Key elements to include:**\n"
            "- **Crossing the Final Threshold**: The protagonist steps back into the world they left, seeing it with **new eyes**.\n"
            "- **Seeing Home as a Stranger**: What was once familiar now feels **smaller, different, or distant**. They are **no longer the same**.\n"
            "- **Bringing the Elixir**: Whether it’s **a magical artifact, wisdom, newfound power, or a personal transformation**, the protagonist **must decide what to do with it**.\n"
            "- **A New Path Awaits**: While this is the end of one journey, **another may yet begin**.\n"
            "\n"
            "**This chapter should bring the story full circle, showing how the protagonist has changed and what they have brought back with them. It should feel like both an ending and the possibility of a new beginning.**\n"
        )


        options_start = "3) Each chapter must be at least 600 words long and should end with 2-3 choices for the userin this format: A) [Option 1] B) [Option 2] C) [Option 3, if applicable]. "


# -------------------------------------------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------------------------------------------#


# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# Creates a chapter of the story along with choices to direct the nerrative
# -------------------------------------------------------------------------------------------------------------------------------------------------------#
    # Call OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Better suited for nuanced storytelling
        messages=[
            {
            "role": "system",
            "content": (
                "You are an assistant skilled at writing long, immersive stories structured like novels. "
                "Each chapter should be detailed and contribute to a multi-chapter narrative arc. "
                "Do include dialogs between characters, making sure that the story is more engaging"
                "The story should follow this structure: "
                "1) Early chapters focus on world-building, character development, and setting up the central conflict. "
                "2) The main conflict or action described in the user's input should not occur until at least the fifth chapter. "
                f"{options_start}"
                "Make sure to write all of the options in a given format and in ONE paragraph"
                "Ensure the pacing feels natural, with gradual tension-building leading to a climactic resolution. "
                "Stop writing after presenting the choices, and do not advance the story further until directed by the user."
            )
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
        max_tokens=3600,
        temperature=0.7
    )

    # Extract story text from the response
    story = response['choices'][0]['message']['content']
    print("STORY: ", story)

    # Update session state
    set_current_chapter(current_chapter + 1)  # Move to the next chapter

    # -------------------------------------------------------------------------#
    # Manages the dictionary with the possible choices for directing the nerrative + prints all of those choices 
    # -------------------------------------------------------------------------#  
    choices = parse_choices(story)
    print ("Choices: ", choices)
    # Split the story into paragraphs
    paragraphs = story.split('\n\n')

    # A data structure to hold a story together with the related picture
    paragraphs_to_chunk = "<br><br>".join(paragraphs[:-1])  # Keep all paragraphs, except the last one
    story = paragraphs_to_chunk
    return jsonify({'story': story, 'choices': choices})  # Wrap in dict



# -------------------------------------------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------------------------------------------#

    # -------------------------------------------------------------------------#
    # Summarises the current chapter of the story and Creates/Updates Dictionary that contain Appernace of characters
    # -------------------------------------------------------------------------#

def summary_func(story,current_chapter):
    global character_dict

        
    # Get the current chapter from session
    current_chapter = get_current_chapter()
    current_chapter1 = current_chapter - 1

    chapter_summary, carryover_text = summarize_chapter(story)

    update_chapter_summary(current_chapter1, chapter_summary, carryover_text)
    # Prints the current summary of the chapter
    #print("SUMMARY OF STORY", chapter_summaries[f"{current_chapter}"]["summary"])
    # Prints the current number of the chapter
    #print("CHAPTER NUMBER", current_chapter)
    # Prints the carryover passage that will be used in the next chapter
    #print("CARRYOVER PASSAGE", chapter_summaries[f"{current_chapter}"]["carryover"])
    # Prints the entire dictionary containing all summaries and carryover passages
    #print("SUMMARY DICTIONARY", chapter_summaries)

# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# Based on the contents of the characters dictionary, an appropriate prompt is to be chosen to be passed to OPenAI API call
# -------------------------------------------------------------------------------------------------------------------------------------------------------#

    if len(character_dict) == 0:
        analysis_prompt = (
            f"Based on the following prompt only: {story}, in format number Name:description! role. identify main characters, their appearance and the role, including vilians. "
            "THE MOST IMPORTANT INSTRUCTIONs:"
            "IMPORTANT!!!! Make sure that it is in format number Name:description!   DO NOT USE ANY OTHER FORMAT, DO NOT USE SYMBOLS LIKE *"
            "The description of appearance should include a really detailed description of how each character looks"
            "Make sure that in description you only include the appearance of the character, nothing else. "
            "IMPORTANT!! Make sure to include only the character's color of eyes, hair color, length of hair, skin color, the outfit they wearing and the accessories, nothing else"
            "Also to appearance description please add some details from yourself, for example, give a detailed infromation about the outfit the character wearing, the hairstyle, the color of face and so on "
            "Make sure the description is AT LEAST 100 CHARACTERS LONG"
        )
    else: 
        analysis_prompt = (
            f"Based on the following prompt only: {story}, in format number Name:description! role. "
            f"Identify any new characters not already present in this list: {character_dict} "
            "For any new characters, describe their appearance and role, including villains. "
            "Make sure that it is in format: number Name:description! role. "
            "The description of appearance should include a really detailed description of how each character looks. "
            "Make sure that in the description you only include the appearance of the character, nothing else. "
            "Include only the character's eye color, hair color, hair length, skin color, the outfit they are wearing, and accessories—nothing else. "
            "Also, in the appearance description, add some details yourself; for example, give detailed information about the outfit, hairstyle, and facial color. "
            "Make sure the description is AT LEAST 100 CHARACTERS LONG."
    )
        
# -------------------------------------------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------------------------------------------#


# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# Extracts character names, descriptions, and roles from the story.
# -------------------------------------------------------------------------------------------------------------------------------------------------------#

    # Call OpenAI API to extract the characters' names, their appearance from the generated chapter of the story
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-4"
        messages=[
            {
                "role": "system",
                "content": 'You are an assistant who helping to extract the name and the description of each character in the story, and their role'
            },
            {
                "role": "user",
                "content": analysis_prompt
            }
        ],
        max_tokens=800,
        temperature=0.5
    )

    character_data_raw = response['choices'][0]['message']['content']

    # Prints all the identified characters from the chapter
    print("Character Data Raw:", character_data_raw)

    # Creates a dictionary from the identified characters from the chapter
    character_dict = characters_extraction.parse_character_data(character_data_raw)

# -------------------------------------------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------------------------------------------#


# -------------------------------------------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------------------------------------------#


# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# Generating illustrations for the story 
# -------------------------------------------------------------------------------------------------------------------------------------------------------#

def generate_picture(paragraphs_to_chunk):
    
    global  character_dict

    # Prompt for scene generation
    scene_prompt = (
        "From the following chapter, extract the **most important and visually striking scene**. "
        "Choose the scene that best represents the chapter's key moment—whether it's a pivotal action, an intense emotional exchange, or a dramatic event. "
        "Ensure the scene captures the heart of the chapter, prioritizing moments of tension, discovery, conflict, or transformation. "
        "IMPORTANT! Make sure to include the names of the characters that are to appear in the scene"
        "\n\n"
        f"Full Chapter:\n{paragraphs_to_chunk}\n\n"
        "Now, extract the single most important scene and describe it with vivid details:\n"
        "- Focus on the **setting, atmosphere, characters' actions, and emotions**.\n"
        "- Ensure the main characters are in dynamic, contextually appropriate poses, interacting with objects or their surroundings.\n"
        "- Avoid describing **how the characters look** (no details on eyes, hair, clothing, or appearance).\n"
        "- Emphasize the **interaction between the characters and their environment**.\n"
        "- Provide a **brief description of the background** to add depth to the scene.\n"
        "- **Limit the description to no more than 150 characters** while ensuring the scene is compelling and immersive."
    )


# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# Generates a scene based on the story 
# -------------------------------------------------------------------------------------------------------------------------------------------------------#
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-4"
        messages=[
            {
                "role": "system",
                "content": 'You are an assistant who helping me to extract a specific scene from the text, that captivates the details and the atmosphere'
            },
            {
                "role": "user",
                "content": scene_prompt
            }
        ],
        max_tokens=500,
        temperature=0.5
    )

    scene = response['choices'][0]['message']['content']
    print(" \n Scene", scene, "\n")

# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# 
# -------------------------------------------------------------------------------------------------------------------------------------------------------#
    
    # Build a prompt including existing character descriptions if available
    relevant_names = extract_character_names_from_scene(scene, character_dict)
    characters_involved_in_scene = build_character_description_prompt_for_scene(scene, character_dict, relevant_names)

    # Creates a prompt for generating the scene with relevant characters
    truncated_prompt = (
        f"Create a vivid and action-packed illustration based on the following scene: '{scene}'. "
        f"Ensure that the characters involved in scene are shown in dynamic, action-driven poses. "
        f"Use the following character descriptions to accurately depict their appearances and ensure they are fully integrated into the scene: {characters_involved_in_scene}. "
        "The scene should showcase their interactions and emotions during the action. "
        "Do not include any characters that were not mentioned, unless the background of the scene involves some characters like humans"
        "The illustration should have a cinematic, dramatic feel with rich lighting, vivid colors, and detailed backgrounds. "
        "Ensure that the characters' actions are at the forefront and the background adds depth, but the focus remains on the interaction between the characters. "
        ##"The final image should capture characters appearance and their emotions, and the grandeur of the moment, without any text, numbers, or symbols."
    )

    #print(" \n Truncated prompt:", truncated_prompt )


# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# Generates illustrations for the story 
# -------------------------------------------------------------------------------------------------------------------------------------------------------#

    response = openai.Image.create(
        
        model="dall-e-3",
        prompt=truncated_prompt,
        n=1,
        quality="hd",
        style = "vivid",
        size="1024x1024"
    )
    image_url = response['data'][0]['url']
    
    return image_url

# -------------------------------------------------------------------------------------------------------------------------------------------------------#
# 
# -------------------------------------------------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':
    app.run(debug=True)
