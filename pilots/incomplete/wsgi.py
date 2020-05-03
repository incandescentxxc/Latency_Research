import sys
import logging
from .incomplete_server import app as application

try:
  gunicorn_error_handlers = logging.getLogger('gunicorn.error').handlers
  application.logger.handlers.extend(gunicorn_error_handlers)
except: 
  pass
application.logger.setLevel(logging.INFO)

# for deployment
if __name__ == "__main__":
  application.run(host="0.0.0.0", port=5000)
