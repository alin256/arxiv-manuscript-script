import re
import os
import subprocess
import shutil

def extract_figures_to_latex(tex_file, output_dir):
    # Create a directory to store extracted figure contents
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        # Clear existing files in the directory if it exists
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))

    # Read the LaTeX file
    with open(tex_file, 'r', encoding='utf-8') as f:
        tex_content = f.read()

    # Define regex pattern to find figure environments
    figure_pattern = r'\\begin{figure}.*?\\end{figure}'
    caption_pattern = r'\\caption(\[.*?\])?\{'
    label_pattern = r'\\label\{.*?\}'

    # Find all figure environments
    figure_matches = re.findall(figure_pattern, tex_content, re.DOTALL)

    def remove_caption_and_extract(content):
        caption_match = re.search(caption_pattern, content)
        if not caption_match:
            return content, None, None
        start_idx = caption_match.start()
        open_braces = 0
        for i in range(start_idx, len(content)):
            if content[i] == '{':
                open_braces += 1
            elif content[i] == '}':
                open_braces -= 1
                if open_braces == 0:
                    end_idx = i
                    break
        caption_text = content[caption_match.end():end_idx].strip()
        content_without_caption = content[:start_idx] + content[end_idx + 1:]

        label_match = re.search(label_pattern, content)
        label_text = label_match.group(0) if label_match else ""

        return content_without_caption, caption_text, label_text

    figure_count = 0
    new_tex_content = tex_content  # Initialize new LaTeX content as a copy of the original

    # Iterate through each figure environment
    for figure_match in figure_matches:
        figure_count += 1

        # Remove the caption from the figure content and extract the caption and label text
        figure_content, caption_text, label_text = remove_caption_and_extract(figure_match)

        # Create a separate tex file for each figure content
        figure_tex_content = f"""
\\documentclass{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{graphicx}}
\\pagestyle{{empty}}  % Remove page numbers

\\begin{{document}}

{figure_content.strip()}

\\end{{document}}
"""

        figure_tex_file = os.path.join(output_dir, f'figure_{figure_count}.tex')

        with open(figure_tex_file, 'w', encoding='utf-8') as f_tex:
            f_tex.write(figure_tex_content)

        # Compile LaTeX to PDF
        pdf_output_file = os.path.join(output_dir, f'figure_{figure_count}.pdf')
        try:
            subprocess.run(['pdflatex', '-interaction=nonstopmode', '-output-directory', output_dir, figure_tex_file], check=True)
            print(f"Compiled {figure_tex_file} to {pdf_output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error compiling {figure_tex_file}:", e)

        # Convert PDF to PS
        ps_output_file = os.path.join(output_dir, f'figure_{figure_count}.ps')
        try:
            subprocess.run(['pdf2ps', '-dLanguageLevel=3', pdf_output_file, ps_output_file], check=True)
            print(f"Converted {pdf_output_file} to {ps_output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error converting {pdf_output_file} to PS:", e)

        # Convert PS to EPS
        eps_output_file = os.path.join(output_dir, f'figure_{figure_count}.eps')
        try:
            subprocess.run(['ps2eps', ps_output_file], check=True)
            print(f"Converted {ps_output_file} to {eps_output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error converting {ps_output_file} to EPS:", e)

        # Remove temporary files
        for extension in ['pdf', 'ps', 'log', 'tex', 'aux']:
            tmp_output_file = os.path.join(output_dir, f'figure_{figure_count}.{extension}')
            os.remove(tmp_output_file)

        # Create new figure environment with the EPS file and label
        new_figure_environment = f"""
\\begin{{figure}}
\\includegraphics[width=\\textwidth]{{figure_{figure_count}.eps}}
\\caption{{{caption_text}}}
{label_text}
\\end{{figure}}
"""

        # Replace the original figure environment with the new one
        new_tex_content = new_tex_content.replace(figure_match, new_figure_environment)

    # Write the new main LaTeX file
    new_main_tex_file = os.path.join(output_dir, 'new_main.tex')
    with open(new_main_tex_file, 'w', encoding='utf-8') as f_new_main:
        f_new_main.write(new_tex_content)

    print(f"Generated new main LaTeX file: {new_main_tex_file}")

    # Copy all files from 'output' directory to 'output_final' directory
    output_dir_path = os.path.abspath('output')
    output_final_dir_path = os.path.abspath(output_dir)
    for file_name in os.listdir(output_dir_path):
        full_file_name = os.path.join(output_dir_path, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, output_final_dir_path)

if __name__ == "__main__":
    tex_file = 'final.tex'  # Replace with your LaTeX manuscript file path
    output_dir = 'output_final'
    extract_figures_to_latex(tex_file, output_dir)
