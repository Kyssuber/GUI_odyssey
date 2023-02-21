from tkinter import *


#create window
root = Tk()

def myclick():
    global counter
    counter+=1
    myLabel=Label(root, text='I clicked the button {} time(s)!'.format(str(counter))).grid(row=1,column=0)
    myLabel2 = Label(root)
    myLabel2.grid(row=2,column=0)
    if counter==50:
        myLabel2.config(text='Go touch grass.')      
    if counter == 100:
        myButton = Button(root, text='Click Me', padx=50,fg='white', command=DISABLED).grid(row=0,column=0)
        touchgrass = Button(root,text='Click to Touch Grass', padx=50, fg='green', command=root.quit).grid(row=3,column=0)

myButton = Button(root, text='Click Me', padx=50, command=myclick).grid(row=0,column=0)

#padx=50 will change width of button padding.
#state=DISABLED will disable the buttton widget.

#create 'event loop.' Allows root to run until user terminates window.
if __name__ == '__main__':
    counter=0
    root.mainloop()
    root.destroy()


