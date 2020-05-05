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
selection = {} #Stores the selected indicies.
colorPointsHistory = []

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

def backBtnCallback():
    #Remove the applied color from color map and update view
    colorPoints[colorPointsHistory[-1],:] = [0,0,0]
    updatePlyViewerWindow(True)
    del colorPointsHistory[-1] #Delete the previous indecies from history
    #Display instructions:
    instructionWindow['landmarkPos'] = instructionWindow['landmarkPos'] - 1
    landmark = instructionWindow['landmarks'][instructionWindow['landmarkPos']-1]
    updateInstructionTxt("Please select " + str(landmark['name'])[1:] + ", then click next. "+str(instructionWindow['landmarkPos']+1)+"/"+str(instructionWindow['landmarks'].shape[0]))
    if instructionWindow['landmarkPos'] == 0:
        disableBackBtn()

def actionBtnCallback():
    landmark = instructionWindow['landmarks'][instructionWindow['landmarkPos']]
    instructionWindow['landmarkPos'] = instructionWindow['landmarkPos'] + 1
    updateInstructionTxt("Please select " + str(landmark['name'])[1:] + ", then click next. "+str(instructionWindow['landmarkPos']+1)+"/"+str(instructionWindow['landmarks'].shape[0]))
    
    #Change color
    if instructionWindow['landmarkPos']>0:
        enableBackBtn()
        colorlandmark = instructionWindow['landmarks'][instructionWindow['landmarkPos']-2]
        print(colorlandmark['name'])
        print([colorlandmark['r'],colorlandmark['g'],colorlandmark['b']])
        selectedIndecies = getSelectedPointsFromPlyViewerWindow()
        if len(selectedIndecies)>0:
            global colorPoints, dataPoints,selection
            colorPoints[selectedIndecies.tolist(),:] = [colorlandmark['r'],colorlandmark['g'],colorlandmark['b']]
            colorPointsHistory.append(selectedIndecies.tolist())
            updatePlyViewerWindow(True)
            selection[str(colorlandmark['name'])] = json.dumps({"indecies":selectedIndecies.tolist(),"points":dataPoints[selectedIndecies.tolist(),:].tolist()})
        else:
            None #Todo: Prompt user if they're sure they want to skip
    #When they're done, save        
    if instructionWindow['landmarkPos'] >= instructionWindow['landmarks'].shape[0]:
        disableActionBtn()
        updateInstructionTxt("You're finished. The file has been saved to the original directory with your name and _annotated as suffixes. Press quit to exit.")
        savePLY()



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
    #Ask for name
    while "user" not in instructionWindow or instructionWindow["user"] == "" or instructionWindow["user"] is None:
        instructionWindow["user"] = simpledialog.askstring("Annotator name", "What's your name? (Keep this answer consistent between files)",
                                parent=root)
    instructionWindow["user"] = str(instructionWindow["user"]).strip()
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

def getSelectedPointsFromPlyViewerWindow():
    try:
        return plyViewerWindow.get('selected')
    except:
        callQuit("Can't connect to viewer") #Can't connect to viewer.

def savePLY():
    global dataPoints, colorPoints, selection
    disableBackBtn()
    #Save indecies:
    with open(instructionWindow["filename"][:-4]+'_'+instructionWindow["user"]+'_selections.json', 'w') as fp:
        json.dump(selection, fp)
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
    PlyData([el]).write(instructionWindow["filename"][:-4]+'_'+instructionWindow["user"]+'_annotated.ply')


if __name__ == "__main__":
    dataPoints, colorPoints, filename = readPly() #Prompt user and get ply file
    instructionWindow, plyViewerWindow = loadGUI(filename) #Load up gui
    #Update the gui for the first cycle
    updatePlyViewerWindow()
    #Read landmarks
    instructionWindow['landmarks'] = np.genfromtxt('landmarks.csv', delimiter=',',skip_header =1,dtype=[('r','i8'),('g','i8'),('b','i8'),('name','S50')])
    instructionWindow['landmarkPos'] = -1
    selection["min"] = np.min(dataPoints,axis=0).tolist() #Save min x y z for calibration later if needed.
    while (keepAlive):
        if debug:
            print(getSelectedPointsFromPlyViewerWindow())
            time.sleep(0.5)
        instructionWindow["window"].update_idletasks()
        instructionWindow["window"].update()
        # getSelectedPointsFromPlyViewerWindow()
        time.sleep(0.05)