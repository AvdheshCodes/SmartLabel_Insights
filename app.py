from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
import pytesseract
import os
from transformers import pipeline
import torch
from torchvision import models, transforms
import json
import requests

app = Flask(__name__)

# Enable CORS for all routes and specifically for the React app
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:3000"}})

# Setup paths
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Load a pipeline for text generation (e.g., GPT-2)
generator = pipeline("text-generation", model="gpt2")

# Load a pre-trained ResNet model for image classification
model = models.resnet50(pretrained=True)
model.eval()

# Define transformation for input image
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Define a function to get class labels (ImageNet labels)
LABELS_URL = 'https://storage.googleapis.com/download.tensorflow.org/data/imagenet_class_index.json'
response = requests.get(LABELS_URL)
labels = json.loads(response.text)

# Mapping of food classes to descriptions and ratings
food_info = {
    "pizza": {"description": "A delicious Italian dish consisting of a flat, round base topped with various ingredients.", "rating": 4.5},
    "hotdog": {"description": "A grilled or steamed sausage served in a sliced bun, often garnished with mustard or ketchup.", "rating": 4.2},
    "hamburger": {"description": "A beef patty served in a bun, often topped with lettuce, tomato, and condiments.", "rating": 4.3},
    "apple": {"description": "A sweet, crunchy fruit, typically red, green, or yellow in color.", "rating": 4.1},
    "banana": {"description": "A soft, sweet yellow fruit with a peelable skin.", "rating": 4.0},
    # Add more food items here as needed
}

def classify_food(image):
    # Convert the image to RGB (to avoid issues with RGBA)
    image = image.convert("RGB")
    
    # Apply the transformation to the image
    image_tensor = transform(image).unsqueeze(0)

    # Perform inference
    with torch.no_grad():
        outputs = model(image_tensor)

    # Get predicted class index
    _, predicted_idx = torch.max(outputs, 1)

    # Get human-readable label
    predicted_class = labels[str(predicted_idx.item())][1]

    # Check if the predicted class is in the food_info dictionary
    if predicted_class in food_info:
        food_description = food_info[predicted_class]["description"]
        food_rating = food_info[predicted_class]["rating"]
    else:
        food_description = "Description not available."
        food_rating = "Rating not available."

    return predicted_class, food_description, food_rating


@app.route("/")
def home():
    return "Flask server is running. Use the '/upload' endpoint to upload files."

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file and file.filename.endswith(('png', 'jpg', 'jpeg')):
        try:
            # Save the uploaded file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Open and process the image
            image = Image.open(file_path)

            # Classify the food in the image
            food_label, food_description, food_rating = classify_food(image)

            # Extract text using OCR (if any)
            extracted_text = pytesseract.image_to_string(image).strip()

            # Handle the OCR and food classification result
            if extracted_text:
                gpt_output = generator(extracted_text, max_length=50, num_return_sequences=1)[0]['generated_text']
                return jsonify({
                    "extracted_text": extracted_text,
                    "gpt_response": gpt_output,
                    "food_label": food_label,
                    "food_description": food_description,
                    "food_rating": food_rating,
                    "filename": file.filename
                })
            else:
                return jsonify({
                    "extracted_text": None,
                    "food_label": food_label,
                    "food_description": food_description,
                    "food_rating": food_rating,
                    "message": "No text found in the image."
                })
        except Exception as e:
            return jsonify({"error": f"Error processing the file: {e}"}), 500

    return jsonify({"error": "Invalid file format. Only PNG, JPG, and JPEG are supported."}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
