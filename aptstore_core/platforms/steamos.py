import sys
from . import PLATFORM_STEAMOS
from .platform import Platform


class SteamOS(Platform):
    """
    SteamDeck platform
    """

    def __init__(self, **kwargs):
        super(SteamOS, self).__init__(**kwargs)
        self.platform_name = PLATFORM_STEAMOS
        self.admin_needed = True
        self.data = {
            'paths': {
                'progress': self.user_home + '/.aptstore/progress/',
            },
        }

    def install(self, **kwargs):
        """
        Validate params and install app with given id
        :param kwargs:
        :return:
        """
        super(SteamOS, self).install(**kwargs)
        self.initialize_platform()

        try:
            self.platform_initialized()
            expected_params = self.get_install_params()
            self.validate_params(kwargs.keys(), expected_params)
        except ValueError:
            return

        try:
            self.install_steamos_app()
        except FileExistsError as err:
            print(err)

    def remove(self, **kwargs):
        """
        Validate params and remove app with given id
        :param kwargs:
        :return:
        """
        super(SteamOS, self).remove(**kwargs)
        self.initialize_platform()

        try:
            self.remove_steamos_app()
        except FileExistsError as err:
            print(err)
            sys.exit("Installation locked")
        except ValueError as err:
            print(err)
            sys.exit("Abort")

    def install_steamos_app(self):
        pass

    def remove_steamos_app(self):
        pass
