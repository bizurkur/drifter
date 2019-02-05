from __future__ import absolute_import, division, print_function
import subprocess

def get_cli(cmd, output=False, shell=False):
    command = cmd
    if isinstance(cmd, list):
        command = map(str, command)
    elif not isinstance(cmd, str):
        command = str(command)

    process = subprocess.Popen(
        command,
        shell=shell,
        stdin=None if output else subprocess.PIPE,
        stdout=None if output else subprocess.PIPE,
        stderr=subprocess.STDOUT,
        close_fds=True
        )
    result = process.communicate()

    response = None
    if result and result[0]:
        response = result[0].strip()

    return (response, int(process.returncode))
