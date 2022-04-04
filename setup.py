from setuptools import setup

setup(
    name='cronitor-airflow',
    version='0.0.1',
    packages=[''],
    install_requires=[
        "airflow>=2.0.0",
        "requests",
    ],
    url='https://github.com/cronitorio/cronitor-airflow',
    license='MIT',
    author='JJ',
    author_email='jj@cronitor.io',
    description='Airflow plugin for Cronitor, with hook, operator, and auto-discovery',
    entry_points={
        "airflow.plugins": ["cronitor = main:CronitorPlugin"],
        "apache_airflow_provider": ["provider_info = get_provider_info:get_provider_info"],
    }
)
