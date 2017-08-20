import os
import logging
import shutil
import tempfile
from string import Template
from codecs import open
from configparser import ConfigParser
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

SHARE_DIR = 'share'

TRANSITION_TEMPLATE_NAME = "transition.ass"
TRANSITION_TEXT_NAME = "transition.ass"

IDLE_TEMPLATE_NAME = "idle.ass"
IDLE_TEXT_NAME = "idle.ass"

ICON_MAP_FILE = "font-awesome.ini"

logger = logging.getLogger(__name__)

class TextGenerator:

    def __init__(self, config):
        # load icon mapping
        self.load_icon_map()

        # load templates
        self.load_templates(config)

        # create temporary directory
        self.create_temp_directory()

        # set text paths
        self.transition_text_path = os.path.join(
                self.tempdir,
                TRANSITION_TEXT_NAME
                )

        self.idle_text_path = os.path.join(
                self.tempdir,
                IDLE_TEXT_NAME
                )

    def load_templates(self, config):
        # create Jinja2 environment
        self.environment = Environment(
                loader=FileSystemLoader(
                    os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        os.pardir,
                        SHARE_DIR
                        )
                    )
                )

        # add filter for converting font icon name to character
        self.environment.filters['icon'] = lambda name: \
                chr(int(self.icon_map.get(name, '0020'), 16))

        transition_template_path = config.get('transitionTemplateName', TRANSITION_TEMPLATE_NAME)
        idle_template_path = config.get('idleTemplateName', IDLE_TEMPLATE_NAME)

        # load templates
        self.load_transition_template(transition_template_path)
        self.load_idle_template(idle_template_path)

    def with_temp_directory(fun):
        """ Decorator that checks there is a temporary
            directory created

            The decorator will create a temporary directory
            and then execute the given function.

            Args:
                fun: the function to decorate.

            Returns:
                the decorated function.
        """
        def call(self, *args, **kwargs):
            if self.tempdir is None:
                self.create_temp_directory()

            return fun(self, *args, **kwargs)

        return call

    def create_temp_directory(self):
        """ Create a temporary directory for text generation
        """
        self.tempdir = tempfile.mkdtemp(suffix=".dakara")
        logger.debug("Creating temporary directory \"{}\"".format(
            self.tempdir
            ))

    @with_temp_directory
    def create_idle_text(self, info):
        """ Create custom idle text and save it

            The acceptable placeholders in the template are:
                - `vlc_version`: version of VLC.

            Args:
                info: dictionnary of additionnal information.

            Returns:
                path of the text containing the idle screen content.
        """
        # using the template
        idle_text = self.idle_template.render(
                **info
                )

        with open(self.idle_text_path, 'w', encoding='utf8') as file:
            file.write(idle_text)

        logger.debug("Create idle screen text file in \
\"{}\"".format(self.idle_text_path))

        return self.idle_text_path

    @with_temp_directory
    def create_transition_text(self, playlist_entry):
        """ Create custom transition text and save it

            The accepted placeholders in the template are:
                - `title`: song title,
                - `artists`: list of artists,
                - `works`: list of works.

            Args:
                playlist_entry: dictionary containing keys for title,
                    artists and works.

            Returns:
                path of the text containing the transition screen
                content.
        """
        transition_text = self.transition_template.render(playlist_entry)

        with open(self.transition_text_path, 'w', encoding='utf8') as file:
            file.write(transition_text)

        logger.debug("Create transition screen text file in \
\"{}\"".format(self.transition_text_path))

        return self.transition_text_path

    def load_icon_map(self):
        """ Load the icon map
        """
        icon_map_path = os.path.join(SHARE_DIR, ICON_MAP_FILE)

        if not os.path.isfile(icon_map_path):
            raise IOError("Icon font map file '{}' not found".format(
                icon_map_path
                ))

        icon_map = ConfigParser()
        icon_map.read(icon_map_path)
        self.icon_map = icon_map['map']

    def load_transition_template(self, template_name):
        """ Load transition screen text template file

            Load the default or customized ASS template for
            transition screen.
        """
        template_path = os.path.join(SHARE_DIR, template_name)
        template_default_path = os.path.join(SHARE_DIR, TRANSITION_TEMPLATE_NAME)

        if os.path.isfile(template_path):
            pass

        elif os.path.isfile(template_default_path):
            logger.warning("Transition template file not found \"{}\", \
using default one".format(template_path))

            template_name = TRANSITION_TEMPLATE_NAME

        else:
            self.clean()
            raise IOError("No template file for transition screen found")

        self.transition_template = self.environment.get_template(template_name)


        logger.debug("Loading transition template file \"{}\"".format(
            template_path
            ))

    def load_idle_template(self, template_name):
        """ Load idle screen text template file

            Load the default or customized ASS template for
            idle screen.
        """
        template_path = os.path.join(SHARE_DIR, template_name)
        template_default_path = os.path.join(SHARE_DIR, IDLE_TEMPLATE_NAME)

        if os.path.isfile(template_path):
            pass

        elif os.path.isfile(template_default_path):
            logger.warning("Idle template file not found \"{}\", \
using default one".format(template_path))

            template_name = IDLE_TEMPLATE_NAME

        else:
            self.clean()
            raise IOError("No template file for idle screen found")

        self.idle_template = self.environment.get_template(template_name)

        logger.debug("Loading idle template file \"{}\"".format(
            template_path
            ))

    def clean(self):
        """ Remove the temp directory
        """
        logger.debug("Deleting temporary directory \"{}\"".format(
            self.tempdir
            ))
        try:
            shutil.rmtree(self.tempdir)
            self.tempdir = None

        except OSError:
            logger.error("Unable to delete temporary directory")
