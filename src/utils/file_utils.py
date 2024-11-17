import os

def file_exists(filename):
    return os.path.isfile(filename)

def get_file_size(filename):
    return os.path.getsize(filename) if file_exists(filename) else 0 