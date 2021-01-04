from datetime import timedelta, datetime
from logging import Logger
from random import Random

import prefect
from prefect import Flow, triggers
from prefect import task, Task, Parameter
from prefect.engine import signals, state
from prefect.engine.state import State
from prefect.schedules import IntervalSchedule
from prefect.tasks.aws import AWSSecretsManager
from prefect.utilities.notifications import callback_factory
from prefect.executors import DaskExecutor, LocalDaskExecutor
from prefect.tasks.secrets import SecretBase, PrefectSecret
from prefect.client.secrets import Secret
from prefect.utilities.debug import is_serializable



@task
def say_hello(person: str) -> None:
    logger = prefect.context.get('logger')
    logger.info(f'Hello, {person}!')


@task(trigger=triggers.always_run)
def say_bye(person: str) -> None:
    logger = prefect.context.get('logger')
    logger.info(f'Bye: {person}')


@task
def print_secret(secret_content: dict) -> None:
    logger = prefect.context.get('logger')
    logger.info(f'Secret: {secret_content}')


class RandomTask(Task):

    def __init__(self, min: int = 0, max: int = 10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min = min
        self.max = max

    def run(self, threshold: int) -> int:
        r = Random()
        v = r.randint(a=self.min, b=self.max)
        if v > threshold:
            raise signals.FAIL(message=f'{v} is greater than {threshold}')
        self.logger.info(f'Value is {v}')
        return v


def notify_on_retry(task: Task, new_state: State):
    logger: Logger = prefect.context.get('logger')
    logger.warning(
        f'Task {task.name}/{task.slug} is retrying at {new_state.start_time}',
    )


log_on_retry = callback_factory(notify_on_retry, lambda s: s.is_retrying())

name = Parameter('name', default='potato')
threshold = Parameter('threshold', default=8)

schedule = IntervalSchedule(
    start_date=datetime.fromisoformat('2021-01-01'),
    interval=timedelta(minutes=2),
)

with Flow(
        name='My first flow!',
        schedule=schedule,
        validate=True,
        executor=LocalDaskExecutor(),
) as flow:
    hello_task = say_hello(person=name)

    random = RandomTask(
        name='Random', max_retries=3,
        retry_delay=timedelta(seconds=1),
    )
    random_1 = random(threshold=threshold)
    random_2 = random(threshold=threshold)
    random_3 = random(threshold=threshold)
    random_x = random.map(threshold=[random_1, random_2, random_3])

    secret_task = AWSSecretsManager(
        secret='prefect/dummy',
        boto_kwargs={
            'use_session': True,
            'profile_name': 'MyProfileName',
            'region_name': 'us-east-1'
        }
    )

    spy_task = print_secret(secret_task)
    bye_task = say_bye(person=name)

    # Task Lineage
    hello_task.set_upstream(spy_task)
    random_1.set_upstream(hello_task)
    bye_task.set_upstream(random_x)

for t in flow.tasks:
    if log_on_retry not in t.state_handlers:
        t.state_handlers.append(log_on_retry)

flow.set_reference_tasks([random_x])

is_serializable(flow)
flow.register(
    project_name='Hello, World!',
    idempotency_key=flow.serialized_hash(),
)
