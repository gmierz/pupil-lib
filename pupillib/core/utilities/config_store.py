from frozendict import frozendict


class ConfigStore:

    class innerConfigStore:
        def __init__(self, config):
            self.frozen_config = frozendict(config)

    instance = None

    @staticmethod
    def get_instance(a_dict=None):
        if a_dict is None:
            a_dict = dict()
        if not ConfigStore.instance:
            ConfigStore.instance = ConfigStore.innerConfigStore(a_dict)
        else:
            return ConfigStore.instance

    @staticmethod
    def set_instance(a_dict=None):
        if a_dict is None:
            a_dict = dict()
        if not ConfigStore.instance:
            ConfigStore.instance = ConfigStore.innerConfigStore(a_dict)