import GPUOpenLoader as gpuo

def main():
    '''
    Utility to download and write GPUOpen materials
    - TODO: Add proper command line logic
    '''
    loader = gpuo.GPUOpenMaterialLoader()
    materials = loader.getMaterials()
    materialCount = loader.updateMaterialNames()
    print(f'Read in {materialCount} materials')
    loader.writeMaterialFiles('GPUOpenMaterialX', 'GPUOpenMaterialX')

    # Create a test expression
    searchExpr = '.*blue painted wood.*'
    searchExpr = 'Oliana Blue Painted Wood'
    foundList = loader.findMaterialsByName(searchExpr)
    if len(foundList) > 0:
        for found in foundList:
            listNumber = found['listNumber']
            materialNumber = found['materialNumber']
            matName = found['title']
            print(f'> Download material: {matName} List: {listNumber}. Index: {materialNumber}')
            [data, title] = loader.downloadPackage(listNumber, materialNumber, 0)
            if data:
                loader.writePackageDataToFile(data, 'GPUOpenMaterialX', title)    

    [data, title] = loader.downloadPackage(0, 0, 0)
    print(f'> Download material: {title} List: 0. Index: 0')
    if data:
        loader.writePackageDataToFile(data, 'GPUOpenMaterialX', title)    
    
    #results = loader.getMaterialsAsJsonString()
    #for result in results:
    #    print(result)

if __name__ == '__main__':
    main()