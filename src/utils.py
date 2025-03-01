import os


def is_valid_path(csv_file):
    """
    Checks if the CSV file path is valid. Verifies that the directory exists and the file is writable.

    :param csv_file: Path to the CSV file
    :return: True if the path is valid, False otherwise
    """
    directory = os.path.dirname(csv_file)

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        print(f"🔨 Directory '{directory}' does not exist. Creating it now...")
        os.makedirs(directory)

    # Check if the file is writable
    try:
        with open(csv_file, "a"):
            pass
        return True
    except IOError:
        print(f"❌ Error: The file '{csv_file}' is not writable.")
        return False
