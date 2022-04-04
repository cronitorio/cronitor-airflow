import typing
from airflow.providers.http.hooks.http import HttpHook
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from requests.auth import AuthBase
import requests
from functools import cached_property
import importlib.metadata
from typing import Optional, Any, Dict, Literal

if typing.TYPE_CHECKING:
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
        r.url = r.url.replace('<cronitor_api_key>', api_key)
        return r


class CronitorHook(HttpHook):
    """
    Hook to manage connection to the Cronitor API
    """

    conn_name_attr = 'cronitor_conn_id'
    default_conn_name = 'cronitor_default'
    conn_type = 'cronitor'
    hook_name = 'Cronitor'
    base_url = "https://cronitor.link/p/<cronitor_api_key>"

    def __init__(self, cronitor_conn_id: str = "cronitor_default"):
        super().__init__(
            http_conn_id=cronitor_conn_id,
            method="POST",
            auth_type=CronitorTelemetryAuth,
        )

    @cached_property
    def cronitor_airflow_version(self):
        return importlib.metadata.version('cronitor-airflow')

    def get_conn(self, headers: Optional[Dict[Any, Any]] = None) -> requests.Session:
        headers = headers or {}
        headers.update({
            'User-Agent': f'cronitor-airflow/{self.cronitor_airflow_version}',
        })
        session = super().get_conn(headers=headers)
        session.base_url = self.base_url
        return session

    def ping(self, monitor_id, state, env=None, series=None):
        data = {
            'state': state,
        }
        if env:
            data['env'] = env
        if series:
            data['series'] = env

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
