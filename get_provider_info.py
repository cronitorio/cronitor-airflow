
def get_provider_info():
    return {
        "package-name": "cronitor-airflow",
        "name": "Cronitor integration for Airflow",
        "description": 'Airflow plugin for Cronitor, with hook, operator, and auto-discovery',
        "hook-class-names": [
            "main.CronitorHook"
        ]
    }