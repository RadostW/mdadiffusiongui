rm -rfI build/ dist/

pyinstaller \
--onefile \
src/mdadiffusiongui.py

cp -r src/css dist/css
cp -r examples dist/examples

tree dist/

zip -r mdadiffusiongui.zip dist
