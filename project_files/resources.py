from PyQt5.QtGui import QIcon
import os

def get_icon_path(name):
    return os.path.join(os.path.dirname(__file__), 'icons', f'{name}.png')

class Icons:
    MAIN = get_icon_path('main')
    ADD = get_icon_path('add')
    DELETE = get_icon_path('delete')
    SAVE = get_icon_path('save')
    EXPORT = get_icon_path('export')
    FILE = get_icon_path('file') 