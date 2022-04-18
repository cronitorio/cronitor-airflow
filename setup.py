from setuptools import setup

setup(
    name='cronitor-airflow',
    version='0.0.1',
    packages=[''],
    install_requires=[
        "apache-airflow>=2.0.0",
        "requests",
    ],
    url='https://github.com/cronitorio/cronitor-airflow',
    license='MIT',
    author='JJ',
    author_email='jj@cronitor.io',
    description='Airflow plugin for Cronitor, with hook, operator, and auto-discovery',
    entry_points={
        "airflow.plugins": ["cronitor = cronitor_airflow:CronitorPlugin"],
        "apache_airflow_provider": ["provider_info = get_provider_info:get_provider_info"],
    },
    classifiers=[
        "Framework :: Apache Airflow",
        "Framework :: Apache Airflow :: Provider",
    ]
)
