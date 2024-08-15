import sys, os
import subprocess

def main() -> int:
    '''
    Main entry point for running commands in the package.
    '''
    argCount = len(sys.argv)
    if argCount < 2:
        print('No arguments provided. Use -h or --help for help.')
        return 1
    if sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print('Usage: python -m materialxMaterials <command> [options] where command is gpuopen or physbased')

    # Check if the command is valid
    cmdArgs = sys.argv[1:]
    if cmdArgs[0] == 'physbased':
        cmdArgs[0] = 'physicallyBasedMaterialXCmd.py'
    elif cmdArgs[0] == 'gpuopen':
        cmdArgs[0] = 'GPUOpenLoaderCmd.py'
    else:
        print('Unknown command specified:', cmdArgs[0])
        return 1
    
    # Build the command
    cmd = ' '.join(cmdArgs)
    packageLocation = os.path.dirname(__file__)
    cmd = 'python ' + packageLocation + '/' + cmd

    # Run the command
    return subprocess.call(cmd, shell=True)

if __name__ == '__main__':
    sys.exit(main())
