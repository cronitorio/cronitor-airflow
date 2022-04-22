
def get_provider_info():
    return {
        "package-name": "apache-airflow-providers-cronitor",
        "name": "Cronitor integration for Airflow",
        "description": 'Airflow plugin for Cronitor, with hook, operator, and auto-discovery',
        "hook-class-names": [
            "cronitor_airflow.hooks.cronitor_hook.CronitorHook"
        ],
        "connection-types": [
            {
                'connection-type': 'cronitor',
                'hook-class-name': "cronitor_airflow.hooks.cronitor_hook.CronitorHook"
            }
        ],
    }