import logging
import sys
import time
import uuid
from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logger():
    # Remove all existing loggers
    logger.remove()
    
    # Add a custom sink for beautiful colorful logging
    # Using a cleaner format focusing on the message
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # Intercept Uvicorn loggers and prevent duplicate access logs
    for logger_name in ("uvicorn", "uvicorn.error", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False
        
    # We disable uvicorn.access because our middleware handles request logging
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False
    
    return logger

class LoguruMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Colorize method
        method = request.method
        if method == "GET":
            method_color = "<blue>GET</blue>"
        elif method == "POST":
            method_color = "<yellow>POST</yellow>"
        elif method == "PUT" or method == "PATCH":
            method_color = "<magenta>PUT</magenta>"
        elif method == "DELETE":
            method_color = "<red>DELETE</red>"
        else:
            method_color = f"<white>{method}</white>"

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            # Colorize status code
            status = response.status_code
            if 200 <= status < 300:
                status_color = f"<green>{status}</green>"
            elif 300 <= status < 400:
                status_color = f"<cyan>{status}</cyan>"
            elif 400 <= status < 500:
                status_color = f"<yellow>{status}</yellow>"
            else:
                status_color = f"<red>{status}</red>"
                
            # Log successful requests (using opt(colors=True) to parse our custom tags)
            logger.opt(colors=True).info(
                f"{method_color} {request.url.path}  →  {status_color}  ({process_time:.1f}ms)"
            )
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.opt(colors=True).error(
                f"{method_color} {request.url.path}  →  <red><bold>500</bold></red>  ({process_time:.1f}ms)"
            )
            logger.exception("An unhandled exception occurred during the request")
            raise e
