import os
from typing import Any, Dict, Optional

from nornir.core.configuration import Config
from nornir.core.connections import ConnectionPlugin

import paramiko


class Paramiko(ConnectionPlugin):
    """
    This plugin connects to the device with paramiko to the device and sets the
    relevant connection.

    Inventory:
        connection_options: maps to argument passed to ``ConnectHandler``.
    """

    def open(
        self,
        hostname: Optional[str],
        username: Optional[str],
        password: Optional[str],
        port: Optional[int],
        platform: Optional[str],
        connection_options: Optional[Dict[str, Any]] = None,
        configuration: Optional[Config] = None,
    ) -> None:
        connection_options = connection_options or {}

        client = paramiko.SSHClient()
        client._policy = paramiko.WarningPolicy()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh_config = paramiko.SSHConfig()
        ssh_config_file = configuration.ssh_config_file  # type: ignore
        if os.path.exists(ssh_config_file):
            with open(ssh_config_file) as f:
                ssh_config.parse(f)
        parameters = {
            "hostname": hostname,
            "username": username,
            "password": password,
            "port": port,
        }

        user_config = ssh_config.lookup(hostname)
        for k in ("hostname", "username", "port"):
            if k in user_config:
                parameters[k] = user_config[k]

        if "proxycommand" in user_config:
            parameters["sock"] = paramiko.ProxyCommand(user_config["proxycommand"])

        self.state["ssh_forward_agent"] = user_config.get("forwardagent") == "yes"

        # TODO configurable
        #  if ssh_key_file:
        #      parameters['key_filename'] = ssh_key_file
        if "identityfile" in user_config:
            parameters["key_filename"] = user_config["identityfile"]

        connection_options.update(parameters)
        client.connect(**connection_options)
        self.connection = client

    def close(self) -> None:
        self.connection.close()