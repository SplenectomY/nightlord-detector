Vendor a portable Tesseract tree here before running scripts/build_windows.ps1:

  resources/Tesseract-OCR/tesseract.exe
  resources/Tesseract-OCR/tessdata/eng.traineddata

The build script copies from "C:\Program Files\Tesseract-OCR" automatically if that folder exists.
Do not commit the binaries; they are large and redistributable separately.
