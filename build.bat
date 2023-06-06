rm -rfI build/ dist/

pyinstaller \
--onefile \
src/mdadiffusiongui.py

cp -r src/css dist/css
cp -r examples dist/examples

tar.exe -cvzf mdadiffusiongui.zip dist
