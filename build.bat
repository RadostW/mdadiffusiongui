python.exe -m pip install -U pip
python.exe -m pip install -r requirements.txt

rmdir /s build
rmdir /s dist

pyinstaller --onefile src/mdadiffusiongui.py

robocopy src\\css dist\\css /E
robocopy examples dist\\examples /E

tar.exe -a -cf mdadiffusiongui.zip dist
