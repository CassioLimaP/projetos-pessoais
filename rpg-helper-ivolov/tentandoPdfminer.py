import pathlib, fitz  # PyMuPDF

fname = "Edrick de Lamar Ficha.pdf"
with fitz.open(fname) as doc:
    text = chr(12).join([page.get_text() for page in doc])
pathlib.Path(fname + ".txt").write_bytes(text.encode())
