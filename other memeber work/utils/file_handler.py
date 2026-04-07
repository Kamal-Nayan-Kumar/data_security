import os

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rb",
    ".php", ".sh", ".json", ".yaml", ".yml", ".env", ".txt", ".cfg", ".ini"
}

def get_all_files(directory):
    """Recursively walk directory and return all supported file paths."""
    file_list = []
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}

    for root, dirs, files in os.walk(directory):
        # Skip unwanted directories in-place
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_EXTENSIONS or file in {"requirements.txt", "package.json", "Dockerfile"}:
                file_list.append(os.path.join(root, file))

    return file_list


def read_file(file_path):
    """Read a file and return its content as a string. Returns empty string on failure."""
    try:
        with open(file_path, "r", errors="ignore", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""