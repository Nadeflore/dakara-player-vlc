import logging
from abc import ABC, abstractmethod
from threading import Timer

from dakara_base.exceptions import DakaraError
from dakara_base.safe_workers import Worker
from path import Path

from dakara_player.background_loader import BackgroundLoader
from dakara_player.resources_manager import PATH_BACKGROUNDS
from dakara_player.audio import get_audio_files
from dakara_player.text_generator import TextGenerator
from dakara_player.version import __version__


TRANSITION_BG_NAME = "transition.png"
TRANSITION_TEXT_NAME = "transition.ass"
TRANSITION_DURATION = 2

IDLE_BG_NAME = "idle.png"
IDLE_TEXT_NAME = "idle.ass"
IDLE_DURATION = 300

PLAYER_CLOSING_DURATION = 3


logger = logging.getLogger(__name__)


class MediaPlayer(Worker, ABC):
    """Abstract class to manipulate a media player.

    The class can be used as a context manager that closes the media player
    automatically on exit.

    Args:
        stop (threading.Event): Stop event that notify to stop the entire
            program when set.
        errors (queue.Queue): Error queue to communicate the exception to the
            main thread.
        config (dict): Dictionary of configuration.
        tempdir (path.Path): Path of the temporary directory.

    Attributes:
        stop (threading.Event): Stop event that notify to stop the entire
            program when set.
        errors (queue.Queue): Error queue to communicate the exception to the
            main thread.
        player_name (str): Name of the media player.
        fullscreen (bool): If True, the media player will be fullscreen.
        kara_folder_path (path.Path): Path to the karaoke folder.
        playlist_entry (dict): Playlist entyr object.
        callbacks (dict): High level callbacks associated with the media
            player.
        warn_long_exit (bool): If True, display a warning message if the media
            player takes too long to stop.
        durations (dict of int): Duration of the different screens in seconds.
        text_paths (dict of path.Path): Path of the different text screens.
        text_generator (dakara_player.text_generator.TextGenerator): Text
            generator instance.
        background_loader
        (dakara_player.background_loader.BackgroundLoader): Background
            loader instance.
    """

    player_name = None

    @staticmethod
    @abstractmethod
    def is_available():
        """Indicate if the implementation is available.

        Must be overriden.

        Returns:
            bool: True if the media player is useable.
        """

    def init_worker(self, config, tempdir, warn_long_exit=True):
        """Initialize the base objects of the media player.

        Actions performed in this method should not have any side effects
        (query file system, etc.).

        Args:
            config (dict): Dictionary of configuration.
            tempdir (path.Path): Path of the temporary directory.
            warn_long_exit (bool): If True, the class will display a warning
                message if the media player takes too long to stop.
        """
        self.check_is_available()

        # karaoke parameters
        self.fullscreen = config.get("fullscreen", False)
        self.kara_folder_path = Path(config.get("kara_folder", ""))

        # inner objects
        self.playlist_entry = None
        self.callbacks = {}
        self.warn_long_exit = warn_long_exit

        # set durations
        config_durations = config.get("durations") or {}
        self.durations = {
            "idle": IDLE_DURATION,
            "transition": config_durations.get(
                "transition_duration", TRANSITION_DURATION
            ),
        }

        # set text paths
        self.text_paths = {
            "idle": tempdir / IDLE_TEXT_NAME,
            "transition": tempdir / TRANSITION_TEXT_NAME,
        }

        # set text generator
        config_texts = config.get("templates") or {}
        self.text_generator = TextGenerator(config_texts)

        # set background loader
        config_backgrounds = config.get("backgrounds") or {}
        self.background_loader = BackgroundLoader(
            directory=Path(config_backgrounds.get("directory", "")),
            default_directory=Path(PATH_BACKGROUNDS),
            background_filenames={
                "transition": config_backgrounds.get("transition_background_name"),
                "idle": config_backgrounds.get("idle_background_name"),
            },
            default_background_filenames={
                "transition": TRANSITION_BG_NAME,
                "idle": IDLE_BG_NAME,
            },
        )

        # set default callbacks
        self.set_default_callbacks()

        # call specialized constructor
        self.init_player(config, tempdir)

    def init_player(self, config, tempdir):
        """Initialize the objects of the specific media player.

        Actions performed in this method should not have any side effects
        (query file system, etc.).

        Can be overriden.

        Args:
            config (dict): Dictionary of configuration.
            tempdir (path.Path): Path of the temporary directory.
        """

    def load(self):
        """Perform base actions with side effects for media player initialization.
        """
        # check kara folder
        self.check_kara_folder_path()

        # load text generator
        self.text_generator.load()

        # load backgrounds
        self.background_loader.load()

        self.load_player()

    def load_player(self):
        """Perform actions with side effects for specialized media player initialization.

        Can be overriden.
        """

    @abstractmethod
    def get_timing(self):
        """Get media player timing.

        Must be overriden.

        Returns:
            int: Current song timing in seconds if a song is playing, or 0 when
                idle or during transition screen.
        """

    @abstractmethod
    def get_version(self):
        """Get media player version.

        Must be overriden.

        Returns:
            packaging.version.Version: Parsed version of the media player.
        """

    @abstractmethod
    def is_playing(self):
        """Query if the media player is playing something.

        Must be overriden.

        Returns:
            bool: True if the media player is playing something.
        """

    @abstractmethod
    def is_paused(self):
        """Query if the media player is paused.

        Must be overriden.

        Returns:
            bool: True if the media player is paused.
        """

    @abstractmethod
    def is_playing_this(self, what):
        """Query if the media player is playing the requested media type.

        Must be overriden.

        Args:
            what (str): Tell if the media player current track is of the
                requested type, but not if it is actually playing it (it can be
                in pause).

        Returns:
            bool: True if the media player is playing the requested type.
        """

    @abstractmethod
    def play(self, what):
        """Request the media player to play something.

        No preparation should be done by this function, i.e. the media track
        should have been prepared already by `set_playlist_entry`.

        Must be overriden.

        Args:
            what (str): What media to play.
        """

    @abstractmethod
    def pause(self, paused):
        """Request the media player to pause or unpause.

        Can only work on transition screens or songs. Pausing should have no
        effect if the media player is already paused, unpausing should have no
        effect if the media player is already unpaused.

        Must be overriden.

        Args:
            paused (bool): If True, pause the media player.
        """

    @abstractmethod
    def skip(self):
        """Request to skip the current media.

        Can only work on transition screens or songs. The media player should
        continue playing, but media has to be considered already finished.

        Must be overriden.
        """

    @abstractmethod
    def stop_player():
        """Request to stop the media player.

        Must be overriden.
        """

    def set_playlist_entry(self, playlist_entry, autoplay=True):
        """Prepare playlist entry base data to be played.

        Check if the song file exists, otherwise consider the song cannot be
        played.

        Args:
            playlist_entry (dict): Playlist entry object.
            autoplay (bool): If True, start to play transition screen as soon
                as possible.
        """
        file_path = self.kara_folder_path / playlist_entry["song"]["file_path"]

        if not file_path.exists():
            logger.error("File not found '%s'", file_path)
            self.callbacks["error"](playlist_entry["id"], "File not found")
            self.callbacks["could_not_play"](playlist_entry["id"])
            return

        self.playlist_entry = playlist_entry

        self.set_playlist_entry_player(playlist_entry, file_path, autoplay)

    @abstractmethod
    def set_playlist_entry_player(self, playlist_entry, file_path, autoplay):
        """Prepare playlist entry data to be played.

        Prepare all media objects, subtitles, etc. for being played, for the
        transition screen and the song. Such data should be stored on a
        dedicated object, like `playlist_entry_data`.

        Must be overriden.

        Args:
            playlist_entry (dict): Playlist entry object.
            file_path (path.Path): Absolute path to the song file.
            autoplay (bool): If True, start to play transition screen as soon
                as possible (i.e. as soon as the transition screen media is
                ready). The song media is prepared when the transition screen
                is playing.
        """

    def clear_playlist_entry(self):
        """Clean playlist entry base data after being played.
        """
        self.playlist_entry = None

        self.clear_playlist_entry_player()

    @abstractmethod
    def clear_playlist_entry_player(self):
        """Clean playlist entry data after being played.

        Must be overriden.
        """

    def set_callback(self, name, callback):
        """Set callback to the media player.

        Args:
            name (str): Name of the callback.
            callback (function): Callback.
        """
        self.callbacks[name] = callback

    @staticmethod
    def get_instrumental_file(filepath):
        """Get the instrumental audio file associated to a given song file.

        Consider that this instrumental file should be the only one audio file found.

        Returns:
            path.Path: Path to the instrumental file. None if not found.
        """
        audio_files = get_audio_files(filepath)

        # accept only one audio file
        if len(audio_files) == 1:
            return audio_files[0]

        # otherwise return None
        return None

    def check_kara_folder_path(self):
        """Check if the karaoke folder exists.
        """
        if not self.kara_folder_path.exists():
            raise KaraFolderNotFound(
                'Karaoke folder "{}" does not exist'.format(self.kara_folder_path)
            )

    def check_is_available(self):
        """Check if the media player is installed and useable.
        """
        # check the target player is available
        if not self.is_available():
            raise MediaPlayerNotAvailableError(
                "{} is not available".format(self.player_name)
            )

    def set_default_callbacks(self):
        """Set dummy callbacks that have to be defined externally.
        """
        self.set_callback("started_transition", lambda playlist_entry_id: None)
        self.set_callback("started_song", lambda playlist_entry_id: None)
        self.set_callback("could_not_play", lambda playlist_entry_id: None)
        self.set_callback("finished", lambda playlist_entry_id: None)
        self.set_callback("paused", lambda playlist_entry_id, timing: None)
        self.set_callback("resumed", lambda playlist_entry_id, timing: None)
        self.set_callback("error", lambda playlist_entry_id, message: None)

    def exit_worker(self, *args, **kwargs):
        """Exit the worker.

        If `warn_long_exit` was True during initialization, send a warning
        after `PLAYER_CLOSING_DURATION` seconds if the worker is not closed
        yet.
        """
        if self.warn_long_exit:
            # send a warning within if the player has not stopped already
            timer_stop_player_too_long = Timer(
                PLAYER_CLOSING_DURATION, self.warn_stop_player_too_long
            )
            timer_stop_player_too_long.start()

        # stop player
        self.stop_player()

        if self.warn_long_exit:
            # clear the warning
            timer_stop_player_too_long.cancel()

    @classmethod
    def warn_stop_player_too_long(cls):
        """Notify the user that the player takes too long to stop.
        """
        logger.warning("{} takes too long to stop".format(cls.player_name))

    def generate_text(self, what, *args, **kwargs):
        """Generate text screens for the requested action.

        Extra arguments are passed to `TextGenerator.create_*_text`.

        Args:
            what (str): What text screen to generate.

        Returns:
            path.Path: Path of the text screen.
        """
        if what == "idle":
            text = self.text_generator.create_idle_text(
                {
                    "notes": [
                        "{} {}".format(self.player_name, self.get_version()),
                        "Dakara player {}".format(__version__),
                    ]
                },
                *args,
                **kwargs
            )

        elif what == "transition":
            text = self.text_generator.create_transition_text(
                self.playlist_entry, *args, **kwargs
            )

        else:
            raise ValueError("Unexpected action to generate text to: {}".format(what))

        self.text_paths[what].write_text(text, "utf-8")

        return self.text_paths[what]


class KaraFolderNotFound(DakaraError):
    """Error raised when the kara folder cannot be found
    """


class MediaPlayerNotAvailableError(DakaraError):
    """Error raised when trying to use a target player that cannot be found
    """


class InvalidStateError(RuntimeError):
    """Error raised when the state of the player is invalid
    """


class VersionNotFoundError(Exception):
    """Error raised when the version of the player cannot be found
    """
