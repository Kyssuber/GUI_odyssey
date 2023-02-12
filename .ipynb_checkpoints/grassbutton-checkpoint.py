from tkinter import *


#create window
root = Tk()

def myclick():
    global counter
    counter+=1
    myLabel=Label(root, text='I clicked the button {} time(s)!'.format(str(counter))).grid(row=1,column=0)
    if counter==10:
        myLabel_two=Label(root,text='Find another use of your time.').grid(row=2,column=0)
    if counter==20:
        myLabel_two=Label(root,text='Did I stutter?').grid(row=3,column=0)
    if counter==25:
        myLabel_two=Label(root,text='KILLING SPREE.').grid(row=4,column=0)
    if counter==30:
        myLabel_two=Label(root,text='ABSOLUTE RAMPAGE.').grid(row=4,column=0)
    if counter==40:
        myLabel_two=Label(root,text='THE POPULATION IS NO MORE.').grid(row=4,column=0)
    if counter==50:
        myLabel_two=Label(root,text='Really. You should cease fire now.').grid(row=4,column=0)
    if counter==60:
        myLabel_two=Label(root,text='You must be fun at parties. STOP CLICKING.').grid(row=4,column=0)
    if counter==70:
        myLabel_yikes=Label(root,text='You are pounding your mousepad into oblivion.').grid(row=4,column=0)
    if counter==80:
        myLabel_yikes=Label(root,text='I will no longer humor you with witless remarks. Go touch grass.').grid(row=4,column=0)        
    if counter == 90:
        myButton = Button(root, text='Click Me', padx=50,fg='white', command=DISABLED).grid(row=0,column=0)
        touchgrass = Button(root,text='Click to Touch Grass',padx=50,fg='green',command=root.quit).grid(row=5,column=0)

myButton = Button(root, text='Click Me', padx=50, command=myclick).grid(row=0,column=0)

#padx=50 will change width of button padding.
#state=DISABLED will disable the buttton widget.

#create 'event loop.' Allows root to run until user terminates window.
if __name__ == '__main__':
    counter=0
    root.mainloop()
    root.destroy()


