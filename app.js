// Get references to the form, file input, and result div
const uploadForm = document.getElementById("uploadForm");
const fileInput = document.querySelector(".file-input");
const analysisSummary = document.getElementById("analysisSummary");
const resultDiv = document.getElementById("resultDiv");

// Event listener for form submission
uploadForm.addEventListener("submit", (event) => {
    event.preventDefault(); // Prevent default form submission

    // Check if a file is selected
    if (fileInput.files.length === 0) {
        alert("Please select an image file to upload.");
        return;
    }

    // Create FormData object to send file data to the server
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // Send the file to the server for analysis
    fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
    })
        .then(response => response.json())
        .then(data => {
            // Extract data from the server response
            const { extracted_text, gpt_response, food_description, food_label, food_rating, message } = data;

            // Update the Analysis Summary section with the response data
            analysisSummary.style.display = "block"; // Show the summary section

            // Populate the resultDiv based on the data received
            resultDiv.innerHTML = `
                <p><strong>Food Label:</strong> ${food_label || "N/A"}</p>
                <p><strong>Description:</strong> ${food_description || "N/A"}</p>
                <p><strong>Rating:</strong> ${food_rating || "N/A"}</p>
                <p><strong>Extracted Text:</strong> ${extracted_text || "No text found in the image."}</p>
                <p><strong>GPT Response:</strong> ${gpt_response || "No GPT response available."}</p>
            `;

            // Show a message if no information is available
            if (!food_label && !extracted_text && !gpt_response) {
                resultDiv.innerHTML = `<p>${message || "No information found for the uploaded image."}</p>`;
            }
        })
        .catch(error => {
            console.error("Error fetching data:", error);
            resultDiv.innerHTML = "<p>Error fetching data. Please try again.</p>";
            analysisSummary.style.display = "block";
        });
});
