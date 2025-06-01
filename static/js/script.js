// Developed by Elizaveta Mikheeva

document
  .getElementById("storyForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    document.getElementById("inputContainer").classList.add("hidden");
    document.getElementById("toggleInputButton").classList.remove("hidden");

    const prompt = document.getElementById("prompt").innerText.trim();
    const preloader = document.getElementById("preloader");

    // Minimise Navigation Bar
    document.getElementById("nav-toggle").checked = true;

    // Show the loding icon
    preloader.style.visibility = "visible";

    // "Expand the size" of the content wrapper
    let contentWrapper = document.getElementById("content-wrapper");
    contentWrapper.style.marginLeft = "var(--navbar-width-min)";

    // Call Generate Story function
    try {
      const storyResponse = await fetch("/generate-story", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt }),
      });

      if (!storyResponse.ok) throw new Error("Failed to fetch story");

      const storyData = await storyResponse.json();
      const storyText = storyData.story || "";
      const choicesDict = storyData.choices || {};

      console.log("Story Received:", storyText);
      console.log("Choices Received:", choicesDict);

      // Styling container for dispaying book pages
      let bookContainer = document.getElementById("bookContainer");
      bookContainer.style.display = "flex";
      bookContainer.style.flexDirection = "row";
      bookContainer.style.gap = "2rem";

      if (!bookContainer.hasChildNodes()) {
        bookContainer.innerHTML = "";
      }

      splitAndAppendText(storyText);

      // Make flipping page buttons visible
      let pagination = document.getElementById("pagination");
      pagination.style.visibility = "visible";

      fetchImageAfterStory(storyText, choicesDict);
      enableFlipping();
    } catch (error) {
      console.error("Error fetching story:", error);
    } finally {
      preloader.style.display = "none";
    }
  });

// Cheking whether the content that is generated of type string or other type (e.g., image)
function appendContent(target, content) {
  if (typeof content === "string") {
    target.innerHTML = content;
  } else if (content instanceof HTMLElement) {
    target.appendChild(content);
  }
}

// Splitting the generated text across two pages// Splitting the generated text across two pages
function splitAndAppendText(text) {
  let bookContainer = document.getElementById("bookContainer");
  let words = text.split(" ");
  let tempText = "";
  let wordIndex = 0;

  // Always create a new page-pair for the story
  let pagePair = document.createElement("div");
  pagePair.classList.add("page-pair");

  let leftPage = document.createElement("div");
  leftPage.classList.add("page", "story-text");

  let rightPage = document.createElement("div");
  rightPage.classList.add("page", "story-text");

  pagePair.appendChild(leftPage);
  pagePair.appendChild(rightPage);
  bookContainer.appendChild(pagePair);

  let currentPage = leftPage; // Start filling the left page first

  // Get the maximum height without causing overflow
  let maxHeight = leftPage.clientHeight;

  while (wordIndex < words.length) {
    let testText = tempText + words[wordIndex] + " ";
    currentPage.innerHTML = testText;

    // Check if adding this word causes overflow
    if (currentPage.scrollHeight > maxHeight) {
      // Revert to the previous text (before overflow)
      currentPage.innerHTML = tempText.trim();

      // Move to the next page
      if (currentPage === leftPage) {
        currentPage = rightPage;
      } else {
        // Create a new pair if the right page is also full
        let remainingText = words.slice(wordIndex).join(" ");
        createNewPage(remainingText, "", "story-text");
        return;
      }

      // Reset the temp text for the new page
      tempText = "";
    } else {
      // No overflow, so keep the current word
      tempText = testText;
      wordIndex++;
    }
  }

  // Apply styling to chapter title
  styleChapterTitle(leftPage);
}

// Function to Apply Styling to the First Paragraph (Chapter Title)
function styleChapterTitle(page) {
  let firstNode = page.childNodes[0]; // Get the first node inside the page

  if (firstNode && firstNode.nodeType === 3) {
    // Ensure it's a text node
    let span = document.createElement("span");
    span.classList.add("chapter-title");
    span.innerText = firstNode.nodeValue.trim(); // Keep original text
    span.textAlign = "center";

    page.replaceChild(span, firstNode); // Replace raw text with styled span
  }
}

