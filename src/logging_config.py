import logging

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the global logging settings for the application.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )