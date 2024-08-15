@echo --------- Building Documents
python mdhtml.py ../README.html -t template.html --top "." -o .. -of index.html
cd ../documents
doxygen
cd ../utilities
