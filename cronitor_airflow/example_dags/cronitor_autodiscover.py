from datetime import timedelta
from datetime import datetime
from airflow.cli import cli_parser
from airflow.configuration import conf
from airflow.models import DagBag, DAG, DagRun
from airflow.decorators import dag, task
import argcomplete
import cronitor
from airflow.operators.python import get_current_context
import os
import logging
from cronitor_airflow.hooks.cronitor_hook import CronitorHook
from airflow.timetables.interval import CronDataIntervalTimetable, DeltaDataIntervalTimetable


def do_parsing(input_args):
    if conf.get("core", "security") == 'kerberos':
        os.environ['KRB5CCNAME'] = conf.get('kerberos', 'ccache')
        os.environ['KRB5_KTNAME'] = conf.get('kerberos', 'keytab')
    parser = cli_parser.get_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(input_args)
    return args.func(args)


def convert_dag_to_monitor(dag: DAG) -> dict:
    monitor = {
        'type': 'job',
        'key': f'airflow.{dag.dag_id}',
        'schedule': dag.timetable.summary,
        'tags': ['airflow'],
    }
    return monitor


@dag(
    description="Autodiscovery of Airflow DAGs to be sent to Cronitor",
    catchup=False,
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2022, 1, 1),
    tags=['cronitor'],
)
def autoprovision_monitors(cronitor_conn_id='cronitor_default'):
    @task()
    def get_dags():
        """Get all active, non-paused DAGs and convert them to Cronitor monitors"""
        dags = DagBag().dags
        outlist = []
        for dag in dags.values():
            if dag.get_is_active() and not dag.get_is_paused():
                if isinstance(dag.timetable, (CronDataIntervalTimetable, DeltaDataIntervalTimetable)):
                    outlist.append(convert_dag_to_monitor(dag))
                else:
                    logging.warning(f"DAG '{dag.dag_id}' does not use a cron-based schedule or has an invalid schedule "
                                    f"or timetable: '{type(dag.timetable)}'. Cronitor autodiscover currently only supports "
                                    f"cron- or interval-based schedules/timetables. Skipping the DAG.")
                    continue
        return outlist

    @task()
    def put_monitors(monitors):
        # Can get context this way rather than having it pass in via args
        # https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html#accessing-context-variables-in-decorated-tasks
        context = get_current_context()
        connection = CronitorHook().get_connection(context['params']['cronitor_conn_id'])
        cronitor.api_key = connection.password
        cronitor.Monitor.put(monitors)

    @task()
    def get_dagruns_for_monitors(monitors):
        pass
        ## Find out the last time this dag was run, and then for every other DAG,
        ## send all of the telemetry since the last run to Cronitor

    monitors = get_dags()
    put_monitors(monitors)
