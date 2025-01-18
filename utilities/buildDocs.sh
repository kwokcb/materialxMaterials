echo "Building Main Documents..."
pushd .
cd utilities
python mdhtml.py ../README.html -t template.html --top "." -o .. -of index.html
python mdhtml.py ../examples/README.html -t template.html --top "../examples" -o ../examples -of index.html
popd

pushd .
cd documents
echo "Building Doxygen Documents..."
doxygen Doxyfile
echo "Finish Doxygen build. See documents/doxygen_warnings.txt for any documentation warnings"
popd
