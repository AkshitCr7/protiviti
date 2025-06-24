import cv2
import pytesseract
from pytesseract import Output
import numpy as np
import os

# Required if tesseract is not in PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Define the labels we care about (can expand this)
TARGET_FIELDS = ["subtotal", "invoice total", "total", "amount", "tax"]

def detect_invoice_field_anomalies(image_path, output_path,
                                   size_threshold=0.5,
                                   spacing_threshold=15,
                                   blur_threshold=100):

    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # OCR: extract word-level data
    data = pytesseract.image_to_data(gray, config='--oem 3 --psm 6', output_type=Output.DICT)

    heights = [data['height'][i] for i in range(len(data['text'])) if data['text'][i].strip()]
    if not heights:
        print("No text detected.")
        return
    avg_height = np.mean(heights)

    print(f"[i] Average text height: {avg_height:.2f}")

    image_output = image.copy()

    for i in range(len(data['text'])):
        word = data['text'][i].strip().lower()
        if word in TARGET_FIELDS:
            # Check for value next to the label
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

            # Look rightward for next value
            for j in range(i + 1, min(i + 6, len(data['text']))):
                value = data['text'][j].strip()
                if not value or not any(char.isdigit() for char in value):
                    continue

                vx, vy, vw, vh = data['left'][j], data['top'][j], data['width'][j], data['height'][j]

                # Font size anomaly
                if abs(vh - avg_height) > size_threshold * avg_height:
                    cv2.rectangle(image_output, (vx, vy), (vx + vw, vy + vh), (0, 0, 255), 2)
                    cv2.putText(image_output, 'size', (vx, vy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

                # Spacing anomaly from label to value
                spacing = vx - (x + w)
                if spacing > spacing_threshold:
                    cv2.rectangle(image_output, (vx, vy), (vx + vw, vy + vh), (255, 0, 0), 2)
                    cv2.putText(image_output, 'gap', (vx, vy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

                break  # Only check the first detected value next to label

    # Save result
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, image_output)
    print(f"[✔] Output saved to: {output_path}")


# ========== Auto Run ==========
if __name__ == "__main__":
    image_path = r"C:\Users\akshi\Downloads\Web_Photo_Editor.png"  # Change to your tampered invoice path
    output_path = os.path.splitext(image_path)[0] + "_analyzed_fields.png"

    detect_invoice_field_anomalies(image_path, output_path)
