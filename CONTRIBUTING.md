# Contributing

## Bootstrap

Use the following commands to create the initial [pyproject.toml](pyproject.toml).

```bash
poetry add python-json-logger
poetry add --group dev black boto3 boto3-stubs "boto3-stubs[ssm]" ddtrace flake8 mypy
serverless plugin install -n serverless-python-requirements
```

```bash
poetry install
```
