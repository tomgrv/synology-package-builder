<!-- @format -->

# Elevated mode

## What is elevated mode?

Elevated mode is a special mode in which the application runs with elevated privileges. This allows the application to perform actions that require higher permissions, such as modifying system files or accessing restricted resources. From DSM 7.0, Synology prevents applications from running with elevated privileges by default. This is a security measure to prevent malicious applications from compromising the system.

## How to enable elevated mode?

This action provides a way to enable elevated mode to start docker containers with elevated privileges. This is useful for applications that require access to system resources or need to perform actions that require higher permissions.

To enable elevated mode, you need to follow these steps:

### Declare docker preset

Create a file named `presets` in the `synology/conf` directory of your application.

```json
{
    "docker": [
        {
            "profile": "./docker/profile.json",
            "preload": false
        }
    ]
}
```

- `profile` points to a docker profile file, as exported from the Synology Container Manager with the Export menu option. This file contains the configuration for the docker container, including the image, environment variables, ports, and other settings. Use `{{ wizard.xxx }}` to reference the install wizard variables in the profile file on installation.
- `preload` is a boolean value that indicates whether the image should be preloaded and included in the application package. If set to `false`, the image will not be preloaded and will be pulled from the registry when the application is installed.

You can have multiple docker profiles in the `docker` array, each with its own configuration. This allows you to run multiple docker containers with different configurations within the same application.

### Package the application

Package with the `tomgrv\synology-package-builder` action and install the package as-is.

> The application will find itself in error state on installation, as it cannot run in elevated mode yet.

### Enable elevated mode

Run the following command in root terminal to enable elevated mode:

```bash
/var/packages/ < app_name > /scripts/postinst
```

with `<app_name>` being the camel-case name of your application.

(you can use the _schelduled task_ feature to run this command, but it is not required)

> The package will now show as _installed_ and will run in elevated until desinstalled.
