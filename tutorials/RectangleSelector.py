###ADAPTED FROM https://gist.github.com/GenevieveBuckley/aa46f72cb64637ae2a9d8c7d88aac588

from matplotlib.widgets import RectangleSelector
from matplotlib import pyplot as plt
import numpy as np

X = np.arange(400).reshape(20, 20)

def _select_rectangle_callback(eclick, erelease):
    """eclick and erelease are the press and release events"""
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata


def toggle_selector(event):
    """Matplotlib interactive selection."""
    if event.key in ['Q', 'q'] and toggle_selector.RS.active:
        toggle_selector.RS.set_active(False)
    if event.key in ['A', 'a'] and not toggle_selector.RS.active:
        toggle_selector.RS.set_active(True)


def select_rectangle(image):
    """Return location of interactive user click on image.
    Parameters
    ----------
    image : AdornedImage or 2D numpy array.
    Returns
    -------
    center, extents
          Rectangle center and extents.
          Coordinates are in x, y format & real space units.
          (Units are the same as the matplotlib figure axes.)
          Rectangle extents are given as: (xmin, xmax, ymin, ymax).
    """
    fig, ax = quick_plot(image)
    # Here are the docs fir the matplotlib RectangleSelector
    # https://matplotlib.org/3.1.0/api/widgets_api.html#matplotlib.widgets.RectangleSelector
    toggle_selector.RS = RectangleSelector(ax, _select_rectangle_callback,
                                           drawtype='box', useblit=True,
                                           # don't use middle button
                                           button=[1, 3],
                                           minspanx=5, minspany=5,
                                           spancoords='pixels',
                                           interactive=True)
    

    
    plt.show()
    center = toggle_selector.RS.center  # xy coord, units same as plot axes
    extents = toggle_selector.RS.extents  # Return (xmin, xmax, ymin, ymax)

    return center, extents


def quick_plot(image):
    """Display image with matplotlib.pyplot
    Parameters
    ----------
    image : Adorned image or numpy array
        Input image.
    Returns
    -------
    fig, ax
        Matplotlib figure and axis objects.
    """
    fig, ax = plt.subplots(1)
    display_image = image.data
    height, width = display_image.shape

    ax.set_xlabel('Distance from origin (pixels)')
    ax.set_xlim(0,display_image.shape[0])
    ax.set_ylim(0,display_image.shape[1])
    ax.imshow(display_image, cmap='rainbow', extent=[0,display_image.shape[0],0,display_image.shape[1]])
    return fig, ax

if __name__ == '__main__':
    center, extents = select_rectangle(X)
    print(center, extents)