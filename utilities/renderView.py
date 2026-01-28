import os, sys, argparse

def getFiles(rootPath, exts = ('mtlx', 'MTLX' )):
    filelist = []
    for subdir, dirs, files in os.walk(rootPath):
        for file in files:
            if file.lower().endswith(exts):
                filelist.append(os.path.join(subdir, file)) 
    return filelist

def main():
    parser = argparse.ArgumentParser(description="Render files using MaterialXView")
    parser.add_argument(dest="inputFileName", help="Filename / folder of the input document.")
    parser.add_argument('-r', '--renderer', dest='renderer', default="", help="Renderer to use. Default is empty.")
    parser.add_argument('-t', '--genTable', dest='genTable', type=bool, help="Generate table from images in folder.")
    opts = parser.parse_args()

    if not opts.genTable:

        renderer = opts.renderer

        # Get environment variable for MATERIALX_VIEWER
        if not renderer:
            if 'MATERIALX_VIEWER' in os.environ:
                renderer =  os.environ['MATERIALX_VIEWER']

        if not renderer:
            print("Error: MATERIALX_VIEWER renderer not set")
            sys.exit(1)

        fileList = []
        if os.path.isdir(opts.inputFileName): 
            fileList = getFiles(opts.inputFileName)
        else:
            fileList.append(opts.inputFileName)

        # Scan for all files in folder ending with ".mtlx"
        for file in fileList:
            if file.endswith(".mtlx"):
                # Run the viewer with the file
                inputFileName = file
                outputFilename = inputFileName.replace(".mtlx", ".png")
                print(f"Rendering: \"{inputFileName}\" to \"{outputFilename}\"...")
                arguments = f" --material \"{inputFileName}\"" 
                arguments += " --drawEnvironment true"
                arguments += " --screenWidth 512 --screenHeight 512 --screenColor \"0.2, 0.2, 0.2\""            
                arguments += f" --captureFilename \"{outputFilename}\""
                print(f"Running: {renderer} {arguments}")
                os.system(renderer + arguments)

    else:
        pixFileList = []
        if os.path.isdir(opts.inputFileName): 
            pixFileList = getFiles(opts.inputFileName, ('png', 'PNG'))

        # Find all names with OPBR in the name
        OPBR_pixFileList = [x for x in pixFileList if "OPBR" in x]
        SS_pixFileList = [x for x in pixFileList if "SS" in x]
        glTF_pixFileList = [x for x in pixFileList if "GLTF" in x]  

        print(f"Found {len(pixFileList)} images in folder {opts.inputFileName}")
        print(f"Found {len(OPBR_pixFileList)} OPBR images")
        print(f"Found {len(SS_pixFileList)} SS images")
        print(f"Found {len(glTF_pixFileList)} glTF images")            

        markdown = "| Material | Render OpenPBR | Render SS | Render glTF |\n"
        markdown += "| --- | --- | --- | --- |\n"
        output_count = 0
        # Create a set of all material names from all three lists
        def extract_material_name(filename, prefix):
            base = os.path.basename(filename)
            return base.replace(prefix, "").replace(".png", "")

        opbr_names = {extract_material_name(f, "PB_OPBR_") for f in OPBR_pixFileList}
        ss_names = {extract_material_name(f, "PB_SS_") for f in SS_pixFileList}
        gltf_names = {extract_material_name(f, "PB_GLTF_") for f in glTF_pixFileList}
        all_names = sorted(opbr_names | ss_names | gltf_names)

        # Helper to get file by material name
        def find_file_by_name(filelist, prefix, name):
            for f in filelist:
                if extract_material_name(f, prefix) == name:
                    return f
            return None

        # SVG placeholder for missing images
        svg_placeholder = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='128' height='128' style='background:#eee;'><rect width='100%' height='100%' fill='%23eee'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-size='16' fill='%23999'>no image</text></svg>")

        missing_files = []
        for name in all_names:
            opbr = find_file_by_name(OPBR_pixFileList, "PB_OPBR_", name)
            if not opbr:
                missing_files.append(f"PB_OPBR_{name}.png")
            ss = find_file_by_name(SS_pixFileList, "PB_SS_", name)
            if not ss:
                missing_files.append(f"PB_SS_{name}.png")
            gltf = find_file_by_name(glTF_pixFileList, "PB_GLTF_", name)
            if not gltf:
                missing_files.append(f"PB_GLTF_{name}.png")

            opbr_img = f'<img src="{opbr}" width=100%>' if opbr else f'<img src="{svg_placeholder}" width=100%>'
            ss_img = f'<img src="{ss}" width=100%>' if ss else f'<img src="{svg_placeholder}" width=100%>'
            gltf_img = f'<img src="{gltf}" width=100%>' if gltf else f'<img src="{svg_placeholder}" width=100%>'

            markdown += f"| {name} | {opbr_img} | {ss_img} | {gltf_img} |\n"
            output_count += 1
        
        if missing_files:
            print("Missing image files:")
            for mf in missing_files:
                print(f" - {mf}")

        print(f"Write markdown table with {output_count} entries to file {'images.md'}")
        with open("images.md", "w") as f:
            f.write(markdown)
        
        # Convert markdown to HTML
        try:
            import markdown as md
            html = md.markdown(markdown, extensions=['tables'])
            style = """
                <style>
                table, th, td {
                border: 1px solid #888;
                border-collapse: collapse;
                }
                th, td {
                padding: 8px;
                }
                table {
                font-family: Arial, sans-serif;
                font-size: 12px;
                width: 100%;
                }
                </style>
                <h2>MaterialXView Rendering of Physically Based Materials</h2>
                """
            html = style + html
            with open("images.html", "w") as f:
                f.write(html)
            print("Write HTML table to file {'images.html'}")
        except ImportError:
            print("Markdown module not found. Skipping HTML generation.")   

if __name__ == '__main__':
    main()

