import os


class Config:
    def method1(self):
        pass

    @staticmethod
    def getConfigs():
        config = {
            'SRC_DIR': os.path.join(os.path.dirname(os.path.dirname(__file__)))
        }
        config['VAR_DIR'] = os.path.join(config['SRC_DIR'], 'var')
        config['CWEB_DIR'] = os.path.join(config['VAR_DIR'], 'www')
        return config
