import asyncio
import json
import logging
import os
import tempfile
from typing import Optional

import boto3
import botocore.config
from ddtrace import tracer
from pythonjsonlogger import jsonlogger  # type: ignore # https://github.com/madzak/python-json-logger/issues/118

from lambda_types import LambdaContext, LambdaDict

# We won't use the root logger, but rather a dedicated logger for this __name__
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def lambda_handler(event: LambdaDict, context: LambdaContext) -> LambdaDict:
    """
    lambda_handler is the default entrypoint of the lambda.
    """
    update_root_logger()
    asyncio.run(run_rclone_sync(event))

    return dict()


@tracer.wrap()
def update_root_logger() -> None:
    """
    update_root_logger overwrites the root logger with a custom json formatter.

    Datadog might patch the root handler formatter at each execution, and we have to overwrite it at each run
    https://github.com/DataDog/datadog-lambda-python/blob/afbbef5/datadog_lambda/tracing.py#L304-L327
    """
    # Craft a dedicated json formatter for the lambda logs
    # We add all available attributes along with the aws request id
    #
    # https://github.com/python/cpython/blob/ea39f82/Lib/logging/__init__.py#L539-L562
    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    # https://docs.datadoghq.com/logs/log_collection/python/?tab=pythonjsonlogger
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(created)f %(filename)s %(funcName)s %(levelname)s %(levelno)s %(lineno)d %(message)s %(module)s %(msecs)d %(name)s %(pathname)s %(process)d %(processName)s %(relativeCreated)d %(thread)d %(threadName)s"
        + "%(aws_request_id)s",
        rename_fields={
            "aws_request_id": "lambda.request_id"
        },  # Remap field to match datadog conventions
        reserved_attrs=jsonlogger.RESERVED_ATTRS
        + (
            "dd.env",
            "dd.service",
            "dd.version",
        ),  # For some reason these tags end up empty, so better exclude them by setting them as reserved attributes
    )

    # We need to change the formatter of the handler of the root logger, since all logs are propagated upwards in the tree
    # In particular, the root logger already has a handler provider by aws lambda bootstrap.py
    #
    # https://docs.python.org/3/library/logging.html#logging.Logger.propagate
    # https://stackoverflow.com/a/50910673
    # https://stackoverflow.com/questions/37703609/using-python-logging-with-aws-lambda
    # https://www.denialof.services/lambda/
    root = logging.getLogger()
    for handler in root.handlers:
        if handler.__class__.__name__ == "LambdaLoggerHandler":
            handler.setFormatter(formatter)


@tracer.wrap()
async def run_rclone_sync(event: LambdaDict) -> None:
    """
    run_rclone_sync is the main function spawning an rclone process and parsing its output.
    """
    logger.info("Starting rclone sync")
    # Passing rclone config through stdin does not work
    # Thus we need to dump the config in a real file first
    #
    # $ cat ~/.config/rclone/rclone.conf | rclone listremotes --config=/dev/stdin
    # Failed to load config file "/dev/stdin": seek /dev/stdin: illegal seek
    #
    # https://github.com/rclone/rclone/blob/386acaa/fs/config/config.go#L343
    # https://github.com/rclone/rclone/blob/386acaa/fs/config/configfile/configfile.go#L95-L100
    # https://github.com/rclone/rclone/blob/386acaa/fs/config/configfile/configfile.go#L53-L93
    # https://github.com/rclone/rclone/blob/386acaa/fs/config/crypt.go#L46-L187
    filename = get_rclone_config_path(
        str(event.get("RCLONE_CONFIG_SSM_NAME", ""))
        or os.environ.get("RCLONE_CONFIG_SSM_NAME")
        or "rclone-config"
    )
    source = (
        str(event.get("RCLONE_SYNC_CONTENT_SOURCE", ""))
        or os.environ.get("RCLONE_SYNC_CONTENT_SOURCE")
        or "source:/"
    )
    destination = (
        str(event.get("RCLONE_SYNC_CONTENT_DESTINATION", ""))
        or os.environ.get("RCLONE_SYNC_CONTENT_DESTINATION")
        or "destination:/"
    )
    cmd = [
        "rclone",
        "--config",
        filename,
        "--use-json-log",
        "--verbose",
        "sync",
        "--stats",
        "10s",
        source,
        destination,
        *os.environ.get("RCLONE_SYNC_EXTRA_FLAGS", "").split(),
    ]
    if os.environ.get("RCLONE_SYNC_DRY_RUN", "false") != "false":
        cmd.append("--dry-run")
    logger.info(f"Running command {cmd}")
    p = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # We need to consume both stdout and stderr to avoid blocking the subprocess
    #
    # https://stackoverflow.com/a/61939464
    await asyncio.gather(p.wait(), log_stdout(p.stdout), log_stderr(p.stderr))
    os.remove(filename)
    logger.info("Finished rclone sync")


@tracer.wrap()
def get_rclone_config_path(rclone_config_ssm_name: str) -> str:
    """
    get_rclone_config_path retrieves rclone config from AWS SSM and dumps it on a temp file.
    """
    boto3_config = botocore.config.Config(
        connect_timeout=5, read_timeout=5, retries={"max_attempts": 2}
    )
    ssm_client = boto3.client("ssm", config=boto3_config)

    rclone_config = ssm_client.get_parameter(
        Name=rclone_config_ssm_name, WithDecryption=True
    )["Parameter"]["Value"]

    f = tempfile.NamedTemporaryFile(buffering=0, delete=False)
    f.write(rclone_config.encode())

    return f.name


@tracer.wrap()
async def log_stdout(stream: Optional[asyncio.StreamReader]) -> None:
    """
    log_stdout consumes rclone stdout line by line and generates python logs out of it.
    """
    if stream is None:
        logger.error("Invalid stream in log_stdout")
        return
    while line := await stream.readline():
        try:
            log_rclone(line)
        except json.JSONDecodeError as _:
            logger.info(line.decode())


@tracer.wrap()
async def log_stderr(stream: Optional[asyncio.StreamReader]) -> None:
    """
    log_stderr consumes rclone stderr line by line and generates python logs out of it.
    """
    if stream is None:
        logger.error("Invalid stream in log_stderr")
        return
    while line := await stream.readline():
        try:
            log_rclone(line)
        except json.JSONDecodeError as _:
            logger.error(line.decode())


@tracer.wrap()
def log_rclone(line: bytes) -> None:
    """
    log_rclone parses and reshapes rclone json logs.
    """
    d = {"rclone": json.loads(line)}

    # Remap message key
    d["message"] = d["rclone"].pop("msg")

    # Notice logs become warning logs in logrus
    # Remap log level accordingly
    if "stats" in d["rclone"]:
        d["level"] = "debug"
    elif "skipped" in d["rclone"]:
        d["level"] = "info"
    else:
        d["level"] = d["rclone"]["level"]
    d["rclone"].pop("level")

    # The log level does not really matter here, since rclone already specifies its own log level
    logger.error(d)
