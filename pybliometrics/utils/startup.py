import warnings
from collections import deque
from configparser import ConfigParser, NoOptionError, NoSectionError
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple, Union

from pybliometrics.utils.constants import CONFIG_FILE, DEFAULT_PATHS, RATELIMITS, VIEWS
from pybliometrics.utils.create_config import create_config

CONFIG: Optional[ConfigParser] = None
CUSTOM_KEYS: Optional[List[str]] = None
CUSTOM_INSTTOKENS: Optional[List[str]] = None # Assuming InstTokens are strings like APIKeys

# Using Deque for Python 3.9+, for older versions it would be deque
_throttling_params: Dict[str, Deque[Any]] = {
    k: deque(maxlen=v) for k, v in RATELIMITS.items()
}


def preserve_case_optionxform(optionstr: str) -> str:
    return optionstr


def init(
    config_path: Optional[Union[str, Path]] = None,
    keys: Optional[List[str]] = None,
    inst_tokens: Optional[List[str]] = None,
    config_dir: Optional[Union[str, Path]] = None, # Deprecated
) -> None:
    """
    Function to initialize the pybliometrics library. For more information refer to the
    `official documentation <https://pybliometrics.readthedocs.io/en/stable/configuration.html>`_.

    :param config_path: Path to the configuration file.  If None, defaults to
                        pybliometrics.utils.constants.CONFIG_FILE.
    :param keys: List of API keys.
    :param inst_tokens: List of corresponding InstTokens. The order must match that
                        of `keys` to avoid errors.
    :param config_dir: (Deprecated) Path to the configuration file. Use `config_path` instead.

    :raises NoSectionError: If the required sections (Directories, Authentication, Request)
                            do not exist.
    :raises ValueError: If there are no or fewer API keys than InstTokens present.
    """
    global CONFIG
    global CUSTOM_KEYS
    global CUSTOM_INSTTOKENS

    # Deprecation inserted in 4.2
    if config_dir is not None:
        msg = (
            "The 'config_dir' parameter is deprecated and will be removed in "
            "a future version. Please use 'config_path' instead."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=2)
        if config_path is None:
            config_path = config_dir

    resolved_config_path: Path
    if not config_path:
        resolved_config_path = CONFIG_FILE
    elif isinstance(config_path, str):
        resolved_config_path = Path(config_path)
    else:
        resolved_config_path = config_path


    if not resolved_config_path.exists():
        CONFIG = create_config(resolved_config_path, keys, inst_tokens)
    else:
        CONFIG = ConfigParser()
        CONFIG.optionxform = preserve_case_optionxform
        CONFIG.read(resolved_config_path)

    if CONFIG is None: # Should not happen if create_config always returns a ConfigParser
        raise RuntimeError("Configuration could not be loaded or created.")

    check_sections(CONFIG)
    check_default_paths(CONFIG, resolved_config_path)
    create_cache_folders(CONFIG)

    CUSTOM_KEYS = keys
    CUSTOM_INSTTOKENS = inst_tokens
    check_keys_tokens()


def check_sections(config: ConfigParser) -> None:
    """Auxiliary function to check if all sections exist."""
    for section in ["Directories", "Authentication", "Requests"]:
        if not config.has_section(section):
            raise NoSectionError(section)


def check_default_paths(config: ConfigParser, config_path: Path) -> None:
    """
    Auxiliary function to check if default cache paths exist.
    If not, the paths are writen in the config.
    """
    modified = False
    for api, path_str in DEFAULT_PATHS.items():
        if not config.has_option("Directories", api):
            config.set("Directories", api, str(path_str))
            modified = True
    if modified:
        with open(config_path, "w", encoding="utf-8") as ouf:
            config.write(ouf)


def check_keys_tokens() -> None:
    """Auxiliary function to check if API keys or InstTokens are set."""
    keys_list = get_keys()
    insttokens_list = get_insttokens() # Assuming this returns list of strings now

    no_keys_no_insttokens = not keys_list and not insttokens_list
    insttokens_no_keys = insttokens_list and not keys_list
    keys_and_insttokens = keys_list and insttokens_list

    if no_keys_no_insttokens:
        raise ValueError(
            "No API keys or InstTokens found. "
            "Please provide at least one API key or InstToken. "
            "For more information visit: "
            "https://pybliometrics.readthedocs.io/en/stable/configuration.html"
        )
    if insttokens_no_keys:
        raise ValueError(
            "InstTokens found but not corresponding API keys. "
            "Please provide the API keys that correspond to the InstTokens. "
            "For more information visit: "
            "https://pybliometrics.readthedocs.io/en/stable/configuration.html"
        )
    if keys_and_insttokens:
        if len(keys_list) < len(insttokens_list):
            raise ValueError(
                "More InstTokens than API keys found, or lists are misaligned. "
                "Please provide all the API keys that correspond to the InstTokens. "
                "For more information visit: "
                "https://pybliometrics.readthedocs.io/en/stable/configuration.html"
            )


def create_cache_folders(config: ConfigParser) -> None:
    """Auxiliary function to create cache folders."""
    # config.items("Directories") returns list of (name, value)
    for api, path_str_val in config.items("Directories"):
        # VIEWS is Dict[str, List[str]]
        # path_str_val is the directory for the api e.g. "/path/to/scopus"
        # view is e.g. "abstracts"
        if api in VIEWS: # Ensure api key exists in VIEWS
            for view in VIEWS[api]:
                view_path = Path(str(path_str_val), view) # Ensure path_str_val is treated as string
                view_path.mkdir(parents=True, exist_ok=True)


def get_config() -> ConfigParser: # Changed Type[ConfigParser] to ConfigParser
    """Function to get the config parser."""
    if CONFIG is None:
        raise FileNotFoundError(
            "No configuration file found."
            "Please initialize Pybliometrics with init().\n"
            "For more information visit: "
            "https://pybliometrics.readthedocs.io/en/stable/configuration.html"
        )
    return CONFIG


def get_insttokens() -> List[str]:
    """Function to get the InstToken and overwrite InstToken in config if needed."""
    global CONFIG # Ensure we are using the global CONFIG
    inst_tokens_list: List[str] = []
    if CUSTOM_INSTTOKENS:
        inst_tokens_list = CUSTOM_INSTTOKENS
    elif CONFIG is not None and not CUSTOM_KEYS:  # if custom keys are set, config inst tokens are not needed
        try:
            raw_token_text = CONFIG.get("Authentication", "InstToken")
            inst_tokens_list = [k.strip() for k in raw_token_text.split(",") if k.strip()]
        except (NoOptionError, NoSectionError): # Added NoSectionError
            inst_tokens_list = []
    elif CONFIG is None:
         raise FileNotFoundError(
            "Configuration not initialized. Call init() first."
        )
    return inst_tokens_list


def get_keys() -> List[str]:
    """Function to get all the API keys and overwrite keys in config if needed."""
    global CONFIG # Ensure we are using the global CONFIG
    keys_list: List[str] = []
    if CUSTOM_KEYS:
        keys_list = CUSTOM_KEYS
    elif CONFIG is not None:
        try:
            raw_keys_text = CONFIG.get("Authentication", "APIKey")
            keys_list = [k.strip() for k in raw_keys_text.split(",") if k.strip()]
        except (NoOptionError, NoSectionError): # Added NoSectionError
            keys_list = []
    elif CONFIG is None:
         raise FileNotFoundError(
            "Configuration not initialized. Call init() first."
        )
    return keys_list
