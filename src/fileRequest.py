#!/usr/bin/python3

import json
import os
import sys
import base64
import datetime

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
            "text/plain",
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


def list_directory(payload=None):
    files = os.listdir(UPLOAD_DIR)
    files_info = [
        {
            "filename": f,
            "size": os.path.getsize(os.path.join(UPLOAD_DIR, f)),
            "created": datetime.datetime.fromtimestamp(
                os.path.getctime(os.path.join(UPLOAD_DIR, f))
            ).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for f in files
    ]
    return files_info


def check_file_size(filesize):
    if filesize > MAX_FILE_SIZE:
        return False
    return True


def check_filetype(filetype):
    if filetype not in ALLOWED_FILETYPE:
        return False
    return True


def check_total_size():
    total_size = sum(
        os.path.getsize(os.path.join(UPLOAD_DIR, f)) for f in os.listdir(UPLOAD_DIR)
    )
    if total_size > MAX_TOTAL_SIZE:
        return False
    return True


def upload_files(payload):
    for file in payload.get("files", []):
        filename = file.get("filename", "")
        filecontent = file.get("content", "")
        filesize = file.get("filesize", 0)
        filetype = file.get("filetype", "")

        if not check_file_size(filesize):
            return {
                "status": "error",
                "message": f"File {filename} exceeds maximum allowed size of {MAX_FILE_SIZE} bytes.",
                "files": list_directory(),
            }

        if not check_filetype(filetype):
            return {
                "status": "error",
                "message": f"File type {filetype} is not allowed. Allowed types: {ALLOWED_FILETYPE}.",
                "files": list_directory(),
            }

        if not check_total_size():
            return {
                "status": "error",
                "message": f"Total upload size exceeds maximum allowed size of {MAX_TOTAL_SIZE} bytes.",
                "files": list_directory(),
            }

        filecontent = base64.b64decode(filecontent)
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as file:
            file.write(filecontent)
        file.close()

    files = list_directory()

    return {
        "status": "success",
        "message": f"File(s) uploaded successfully.",
        "files": files,
    }


def delete_files(payload):
    for filename in payload.get("files", []):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    files = list_directory()

    return {
        "status": "success",
        "message": f"File(s) deleted successfully.",
        "files": files,
    }


def download_files(payload):
    downloaded_files = []
    for filename in payload.get("files", []):
        file_path = os.path.join(UPLOAD_DIR, filename)
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
