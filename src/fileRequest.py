#!/usr/bin/python3

import json
import os
import sys
import base64
import datetime
import mimetypes
import shutil

UPLOAD_DIR = ""
MAX_FILE_SIZE = (0,)
MAX_TOTAL_SIZE = (0,)
ALLOWED_FILETYPE = []


def read_config(configfile):
    try:
        with open(configfile, "r") as file:
            config = json.load(file)
        file.close()
    except FileNotFoundError:
        config = {}

    global UPLOAD_DIR, MAX_FILE_SIZE, MAX_TOTAL_SIZE, ALLOWED_FILETYPE

    UPLOAD_DIR = config.get("UPLOAD_DIR", "/tmp/uploads/")
    MAX_FILE_SIZE = config.get("MAX_FILE_SIZE", 10485760)
    MAX_TOTAL_SIZE = config.get("MAX_TOTAL_SIZE", 104857600)
    ALLOWED_FILETYPE = config.get(
        "ALLOWED_FILETYPE",
        [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/gif",
            "application/pdf",
            "application/zip",
            "application/json",
            "text/plain",
            "text/csv",
            "text/html",
            "text/markdown",
        ],
    )


def print_headers():
    print(f"Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()


def post_request():
    payload = {}

    if os.environ.get("REQUEST_METHOD", "") == "POST":
        content_length = int(os.environ.get("CONTENT_LENGTH", 0))
        raw_payload = sys.stdin.read(content_length)

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as e:
            payload = {"status": "error", "message": "Invalid JSON payload"}

    return payload


def list_directory(payload):
    dir = payload.get("dir")
    absolute_path = UPLOAD_DIR
    files_info = []

    if dir:
        absolute_path = os.path.join(UPLOAD_DIR, dir)

    files = os.listdir(absolute_path)

    for f in files:
        size = round(os.path.getsize(os.path.join(absolute_path, f)) / 1000, 2)
        created = datetime.datetime.fromtimestamp(
            os.path.getctime(os.path.join(absolute_path, f))
        ).strftime("%Y-%m-%d %H:%M:%S")
        ifFolder = True if os.path.isdir(os.path.join(absolute_path, f)) else False
        filetype = (
            "folder"
            if ifFolder
            else (
                mimetypes.guess_type(f)[0].split("/")[0]
                if mimetypes.guess_type(f)[0]
                else "unknown"
            )
        )

        files_info.append(
            {
                "filename": f,
                "size": size,
                "created": created,
                "filetype": filetype,
                "isFolder": ifFolder,
            }
        )

    if dir:
        files_info.append(
            {
                "filename": "..",
                "size": 0,
                "created": "",
                "filetype": "folder",
                "isFolder": True,
            }
        )

    return {"files": files_info, "totalSize": [total_size(UPLOAD_DIR), MAX_TOTAL_SIZE]}


def check_file_size(filesize):
    if filesize > MAX_FILE_SIZE:
        return False
    return True


def check_filetype(filetype):
    if filetype not in ALLOWED_FILETYPE:
        return False
    return True


def total_size(path):
    total = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            total += os.path.getsize(os.path.join(root, file))
    return total
  

def check_total_size(path):
    if total_size(path) > MAX_TOTAL_SIZE:
        return False
    return True


def upload_files(payload):
    dir = payload.get("dir")
    absolute_path = UPLOAD_DIR

    if dir:
        absolute_path = os.path.join(UPLOAD_DIR, dir)

    for file in payload.get("files", []):
        filename = file.get("filename", "")
        filecontent = file.get("content", "")
        filesize = file.get("filesize", 0)
        filetype = file.get("filetype", "")

        if not check_file_size(filesize):
            return {
                "status": "error",
                "message": f"File {filename} exceeds maximum allowed size of {MAX_FILE_SIZE} bytes.",
                "files": list_directory(payload)["files"],
            }

        if not check_filetype(filetype):
            return {
                "status": "error",
                "message": f"File type {filetype} is not allowed. Allowed types: {ALLOWED_FILETYPE}.",
                "files": list_directory(payload)["files"],
            }

        if not check_total_size(absolute_path):
            return {
                "status": "error",
                "message": f"Total upload size exceeds maximum allowed size of {MAX_TOTAL_SIZE} bytes.",
                "files": list_directory(payload)["files"],
            }

        filecontent = base64.b64decode(filecontent)
        file_path = os.path.join(absolute_path, filename)

        with open(file_path, "wb") as file:
            file.write(filecontent)
        file.close()

    files = list_directory(payload)["files"]

    return {
        "status": "success",
        "message": f"File(s) uploaded successfully.",
        "files": files,
        "totalSize": [total_size(UPLOAD_DIR), MAX_TOTAL_SIZE],
    }


def delete_files(payload):
    dir = payload.get("dir")
    absolute_path = UPLOAD_DIR

    if dir:
        absolute_path = os.path.join(UPLOAD_DIR, dir)

    for filename in payload.get("files", []):
        file_path = os.path.join(absolute_path, filename)
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                os.rmdir(file_path)
            else:
                os.remove(file_path)

    files = list_directory(payload)["files"]

    return {
        "status": "success",
        "message": f"File(s) deleted successfully.",
        "files": files,
        "totalSize": [total_size(UPLOAD_DIR), MAX_TOTAL_SIZE],
    }


def download_files(payload):
    dir = payload.get("dir")
    absolute_path = UPLOAD_DIR

    if dir:
        absolute_path = os.path.join(UPLOAD_DIR, dir)

    downloaded_files = []
    for filename in payload.get("files", []):
        file_path = os.path.join(absolute_path, filename)
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                file_data = file.read()
                encoded_content = base64.b64encode(file_data).decode("utf-8")
                downloaded_files.append(
                    {
                        "filename": filename,
                        "content": f"data:;base64,{encoded_content}",
                    }
                )
            file.close()

    return {
        "status": "success",
        "message": f"File(s) downloaded successfully.",
        "files": downloaded_files,
    }


def createFolder(payload):
    dir = payload.get("dir")
    absolute_path = UPLOAD_DIR

    if dir:
        absolute_path = os.path.join(UPLOAD_DIR, dir)

    folder_name = payload.get("foldername", "")
    folder_path = os.path.join(absolute_path, folder_name)

    try:
        os.makedirs(folder_path, exist_ok=True)
        return {
            "status": "success",
            "message": f"Folder '{folder_name}' created successfully.",
            "files": list_directory(payload)["files"],
            "totalSize": [total_size(UPLOAD_DIR), MAX_TOTAL_SIZE],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def renameFile(payload):
    dir = payload.get("dir")
    absolute_path = UPLOAD_DIR

    if dir:
        absolute_path = os.path.join(UPLOAD_DIR, dir)

    old_filename = payload.get("old_filename", "")
    new_filename = payload.get("new_filename", "")

    old_file_path = os.path.join(absolute_path, old_filename)
    new_file_path = os.path.join(absolute_path, new_filename)

    try:
        os.rename(old_file_path, new_file_path)
        return {
            "status": "success",
            "message": f"File '{old_filename}' renamed to '{new_filename}' successfully.",
            "files": list_directory(payload)["files"],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


if __name__ == "__main__":
    configFile = os.path.join(os.environ.get("HOME"), ".badCloud.json")
    read_config(configFile)

    payload = post_request()
    payload_task = payload.get("task", "")
    tasks = {
        "list": list_directory,
        "upload": upload_files,
        "download": download_files,
        "delete": delete_files,
        "create_folder": createFolder,
        "rename_file": renameFile,
    }

    print_headers()

    try:
        response = tasks[payload_task](payload)
    except KeyError:
        response = {
            "status": "error",
            "message": f"Invalid task: {payload_task}",
        }
    except Exception as e:
        response = {
            "status": "error",
            "message": str(e),
        }

    print(json.dumps(response))