// Function to Create Page Pairs
function createNewPage(leftContent, rightContent, className) {
  const bookContainer = document.getElementById("bookContainer");
  if (!bookContainer) {
    console.error("Cannot create a page: `bookContainer` does not exist.");
    return;
  }

  // Create a new page-pair if both pages are occupied
  const pagePair = document.createElement("div");
  pagePair.classList.add("page-pair");

  leftPage = document.createElement("div");
  leftPage.classList.add("page", className);

  rightPage = document.createElement("div");
  rightPage.classList.add("page", className);

  appendContent(leftPage, leftContent);
  appendContent(rightPage, rightContent);

  pagePair.appendChild(leftPage);
  pagePair.appendChild(rightPage);
  bookContainer.appendChild(pagePair);
}

// Automatically Place Images & Choices in Right Spot
function fetchImageAfterStory(storyContent, choicesDict) {
  // Call Generate Image Function
  fetch("/generate-summary-and-image", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ story: storyContent }),
  })
    .then((imageResponse) => {
      if (!imageResponse.ok) throw new Error("Failed to fetch image");
      return imageResponse.json();
    })
    .then((imageData) => {
      if (imageData.image) {
        let imageElement = document.createElement("img");
        imageElement.src = imageData.image;
        imageElement.alt = "Generated Image";
        imageElement.style.width = "95%";
        imageElement.style.height = "auto";
        imageElement.style.borderRadius = "0.5em";
        imageElement.style.boxShadow = "0 0 1.8em -0.3em #8b5a2b";

        let choicesContainer = showChoices1(choicesDict);

        // Append onto page pair generated image adn choices
        createNewPage(imageElement, choicesContainer, "image-page");
        enableFlipping();
      }
    })
    .catch((error) => console.error("Error fetching image:", error));
}

// Function to Show Choices as Buttons
function showChoices1(choicesDict) {
  let choicesContainer = document.createElement("div");
  choicesContainer.innerHTML = "";
  choicesContainer.style.margin = "0 auto";
  choicesContainer.style.display = "inline-block";
  choicesContainer.style.height = "100vh";
  choicesContainer.style.alignItems = "center";
  choicesContainer.style.alignContent = "center";
  choicesContainer.style.textAlign = "center";

  // Instructional Text Before Choices
  const instructionText = document.createElement("p");
  instructionText.className = "instruction-text";
  instructionText.innerText =
    "The story now stands at a turning point. Choose wisely, for your decision will shape the next chapter of this journey.";
  instructionText.style.fontSize = "1.2em";
  instructionText.style.fontWeight = "bold";
  instructionText.style.color = "#6B4226";
  instructionText.style.textAlign = "center";
  instructionText.style.marginBottom = "rem";

  choicesContainer.appendChild(instructionText);

  let selectedChoice = ""; // Stores the choice before generating
  let selectedButton = null; // Stores the currently active button

  Object.entries(choicesDict).forEach(([key, value]) => {
    const button = document.createElement("button");
    button.className = "choice-button";
    button.innerText = `${key} ${value}`;

    button.addEventListener("click", () => {
      if (selectedButton) {
        selectedButton.classList.remove("active"); // Remove active state from previous selection
      }

      button.classList.add("active"); // Apply active class to new selection
      selectedButton = button; // Store the selected button
      selectedChoice = key; // Store selected choice
    });

    choicesContainer.appendChild(button);
  });

  // Create "Generate" button
  const generateButton = document.createElement("button");
  generateButton.className = "generate-button";
  generateButton.innerText = "Continue";

  generateButton.addEventListener("click", () => {
    if (selectedChoice) {
      // Replace text with GIF while generating
      if (selectedButton) {
        selectedButton.classList.add("writing");
        selectedButton.innerHTML = `<img src="/static/images/loader2.gif" class="pen-gif" alt="Writing...">`; //
      }

      handleChoice(selectedChoice).then(() => {
        // Restore text of the button after chapter is generated
        if (selectedButton) {
          selectedButton.classList.remove("writing");
          selectedButton.innerText = `${selectedChoice} ${choicesDict[selectedChoice]}`;
        }
      });
    }
  });

  choicesContainer.appendChild(generateButton);
  return choicesContainer;
}

