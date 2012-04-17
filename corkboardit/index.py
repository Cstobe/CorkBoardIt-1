import sys
corkboardit = "/home/pstoica/webapps/corkboardit/htdocs"
if not corkboardit in sys.path:
    sys.path.insert(0, corkboardit)

from corkboardit import app as application