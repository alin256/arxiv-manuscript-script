#import re
import os
import glob
import shutil
import argparse
import subprocess

prefix = "../"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Package a LaTeX paper and its dependencies into ../output/."
    )
    parser.add_argument(
        "texfile",
        nargs="?",
        default="main",
        help="LaTeX file to process (extension optional). Defaults to 'main'.",
    )
    parser.add_argument(
        "--engine",
        choices=["pdflatex", "xelatex", "lualatex"],
        default="pdflatex",
        help="LaTeX engine used to generate the .dep file. Defaults to 'pdflatex'.",
    )
    return parser.parse_args()


args = parse_args()
filename_to_process = os.path.splitext(os.path.basename(args.texfile))[0]
engine = args.engine
convert_pdfs = False

foldername = "output"
prefix2 = "output/"

# Copy the LaTeX source to a temporary file with the snapshot package prepended,
# then compile it so that pdflatex emits the .dep dependency list. The temporary
# files use a distinctive mask so they can always be cleaned up afterwards,
# even if compilation fails.
tmp_basename = "_snapshot_" + filename_to_process + "_snapshot"


def _cleanup_snapshot_files():
    for path in glob.glob(prefix + tmp_basename + ".*"):
        os.remove(path)


with open(prefix + filename_to_process + ".tex", "r", encoding="utf-8") as src:
    tex_body = src.read()
with open(prefix + tmp_basename + ".tex", "w", encoding="utf-8") as tmp:
    tmp.write("\\RequirePackage{snapshot}\n")
    tmp.write(tex_body)

# Compile the temporary file to generate the .dep. On success the temporary
# files are removed; if the LaTeX run (or .dep read) fails they are kept so the
# .log can be inspected.
try:
    subprocess.run(
        [engine, "-interaction=nonstopmode", tmp_basename + ".tex"],
        cwd=prefix,
        check=True,
    )
    with open(prefix + tmp_basename + ".dep", "r") as depf:
        dep_lines = depf.readlines()
except Exception:
    print(
        "LaTeX run failed; keeping temporary files '"
        + prefix + tmp_basename + ".*' for inspection."
    )
    raise

_cleanup_snapshot_files()

output = open("script.cmd", 'w')
# output.write("cp " + prefix + filename_to_process + ".tex" +
#                          " " + prefix + foldername + "/" + " \n")
output.write("mkdir " + prefix + foldername + " \n")
pairs = {}
for x in dep_lines:
    xs = x.split('{')
    if len(xs) > 2:
        if True or "/" in xs[2]:
            s = xs[2].strip("} ")
            if s.endswith('.out') or s.endswith('.spl'):
                print("skipping", s)
                continue
            if os.path.isfile(prefix + s + ".sty"):
                print(prefix + s)
                output.write("cp " + prefix + s + ".sty" +
                             " " + prefix + foldername + "/" + " \n")
            if os.path.isfile(prefix + s + ".cls"):
                print(prefix + s)
                output.write("cp " + prefix + s + ".cls" +
                             " " + prefix + foldername + "/" + " \n")
            if not os.path.isfile(prefix + s):
                print("skipping", s)
                continue

            print(prefix + s)
            print(prefix + s.replace("/", "-"))
            print()
            pairs[s] = s.replace("/", "-")
            output.write("cp " + prefix + s +
                         " " + prefix + prefix2 + pairs[s] + "\n")

            if s.endswith(".pdf") and convert_pdfs:
                cur_file = prefix + prefix2 + pairs[s]
                ps_file_name = cur_file.replace(".pdf", ".ps")
                output.write("pdf2ps -dLanguageLevel=3 " + cur_file + " " + ps_file_name + "\n")
                output.write("ps2eps " + ps_file_name + "\n")
                output.write("rm " + cur_file + "\n")
                output.write("rm " + ps_file_name + "\n")
                pairs[s] = pairs[s].replace(".pdf",".eps")

        elif "-" in xs[2]:
            s = xs[2].strip("} ")
            if not os.path.isfile(prefix + s.replace("-", "/")):
                print("skipping", s)
                continue
            print(prefix + s.replace("-", "/"))
            print(prefix + s)
            print()
            pairs[s.replace("-", "/")] = s
            output.write("cp " + prefix + pairs[s] +
                         " " + prefix + s + "\n")

            if s.endswith(".pdf") and convert_pdfs:
                output.write("pdf2ps -dLanguageLevel=3 " + prefix + s + "\n")
                ps_file_name = (prefix + s).replace(".pdf", ".ps")
                output.write("ps2eps " + ps_file_name + "\n")
                output.write("rm " + prefix + s)
                output.write("rm " + ps_file_name)
                pairs[s] = pairs[s].replace(".pdf",".eps")

with open(prefix + filename_to_process+'.tex', "r") as fin:
    with open(prefix + tmp_basename + '.tex', 'w') as fout:
        for line in fin:
            if '/' in line:
                print(line)
                for to_replace in pairs:
                    # if to_replace in line:
                    line = line.replace(to_replace, pairs[to_replace])
            if "\\bibliography{" in line:
                end_of_line = line.replace("\\bibliography{","")
                bib_file = end_of_line.split("}")[0]
                output.write("cp " +
                             prefix + bib_file + '.bib' + ' ' +
                             prefix + prefix2 + bib_file + '.bib' +
                             " \n")
            fout.write(line)

output.write("cp " +
             prefix + tmp_basename + '.tex' + ' '+
             prefix + prefix2 + filename_to_process+'.tex' +
             " \n")
output.close()

# Run the generated script to populate the separate output folder.
subprocess.run(["sh", "script.cmd"], check=True)

# Remove the flattened intermediate .tex now that it has been copied.
_cleanup_snapshot_files()

# Final step: compile the packaged paper and place the resulting PDF in a
# separate folder, keeping the package folder free of build byproducts.
pdf_foldername = "output_pdf"
output_dir = prefix + foldername
pdf_dir = prefix + pdf_foldername
os.makedirs(pdf_dir, exist_ok=True)

# Full build sequence so citations and cross-references resolve:
# engine -> bibtex -> engine -> engine.
subprocess.run(
    [engine, "-interaction=nonstopmode", filename_to_process + ".tex"],
    cwd=output_dir,
    check=True,
)
subprocess.run(["bibtex", filename_to_process], cwd=output_dir, check=True)
for _ in range(2):
    subprocess.run(
        [engine, "-interaction=nonstopmode", filename_to_process + ".tex"],
        cwd=output_dir,
        check=True,
    )

shutil.move(
    os.path.join(output_dir, filename_to_process + ".pdf"),
    os.path.join(pdf_dir, filename_to_process + ".pdf"),
)

# Remove compilation byproducts from the package folder.
for ext in (".aux", ".log", ".out", ".toc", ".blg"):
    byproduct = os.path.join(output_dir, filename_to_process + ext)
    if os.path.isfile(byproduct):
        os.remove(byproduct)

print("PDF written to " + os.path.join(pdf_dir, filename_to_process + ".pdf"))
