"""Constants for the Neewer Cloud integration."""

DOMAIN = "neewer_cloud"

BASE_URL = "https://homeapp.neewer.cn"
AUTH_HEADER = "Bearer es_fuzzy_search_token_2024"
CLIENT_VERSION = "2.2.4"
CLIENT_NAME = "Home Assistant"

CONF_ACCOUNT = "account"
CONF_PASSWORD = "password"
CONF_CLIENT_ID = "client_id"
CONF_ZONE = "zone"

DEFAULT_ZONE = "GB"
DEFAULT_LANGUAGE = "en"

EP_LOGIN = "/neewerhome/app/user/login/loginByPassword"
EP_LOGOUT = "/neewerhome/app/user/logout"
EP_GROUPS = "/neewerhome/app/group/listGroup"
EP_DEVICES_BY_GROUP = "/neewerhome/app/device/getDevicesByGroupId"
EP_SCENES = "/neewerhome/app/device/sceneEffect/getSceneEffectByDeviceId"
EP_SCENE_EXECUTE = "/neewerhome/app/device/sceneEffect/execute"
EP_TURN_ON = "/neewerhome/app/device/turnOn"
EP_LIGHTING = "/neewerhome/app/device/lightingSetting"
EP_COLOR = "/neewerhome/app/device/colorSetting"

CODE_OK = 0
CODE_TOKEN_EXPIRED = 10011
CODE_TOKEN_INVALID = 10012
