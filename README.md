<a name="readme-top"></a>
<div align="center">
  <a href="https://github.com/ElizavetaMikheeva/ai-storyteller">
    <img width="484" alt="image" src="https://github.com/ElizavetaMikheeva/ai-storyteller/blob/main/static/images/new_logo.png">
    
  </a>

<h3 align="center"> Chrona </h3>

  <p align="center">
    Chrona. Interactive AI Storyteller with Visuals & User-Driven Choices
    <br/>
  </p>
</div>

---
<!-- TABLE OF CONTENTS -->

## Table of Contents:

  <ol>
    <li><a href="#project-overview">Project Overview</a> </li>
    <li><a href="#key-features">Key Features </a></li>
    <li><a href="#technologies-used">Technologies Used</a></li>
    <li><a href="#app-preview">App Preview</a></li>
    <li> <a href="#project-structure">Project Structure</a> </li>
    <li> <a href="#setup-instructions">Setup Instructions</a> </li>
    <li> <a href="#future-improvements-to-be-made">Future improvements to be made</a> </li>
    <li><a href="#disclaimer">Disclaimer</a></li>
    <li><a href="#author">Author</a></li>
  </ol>

---

<!-- Project Overview -->

### Project Overview

This project is an AI-driven interactive storytelling web application developed as part of my final-year dissertation. It allows users to create their own dynamic stories by submitting a prompt and making choices as the narrative progresses. Each story unfolds chapter by chapter, accompanied by AI-generated illustrations to enhance the experience.

The app simulates a digital book, offering a visually rich and engaging format. By combining text generation, image synthesis, and user nteraction, the project explores how generative AI can be used to support creativity and narrative immersion.

---

<!-- Key Features -->

### Key Features

<li> Prompt-based storytelling: Users enter their own story idea to begin a custom narrative. </li>
<li> Branching storylines: Stories evolve based on user choices at key moments. </li>
<li> AI-generated illustrations: Each chapter includes unique visuals created with the help of AI. </li>
<li> Chapter-to-chapter continuity: Characters and story elements carry over between chapters for a cohesive plot. </li>

 <p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- App Preview -->

## App Preview


To see how Chrona works, please follow the link below to watch a short video that demonstrates its main features and output: 
https://youtu.be/RfLT3vof4zU


----

<!-- Technologies Used -->

### Technologies Used

<li> Backend: Python (Flask) </li>
<li> Frontend: HTML, CSS, JavaScript </li>
<li> AI APIs: OpenAI GPT-4 / GPT-3.5-Turbo, DALL-E 3 </li>
<li> Session Management: Flask session </li>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- Project Structure -->

## Project Structure

 . ├── static/ │ ├── css/ │ ├── images/ │ └── js/ ├── templates/ │ └── index.html ├── app.py ├── characters_extraction.py ├── requirements.txt ├── README.md 

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- Setup Instuctions -->

## Setup Instructions

1. Clone the Repository
   - git clone https://github.com/your-username/interactive-ai-storyteller.git
2. Install Dependencies
   - pip install -r requirements.txt
3. Add Your OpenAI API Key
   - Set your API key securely in app.py
4. Run the App
   - python app.py
5. Open http://127.0.0.1:5000 in your browser to start using an AI-Storyteller

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- Future improvements to be made -->

## Future improvements to be made

<li> Refine the page transition effect to more closely resemble the tactile, natural motion of flipping pages in a real book.</li>
<li> Ensure the application works seamlessly across all devices and screen sizes, including mobile phones and tablets.</li>
<li> Make the app more accessible.</li>
<li> Add text-to-speech feature, that would read the story to the user</li>
<li> Develop an interactive onboarding tutorial to guide new users through the application’s core features and storytelling process.</li>
<li>Enable users to save and organize their generated stories in a dedicated library, allowing them to revisit and manage past narratives within the application.</li>
<li>Introduce features that allow users to publish their stories, explore narratives created by others, and engage with a shared community archive for inspiration and feedback.</li>
<li>Add a button or section that shows ready-made prompts to inspire users and help them begin writing.</li>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- Disclaimer -->

## Disclaimer

This project was developed for educational and research purposes only as part of a university dissertation. **Commercial use, distribution, or resale of this application or its components is strictly prohibited.** All rights reserved by the author.

 <p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- Author -->

## Author

Author: Elizaveta Mikheeva

<p align="right">(<a href="#readme-top">back to top</a>)</p>
