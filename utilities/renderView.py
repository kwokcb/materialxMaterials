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
    parser.add_argument('--renderer', dest='renderer', default="", help="Renderer to use. Default is empty.")
    parser.add_argument('--genTable', dest='genTable', type=bool, help="Generate table from images in folder.")
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

        print(f"Found {len(OPBR_pixFileList)} OPBR images")
        print(f"Found {len(SS_pixFileList)} SS images")
        print(f"Found {len(glTF_pixFileList)} glTF images")    

        markdown = "| Material | Render OpenPBR | Render SS | Render glTF |\n"
        markdown += "| --- | --- | --- | --- |\n"
        for opbr, ss, gltf in zip(OPBR_pixFileList, SS_pixFileList, glTF_pixFileList):
            # Strip off PB_ and OPBR from filename
            materialName = os.path.basename(opbr).replace("PB_OPBR_", "").replace(".png", "")
            markdown += f"| {materialName} | <img src=\"{opbr}\" width=100%> | <img src=\"{ss}\" width=100%> | <img src=\"{gltf}\" width=100%> |\n"
        
        with open("images.md", "w") as f:
            f.write(markdown)

if __name__ == '__main__':
    main()

