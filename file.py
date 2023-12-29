import logger


def read(file_path):
    try:
        with open(file_path, 'r', encoding="utf8") as file:
            return file.read()
    except FileNotFoundError as e:
        logger.error(f'Error: {e}')
