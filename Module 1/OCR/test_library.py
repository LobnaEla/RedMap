import os
from ocr_library import extract_text

# ========== CONFIGURATION ==========
INPUT_FOLDER = "image"  # The folder containing images to test
OUTPUT_FOLDER = "test_output"  # The folder where results will be saved

# Create the output directory if it doesn't exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def run_test():
    """
    Runs the OCR extraction test on all images in the input folder.
    """
    print(f"--- Starting OCR Library Test ---")
    print(f"Input folder: {INPUT_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}\n")

    # Get a list of all image files
    try:
        image_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp'))]
    except FileNotFoundError:
        print(f"Error: Input folder '{INPUT_FOLDER}' not found.")
        return

    if not image_files:
        print("No images found in the input folder.")
        return

    # Process each image
    for filename in image_files:
        image_path = os.path.join(INPUT_FOLDER, filename)
        print(f"🔍 Processing: {filename}...")

        try:
            # Extract text using the library function
            extracted_text = extract_text(image_path)

            # Save the cleaned text to the output folder
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}_output.txt")
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            print(f"✅ Success! Cleaned text saved to: {output_path}\n")

        except FileNotFoundError as e:
            print(f"❌ Error: {e}\n")
        except Exception as e:
            print(f"❌ An unexpected error occurred while processing {filename}: {e}\n")

    print("--- Test Complete ---")

if __name__ == "__main__":
    run_test()
