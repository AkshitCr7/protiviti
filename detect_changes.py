import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os

def detect_forgery(original_path, edited_path, output_dir="output", area_threshold=100, use_color=False):
    # Check file existence
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"Original image not found at: {original_path}")
    if not os.path.exists(edited_path):
        raise FileNotFoundError(f"Edited image not found at: {edited_path}")

    os.makedirs(output_dir, exist_ok=True)

    # Load images
    original = cv2.imread(original_path)
    edited = cv2.imread(edited_path)

    if not use_color:
        original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        edited_gray = cv2.cvtColor(edited, cv2.COLOR_BGR2GRAY)
    else:
        original_gray = original.copy()
        edited_gray = edited.copy()

    # Resize edited to match original
    edited_gray = cv2.resize(edited_gray, (original_gray.shape[1], original_gray.shape[0]))

    # Compute SSIM
    score, diff = ssim(original_gray, edited_gray, full=True)
    diff = (diff * 255).astype("uint8")
    print(f"🔍 Structural Similarity Index: {score:.4f}")

    # Save diff image
    diff_map_path = os.path.join(output_dir, "ssim_diff_map.png")
    cv2.imwrite(diff_map_path, diff)

    # Threshold and find contours
    _, thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw bounding boxes
    output = edited.copy()
    for contour in contours:
        if cv2.contourArea(contour) > area_threshold:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # Save final output
    output_path = os.path.join(output_dir, "differences_detected.png")
    cv2.imwrite(output_path, output)

    print(f"✅ Differences highlighted and saved to: {output_path}")
    print(f"📄 SSIM difference map saved to: {diff_map_path}")
    return score

# ==== RUN SCRIPT ====
if __name__ == "__main__":
    original_image_path = r"C:\Users\akshi\Desktop\IMP\Protiviti\Image Document Evidence Analysis\original.png"
    edited_image_path = r"C:\Users\akshi\Desktop\IMP\Protiviti\Image Document Evidence Analysis\edited.png"

    detect_forgery(original_image_path, edited_image_path, use_color=False)