// Function to Reset Session (Start a New Story)
async function resetSession() {
  try {
    const response = await fetch("/reset-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const data = await response.json();
    console.log(data.message);
    alert("Session has been reset. You can start a new story.");

    // Clear frontend UI
    document.getElementById("bookContainer").innerHTML = "";
  } catch (error) {
    console.error("Error resetting session:", error);
  }
}

// Function to handle choices
function handleChoice(choice) {
  console.log("You selected:", choice);

  const currentStory =
    document.querySelector(".story-text")?.innerText.trim() || "";

  fetch("/generate-story", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: currentStory,
      previous_choice: choice,
    }),
  })
    .then((response) => {
      if (!response.ok) throw new Error("Failed to fetch next chapter");
      return response.json();
    })
    .then((data) => {
      const storyText = data.story || "";
      const choicesDict = data.choices || {};
      console.log("Story Received:", storyText);

      // First, add the text to a new page
      splitAndAppendText(storyText);

      // Allow automatic movement AFTER a choice is made
      allowMoveAfterChoice();

      // Move to the latest generated chapter (WITH flipping effect)
      setTimeout(() => {
        moveToLatestPageAfterChoice();
      }, 500);

      // Fetch images and choices, but DO NOT trigger movement
      return fetchImageAfterStory(storyText, choicesDict);
    })
    .then(() => {
      // Re-enable flipping after updating pages
      enableFlipping();

      // Restore original button text after new chapter is generated
      const selectedButton = document.querySelector(".choice-button.writing");
      if (selectedButton) {
        selectedButton.classList.remove("writing");
        selectedButton.innerText = `Chosen`;
      }
    })
    .catch((error) => {
      console.error("Error fetching story:", error);
    });
}

// Function to Toggle Input Visibility
document
  .getElementById("toggleInputButton")
  .addEventListener("click", function () {
    document.getElementById("inputContainer").classList.toggle("hidden");
    this.classList.toggle("flipped");
  });

// Function to flip the pages
function enableFlipping() {
  let pagePairs = document.querySelectorAll(".page-pair");
  let currentPage = pagePairs.length - 1;
  let firstTimeRendered = true;
  let moveAfterChoice = false;
  let manualFlip = false; // Track if the user manually flipped pages

  function showPage(index, direction, autoMove = false) {
    pagePairs.forEach((pair, i) => {
      let leftPage = pair.children[0];
      let rightPage = pair.children[1];

      if (i === index) {
        pair.style.display = "flex";

        if (index === 0 && firstTimeRendered) {
          // First chapter appears without flipping
          leftPage.style.transform = "none";
          rightPage.style.transform = "none";
          firstTimeRendered = false;
        } else {
          // Flip when moving to a new page manually OR after a choice
          animateFlip(pair, direction);
        }
      } else {
        pair.style.display = "none";
      }
    });

    if (autoMove) {
      moveAfterChoice = false;
      manualFlip = false; // Reset after automatic movement
    }
  }

  function animateFlip(pagePair, direction) {
    let leftPage = pagePair.children[0];
    let rightPage = pagePair.children[1];

    if (direction === "next") {
      rightPage.style.transformOrigin = "left center";
      rightPage.classList.add("flip-next");
      setTimeout(() => rightPage.classList.remove("flip-next"), 800);
    } else if (direction === "prev") {
      leftPage.style.transformOrigin = "right center";
      leftPage.classList.add("flip-prev");
      setTimeout(() => leftPage.classList.remove("flip-prev"), 800);
    }
  }

  // Function to automatically flip the page to newly generated
  function moveToLatestPageAfterChoice() {
    if (moveAfterChoice) {
      pagePairs = document.querySelectorAll(".page-pair");
      currentPage = pagePairs.length - 1;

      // Ensure flipping effect happens when moving to a new chapter
      showPage(currentPage, "next");
      animateFlip(pagePairs[currentPage], "next");
    }
  }

  window.moveToLatestPageAfterChoice = moveToLatestPageAfterChoice;

  function allowMoveAfterChoice() {
    moveAfterChoice = true;
    manualFlip = true; // Ensure movement was user-triggered
  }

  window.allowMoveAfterChoice = allowMoveAfterChoice;

  showPage(currentPage);

  document.getElementById("nextPage").addEventListener("click", function () {
    if (currentPage < pagePairs.length - 1) {
      manualFlip = true; // Track that the user manually flipped the page
      currentPage++;
      showPage(currentPage, "next");
    }
  });

  document.getElementById("prevPage").addEventListener("click", function () {
    if (currentPage > 0) {
      manualFlip = true; // Track that the user manually flipped the page
      currentPage--;
      showPage(currentPage, "prev");
    }
  });
}

// Ensure `bookContainer` Exists on Page Load
window.onload = function () {
  if (!document.getElementById("bookContainer")) {
    let bookContainer = document.createElement("div");
    bookContainer.id = "bookContainer";
    bookContainer.classList.add("box_area");
    document.querySelector(".content-wrapper").appendChild(bookContainer);
  }

  // Enable flipping once pages exist
  enableFlipping();
};
