# Rclone Lambda Sync

[![Github Actions Lint](https://github.com/badouralix/rclone-lambda-sync/actions/workflows/lint.yaml/badge.svg)](https://github.com/badouralix/rclone-lambda-sync/actions/workflows/lint.yaml)

A lambda function to run `rclone sync` periodically.

## Prerequisites

Install a lambda layer with rclone, such as [rclone-lambda-layer](https://github.com/badouralix/rclone-lambda-layer).

Create a valid rclone config with two remotes `source` and `destination`. See <https://rclone.org/docs/#configure> for details.

```bash
rclone config create "source" ...
rclone config create "destination" ...
```

This creates a local file that looks like this :

```bash
$ cat ~/.config/rclone/rclone.conf
[source]
...

[destination]
...
```

Upload this config in the SSM parameter `rclone-config`, either using the console or the following one-liner :

```bash
aws ssm put-parameter --region eu-west-3 --name rclone-config --type SecureString --value file://$HOME/.config/rclone/rclone.conf --description "Entire rclone.conf for rclone-lambda"
```

![AWS Systems Manager > Parameter Store > rclone-config > Overview](https://user-images.githubusercontent.com/19719047/144329662-cb0761db-ba3c-46db-8ef3-e8c5b6ec138f.png)

Also set `DEPLOYMENT_BUCKET` and `EVENTS_FILE` in a new `.env` local file.

## Deploy

```bash
serverless deploy
```

## Test

```bash
serverless invoke --function sync
```

## Configuration

|       Environment Variable        |                                     Description                                     |                     Default                      |
| :-------------------------------: | :---------------------------------------------------------------------------------: | :----------------------------------------------: |
|     `RCLONE_CONFIG_SSM_NAME`      |                 Name of the SSM parameter to fetch the config from.                 |                 `rclone-config`                  |
| `RCLONE_SYNC_CONTENT_DESTINATION` |               Name of the sync destination in the format "dest:path".               |                 `destination:/`                  |
|   `RCLONE_SYNC_CONTENT_SOURCE`    |                Name of the sync source in the format "source:path".                 |                    `source:/`                    |
|       `RCLONE_SYNC_DRY_RUN`       |                      Do a trial run with no permanent changes.                      |                     `false`                      |
|     `RCLONE_SYNC_EXTRA_FLAGS`     | List of flags passed to rclone. See available flags in <https://rclone.org/flags/>. | `--exclude /Downloads/** --exclude /External/**` |

## Schedules

By default, `rclone-lambda-sync` runs once a day around 00:00 UTC. See [rclone_lambda_daily.yaml](./rclone_lambda_daily.yaml). This behavior can be customized by following these steps :

1. Create a custom yaml file containing the desired schedules

    ```yaml
    - schedule:
        name: rclone-lambda-daily-1
        rate: cron(0 1 * * ? *)
        input:
          RCLONE_CONFIG_SSM_NAME: rclone-config-1

    - schedule:
        name: rclone-lambda-daily-2
        rate: cron(0 2 * * ? *)
        input:
          RCLONE_CONFIG_SSM_NAME: rclone-config-2
    ```

1. Change `EVENTS_FILE` value to the name of the custom yaml file in the `.env` local file
1. Test with a slightly different command

    ```bash
    serverless invoke --function sync --data '{"RCLONE_CONFIG_SSM_NAME": "rclone-config-1"}'
    ```

## Documentation

- <https://rclone.org/docs/>
- <https://itnext.io/a-deep-dive-into-serverless-tracing-with-aws-x-ray-lambda-5ff1821c3c70>

## License

Unless explicitly stated to the contrary, all contents licensed under the [MIT License](LICENSE).
