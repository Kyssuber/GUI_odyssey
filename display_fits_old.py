'''
GOAL: in a GUI, display and loop through all .fits files (if any) in user directory. 
Gnarly features: status label, forward/back buttons in order to browse images, entry bar to change color schemes. 
'''

#import various libraries
from tkinter import *
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from astropy.io import fits
from tkinter import font as tkFont  # for convenience

#set up main GUI window
root = Tk()
root.title('FITS Viewer')

#create a font preference
helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')

#create two frames, side-by-side.
frame_display = LabelFrame(root,text='Display',padx=5,pady=5)
frame_display.grid(row=0,column=0)

frame_widgets = LabelFrame(root,text='Edit Color Scheme',padx=2,pady=2)
frame_widgets.grid(row=0,column=1,sticky='N')

###########

#create a wittle section to print x,y coordinates of cursor position (when left-clicked)
frame_coord = LabelFrame(root,text='Image Coordinates',padx=5,pady=5)
frame_coord.grid(row=0,column=1)

#add empty label
labelle = Label(frame_coord,text='(x_coord, y_coord)',font=helv20)
labelle.grid(row=0,column=0)

#create command function
def print_location(event, length):
    
    #print(event.x,event.y)
    
    '''
    canvas returns the pixel coordinates of the CANVAS, not of the plot. A few complications:
       1. pixels are not 1-to-1, so moving from pixel (40,40) to pixel (41,41) on canvas will
          not necessarily go from (10,10) to (11,11) on the plot. Scale is different!
       2. there is a bit of white space in between the canvas and the beginning of the plot
    through heaps of trial and error, I have settled on an empirically-derived scale (length of image/465)
    as well as subtracting from that the similarly empirically-derived white space (~75 canvas pixels)*(scale)
    note that I subtract these values from the image's height, since the y-coordinate is flipped in Canvas.
    ONE YET UNRESOLVED PROBLEM --> if I rescale the window, the modifications below no longer apply.
    '''
    
    scale = length/463
    x = np.round(event.x*scale - 75*scale, 2)
    y = np.round(length - (event.y*scale - 75*scale), 2)
    
    #edit the coordinate label
    if (x<=length) & (y<=length) & (x>0) & (y>0):
        labelle.config(text=f'({x}, {y})',font=helv20)   
    else:
        labelle.config(text='(x_coord, y_coord)',font=helv20)
                    
    #print(f' location of x={event.x*scale - 75*scale}, location of y={length - (event.y*scale - 75*scale)}')

###########

#grab current directory, generate list of strings representing item names in said directory
path_to_dir = os.getcwd()
filenames = os.listdir(path_to_dir)

#empty data list
data_list = []

#filters out directory items that are not fits files; adds fits data from correct files to data_list.
for file in np.asarray(filenames):
    if ('.fits' not in file):
        filenames.remove(file)
    else:
        data_list.append(fits.getdata(file))

#if there are no relevant fits files, then errors abound.
if filenames==0:
    print('No FITS files are in cwd. You may encounter errors when compiling the GUI.')

#entry widget...to enter colorbar data.
e = Entry(frame_widgets, width=35, borderwidth=5, bg='black',fg='lime green', font=('Arial 20'))
e.grid(row=0,column=0)     

#some .fits files in the directory may not be 2D images; in this case, I simply plot a 200x200 matrix of noise,
#since python dislikes trying to plt.imshow a data table. 
plt.figure(figsize=(3,3))

try:
    im = plt.imshow(data_list[0],origin='lower')
    plt.title(filenames[0],fontsize=10)
    #define image length; will need for label.bind command (in order to callibrate pixel coordinates)
    im_length = len(data_list[0])
    
except:
    dat=np.random.random((200,200))
    im = plt.imshow(dat,origin='lower')
    plt.title(filenames[0]+' not a 2D image.',fontsize=6)    
    im_length = 200

canvas = FigureCanvasTkAgg(plt.gcf(), master=frame_display) 
    
#create a label instance for the canvas window
label = canvas.get_tk_widget()
label.grid(row=0,column=0,columnspan=3,rowspan=4)
label.bind("<Motion>", lambda event:print_location(event,length=im_length))
    
#command to change colormap of the cutout pixels
change_colormap_manual = lambda: (im.set_cmap(e.get()), canvas.draw())

#add status bar
n_images = str(len(filenames))
status = Label(frame_display, text="Image 1 of {}".format(n_images), bd=1, relief=SUNKEN)

