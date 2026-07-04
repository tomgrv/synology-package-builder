<!-- @format -->

# Elevated mode

## Why elevation is needed

Since DSM 7.0, Synology only honours `"run-as": "root"` in a package's
`privilege` file for packages signed by Synology. Unsigned third-party
packages run every lifecycle script as an unprivileged package user, so a
package that manages Docker containers (via `synowebapi` and the Docker
socket) cannot work out of the box.

This action ships an elevation flow that keeps that constraint in place
while reducing the workaround to a **single, explicit, least-privilege
approval** by the NAS administrator.

## How it works

The security model is a **root broker**:

1. The package installs and runs entirely as its package user. The install
   never errors out: the container profile is rendered from the install
   wizard values and kept private (`0600`) in the package home, and the
   package waits in the stopped state.

2. The administrator runs, **once**:

    ```bash
    sudo /var/packages/<app_name>/scripts/elevate
    ```

    with `<app_name>` being the name of your application. The script:

    - refuses to proceed if the package scripts or configuration are not
      root-owned or are writable by non-root users (tamper check);
    - displays what it is about to approve — image, container name,
      privileged flag, volume bindings — and asks for confirmation
      (`-y` skips the prompt, e.g. for a scheduled task);
    - installs a root-owned broker under
      `/usr/local/lib/synopkg-broker/<app_name>/` together with a snapshot
      of the approved container profile(s) and the SHA-256 of the shipped
      profile template(s);
    - adds `/etc/sudoers.d/synopkg-<app_name>` allowing the package user to
      run **that single broker command and nothing else** (validated with
      `visudo` before installation);
    - creates the container(s) and starts the package.

3. From then on, day-to-day operation needs no root access: `start`,
   `stop`, `status`, upgrades and uninstall call `sudo -n <broker> <verb>`.
   The broker accepts a fixed set of verbs and derives everything else from
   its own root-owned directory — never from caller arguments, caller
   environment, or package-user-writable files — so the package user cannot
   make root do anything that was not approved.

4. **Upgrades keep the approval.** The broker and sudoers entry live outside
   `/var/packages/<app_name>` and survive package upgrades. If an upgrade
   ships a *different* container profile (for example a new image tag), the
   broker detects the template hash mismatch, refuses to apply it, and the
   package asks the administrator to re-run `elevate` to review and approve
   the change.

5. **Uninstalling revokes everything**: the container is removed, the
   sudoers entry is deleted and the broker directory is purged.

## How to enable it in your package

### Declare a docker preset

Create a file named `presets` in the `synology/conf` directory of your
application:

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

- `profile` points to a Docker container profile file, as exported from the
  Synology Container Manager with the Export menu option. It contains the
  configuration for the container: image, environment variables, ports,
  volumes, and other settings. Use `{{ wizard.xxx }}` to reference install
  wizard variables; they are substituted when the package is installed.
- `preload` is either `false`, or the path of an `xz`-compressed
  `docker save` archive to ship inside the package. When set, the broker
  loads the image from that file instead of pulling it from the registry.

You can declare several docker profiles in the `docker` array; each one is
approved, created and managed independently within the same application.

### Package and install

Package with the `tomgrv/synology-package-builder` action and install the
`.spk`. The package installs cleanly and stays stopped; the install log and
any start attempt display the exact `elevate` command to run.

### Approve

Run the command from step 2 above in a root shell (SSH). The package starts
automatically once approved.

## Security properties

| Property        | Old flow (≤ v2)                                     | Broker flow                                                 |
| --------------- | --------------------------------------------------- | ----------------------------------------------------------- |
| Admin consent   | Run `postinst` as root, blind                        | One command, shows image/mounts/privileged before approving |
| Privilege scope | Whole package flipped to `run-as: root`              | Package user may run one root-owned broker, fixed verbs     |
| Tampering       | Root re-runs package-user-writable scripts           | Broker + approved profiles are root-owned snapshots         |
| Upgrades        | Background monitor re-runs `postinst` as root        | Approval persists; profile changes require re-approval      |
| Revocation      | Uninstall only, elevation traces left in `privilege` | Uninstall removes container, sudoers entry and broker       |
