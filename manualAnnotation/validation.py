import numpy as np
import pptk
import time
import json
from plyfile import PlyData, PlyElement
import tkinter
from tkinter import Tk, Button, Label, TOP, RIGHT,LEFT, simpledialog
from tkinter.filedialog import askopenfilename

# Define some global vars
instructionWindow = None
plyViewerWindow = None
dataPoints = None
colorPoints = None
keepAlive = True
debug = False
jsonData = []

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

def readJSON():
    global jsonData
    filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file
    print(filename)
    if ("json" not in filename):
        raise RuntimeError("You should supply a json file")
    with open(filename) as f:
        jsonData = json.load(f)

def backBtnCallback():
    enableActionBtn()
    #Display instructions:
    instructionWindow['landmarkPos'] = instructionWindow['landmarkPos'] - 1
    if instructionWindow['landmarkPos'] == 0:
        disableBackBtn()
    validateLandmark()    

def actionBtnCallback():
    instructionWindow['landmarkPos'] = instructionWindow['landmarkPos'] + 1
    validateLandmark()
    if instructionWindow['landmarkPos']+1 >= instructionWindow['landmarks'].shape[0]:
        disableActionBtn()
    if instructionWindow['landmarkPos'] > 0:
        enableBackBtn()
        
def validateLandmark():
    global jsonData, colorPoints
    landmark = instructionWindow['landmarks'][instructionWindow['landmarkPos']]
    updateInstructionTxt("Showing " + str(landmark['name'])[1:] + ". "+str(instructionWindow['landmarkPos']+1)+"/"+str(instructionWindow['landmarks'].shape[0]))
    colorPoints[:,:] = [0, 0, 0]
    if str(landmark['name']) in jsonData:
        landmark_data = jsonData[str(landmark['name'])]
        indecies= json.loads(landmark_data)["indecies"]
        colorPoints[indecies,:] = [255, 0, 0]
    else:
        updateInstructionTxt("Landmark " + str(landmark['name'])[1:] + " was skipped. "+str(instructionWindow['landmarkPos']+1)+"/"+str(instructionWindow['landmarks'].shape[0]))
    updatePlyViewerWindow(True)


def disableActionBtn():
    global instructionWindow
    instructionWindow["actionBtn"]["state"]="disabled"
def enableActionBtn():
    global instructionWindow
    instructionWindow["actionBtn"]["state"]="normal"
def disableBackBtn():
    global instructionWindow
    instructionWindow["backBtn"]["state"]="disabled"
def enableBackBtn():
    global instructionWindow
    instructionWindow["backBtn"]["state"]="normal"


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
    instructionTxt = Label(root, text="Click Next to get started.",
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
    #Back button:
    backBtn = Button(root, 
       text='Go Back', 
       fg="darkgreen", 
       command= backBtnCallback,
       state="disabled")
    instructionWindow["backBtn"] = backBtn
    backBtn.pack(side=LEFT, padx=10)
    #Quit button:
    Button(root,text='Quit', 
        command=callQuit).pack(side=RIGHT, padx=10)
    root.protocol("WM_DELETE_WINDOW", callQuit) #If you x out, call callQuit()
    #Create pptk point cloud viewer:
    plyViewerWindow = pptk.viewer([0,0,0],debug=True)
    plyViewerWindow.set(point_size=0.001,show_grid=True)
    plyViewerWindow.color_map('jet')
    return instructionWindow,plyViewerWindow

def updateInstructionTxt(msg):
    global instructionWindow
    instructionWindow["instructionTxt"]["text"] = msg

def updatePlyViewerWindow(attributesOnly = False):
    global plyViewerWindow, dataPoints, colorPoints
    if attributesOnly:
        plyViewerWindow.attributes(colorPoints)
        plyViewerWindow.set(selected=[])
        return
    plyViewerWindow.clear()
    plyViewerWindow.load(dataPoints, colorPoints)



if __name__ == "__main__":
    dataPoints, colorPoints, filename = readPly() #Prompt user and get ply file
    readJSON()
    instructionWindow, plyViewerWindow = loadGUI(filename) #Load up gui
    #Update the gui for the first cycle
    updatePlyViewerWindow()
    #Read landmarks
    instructionWindow['landmarks'] = np.genfromtxt('landmarks.csv', delimiter=',',skip_header =1,dtype=[('r','i8'),('g','i8'),('b','i8'),('name','S50')])
    instructionWindow['landmarkPos'] = -1
    while (keepAlive):
        instructionWindow["window"].update_idletasks()
        instructionWindow["window"].update()
        time.sleep(0.05)