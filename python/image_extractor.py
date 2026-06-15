import re
import shutil
import os
import mimetypes


def extract_images_from_tex(tex_file, output_dir):
    # Create a directory to store extracted images
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        # Clear existing files in the directory if it exists
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))

    # Read the LaTeX file
    with open(tex_file, 'r', encoding='utf-8') as f:
        tex_content = f.read()

    # Define regex patterns
    figure_pattern = r'\\begin{figure.*?\\end{figure}'
    includegraphics_pattern = r'\\includegraphics(?:\[.*?\])?\{(.*?)\}'

    # Find all figure environments
    figure_matches = re.findall(figure_pattern, tex_content, re.DOTALL)

    figure_count = 0
    image_count = 0

    # Iterate through each figure environment
    for figure_match in figure_matches:
        figure_count += 1
        # Find all \includegraphics commands within this figure environment
        includegraphics_matches = re.findall(includegraphics_pattern, figure_match)
        image_count = 0
        
        # Copy matched image files to the output directory
        for match in includegraphics_matches:
            image_count += 1
            # Determine the file extension of the matched image file
            file_ext = os.path.splitext(match)[1]
            if file_ext == '':
                print(f"Skipping '{match}' (no file extension).")
                continue

            # Construct destination filename based on figure and image count
            dest_filename = f'{figure_count}{chr(96 + image_count)}{file_ext.lower()}'

            # Copy the image file to the output directory
            try:
                shutil.copy(match, os.path.join(output_dir, dest_filename))
            except FileNotFoundError:
                print(f"File '{match}' not found. Skipping...")

    print(f"Extracted {image_count} images from {figure_count} figure environments.")


if __name__ == "__main__":
    tex_file = 'final.tex'  # Replace with your LaTeX manuscript file path
    output_dir = 'output_final'
    extract_images_from_tex(tex_file, output_dir)
