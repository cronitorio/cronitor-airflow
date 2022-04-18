
def get_provider_info():
    return {
        "package-name": "cronitor-airflow",
        "name": "Cronitor integration for Airflow",
        "description": 'Airflow plugin for Cronitor, with hook, operator, and auto-discovery',
        "hook-class-names": [
            "cronitor_airflow.CronitorHook"
        ],
        "connection-types": [
            {
                'connection-type': 'cronitor',
                'hook-class-name': "cronitor_airflow.CronitorHook"
            }
        ],
    }