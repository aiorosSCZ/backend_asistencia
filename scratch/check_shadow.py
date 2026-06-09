import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import routers.admin

print("routers.admin.datetime is:", routers.admin.datetime)
print("Type of routers.admin.datetime is:", type(routers.admin.datetime))
