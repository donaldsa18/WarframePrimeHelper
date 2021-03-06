copy *.py src\main\python\
rmdir /S /Q "target\Warframe Prime Helper\"
for %%X in (myExecutable.exe) do (set FOUND=%%~$PATH:X)
if not defined FOUND (
    pip install fbs
)

fbs freeze %1
xcopy "resources" "target\Warframe Prime Helper\resources\" /s /i
xcopy "tesseract4win64-4.0-beta" "target\Warframe Prime Helper\tesseract4win64-4.0-beta\" /s /i
mkdir "target\Warframe Prime Helper\temp"
mkdir "target\Warframe Prime Helper\logs"
mkdir "target\Warframe Prime Helper\screenshots"