#define the 'forward button widget'
def forward(image_index):
    
    #call variables
    global label
    global button_forward
    global button_back
    global n_images
    
    #eliminate the current canvas object, then close the plot. I add plt.close() for memory/performance purposes
    label.unbind('<Return>')
    label.delete('all')
    plt.close()
    
    #some .fits files in the directory may not be 2D images; in this case, I simply plot a 200x200 matrix of noise,
    #since python dislikes trying to plt.imshow a data table. 
    plt.figure(figsize=(3,3))
    try:
        im = plt.imshow(data_list[image_index],origin='lower')
        plt.title(filenames[image_index],fontsize=10)        
        im_length = len(data_list[image_index])
    except:
        dat=np.random.random((200,200))
        im = plt.imshow(dat,origin='lower')
        plt.title(filenames[image_index]+' not a 2D image.',fontsize=6)
        im_length = 200
        print('Not a 2D image.')
    
    canvas = FigureCanvasTkAgg(plt.gcf(), master=frame_display)
    
    #create a label instance for the canvas window
    label = canvas.get_tk_widget()
    label.bind('<Return>', lambda event, arg=im_length:print_location(event,length=arg))

    #forward button will bring user to the next, next image (image_index+1). sort of neat how you can call the function within the function. Likewise with the back button.
    button_forward = Button(frame_display, text='>>', font=helv20, fg='magenta', command=lambda: forward(image_index+1))
    button_back = Button(frame_display, text='<<', font=helv20, fg='magenta', command=lambda: back(image_index-1))
    
    #if user has arrived at the last image, then disable the forward button.
    if image_index == len(filenames)-1:
        button_forward = Button(frame_display, text='>>', font=helv20, state=DISABLED)
    
    #new image; new colorbar command. I *could* create a function for this line, but I can't be bothered.
    change_colormap_manual = lambda: (im.set_cmap(e.get()), canvas.draw())
    
    #add color button
    color_button = Button(frame_widgets, text='Set Manual Color Scheme', font=helv20, command=change_colormap_manual)
    color_button.grid(row=1,column=0)
    
    #update status label
    status = Label(frame_display, text="Image {} of ".format(str(image_index+1))+n_images, bd=1, relief=SUNKEN)
        
    #add status and...every other button.
    label.grid(row=0,column=0,columnspan=3,rowspan=4)
    button_back.grid(row=4,column=0)
    button_forward.grid(row=4,column=2)
    status.grid(row=5,column=0,columnspan=3,sticky=W+E)
    
    
#define the 'back button' widget (see above for notes)    
def back(image_index):
    global label
    global button_forward
    global button_back
    global n_images
    
    label.delete('all')
    plt.close()
    
    #some .fits files in the directory may not be 2D images; in this case, I simply plot a 200x200 matrix of noise,
    #since python dislikes trying to plt.imshow a data table. 
    plt.figure(figsize=(3,3))
    try:
        im = plt.imshow(data_list[image_index],origin='lower')
        plt.title(filenames[image_index],fontsize=10)
        canvas = FigureCanvasTkAgg(plt.gcf(), master=frame_display)    
    except:
        dat=np.random.random((200,200))
        im = plt.imshow(dat,origin='lower')
        plt.title(filenames[image_index]+' not a 2D image.',fontsize=6)
        canvas = FigureCanvasTkAgg(plt.gcf(), master=frame_display)
    
    label = canvas.get_tk_widget()
    button_forward = Button(frame_display, text='>>', font=helv20, fg='magenta', command=lambda: forward(image_index+1))
    button_back = Button(frame_display, text='<<', font=helv20, fg='magenta', command=lambda: back(image_index-1))
    
    if image_index == 0:
        button_back = Button(frame_display, text='<<', font=helv20, state=DISABLED)
    
    change_colormap_manual = lambda: (im.set_cmap(e.get()), canvas.draw())
    color_button = Button(frame_widgets, text='Set Manual Color Scheme', font=helv20, command=change_colormap_manual)
    color_button.grid(row=1,column=0)
    
    status = Label(frame_display, text="Image {} of ".format(str(image_index+1))+n_images, bd=1, relief=SUNKEN)

    label.bind("<Button-1>", print_location)
    
    label.grid(row=0,column=0,columnspan=3,rowspan=4)
    button_back.grid(row=4,column=0)
    button_forward.grid(row=4,column=2)
    status.grid(row=5,column=0,columnspan=3,sticky=W+E)

#in the initial frames, define and add the buttons! And the status! 
color_button = Button(frame_widgets,text='Set Manual Color Scheme', font=helv20, command=change_colormap_manual)
button_back = Button(frame_display, text='<<', font=helv20, fg='magenta', command=lambda: back(0), state=DISABLED)
button_forward = Button(frame_display, text='>>', font=helv20, fg='magenta', command=lambda: forward(1))
button_quit = Button(frame_display, text='Terminate', padx=20, pady=10, font=helv20, command=root.quit)

color_button.grid(row=1,column=0) 
button_back.grid(row=4,column=0)
button_quit.grid(row=4,column=1)
button_forward.grid(row=4,column=2)

status.grid(row=5,column=0,columnspan=3,sticky=W+E)

#control dynamic resizing of widgets
for i in range(5):
    frame_display.grid_columnconfigure(i,weight=1)
    frame_display.grid_rowconfigure(i,weight=1)
    frame_widgets.grid_columnconfigure(i,weight=1)
    frame_widgets.grid_rowconfigure(i,weight=1)
    frame_coord.grid_columnconfigure(i,weight=1)
    frame_coord.grid_rowconfigure(i,weight=1)
    
    root.grid_columnconfigure(i,weight=1)
    root.grid_rowconfigure(i,weight=1)

#annnnnnnnd, activate.
root.mainloop()