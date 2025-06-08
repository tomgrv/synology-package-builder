<!-- @format -->

# Synology Package Structure

## Simplified Structure

Your project should have the _minimum_ following structure as described in the [Synology Developper Guide](https://help.synology.com/developer-guide/synology_package/introduction.html):

```
root/
  ├── conf/
  │   ├── privilege
  │   └── resource
  ├── WIZARD_UIFILES/
  │   ├── install_uifiles
  |   └── uninstall_uifiles
  ├── PACKAGE_ICON.PNG
  └── PACKAGE_ICON_256.PNG
```

## Clean Structure

For a cleaner structure, you can use the following:

```
root/
  ├── synology/
  │   ├── conf/
  │   │   ├── privilege
  │   │   └── resource
  │   ├── WIZARD_UIFILES/
  │   │   ├── install_uifiles
  │   │   └── uninstall_uifiles
  │   ├── PACKAGE_ICON.PNG
  │   └── PACKAGE_ICON_256.PNG
  └── (your package source code)
```

or the following, with `target: "src"` in a `package.json`:

```
root/
  ├── synology/
  │   ├── conf/
  │   │   ├── privilege
  │   │   └── resource
  │   ├── WIZARD_UIFILES/
  │   │   ├── install_uifiles
  │   │   └── uninstall_uifiles
  │   ├── PACKAGE_ICON.PNG
  │   └── PACKAGE_ICON_256.PNG
  ├── src/
  |   └── (your package source code)
  └── package.json
```

## Package.json structure

You may need to skip the INFO file generation by adding a `package.json` file in your project root with the following structure:

```json
{
    "name": "your-package-name", // Used as 'package', defaults to the folder name
    "version": "1.0.0",
    "description": "Your package description",
    "synology": {
        "maintainer": "Your Name", // Defaults to author name field
        "maintainer_url": "https://your.website", // Defaults to homepage field
        "arch": "noarch", // Defaults to cpu field with 'dsm:' prefix
        "displayName": "Your Package Display Name",
        "os_max_ver": "7",
        "os_min_ver": "7.0-40337", // Defaults to os field with 'dsm:' prefix
        "install_dep_packages": ["ContainerManager>=20.0.0-0"]
    },
    "target": "./src"
}
```

- `beta` field is automatically set to `true` if the version is a pre-release (e.g., `1.0.0-beta.1`).
- `thirdparty` field is automatically set to `true` as not developed by Synology.
