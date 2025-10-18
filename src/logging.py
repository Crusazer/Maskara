import logging

logging.getLogger('passlib').setLevel(logging.ERROR)
logging.getLogger('pdfminer').setLevel(logging.WARNING)

def set_logging() -> None:
    ...