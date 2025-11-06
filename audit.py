#!/usr/bin/env python3
import os
import shutil
import subprocess
import termcolor
import config
import time


# Directory where the script lives
INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
# Expand environment variables and metacharacters in the log folder path
config.AUDIT_FOLDER = os.path.expanduser(os.path.expandvars(config.AUDIT_FOLDER))


# ---------------------- Logging Utilities ----------------------

def log_info(logstr):
    print(termcolor.colored('[+] ' + logstr, 'green'))


def log_warning(logstr):
    print(termcolor.colored('[!] ' + logstr, 'yellow'))


def log_error(logstr):
    print(termcolor.colored('[X] ' + logstr, 'red'))


# ---------------------- Core Utilities ----------------------

def get_fullpath(audit_name, raiseerror=True):
    fullpath = os.path.join(config.AUDIT_FOLDER, audit_name)
    if not os.path.exists(fullpath) and raiseerror:
        raise Exception(f"Audit folder does not exist : {fullpath}")
    return fullpath


def get_home_folder():
    home = os.environ.get('USERPROFILE') or os.path.expanduser('~')
    if not os.path.exists(home):
        raise EnvironmentError("Cannot determine home directory.")
    return home


# ---------------------- File Inventory Logger ----------------------

def generate_audit_file_log(audit_name, mode="start"):
    """Scan the audit folder and generate a log of all files with size and last modified date."""
    audit_path = get_fullpath(audit_name)
    log_file = os.path.join(audit_path, 'logs', 'audit_file_list.txt')

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n=== Audit File Inventory ({mode.upper()} SESSION) ===\n")
        f.write(f"Audit: {audit_name}\n")
        f.write(f"Generated: {time.ctime()}\n\n")

        for root, _, files in os.walk(audit_path):
            for file in files:
                if file == 'audit_file_list.txt':
                    continue  # skip self
                file_path = os.path.join(root, file)
                try:
                    size_kb = os.path.getsize(file_path) / 1024
                    modified = time.ctime(os.path.getmtime(file_path))
                    relative_path = os.path.relpath(file_path, audit_path)
                    f.write(f"{relative_path:80}  {size_kb:10.2f} KB   Modified: {modified}\n")
                except Exception as e:
                    f.write(f"ERROR reading {file}: {e}\n")

    log_info(f"Generated audit file list ({mode}) at: {log_file}")


# ---------------------- Core Functions ----------------------

def list_audits():
    if not os.path.exists(config.AUDIT_FOLDER):
        raise Exception(f"Main folder {config.AUDIT_FOLDER} does not exist.")
    for file in os.listdir(config.AUDIT_FOLDER):
        if os.path.exists(os.path.join(config.AUDIT_FOLDER, file, '.audit')):
            log_info(file)


def init(audit_name):
    if not os.path.exists(config.AUDIT_FOLDER):
        raise Exception(f"Main folder {config.AUDIT_FOLDER} does not exist.")
    fullpath = get_fullpath(audit_name, raiseerror=False)

    if os.path.exists(fullpath):
        raise Exception(f"Audit folder already exists: {fullpath}")

    shutil.copytree(os.path.join(INSTALL_FOLDER, 'skel'), fullpath)

    # Initialize Git repository (Windows version)
    if config.GIT_AUTOCOMMIT:
        try:
            subprocess.check_output(["git", "init", fullpath], shell=True)
            subprocess.check_output(["git", "-C", fullpath, "add", "."], shell=True)
            subprocess.check_output(["git", "-C", fullpath, "commit", "-m", "Initial audit project"], shell=True)
        except Exception as e:
            log_warning(f"Git initialization failed: {e}")

    log_info(f"Created audit project in {get_fullpath(audit_name)}")


def start(audit_name):
    log_info(f"Starting audit session: {audit_name}")
    log_info("Logging of activities and evidence capture simulated (Windows mode)")

    # Auto-generate initial file inventory
    generate_audit_file_log(audit_name, mode="start")

    if config.SCREENSHOTS:
        log_warning("Screenshot automation not supported natively on Windows in this version.")
    if config.GIT_AUTOCOMMIT:
        log_info("Git auto-commit active (manual Windows scheduling required).")

    log_info("Audit session started. You can now perform your tasks.")
    log_info("Use 'python audit.py stop <audit_name>' to end the session.")


def stop(audit_name):
    log_info(f"Stopping audit session: {audit_name}")

    # Auto-generate final file inventory
    generate_audit_file_log(audit_name, mode="stop")

    log_info("Audit stopped. All evidence logs and notes remain in the project folder.")


def export_shell_log(audit_name):
    audit_path = get_fullpath(audit_name)
    logs_dir = os.path.join(audit_path, 'logs')
    shell_dir = os.path.join(logs_dir, 'shell')

    if not os.path.exists(shell_dir):
        log_error(f"No shell logs found in {shell_dir}")
        return

    all_logs = ""
    for root, _, files in os.walk(shell_dir):
        for file in files:
            if file.endswith(".log"):
                with open(os.path.join(root, file), 'r', errors='ignore') as f:
                    all_logs += f"\n{'='*80}\n{file}\n{'='*80}\n{f.read()}"

    html_file = os.path.join(audit_path, "shell_log.html")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write("<html><body><pre>" + all_logs + "</pre></body></html>")

    log_info(f"Exported audit logs to {html_file}")


# ---------------------- CLI Entry Point ----------------------

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description='audit.py (Windows-compatible IT Audit Automation Tool)')
    parser.add_argument('action', help='init|start|stop|export|list')
    parser.add_argument('audit_name', nargs='?', help='Audit name')
    args = parser.parse_args()

    if args.action not in ['init', 'start', 'stop', 'export', 'list']:
        log_error('Invalid action. Use one of: init|start|stop|export|list')
        parser.print_help()
        exit(1)

    if args.action in ['init', 'start', 'stop', 'export'] and not args.audit_name:
        log_error('Specify an audit name.')
        exit(1)

    if args.audit_name:
        args.audit_name = os.path.basename(args.audit_name)

    try:
        if args.action == 'init':
            init(args.audit_name)
        elif args.action == 'start':
            start(args.audit_name)
        elif args.action == 'stop':
            stop(args.audit_name)
        elif args.action == 'export':
            export_shell_log(args.audit_name)
        elif args.action == 'list':
            list_audits()
    except Exception as e:
        log_error(str(e))
