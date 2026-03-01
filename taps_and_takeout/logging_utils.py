import json
import logging


log = logging.getLogger(__name__)


def log_admin_action(action, **details):
    log.info("admin_action %s", json.dumps({"action": action, **details}, default=str, sort_keys=True))


def log_validation_failure(form_name, **details):
    log.warning("validation_failure %s", json.dumps({"form": form_name, **details}, default=str, sort_keys=True))
