import yaml

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True