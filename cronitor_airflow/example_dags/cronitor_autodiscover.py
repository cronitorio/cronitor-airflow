from datetime import timedelta
from datetime import datetime
from airflow.cli import cli_parser
from airflow.configuration import conf
from airflow.models import DagBag, DAG
from airflow.decorators import dag, task
import argcomplete
import croniter
import cronitor
import os
import logging
from cronitor_airflow.hooks.cronitor_hook import CronitorHook


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
def autocollect_dags(cronitor_conn_id='cronitor_default'):
    @task()
    def get_dags():
        """Get all active, non-paused DAGs and convert them to Cronitor monitors"""
        dags = DagBag().dags
        outlist = []
        for dag in dags.values():
            if dag.get_is_active() and not dag.get_is_paused():
                # TODO: This doesn't work yet, this isn't the right way to check if
                # the schedule is a weird timetable or a regular cron expression
                if croniter.croniter.is_valid(dag.timetable.summary):
                    outlist.append(convert_dag_to_monitor(dag))
                else:
                    logging.warning(f"DAG '{dag.dag_id}' does not use a cron-based schedule or has an invalid schedule "
                                    f"or timetable: '{dag.timetable.summary}'. Cronitor autodiscover currently only supports cron-based "
                                    f"schedules/timetables. Skipping the DAG.")
                    continue
        return outlist

    @task()
    def put_monitors(monitors):
        CronitorHook().get_connection(cronitor_conn_id)
        cronitor.api_key = ''
        cronitor.Monitor.put(monitors)

    monitors = get_dags()
    put_monitors(monitors)