'''
+---------------------------------------------------------------------------------+
|                       🔍🛠️ ComfyUI_EnvAutopsyAPI 🛠️🔍                           |
+---------------------------------------------------------------------------------+
|                          ⚠️ SECURITY WARNING ⚠️                                 |
+---------------------------------------------------------------------------------+
| This tool can expose sensitive info if running on a server with a public IP.    |
+---------------------------------------------------------------------------------+
| ➤ Use ONLY for debugging in secure, private environments.                       |
| ➤ DO NOT use on publicly accessible servers without stringent security measures.|
| ➤ Exposed info may include system environments, file paths, and configurations. |
+---------------------------------------------------------------------------------+
| Remember: Prioritize your system's security when using diagnostic tools!        |
+---------------------------------------------------------------------------------+

'''
# warn user of security issues: This should work in terminals:
# TODO: Could make it only if ip is outward facing?
print(__doc__)


import sys,os

# check if dep tree software is installed. If not, see if it is in _plugin_libs (self contained plugin libs)
try:
    import pipdeptree
except Exception as err:
    # lets look in a _plugin_libs directory
    plugin_libs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'_plugin_libs')
    pipdeptree_main_filepath = os.path.join(plugin_libs_path,'pipdeptree','__main__.py')

    if not os.path.exists(pipdeptree_main_filepath):
        print(f'WARNING: EnvAutopsyAPI:dependency_tree execution may not function properly: \n\tFile DOES NOT EXIT {pipdeptree_main_filepath}')
    else:
        if not os.environ.get('PYTHONPATH'):
            os.environ['PYTHONPATH'] = ''
        if plugin_libs_path not in os.environ['PYTHONPATH']:
            os.environ['PYTHONPATH'] += f"{os.pathsep}{plugin_libs_path}"
           
from .nodes import NODE_CLASS_MAPPINGS

# publish the mappings
__all__ = ['NODE_CLASS_MAPPINGS']

