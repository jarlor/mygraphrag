import threading
from pathlib import Path
from datetime import datetime


def create_folder(root_dir, folder_name):
    """
    Create a folder in the root directory
    Args:
        root_dir: root directory
        folder_name: folder name

    Returns:
        bool: True if the folder is created, False if the folder already exists
        folder_path: Path object of the folder

    """
    folder_path = Path(root_dir) / folder_name

    if not folder_path.exists():
        folder_path.mkdir(parents=True)
    else:  # folder exists
        return False, folder_path

    return True, folder_path


def get_folders_sorted_by_creation_time(path: Path):
    """
    Get a list of folder names and their creation times in the given directory,
    sorted by creation time in descending order.

    Args:
        path (Path): The directory path.

    Returns:
        dict: A dictionary where the key is the folder name with creation time and the value is the folder
    """
    if not path.is_dir():
        raise ValueError(f"The path {path} is not a directory.")

    folders = []

    # Get all directories in the given path with their creation times
    for item in path.iterdir():
        if item.is_dir():
            creation_time = item.stat().st_ctime
            formatted_creation_time = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
            folders.append((item.name, formatted_creation_time))

    # Sort the folder list by creation time in descending order
    folders_sorted = sorted(folders, key=lambda x: x[1], reverse=True)
    show_folders_sorted = {f"{folder} ({creation_time})": (path / folder).absolute() for folder, creation_time in folders_sorted}
    return show_folders_sorted


def start_webserver(index_dir):
    with open('webserver/configs/index_dir', 'w') as f:
        f.write(str(index_dir))
    from webserver.configs import settings

    def run_webserver():
        import uvicorn

        uvicorn.run("webserver.main:app", host="localhost", port=settings.server_port)

    server_thread = threading.Thread(target=run_webserver, daemon=True)
    server_thread.start()
    return settings.server_port
