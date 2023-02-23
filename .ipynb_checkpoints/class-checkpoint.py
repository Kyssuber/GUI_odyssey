'''
GOAL: re-format display_fits_RADEC.py in a more readable format.
Layout adopted from https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter/7557028#7557028
'''

import tkinter as tk
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt
from astropy.io import fits
from astropy.wcs import WCS
from tkinter import font as tkFont
from tkinter import messagebox

class App(tk.Tk):
    
    def __init__(self, *args, **kwargs):          #INITIALIZE; will always run when App class is called.
        tk.Tk.__init__(self, *args, **kwargs)     #initialize tkinter; args are parameter arguments, kwargs can be dictionary arguments
        
        self.title('Sample Tkinter Structuring')
        self.geometry('1100x700')
        self.resizable(True, True)
        
        #will be filled with heaps of frames and frames of heaps. 
        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)     #fills entire container space
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)

        ## Initialize Frames
        self.frames = {}     #empty dictionary
        frame = MainPage(container, self)   #define frame  
        self.frames[MainPage] = frame     #assign new dictionary entry {MainPage: frame}
        frame.grid(row=0,column=0,sticky='nsew')   #define where to place frame within the container...CENTER!
        
        self.show_frame(MainPage)  #a method to be defined below
    
    def show_frame(self, cont):     #cont represents the controller, enables switching between frames/windows
        frame = self.frames[cont]
        frame.tkraise()   #will raise window/frame to the 'front'
        
        
#inherits all from tk.Frame; will be on first window
class MainPage(tk.Frame):    
    
    def __init__(self, parent, controller):
        #first frame...
        tk.Frame.__init__(self,parent)
        
        self.frame_display=tk.LabelFrame(self,text='Display',font='Vendana 15',padx=5,pady=5)
        self.frame_display.grid(row=0,column=0,rowspan=10)
        
        self.get_filedat()
    
        #some .fits files in the directory may not be 2D images; in this case, I simply plot a 200x200 matrix of noise, since python dislikes trying to plt.imshow a data table. 
        plt.figure(figsize=(3,3))
        try:
            dat = self.data_list[0]
            im = plt.imshow(dat,origin='lower')
            plt.title(self.filenames[0],fontsize=10)
            self.file_titles.append(self.filenames[0])
        except:
            dat=np.random.random((200,200))
            im = plt.imshow(dat,origin='lower')
            plt.title(self.filenames[0]+' not a 2D image.',fontsize=6)
            self.file_titles.append(self.filenames[0]+'.')
        im_length = len(dat)
                
        #set up canvas
        canvas = FigureCanvasTkAgg(plt.gcf(), master=self.frame_display) 
        
        #binds left-click to extract the plot's x,y pixel coordinates, and the value at these coordinates
        #canvas.mpl_connect('button_press_event', lambda event: self.plotClick(event, self.file_titles[0]))
        #canvas.mpl_connect('button_press_event',lambda event: self.plotValue(event, dat, im_length))

        #create a label instance for the canvas window
        label = canvas.get_tk_widget()
        
        #label.config(width=800, height=800)
        label.grid(row=0,column=0,columnspan=3,rowspan=4)
        
       
    def get_filedat(self):    
        path_to_dir = os.getcwd()   #get current working directory
        self.filenames = os.listdir(path_to_dir)   #create list of all filenames in working directory
        
        self.data_list = []
        self.file_titles = []     #titles for plt.imshow. if a 2D image, then title will be same a filename. 
        
        #filters out directory items that are not fits files and reads data from those that are.
        for file in np.asarray(self.filenames):
            if ('.fits' not in file):
                self.filenames.remove(file)
            else:
                self.data_list.append(fits.getdata(file))
         
        if self.filenames==0:
            print('No FITS files in cwd. GUI may not compile correctly, if at all.')

        
        
        
    
if __name__ == "__main__":
    app = App()
    app.mainloop()
    #app.destroy()