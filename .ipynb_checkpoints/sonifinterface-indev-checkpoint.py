'''
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
from tkinter import filedialog

import sys
from midiutil import MIDIFile
from audiolazy import str2midi
from pygame import mixer
from io import BytesIO

from scipy.stats import scoreatpercentile
from astropy.visualization import simple_norm

homedir = os.getenv('HOME')

#create main window container, into which the first page will be placed.
class App(tk.Tk):
    
    def __init__(self, *args, **kwargs):          #INITIALIZE; will always run when App class is called.
        tk.Tk.__init__(self, *args, **kwargs)     #initialize tkinter; args are parameter arguments, kwargs can be dictionary arguments
        
        self.title('Sample Tkinter Structuring')
        self.geometry('1000x700')
        self.resizable(True,True)
        self.rowspan=10
        
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
        for i in range(self.rowspan):
            frame.columnconfigure(i, weight=1)
            frame.rowconfigure(i, weight=1)
        
        self.show_frame(MainPage)  #a method to be defined below (see MainPage class)
    
    def show_frame(self, cont):     #'cont' represents the controller, enables switching between frames/windows...I think.
        frame = self.frames[cont]
        frame.tkraise()   #will raise window/frame to the 'front;' if there is more than one frame, quite handy.
        
        
#inherits all from tk.Frame; will be on first window
class MainPage(tk.Frame):    
    
    def __init__(self, parent, controller):
        
        #defines the number of rows/columns to resize when resizing the entire window.
        self.rowspan=10
        
        #define a font
        self.helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')
        
        self.textbox="GOAL: Generate and interact with a 2D sonified galaxy cutout. \n \n GENERAL INSTRUCTIONS: \n \n (1) Enter filepath into the top entry box click 'Browse' in order to search your local machine's good ol' inventory. Then click 'Enter'. \n \n (2) Clicking 'Sonify!' will create consecutive vertical strips of pixels, calculate the mean value of each band, and map the resulting array of means to a MIDI note which is ultimately translated into a piano key. [Presently, the only chord available is D-major.] The full sonification will play automatically upon clicking the button, using the default y scale (scales the mean pixel data, ydata**yscale), min and max velocities (the min and max volume, respectively, ranging from 0 to 127), and the BPM (beats per minute -- higher BPM begets a speedier tune). The user can edit these values to manipulate the sound, clicking 'Sonify!' once more to audibly harvest the outcome of their fiddling. \n \n (3) Left-clicking the figure to the left will allow the user to visualize an individual column of sonified pixels (red bar), as well as simultaneously hear the MIDI note corresponding to the mean pixel value of that column. The bottom-right widget of the GUI handily displays this mean value if the user is so inclined to know. \n \n (4) If the user wishes to view another galaxy, they may click 'Browse' to find a second FITS file and go wild. I certainly cannot thwart their efforts, for I am a simple text box."
        
        #first frame...
        tk.Frame.__init__(self,parent)
        
        #NOTE: columnconfigure and rowconfigure below enable minimization and maximization of window to also affect widget size
        
        #create display frame, which will hold the canvas and a few button widgets underneath.
        self.frame_display=tk.LabelFrame(self,text='Display',font='Vendana 15',padx=5,pady=5)
        self.frame_display.grid(row=0,column=0,rowspan=5)
        for i in range(self.rowspan):
            self.frame_display.columnconfigure(i, weight=1)
            self.frame_display.rowconfigure(i, weight=1)
        
        #create buttons frame, which currently only holds the 'save' button, 'browse' button, and entry box.
        self.frame_buttons=tk.LabelFrame(self,text='File Browser',padx=5,pady=5)
        self.frame_buttons.grid(row=2,column=1)
        for i in range(self.rowspan):
            self.frame_buttons.columnconfigure(i, weight=1)
            self.frame_buttons.rowconfigure(i, weight=1)
            
        #create soni frame, which holds the event button for converting data into sound (midifile).
        self.frame_soni=tk.LabelFrame(self,padx=5,pady=5)
        self.frame_soni.grid(row=3,column=1,sticky='se')
        for i in range(self.rowspan):
            self.frame_soni.columnconfigure(i, weight=1)
            self.frame_soni.rowconfigure(i, weight=1)
        
        #create coord frame, which holds the event labels for the mean pixel value.
        self.frame_value=tk.LabelFrame(self,padx=5,pady=5)
        self.frame_value.grid(row=4,column=1,sticky='se')
        for i in range(self.rowspan):
            self.frame_value.columnconfigure(i, weight=1)
            self.frame_value.rowconfigure(i, weight=1)
        
        self.galaxy_to_display()
        '''
        INSERT FUNCTIONS TO RUN HERE.
        '''
        self.initiate_vals()
        self.add_info_button()
        self.create_soni_widget()
        
    def initiate_vals(self):
        self.val = tk.Label(self.frame_value,text='Pixel Value: ',font='Ariel 20')
        self.val.grid(row=0,column=0)
    
    def galaxy_to_display(self):
        self.path_to_im = tk.Entry(self.frame_buttons, width=35, borderwidth=2, bg='black', fg='lime green', font='Arial 20')
        self.path_to_im.insert(0,'enter path/to/image.fits')
        self.path_to_im.grid(row=0,column=0,columnspan=2)
        self.add_browse_button()
        self.add_enter_button()
        
    def create_soni_widget(self):
        
        #create all entry textboxes (with labels and initial values), midi button
        
        ylab = tk.Label(self.frame_soni,text='yscale').grid(row=0,column=0)
        self.y_scale_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', font='Arial 15')
        self.y_scale_entry.insert(0,'0.5')
        self.y_scale_entry.grid(row=0,column=1,columnspan=1)
        
        vmin_lab = tk.Label(self.frame_soni,text='Min Velocity').grid(row=1,column=0)
        self.vel_min_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', font='Arial 15')
        self.vel_min_entry.insert(0,'10')
        self.vel_min_entry.grid(row=1,column=1,columnspan=1)
        
        vmax_lab = tk.Label(self.frame_soni,text='Max Velocity').grid(row=2,column=0)
        self.vel_max_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', font='Arial 15')
        self.vel_max_entry.insert(0,'100')
        self.vel_max_entry.grid(row=2,column=1,columnspan=1)
        
        bpm_lab = tk.Label(self.frame_soni,text='BPM').grid(row=3,column=0)
        self.bpm_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', font='Arial 15')
        self.bpm_entry.insert(0,'35')
        self.bpm_entry.grid(row=3,column=1,columnspan=1)
        
        self.add_midi_button()

    def add_info_button(self):
        self.info_button = tk.Button(self.frame_display, text='Click for Info', padx=15, pady=10, font='Ariel 20', command=self.popup)
        self.info_button.grid(row=8,column=1)
    
    def add_browse_button(self):
        self.button_explore = tk.Button(self.frame_buttons ,text="Browse", padx=20, pady=10, font=self.helv20, command=self.browseFiles)
        self.button_explore.grid(row=1,column=0)
        
    def add_enter_button(self):
        self.path_button = tk.Button(self.frame_buttons, text='Enter', padx=20, pady=10, font=self.helv20, command=self.initiate_canvas)
        self.path_button.grid(row=1,column=1)
    
    def add_midi_button(self):
        self.midi_button = tk.Button(self.frame_soni, text='Sonify!', padx=20, pady=10, font=self.helv20, command=self.midi_setup)
        self.midi_button.grid(row=5,column=0,columnspan=2)
    
    def initiate_canvas(self):
        self.dat = fits.getdata(str(self.path_to_im.get()))
        plt.figure(figsize=(5,5))
        self.im=plt.imshow(self.dat,origin='lower')
        plt.title(self.path_to_im.get(),fontsize=10)

        self.im_length = np.shape(self.dat)[0]
        self.y_min = int(self.im_length/2-(0.20*self.im_length))
        self.y_max = int(self.im_length/2+(0.20*self.im_length))
        self.x=self.im_length/2
        
        self.current_bar=plt.scatter(np.zeros(100)+self.x, np.linspace(self.y_min,self.y_max,100), s=3, color='None')
        self.canvas = FigureCanvasTkAgg(plt.gcf(), master=self.frame_display)    
        self.canvas.mpl_connect('button_press_event', self.placeBar)
        try:
            self.canvas.mpl_connect('button_press_event', self.midi_singlenote)
        except:
            print('Sonify first!')
        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=6)
    
    #create command function to print info popup message
    def popup(self):
        messagebox.showinfo('Unconventional README.md',self.textbox)
    
    def placeBar(self, event):  
        self.x=int(event.xdata)
        #if user clicks outside the image bounds, then x is NoneType. y cannot be None, by design. only need to check x.
        if self.x is not None:
            #re-plot bar
            line_x = np.zeros(150)+self.x
            line_y = np.linspace(self.y_min,self.y_max,150)       
            self.current_bar.remove()
            self.current_bar = plt.scatter(line_x,line_y,s=3,color='red')
            
            #extract the mean pixel value from this bar
            value_list = np.zeros(100)
            for index in range(100):
                y_coord = line_y[index]
                px_value = self.dat[int(y_coord)][self.x]   #x will be the same...again, by design.
                value_list[index] = px_value
            mean_px = round(np.mean(value_list),3)
            self.val.config(text=f'Pixel Value: {mean_px}',font='Ariel 16')
            self.canvas.draw()
            
        else:
            print('Click inside of the image!')
            self.val.config(text='Pixel Value: None', font='Ariel 16')
    
    # Function for opening the file explorer window
    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = "/Users/k215c316/vf_html/all_input_fits/", title = "Select a File", filetypes = ([("FITS Files", ".fits")]))
        self.path_to_im.delete(0,tk.END)
        self.path_to_im.insert(0,filename)        
    
##########
#the sonification-specific functions...
##########

    #typical sonification mapping function; maps value(s) from one range to another range; returns floats
    def map_value(self, value, min_value, max_value, min_result, max_result):
        result = min_result + (value - min_value)/(max_value - min_value)*(max_result - min_result)
        return result
    
    def midi_setup(self):
        
        #define various quantities required for midi file generation
        self.y_scale = float(self.y_scale_entry.get())
        self.strips_per_beat = 10
        self.vel_min = int(self.vel_min_entry.get())
        self.vel_max = int(self.vel_max_entry.get())
        self.bpm = int(self.bpm_entry.get())
        self.note_names = 'D2-E2-F#2-G2-A2-B2-C#2-D3-E3-F#3-G3-A3-B3-C#3-D4-E4-F#4-G4-A4-B4-C#4-D5-E5-F#5-G5-A5-B5-C#5-D6'   #D-major
        self.note_names = self.note_names.split("-")   #converts self.note_names into a proper list of note strings
        self.soundfont = '/opt/anaconda3/share/soundfonts/FluidR3_GM.sf2'
        
        band = self.dat[:,self.y_min:self.y_max]   #isolates pixels within horizontal band across the image from y_min to y_max
        strips = []   #create empty array for 1px strips
        mean_strip_values = np.zeros(self.im_length)
        
        for i in range(self.im_length):
            strips.append(band[i,:])   #individual vertical strips
            mean_strip_values[i] = np.mean(strips[i])   #the 'ydata'
        
        #rescale strip number to beats
        self.t_data = np.arange(0,len(mean_strip_values),1) / self.strips_per_beat   #convert to 'time' steps
        duration_beats=np.max(self.t_data)   #duration is end of the t_data list, or the max value in this list
        #print('Duration:',duration_beats, 'beats')
        #one beat = one quarter note
        
        y_data = self.map_value(mean_strip_values,min(mean_strip_values),max(mean_strip_values),0,1)   #normalizes values
        y_data_scaled = y_data**self.y_scale
        
        note_midis = [str2midi(n) for n in self.note_names]  #list of midi note numbers
        n_notes = len(note_midis)
        #print('Resolution:',n_notes,'notes')

        #MAPPING DATA TO MIDIS!
        self.midi_data = []
        #for every data point, map y_data_scaled values such that smallest/largest px is lowest/highest note
        for i in range(len(self.t_data)):   #assigns midi note number to whichever y_data_scaled[i] is nearest
            note_index = round(self.map_value(y_data_scaled[i],0,1,0,len(note_midis)-1))
            self.midi_data.append(note_midis[note_index])
    
        #map data to note velocities (equivalent to the sound volume)
        self.vel_data = []
        for i in range(len(y_data_scaled)):
            note_velocity = round(self.map_value(y_data_scaled[i],0,1,self.vel_min,self.vel_max)) #larger values, heavier sound
            self.vel_data.append(note_velocity)
        
        self.midi_allnotes() 
        
    def midi_allnotes(self):
        #create midi file object, add tempo
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        midi_file = MIDIFile(1) #one track
        midi_file.addTempo(track=0,time=0,tempo=self.bpm) #only one track, so track=0th track; begin at time=0, tempo is bpm

        #add midi notes to file
        for i in range(len(self.t_data)):
            midi_file.addNote(track=0, channel=0, pitch=self.midi_data[i], time=self.t_data[i], duration=2, volume=self.vel_data[i])
        midi_file.writeFile(self.memfile)
        
        mixer.init()
        self.memfile.seek(0)
        mixer.music.load(self.memfile)
        mixer.music.play()

    def midi_singlenote(self,event):
        #the setup for playing *just* one note...
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        
        midi_file = MIDIFile(1) #one track
        midi_file.addTrackName(0,0,'Note')
        midi_file.addTempo(track=0, time=0, tempo=self.bpm)
        
        midi_file.addNote(track=0, channel=0, pitch=self.midi_data[self.x], time=self.t_data[1], duration=2, volume=self.vel_data[self.x])
        
        midi_file.writeFile(self.memfile)
        #with open(homedir+'/Desktop/test.mid',"wb") as f:
        #    self.midi_file.writeFile(f)
        
        mixer.init()
        self.memfile.seek(0)   #for whatever reason, have to manually 'rewind' the track in order for mixer to play
        mixer.music.load(self.memfile)
        mixer.music.play()       
        
        
if __name__ == "__main__":
    app = App()
    app.mainloop()
    app.destroy()