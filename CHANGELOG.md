# Changelog

<!---
## 0.0.1 - 1970-01-01

### Added

- New stuff.

### Changed

- Changed stuff.

### Deprecated

- Deprecated stuff.

### Removed

- Removed stuff.

### Fixed

- Fixed stuff.

### Security

- Security related fix.
-->

## Unreleased

### Update notes

Since the project has been renamed, you should migrate your configuration file, if you have one.
On Linux:

```sh
mv ~/.config/dakara/player_vlc.yaml ~/.config/dakara/player.yaml
```

On Windows:

```cmd
# cmd
move %APPDATA%\Dakara\player_vlc.yaml %APPDATA%\Dakara\player.yaml
# powershell
mv $env:APPDATA\Dakara\player_vlc.yaml $env:APPDATA\Dakara\player.yaml
```

### Added

- mpv is supported as an alternative player.
  In the config file, the player can be selected in the `player.player_name` key.
  Current accepted values are `vlc` and `mpv`.

### Changed

- The project is renamed:
  - Repository name: `dakara-player-vlc` > `dakara-player`;
  - Module name `dakara_player_vlc` > `dakara_player`;
  - Pypi package name `dakaraplayervlc` > `dakaraplayer`;
  - Config file name `player_vlc.yamd` > `player.yaml`;
  - Command name `dakara-play-vlc` > `dakara-play`.

## 1.6.0 - 2020-09-05

### Added

- Manage instrumental tracks.

## 1.5.2 - 2019-12-06

### Fixed

- Dead symbolic links to fonts in user font directory are now automatically removed to avoid crash.
- Some installed fonts could be left uninstalled, this problem has been fixed.

## 1.5.1 - 2019-12-05

### Fixed

- Installation directions in readme.

## 1.5.0 - 2019-12-05

### Added

- The project can be installed with `pip`.

### Changed

- In the config file, the `player.transition_duration` is moved to `player.durations.transition_duration`;
- To run the player, invoke the command `dakara-play-vlc` or `python -m dakara_player_vlc`, instead of `dakara.py`;
- Configuration is now stored in the user directory. You can create a new config file with the command `dakara-play-vlc create-config` or `python -m dakara_player_vlc create-config`.

## 1.4.0 - 2019-05-03

### Changed

- In the config file, the `server.url` parameter is renamed `server.address` and contains the hostname of the server (without `http://` or `https://`). The encryption of the connection is obtained with the `server.ssl` parameter.

## 1.3.0 - 2018-10-07

### Changed

- Better Windows OS support.

## 1.2.1 - 2018-06-04

### Fixed

- Fix documentation inconsistency.

## 1.2.0 - 2018-06-03

### Added

- Tests can be executed with `./tests.py`.
- Resources folder, with default/example templates and backgrounds, is moved: `share` > `dakara_player_vlc/resources`.
- Work link long name can be obtained withe the `| link_type_name` filter.

### Changed

- Config file uses the [Yaml](http://yaml.org/start.html) format and should be `config.yaml`, example file is `config.yaml.example`.
- Calling `dakara.py -d` activates debug logging.

## 1.0.1 - 2017-10-22

### Added

- Changelog.
- Version file.
- Display version in log and idle screen.
- Version bump script.

## 1.0.0 - 2017-10-22

### Added

- First version.
