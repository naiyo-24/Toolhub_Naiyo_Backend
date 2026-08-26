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
    # Using a cleaner format focusing on the message without extra timestamp and level tags 
    # since we will format the box ourselves
    logger.add(
        sys.stderr,
        format="<level>{message}</level>",
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
        elif method in ("PUT", "PATCH"):
            method_color = "<magenta>PUT</magenta>"
        elif method == "DELETE":
            method_color = "<red>DELETE</red>"
        else:
            method_color = f"<white>{method}</white>"

        url = str(request.url)
        
        # Request Logging (Pretty Dio Logger style)
        req_log = []
        req_log.append("╔" + "═" * 80)
        req_log.append(f"║ Request ║ {method_color} ")
        req_log.append(f"║ <cyan>{url}</cyan>")
        
        headers = dict(request.headers)
        if headers:
            req_log.append("║")
            req_log.append("║ Headers:")
            for k, v in headers.items():
                req_log.append(f"║  - {k}: {v}")
                
        query_params = dict(request.query_params)
        if query_params:
            req_log.append("║")
            req_log.append("║ Query Parameters:")
            for k, v in query_params.items():
                req_log.append(f"║  - {k}: {v}")
                
        req_log.append("╚" + "═" * 80)
        
        logger.opt(colors=True).info("\n".join(req_log))

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
                
            res_log = []
            res_log.append("╔" + "═" * 80)
            res_log.append(f"║ Response ║ {status_color} ║ {process_time:.1f}ms")
            res_log.append(f"║ <cyan>{url}</cyan>")
            res_log.append("╚" + "═" * 80)
            
            logger.opt(colors=True).info("\n".join(res_log))
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            err_log = []
            err_log.append("╔" + "═" * 80)
            err_log.append(f"║ Response ║ <red><bold>500</bold></red> ║ {process_time:.1f}ms")
            err_log.append(f"║ <cyan>{url}</cyan>")
            err_log.append("╚" + "═" * 80)
            
            logger.opt(colors=True).error("\n".join(err_log))
            logger.exception("An unhandled exception occurred during the request")
            raise e
