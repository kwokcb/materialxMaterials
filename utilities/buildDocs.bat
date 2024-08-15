@echo --------- Building Documents
python mdhtml.py ../README.html -t template.html --top "." -o .. -of index.html
python mdhtml.py ../examples/README.html -t template.html --top "../examples" -o ../examples -of index.html
cd ../documents
doxygen
cd ../utilities
