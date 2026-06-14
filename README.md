# rename-files

Interactive Python script to remove a substring from filenames. Useful when you've downloaded PowerPoints as PDFs and the filenames still have `.pptx` embedded in them (e.g. `lecture.pptx.pdf` → `lecture.pdf`).

Works on any file type, on Windows, Mac, and Linux. No dependencies , just Python 3.9+.

## Usage

Download `rename_files.py` and run it from a terminal:

```
python rename_files.py
```

It will ask you:

1. Which folder or file to process (you can drag and drop into the terminal)
2. Whether to limit to specific extensions (e.g. `pdf`, or blank for all)
3. What text to remove (e.g. `.pptx`)
4. Confirmation before anything is renamed

Nothing is changed until you type `y` at the final prompt.

## Example

```
Folder or file to process [.]: ~/Downloads
Found 12 file(s) in /Users/you/Downloads: 12 .pdf

Limit to specific extensions? (e.g. 'pdf' or 'pdf, docx' — blank = all):
What text should I remove from the filenames? [.pptx]: .pptx
Remove every occurrence (not just the first)? [Y/n]: y

The following 8 file(s) would be renamed:
  lecture1.pptx.pdf
   -> lecture1.pdf
  ...

Apply these renames? [y/N]: y
Done. Renamed 8 of 8 file(s).
```

## License

MIT