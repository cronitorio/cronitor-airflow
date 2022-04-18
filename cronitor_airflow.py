from airflow.providers.http.hooks.http import HttpHook
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from requests.auth import AuthBase
import requests
from functools import cached_property
import importlib.metadata
from typing import Optional, Any, Dict, Literal
from airflow.utils.context import Context


CronitorState = Literal["run", "complete", "fail", "ok"]


class CronitorTelemetryAuth(AuthBase):
    """
    Custom requests auth provider that puts the api key into the URL
    as required by the Cronitor Telemetry API
    """
    def __init__(self, login=None, password=None):
        self.login = login
        self.password = password

    def __call__(self, r):
        if self.password:
            api_key = self.password
        elif self.login:
            api_key = self.login
        else:
            api_key = ''
        r.url = r.url.replace('<cronitor_api_key>', api_key).replace('%3Ccronitor_api_key%3E', api_key)
        return r


class CronitorHook(HttpHook):
    """
    Hook to manage connection to the Cronitor API
    """

    conn_name_attr = 'cronitor_conn_id'
    default_conn_name = 'cronitor_default'
    conn_type = 'cronitor'
    hook_name = 'Cronitor'

    @property
    def base_url(self):
      return "https://cronitor.link/p/<cronitor_api_key>"

    @base_url.setter
    def base_url(self, a):
        """Do not allow base_url to be set or overridden"""

    @staticmethod
    def get_ui_field_behaviour() -> Dict:
        return {
            "hidden_fields": [
                "host", "schema", "login", "port", "extra",
            ],
            "relabeling": {
                "password": "Cronitor API Key",
            },
            "placeholders": {
                "password": "Your Cronitor API Key",
            }
        }

    def __init__(self, cronitor_conn_id: str = "cronitor_default"):
        BASE_URL = self.base_url
        # HttpHook init sets self.base_url as well
        super().__init__(
            http_conn_id=cronitor_conn_id,
            method="GET",
            auth_type=CronitorTelemetryAuth,
        )
        self.base_url = BASE_URL

    @cached_property
    def cronitor_airflow_version(self):
        return importlib.metadata.version('cronitor-airflow')

    def get_conn(self, headers: Optional[Dict[Any, Any]] = None) -> requests.Session:
        headers = headers or {}
        headers.update({
            'User-Agent': f'cronitor-airflow/{self.cronitor_airflow_version}',
        })
        connection = self.get_connection(self.http_conn_id)
        session = super().get_conn(headers=headers)
        session.base_url = self.base_url
        session.auth = self.auth_type(connection.login, connection.password)
        return session

    # To be implemented at some opint
    # def test_connection(self):
    #     pass

    def ping(self, monitor_id, state, env=None, series=None):
        data = {
            'state': state,
        }
        if env:
            data['env'] = env
        if series:
            data['series'] = series

        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=52264, stdoutToServer=True, stderrToServer=True)

        return self.run(f'/{monitor_id}', data=data)


class CronitorOperator(BaseOperator):
    """
    This operator allows you to ping Cronitor to inform the monitor of the status of your DAG.

    :param monitor_id: Required. The ID within Cronitor of the monitor you want to ping
    :param state: Required. The status of the DAG. One of ["run", "complete", "fail", "ok"]
    :param env: Optional. The environment key in Cronitor
    :param cronitor_conn_id: The Cronitor connection name in Airflow. Defaults to 'cronitor_default'
    """
    def __init__(
            self,
            monitor_id: str,
            state: CronitorState,
            env: Optional[str] = None,
            cronitor_conn_id: str = 'cronitor_default',
            **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.monitor_id = monitor_id
        self.state = state
        self.env = env
        self.cronitor_conn_id = cronitor_conn_id

    def execute(self, context: Context) -> None:
        hook = CronitorHook(cronitor_conn_id=self.cronitor_conn_id)
        series = context['run_id']
        self.log.info('Sending ping %s to Cronitor for run_id %s', self.state, series)
        response: requests.Response = hook.ping(self.monitor_id, self.state, self.env, series)
        response.raise_for_status()


class CronitorPlugin(AirflowPlugin):
    name = 'cronitor'

    hooks = [CronitorHook]
    operator = [CronitorOperator]
