
# You'll need to add these two lines in The Grove's __init__.py file in order for
# the plugin to recognize the GardenerBuild file you need to add.


# INSTALLATION : Add this below line 112 in __init__.py

importlib.reload(GardenerBuild)

# INSTALLATION : Add this below line 153 in __init__.py

from . import GardenerBuild