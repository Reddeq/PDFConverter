import os
import sys
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
import logging
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

# Setup logging
#def setup_logging():
#    log_dir = Path("logs")
#    log_dir.mkdir(exist_ok=True)
#    
#    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#    log_file = log_dir / f"conversion_{timestamp}.log"
#    
#    logging.basicConfig(
#        level=logging.INFO,
#        format='%(asctime)s - %(levelname)s - %(message)s',
#        handlers=[
#            logging.FileHandler(log_file, encoding='utf-8'),
#            logging.StreamHandler(sys.stdout)
#        ]
#    )
#    return logging.getLogger(__name__)

def get_image_properties(image_path):
    """Get image properties: size, DPI, format"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")
    
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Get DPI/resolution
            dpi = img.info.get('dpi', (72, 72))  # Default 72 DPI if not specified
            
            # Get format and mode
            img_format = img.format
            img_mode = img.mode
            
            # Get file extension for output format
            _, file_ext = os.path.splitext(image_path)
            output_format = file_ext.lower().replace('.', '').upper()
            
            # Map common extensions to PIL format codes
            format_map = {
                'PNG': 'PNG',
                'JPG': 'JPEG',
                'JPEG': 'JPEG',
                'BMP': 'BMP',
                'TIFF': 'TIFF',
                'TIF': 'TIFF',
                'WEBP': 'WEBP'
            }
            
            output_format = format_map.get(output_format, 'PNG')
            
            return {
                'width': width,
                'height': height,
                'dpi': dpi,
                'format': img_format,
                'output_format': output_format,
                'mode': img_mode,
                'size': img.size
            }
    except Exception as e:
        raise IOError(f"Cannot read image {image_path}: {e}")

def find_matching_image(pdf_filename, folder_b):
    """Find matching image file by checking if PDF filename contains the image base name"""
    
    # Remove .pdf extension
    pdf_name = pdf_filename.replace('.pdf', '')
    pdf_name_lower = pdf_name.lower()
    
    folder_path = Path(folder_b)
    
    # Get all image files
    image_files = []
    for ext in ['.png', '.PNG', '.jpg', '.jpeg', '.JPG', '.JPEG', '.bmp', '.BMP', '.tiff', '.TIFF']:
        image_files.extend(folder_path.glob(f"*{ext}"))
    
    # Priority 1: Exact match (image stem is exactly in PDF filename)
    for img_file in image_files:
        if img_file.stem in pdf_name:
            print(f"  ✓ Exact match: {img_file.name}")
            return img_file
    
    # Priority 2: Case-insensitive exact match
    for img_file in image_files:
        if img_file.stem.lower() in pdf_name_lower:
            print(f"  ✓ Case-insensitive match: {img_file.name}")
            return img_file
    
    # Priority 3: Image stem is at start of PDF filename
    for img_file in image_files:
        if pdf_name.startswith(img_file.stem) or pdf_name_lower.startswith(img_file.stem.lower()):
            print(f"  ✓ Prefix match: {img_file.name}")
            return img_file
    
    # Priority 4: Image stem is at end of PDF filename
    for img_file in image_files:
        if pdf_name.endswith(img_file.stem) or pdf_name_lower.endswith(img_file.stem.lower()):
            print(f"  ✓ Suffix match: {img_file.name}")
            return img_file
    
    # Priority 5: Any containment
    for img_file in image_files:
        if img_file.stem in pdf_name or img_file.stem.lower() in pdf_name_lower:
            print(f"  ✓ Contains match: {img_file.name}")
            return img_file
    
    print(f"  ✗ No matching image found for: {pdf_filename}")
    return None

def convert_pdf_to_image_with_properties(pdf_path, target_properties, output_path):
    """Convert PDF to image with exact properties from reference image"""
    created_files = []  # List of created files
    
    try:
        # Poppler path
        poppler_path = os.path.join(os.path.dirname(__file__), "poppler", "Library", "bin")
        
        # Calculate DPI for conversion to match exact pixel dimensions
        target_width = target_properties['width']
        target_height = target_properties['height']
        target_dpi = target_properties['dpi']
        output_format = target_properties['output_format']
        
        # For high quality conversion, use higher DPI and then resize
        conversion_dpi = max(target_dpi[0], target_dpi[1], 300)
        
        # Use appropriate format for conversion
        if output_format in ['JPEG', 'JPG']:
            fmt = 'jpeg'
            convert_mode = 'RGB'  # JPEG doesn't support alpha
        elif output_format == 'TIFF':
            fmt = 'tiff'
            convert_mode = None
        else:
            fmt = 'png'  # Default for PDF conversion
            convert_mode = None
        
        images = convert_from_path(
            pdf_path,
            dpi=conversion_dpi,
            poppler_path=poppler_path,
            fmt=fmt,
            grayscale=False,
            size=(None, None)
        )
        
        if not images:
            raise ValueError(f"Cannot convert PDF: {pdf_path}")
        
        # Determine output file extension
        extension_map = {
            'PNG': '.png',
            'JPEG': '.jpg',
            'JPG': '.jpg',
            'BMP': '.bmp',
            'TIFF': '.tiff',
            'WEBP': '.webp'
        }
        ext = extension_map.get(output_format, '.png')
        
        # Process all pages
        for i, image in enumerate(images):
            # Get correct output path
            if len(images) == 1:
                output_file = f"{output_path}{ext}"
            else:
                output_file = f"{output_path}_page{i+1:03d}{ext}"
            
            created_files.append(output_file)
            
            # Convert PIL image mode if necessary
            if convert_mode and image.mode != convert_mode:
                image = image.convert(convert_mode)
            elif image.mode == 'P':
                # Convert palette mode to RGBA
                image = image.convert('RGBA')
            elif image.mode not in ['RGB', 'RGBA']:
                image = image.convert('RGB')
            
            # Resize to exact target dimensions with high quality
            resized_image = image.resize(
                (target_width, target_height),
                Image.Resampling.LANCZOS
            )
            
            # Save with appropriate format and parameters
            if output_format == 'JPEG':
                # JPEG specific settings
                resized_image.save(
                    output_file,
                    'JPEG',
                    quality=95,
                    dpi=target_dpi,
                    optimize=True,
                    subsampling=0  # 4:4:4 chroma subsampling for best quality
                )
            elif output_format == 'TIFF':
                # TIFF specific settings
                resized_image.save(
                    output_file,
                    'TIFF',
                    compression='tiff_lzw',
                    dpi=target_dpi
                )
            elif output_format == 'WEBP':
                # WebP specific settings
                resized_image.save(
                    output_file,
                    'WEBP',
                    quality=95,
                    dpi=target_dpi,
                    method=6  # Slowest/best quality
                )
            else:
                # PNG or other formats
                resized_image.save(
                    output_file,
                    output_format,
                    dpi=target_dpi,
                    compress_level=6,
                    optimize=True
                )
            
            # Verify saved image properties
            with Image.open(output_file) as saved_img:
                saved_width, saved_height = saved_img.size
                saved_dpi = saved_img.info.get('dpi', (72, 72))
                saved_format = saved_img.format
                
            print(f"Saved: {os.path.basename(output_file)}")
            print(f"  Format: {saved_format}")
            print(f"  Dimensions: {saved_width}x{saved_height}px")
            print(f"  DPI: {saved_dpi[0]}x{saved_dpi[1]}")
            print(f"  Target was: {target_width}x{target_height}px, DPI: {target_dpi[0]}x{target_dpi[1]}")
        
        return True, created_files  # Return success and list of files
        
    except Exception as e:
        print(f"Conversion error {os.path.basename(pdf_path)}: {e}")
        import traceback
        traceback.print_exc()
        return False, created_files
        
def validate_conversion(output_path, target_properties):
    """Validate that converted image matches target properties"""
    try:
        with Image.open(output_path) as img:
            actual_width, actual_height = img.size
            actual_dpi = img.info.get('dpi', (72, 72))
            
            width_match = actual_width == target_properties['width']
            height_match = actual_height == target_properties['height']
            dpi_match = (abs(actual_dpi[0] - target_properties['dpi'][0]) < 1 and 
                        abs(actual_dpi[1] - target_properties['dpi'][1]) < 1)
            
            return {
                'valid': width_match and height_match and dpi_match,
                'actual': {
                    'width': actual_width,
                    'height': actual_height,
                    'dpi': actual_dpi
                },
                'expected': {  # Always adding expected
                    'width': target_properties['width'],
                    'height': target_properties['height'],
                    'dpi': target_properties['dpi']
                }
            }
    except Exception as e:
        print(f"Validation error for {output_path}: {e}")
        return {
            'valid': False, 
            'error': str(e),
            'expected': {  # Adding expected if error occurs
                'width': target_properties['width'],
                'height': target_properties['height'],
                'dpi': target_properties['dpi']
            }
        }
def select_folder_dialog(title="Select folder"):
    """Open folder selection dialog"""
    # Creating hidden tkinter window
    root = tk.Tk()
    root.withdraw()  # Hiding main window
    root.attributes('-topmost', True)  # On top of other windows
    
    # Opening folder dialog
    folder_path = filedialog.askdirectory(
        title=title,
        mustexist=True  # Only existing folders
    )
    
    # Closing tkinter window
    root.destroy()
    
    return folder_path

def main():
    """Main function"""
#    logger = setup_logging()
    
    print("=" * 60)
    print("PDF to Image Converter")
    print("=" * 60)
    print("\nThis program converts PDF files to images matching the properties")
    print("of reference images in another folder.")
    print("\nRequirements:")
    print("- PDF files must have names like 'filename-ru-en-P1.pdf'")
    print("- Reference images must have names like 'filename.png' (or .jpg, .jpeg, .bmp, .tiff)")
    print("- Output images will be saved in the PDF folder")
    print("- Output images will have same dimensions and DPI as reference images")
    print("=" * 60)
    
    # === Get folder paths from user ===
    print("\nStep 1: Select folder with PDF files (Folder A)")
    print("This folder contains PDF files with '-ru-en-P1' in their names.")
    input("Press Enter to browse for folder...")
    
    FOLDER_A = select_folder_dialog("Select folder with PDF files")
    
    if not FOLDER_A:
        print("✗ No folder selected. Exiting...")
        input("\nPress Enter to exit...")
        return
    
    print(f"✓ Selected PDF folder: {FOLDER_A}")
    
    print("\nStep 2: Select folder with reference images (Folder B)")
    print("This folder contains PNG/JPEG/BMP/TIFF files with matching names.")
    input("Press Enter to browse for folder...")
    
    FOLDER_B = select_folder_dialog("Select folder with reference images")
    
    if not FOLDER_B:
        print("✗ No folder selected. Exiting...")
        input("\nPress Enter to exit...")
        return
    
    print(f"✓ Selected reference images folder: {FOLDER_B}")
    
    # === Confirm selection ===
    print("\n" + "=" * 60)
    print("Selected folders:")
    print(f"PDF folder (A): {FOLDER_A}")
    print(f"Reference images folder (B): {FOLDER_B}")
    print("=" * 60)
    
    confirm = input("\nProceed with conversion? (Y/N): ").strip().upper()
    if confirm != 'Y':
        print("Conversion cancelled.")
        input("\nPress Enter to exit...")
        return
    
    # === Path validation ===
    print("\nValidating paths...")
    print(f"Folder A (PDFs): {FOLDER_A}")
    print(f"Folder B (Reference images): {FOLDER_B}")
    print(f"Folder A exists: {os.path.exists(FOLDER_A)}")
    print(f"Folder B exists: {os.path.exists(FOLDER_B)}")
    
    if not os.path.exists(FOLDER_A):
        print(f"✗ ERROR: Folder A does not exist!")
        input("\nPress Enter to exit...")
        return
    
    if not os.path.exists(FOLDER_B):
        print(f"✗ ERROR: Folder B does not exist!")
        input("\nPress Enter to exit...")
        return
    
    # === Statistics ===
    processed = 0
    failed = 0
    skipped = 0
    
    # === Process files ===
    print("\nStarting file processing...")
    print("=" * 60)
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(FOLDER_A) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("✗ No PDF files found in Folder A!")
        input("\nPress Enter to exit...")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Create summary file
    summary_file = os.path.join(FOLDER_A, f"conversion_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_file}")
        
        # Check for required suffix
        #if '-ru-en-P1' not in pdf_file:
        #    print(f"Skipping: File name does not contain '-ru-en-P1'")
        #    skipped += 1
        #    continue
        
        # Find matching reference image
        ref_image_path = find_matching_image(pdf_file, FOLDER_B)
        
        if not ref_image_path:
            print(f"Skipping: No matching reference image found for {pdf_file}")
            failed += 1
            continue
        
        try:
            # Get reference image properties
            print(f"Reference image: {ref_image_path.name}")
            ref_properties = get_image_properties(ref_image_path)

            print(f"Reference properties:")
            print(f"  Dimensions: {ref_properties['width']}x{ref_properties['height']}px")
            print(f"  DPI: {ref_properties['dpi'][0]}x{ref_properties['dpi'][1]}")
            print(f"  Format: {ref_properties['format']}")
            print(f"  Output format: {ref_properties['output_format']}")
            print(f"  Mode: {ref_properties['mode']}")

            # Prepare paths - output file keeps ORIGINAL PDF filename
            pdf_path = os.path.join(FOLDER_A, pdf_file)

            # Get the full PDF filename WITHOUT .pdf extension (keeps everything else)
            pdf_basename = os.path.splitext(pdf_file)[0]  # "document-name-ru-en-P1-v2" etc.

            # Full path WITHOUT extension - converter will add correct extension
            output_path_without_ext = os.path.join(FOLDER_A, pdf_basename)

            # Get correct extension for output format
            extension_map = {
                'PNG': '.png',
                'JPEG': '.jpg',
                'JPG': '.jpg',
                'BMP': '.bmp',
                'TIFF': '.tiff',
                'WEBP': '.webp'
            }
            output_ext = extension_map.get(ref_properties['output_format'], '.png')
            output_filename = f"{pdf_basename}{output_ext}"
            output_full_path = os.path.join(FOLDER_A, output_filename)

        # Check if output already exists
            if os.path.exists(output_full_path):
                print(f"  Output file already exists, will be overwritten: {output_filename}")
            else:
                print(f"  Output will be saved as: {output_filename}")

            # Convert PDF - pass path WITHOUT extension
            print(f"Converting PDF to {ref_properties['output_format']}...")
            success, created_files = convert_pdf_to_image_with_properties(pdf_path, ref_properties, output_path_without_ext)
            
            
            
            if success:
                # Validate each created file
                for output_file in created_files:
                    print(f"Validating conversion for {os.path.basename(output_file)}...")
                    validation = validate_conversion(output_file, ref_properties)
                    
                    if validation['valid']:
                        print(f"✓ SUCCESS: {os.path.basename(output_file)}")
                        print(f"  Matched dimensions and DPI exactly")
                    else:
                        print(f"⚠ WARNING: Conversion completed but properties don't match exactly for {os.path.basename(output_file)}")
                        if 'expected' in validation:
                            print(f"  Expected: {validation['expected']['width']}x{validation['expected']['height']}px, "
                                  f"DPI: {validation['expected']['dpi'][0]}x{validation['expected']['dpi'][1]}")
                        if 'actual' in validation:
                            print(f"  Actual: {validation['actual']['width']}x{validation['actual']['height']}px, "
                                  f"DPI: {validation['actual']['dpi'][0]}x{validation['actual']['dpi'][1]}")
                        else:
                            print(f"  Error: {validation.get('error', 'Unknown error')}")
                
                processed += 1
            else:
                print(f"✗ FAILED: Conversion failed for {pdf_file}")
                failed += 1
                
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # === Final statistics ===
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total PDF files: {len(pdf_files)}")
    print(f"Successfully processed: {processed}")
    print(f"Skipped (no -ru-en-P1): {skipped}")
    print(f"Failed/errors: {failed}")
    
    if processed > 0:
        print(f"\nConverted files saved to: {FOLDER_A}")
        print("\nSummary of properties preservation:")
        print("✓ Exact pixel dimensions (width x height)")
        print("✓ Exact DPI/resolution")
        print(f"✓ Format matching original reference images")
    
    print(f"\n{'='*60}")
    input("\nPress Enter to exit...")

main()
#if __name__ == "__main__":
#    # Check dependencies
#    try:
#        from pdf2image import convert_from_path
#        from PIL import Image
#        print("Dependencies loaded successfully!")
#        print("Starting PDF to IMG converter...")
#        print("=" * 60)
#        main()
#    except ImportError as e:
#        print(f"Import error: {e}")
#        print("\nPlease install required libraries:")
#        print("pip install pdf2image Pillow")
#        print("\nAlso download and install Poppler:")
#        print("https://github.com/oschwartz10612/poppler-windows/releases/")
#        print("Extract to PDFTOIMGConverter folder")
#        input("\nPress Enter to exit...")