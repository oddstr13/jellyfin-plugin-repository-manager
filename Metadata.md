# Plugin metadata file

The build metadata file should be placed in one of the [following locations][CONFIG_LOCATIONS]:

- `jprm.yaml`
- `.jprm.yaml`
- `.ci/jprm.yaml`
- `.github/jprm.yaml`
- `.gitlab/jprm.yaml`
- `meta.yaml`
- `build.yaml`

If there are multiple, the first file found is used.

| key | type | required | comment |
|-----|------|----------|---------|
| `name` | string | ✔️ | Full plugin name |
| `guid` | string | ✔️ | Plugin GUID – Must be unique! |
| `image` | string | ❌ | Defaults to [`image.png`][DEFAULT_IMAGE_FILE] if present |
| `imageUrl` | string | ❌ | Fully qualified link to the image to display in the plugin catalog. Gets overwritten by `image` on `repo add` if it is present. |
| `version` | int \| string | ✔️ | Plugin version – must be a valid C# assembly version number (`major.minor.build.revision`) – only major is required, the rest defaults to `0` |
| `targetAbi` | string | ✔️ | Minimum Jellyfin version |
| `framework` | string | ❌ | Framework version to build with – must be same or higher than what your targeted Jellyfin version is built with. Defaults to [`netstandard2.1`][DEFAULT_FRAMEWORK] for legacy reasons, please specify. |
| `overview` | string | ✔️ | A short single-line description (tagline) of your plugin |
| `description` | string | ✔️ | A longer multi-line description |
| `category` | string | ✔️ | `Authentication` / `Channels` / `General` / `Live TV` / `Metadata` / `Notifications` |
| `owner` | string | ✔️ | Name of maintainer |
| `artifacts` | list[string] | ✔️ | List of artifacts to include in the plugin zip |
| `changelog` | string | ✔️ | Changes since last release. Can be overridden by `plugin build --changelog` or the action `changelog` input. |

[DEFAULT_IMAGE_FILE]: https://github.com/oddstr13/jellyfin-plugin-repository-manager/blob/a2267abe5cbffe602dd8dd0d5c532ea32da7bafe/jprm/__init__.py#L35
[DEFAULT_FRAMEWORK]: https://github.com/oddstr13/jellyfin-plugin-repository-manager/blob/a2267abe5cbffe602dd8dd0d5c532ea32da7bafe/jprm/__init__.py#L36
[CONFIG_LOCATIONS]: https://github.com/oddstr13/jellyfin-plugin-repository-manager/blob/a2267abe5cbffe602dd8dd0d5c532ea32da7bafe/jprm/__init__.py#L37-L45
