import numpy as np
import pptk
import time
from plyfile import PlyData, PlyElement
import tkinter
from tkinter import *
from tkinter.filedialog import askopenfilename

def readPly():
    global filename
    tkinter.Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file
    print(filename)
    if ("ply" not in filename):
        raise RuntimeError("You should supply a ply file")
    ply = PlyData.read(filename)
    vertex = ply['vertex']
    dataPoints = np.vstack([vertex['x'],vertex['y'],vertex['z']]).T
    colorPoints = np.zeros_like(dataPoints)
    return dataPoints, colorPoints, filename

def actionBtnCallback():
    updateInstructionTxt("hi")
    disableActionBtn()
    print("next")
    savePLY()

def disableActionBtn():
    global instructionWindow
    instructionWindow["actionBtn"]["state"]="disabled"
def enableActionBtn():
    global instructionWindow
    instructionWindow["actionBtn"]["state"]="normal"


def callQuit(msg = None):
    if msg is not None:
        print(msg) #print a message if we have it
    global keepAlive, instructionWindow, plyViewerWindow
    if instructionWindow["window"] is not None:
        instructionWindow["window"].quit() #try quitting the tK gui
    if plyViewerWindow is not None:
        plyViewerWindow.close() #try quitting the point cloud viewer
    keepAlive = False
    print("Exiting..")

def loadGUI(filename):
    #Create instruction window
    instructionWindow = {} #We'll save the interactive Buttons and Labels here.  
    instructionWindow["filename"] = filename #Save the filename
    root = Tk() #Create the window
    instructionWindow["window"] = root #Save a pointer to the window
    root.title("Human segmentation manual annotation")
    #What file did we load:
    Label(root, text="Loaded file: "+filename).pack(side=TOP,pady=10)
    #Instruction text:
    instructionTxt = Label(root, text="Click Next to get started. Use ctrl + drag to highlight points. Right click to clear.",
        fg="red")
    instructionWindow["instructionTxt"] = instructionTxt
    instructionTxt.pack(side=TOP, pady=10)
    #Action button:
    actionBtn = Button(root, 
       text='Next', 
       fg="darkgreen", 
       command= actionBtnCallback)
    instructionWindow["actionBtn"] = actionBtn
    actionBtn.pack(side=LEFT, padx=10)
    #Quit button:
    Button(root,text='Quit', 
        command=callQuit).pack(side=RIGHT, padx=10)
    root.protocol("WM_DELETE_WINDOW", callQuit) #If you x out, call callQuit()
    #Create pptk point cloud viewer:
    plyViewerWindow = pptk.viewer([0,0,0])
    plyViewerWindow.set(point_size=0.001,show_grid=True)
    #Update the gui for the first cycle
    updatePlyViewerWindow()
    return instructionWindow,plyViewerWindow

def updateInstructionTxt(msg):
    global instructionWindow
    instructionWindow["instructionTxt"]["text"] = msg

def updatePlyViewerWindow():
    global plyViewerWindow, dataPoints, colorPoints
    plyViewerWindow.load(dataPoints, colorPoints)

def getSelectedPointsFromPlyViewerWindow():
    try:
        return plyViewerWindow.get('selected')
    except:
        callQuit("Can't connect to viewer") #Can't connect to viewer.

def savePLY():
    global dataPoints, colorPoints
    #Create an empty array to save different datatypes.
    wtype=np.dtype([('x', 'f4'), ('y', 'f4'),('z', 'f4'),('red', 'u1'), ('green', 'u1'), ('blue', 'u1')])
    w=np.empty(dataPoints.shape[0],dtype=wtype)
    w['x'] = dataPoints[:,0]
    w['y'] = dataPoints[:,1]
    w['z'] = dataPoints[:,2]
    w['red'] = colorPoints[:,0]
    w['green'] = colorPoints[:,1]
    w['blue'] = colorPoints[:,2]
    #Create a vertex element (Required by PLY standards)
    el = PlyElement.describe(w, 'vertex')
    #Write it to "{original filename}_annotated.ply"
    PlyData([el]).write(instructionWindow["filename"][:-4]+'_annotated'+'.ply')


instructionWindow = None
plyViewerWindow = None
dataPoints = None
colorPoints = None
keepAlive = True
debug = False
if __name__ == "__main__":
    dataPoints, colorPoints, filename = readPly() #Prompt user and get ply file
    instructionWindow,plyViewerWindow = loadGUI(filename) #Load up gui
    while (keepAlive):
        if debug:
            print(getSelectedPointsFromPlyViewerWindow())
            time.sleep(0.5)
        instructionWindow["window"].update_idletasks()
        instructionWindow["window"].update()