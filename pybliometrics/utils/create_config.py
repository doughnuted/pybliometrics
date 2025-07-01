import configparser
from pathlib import Path
from typing import Optional, Union

from pybliometrics.utils.constants import CONFIG_FILE


def create_config(
    config_dir: Optional[Union[str, Path]] = None,
    keys: Optional[list[str]] = None,
    insttoken: Optional[list[str]] = None,
):
    """
    Initiates process to generate configuration file.

    :param config_dir: The location of the configuration file.
    :param keys: If you provide a list of keys, pybliometrics will skip the
                 prompt.  It will also not ask for InstToken.  This is
                 intended for workflows using CI, not for general use.
    :param insttoken: An InstToken to be used alongside the key(s). Will only
                      be used if `keys` is not empty.
    """
    from pybliometrics.utils.constants import DEFAULT_PATHS

    if not config_dir:
        resolved_config_dir = CONFIG_FILE
    elif isinstance(config_dir, str):
        resolved_config_dir = Path(config_dir)
    else:
        resolved_config_dir = config_dir

    config = configparser.ConfigParser()

    def preserve_case_optionxform(optionstr: str) -> str:
        return optionstr

    config.optionxform = preserve_case_optionxform
    print(f"Creating config file at {resolved_config_dir} with default paths...")

    # Set directories
    config.add_section("Directories")
    for api, path in DEFAULT_PATHS.items():
        config.set("Directories", api, str(path))

    # Set authentication
    config.add_section("Authentication")

    keys_str: Optional[str] = None
    insttoken_str: Optional[str] = None

    # Get keys and tokens
    if keys:
        if not isinstance(keys, list):
            raise ValueError("Parameter `keys` must be a list.")
        keys_str = ", ".join(keys)
    if insttoken:
        if not isinstance(insttoken, list):
            raise ValueError("Parameter `inst_tokens` must be a list. ")
        insttoken_str = ", ".join(insttoken)

    # If no keys or tokens are provided, ask for them
    if not (keys_str or insttoken_str):
        prompt_key = (
            "Please enter your API Key(s), obtained from "
            "http://dev.elsevier.com/myapikey.html.  Separate "
            "multiple keys by comma:\n"
        )
        keys_str = input(prompt_key)
        prompt_token = (
            "API Keys are sufficient for most users.  If you "
            "have an InstToken, please enter the tokens pair now. "
            "Separate multiple tokens by a comma. The correspondig "
            "key's position should match the position of the token."
            "If you don't have tokens, just press Enter:\n"
        )
        insttoken_str = input(prompt_token)

    # Set keys and tokens in config
    if keys_str: # Ensure keys_str is not None before setting
        config.set("Authentication", "APIKey", keys_str)
    else:
        # Handle case where keys_str might still be None if not provided by user or params
        # Depending on requirements, could set a default, raise error, or leave empty
        config.set("Authentication", "APIKey", "") # Example: set to empty string

    if insttoken_str:
        config.set("Authentication", "InstToken", insttoken_str)

    # Set default values
    config.add_section("Requests")
    config.set("Requests", "Timeout", "20")
    config.set("Requests", "Retries", "5")

    # Write out
    resolved_config_dir.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved_config_dir, "w") as ouf:
        config.write(ouf)
    print(
        f"Configuration file successfully created at {config_dir}\n"
        "For details see https://pybliometrics.rtfd.io/en/stable/configuration.html."
    )
    return config
