from typing import Literal, Optional

import requests
from airflow.models import BaseOperator
from airflow.utils.context import Context

from cronitor_airflow.hooks.cronitor_hook import CronitorHook

CronitorState = Literal["run", "complete", "fail", "ok"]


class CronitorOperator(BaseOperator):
    """
    This operator allows you to ping Cronitor to inform the monitor of the status of your DAG.

    :param monitor_key: Required. The ID within Cronitor of the monitor you want to ping
    :param state: Required. The status of the DAG. One of ["run", "complete", "fail", "ok"]
    :param env: Optional. The environment key in Cronitor
    :param cronitor_conn_id: The Cronitor connection name in Airflow. Defaults to 'cronitor_default'
    """
    def __init__(
            self,
            monitor_key: str,
            state: CronitorState,
            env: Optional[str] = None,
            cronitor_conn_id: str = 'cronitor_default',
            **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.monitor_key = monitor_key
        self.state = state
        self.env = env
        self.cronitor_conn_id = cronitor_conn_id

    def execute(self, context: Context) -> None:
        hook = CronitorHook(cronitor_conn_id=self.cronitor_conn_id)
        series = context['run_id']
        self.log.info('Sending ping %s to Cronitor for run_id %s', self.state, series)
        response: requests.Response = hook.ping(self.monitor_key, self.state, self.env, series)
        response.raise_for_status()