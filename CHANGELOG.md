# Rclone Lambda Sync Changelog

## Unreleased

- Bump davidanson/markdownlint-cli2-action from 7 to 9

## 3.1.0

- Bump rclone lambda layer to version 2
- Add better display of default config
- Remove docker image override
- Fix pylance warning

## 3.0.0

- Use official markdownlint github action
- Update default schedule filename
- Upgrade dependencies
- Change default architecture to arm64

## v2.0.1

- Fix mypy errors
- Add changelog

## v2.0.0

- Upgrade dependencies
- Add config flags for sync source and destination
- Fix crash on missing environment variables
- Define lambda schedules in an external file

## v1.3.0

- Bump rclone lambda layer to version 9
- Add dependabot config file
- Bump actions/checkout from 2 to 3 (<https://github.com/badouralix/rclone-lambda-sync/pull/2>)
- Bump ibiqlik/action-yamllint from 1 to 3 (<https://github.com/badouralix/rclone-lambda-sync/pull/3>)
- Bump version of all lambda layers
- Switch build to aws-provided build container image
- Add rclone extra flags using environment variables
- Bump license year
- Add guide to create rclone-config ssm parameter
- Upgrade dependencies

## v1.2.0

- Rename lint workflow
- Add status badge
- Lint imports with isort
- Upgrade dependencies
- Upgrade to serverless v3

## v1.1.0

- Upgrade to python 3.9

## v1.0.0

- Commit for a dream
