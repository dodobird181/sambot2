"""
File-system utils.
"""


# TODO: THis might be deprecated... should check later :)
def read(filename) -> str:
    """Read and return the contents of a file as a string."""
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()
