# Paper packaging scripts

Utilities for collecting a LaTeX paper and its dependencies into a self-contained
`output/` folder (e.g. for an arXiv submission).

## `renamer.py` (main entry point)

Reads the LaTeX source, generates the dependency list, and copies every
dependency into a separate `output/` folder with flattened file names.

### How it works

1. Copies `<name>.tex` to a temporary `<name>_snapshot.tex` with
   `\RequirePackage{snapshot}` prepended.
2. Runs `pdflatex` on the temporary file so the `snapshot` package emits a
   `.dep` dependency list.
3. Generates `script.cmd` and runs it to populate `../output/`.
4. Removes the temporary `*_snapshot.*` files (on success).
5. Compiles the packaged paper (`engine` → `bibtex` → `engine` → `engine`) and
   moves the resulting PDF into `../output_pdf/`, leaving `../output/` free of
   build byproducts.

### Usage

Run it **from the `python/` directory** (it uses `../` to reach the repo root;
running it from the repo root will break the paths):

```sh
cd python
python renamer.py            # defaults to main.tex
python renamer.py templateArxiv   # or pass a tex file name (extension optional)
python renamer.py templateArxiv --engine lualatex   # choose the LaTeX engine
```

Use `--engine` to pick the LaTeX engine (`pdflatex`, `xelatex`, or `lualatex`;
defaults to `pdflatex`). Choose `lualatex` or `xelatex` if the document needs
them (e.g. the `emoji` package requires LuaTeX).

The packaged paper is written to `../output/`.

### Requirements

- The chosen LaTeX engine (`pdflatex`, `xelatex`, or `lualatex`) and the
  `snapshot` LaTeX package on your `PATH`.

### LaTeX build sequence (important for the bibliography)

The `snapshot` package writes the `.dep` at `\end{document}`, listing only files
that were actually **read during that run**. The `.bbl` is captured only if it
already exists on disk.

If your document uses **BibTeX**, build it with the full sequence before
packaging so the `.bbl` exists and is captured:

1. `pdflatex` — produces `.aux` with `\citation{...}`
2. `bibtex`  — produces `.bbl`
3. `pdflatex` — reads the `.bbl` (records it in `.dep`), resolves citations
4. `pdflatex` — settles cross-reference / citation numbers

A single `pdflatex` run is enough only if a `.bbl` already exists. Documents
using `biblatex`/`biber` should run `biber` instead of `bibtex`.

## Other scripts

- `figure_generator.py` — standalone helper that compiles each `figure`
  environment of `final.tex` to EPS into `output_final/`.
- `image_extractor.py` — standalone helper that copies images referenced by the
  figures in `final.tex` into `output_final/`.

These two are independent of `renamer.py`.
