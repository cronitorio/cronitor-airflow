from setuptools import setup

setup(
    name='cronitor-airflow',
    version='0.0.1',
    packages=['cronitor_airflow',
              'cronitor_airflow.operators',
              'cronitor_airflow.hooks',
              'cronitor_airflow.example_dags'],
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
        "apache_airflow_provider": ["provider_info = cronitor_airflow.__init__:get_provider_info"],
    },
    classifiers=[
        "Framework :: Apache Airflow",
        "Framework :: Apache Airflow :: Provider",
    ]
)
