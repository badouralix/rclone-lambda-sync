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

Also set `DEPLOYMENT_BUCKET` in a new `.env` local file.

## Deploy

```bash
serverless deploy
```

## Test

```bash
serverless invoke --function sync
```

## Configuration

|       Environment Variable        |                                     Description                                     |
| :-------------------------------: | :---------------------------------------------------------------------------------: |
|     `RCLONE_CONFIG_SSM_NAME`      |   Name of the SSM parameter to fetch the config from. ( default "rclone-config" )   |
| `RCLONE_SYNC_CONTENT_DESTINATION` | Name of the sync destination in the format "dest:path" ( default "destination:/" )  |
|   `RCLONE_SYNC_CONTENT_SOURCE`    |     Name of the sync source in the format "source:path" ( default "source:/" )      |
|       `RCLONE_SYNC_DRY_RUN`       |             Do a trial run with no permanent changes. ( default false )             |
|     `RCLONE_SYNC_EXTRA_FLAGS`     | List of flags passed to rclone. See available flags in <https://rclone.org/flags/>. |

## Documentation

- <https://rclone.org/docs/>
- <https://itnext.io/a-deep-dive-into-serverless-tracing-with-aws-x-ray-lambda-5ff1821c3c70>

## License

Unless explicitly stated to the contrary, all contents licensed under the [MIT License](LICENSE).
