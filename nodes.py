'''
    ComfyUI_EnvAutopsyAPI is a powerful debugging tool designed for ComfyUI that provides 
    in-depth analysis of your environment and dependencies through an API interface. 
    This tool allows you to inspect environment variables, pip packages, and dependency trees, 
    making it easier to diagnose and resolve issues in your ComfyUI setup.

'''

import os,sys
import subprocess
import json

from aiohttp import web
from server import PromptServer
import asyncio

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader

from server import PromptServer

# Setup Jinja2 environment
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'templates')
env = Environment(loader=FileSystemLoader(template_dir))

# Content types for the API
content_types = {
    'json': {'content_type': 'application/json'},
    'html': {'content_type': 'text/html'},
    'plain': {'content_type': 'text/plain'},
    'text': {'content_type': 'text/plain'},
    None: {'content_type': 'text/plain'},
}

# Get content type based on query parameters
# thses can be used to trigger different content types in endpoints
def get_content_type(request):
    content_type = None
    # get the query parameters

    for key in ('ct','content-type'):
        if key in request.query:
            content_type = request.query[key]
            break
    if not content_type:
        for key in content_types:
            if key in request.query:
                content_type = key
                break
    
    return {'content_type':content_types[content_type],'name':content_type}


@dataclass
class Package:
    name: str
    version: str

# utility function to run a command and get the output
async def run_command(cmd: list) -> Dict[str, str]:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return {
        'stdout': stdout.decode('utf-8'),
        'stderr': stderr.decode('utf-8')
    }


######################################################
############# Get environment variables ##############
######################################################
def get_environment() -> Dict[str, str]:
    return dict(os.environ)

@PromptServer.instance.routes.get("/api/env")
async def serve_environment(request: web.Request) -> web.Response:
    try:
        environment = get_environment()
        template = env.get_template('environment.html')
        html_content = template.render(environment=environment, os=os)
        return web.Response(text=html_content, content_type='text/html')
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return web.Response(text=error_message, status=500)


######################################################
############# Get PIP freeze information #############
######################################################
async def get_pip_freeze() -> List[Package]:
    result = await run_command(['pip', 'freeze'])
    return [Package(*line.split('==')) for line in result['stdout'].splitlines() if '==' in line]


@PromptServer.instance.routes.get("/api/packages")
async def serve_pip_freeze(request: web.Request) -> web.Response:
    try:
        packages = await get_pip_freeze()
        template = env.get_template('pip_freeze.html')
        html_content = template.render(packages=packages)
        return web.Response(text=html_content, content_type='text/html')
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return web.Response(text=error_message, status=500)




######################################################
############# Get python information #############
######################################################

@PromptServer.instance.routes.get("/api/python")
async def serve_pip_freeze(request: web.Request) -> web.Response:
    try:
        packages = sys
        template = env.get_template('python.html')
        html_content = template.render(packages=packages)
        return web.Response(text=html_content, content_type='text/html')
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return web.Response(text=error_message, status=500)



######################################################
############# Get pip dependency tree info ###########
######################################################
def parse_pipdeptree_output(warnings_stderr: str, json_stdout: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    # Parse warnings from stderr of the basic call
    warnings = [line.strip() for line in warnings_stderr.split('\n') if line.strip()]
    
    # If no warnings found, add a message
    if not warnings:
        warnings.append("No warnings found. Your environment appears to be conflict-free!")

    # Parse JSON for dependency tree
    json_data = json.loads(json_stdout)
    
    def process_package(package: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": package.get("package_name", "Unknown"),
            "version": package.get("installed_version", "Unknown"),
            "required_version": package.get("required_version"),
            "dependencies": [process_package(dep) for dep in package.get("dependencies", [])]
        }
    
    tree = [process_package(package) for package in json_data]
    return warnings, tree

# Serve the dependency tree
@PromptServer.instance.routes.get("/api/dependency_tree")
async def serve_dependency_tree(request: web.Request) -> web.Response:
    try:
        pyexec = sys.executable

        # Run pipdeptree twice: once for warnings, once for JSON tree (unfortunate)
        ret = await run_command([pyexec,'-m','pipdeptree'])
        warnings_raw_text = ret['stderr']
        raw_text = ret['stdout']

        # more universal way to run: must test for stderr and stdout to validate that it works
        json_result = await run_command([pyexec,'-m','pipdeptree','--json-tree'])
        
        warnings, tree = parse_pipdeptree_output(warnings_raw_text, json_result['stdout'])
        
        # Add debug information
        debug_info = {
            'warnings_count': len(warnings),
            'tree_count': len(tree),
            'first_warning': warnings[0] if warnings else 'No warnings',
            'first_package': tree[0]['name'] if tree else 'No packages'
        }
        
        template = env.get_template('dependency_tree.html')
        html_content = template.render(warnings=warnings, tree=tree, debug=debug_info, raw_text=raw_text, warnings_raw_text=warnings_raw_text)
        
        return web.Response(text=html_content, content_type='text/html')
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return web.Response(text=error_message, status=500)

# Add this line to serve static files
PromptServer.instance.app.router.add_static('/env-autopsy-api/', path=os.path.join(current_dir, 'static'), name='static')

#############################################################
NODE_CLASS_MAPPINGS = {}

