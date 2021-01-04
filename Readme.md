## Concepts

- **Task** : Step
- **Flow** : Describes dependencies between tasks, such as their order or how they pass data around.
- [**Context**](https://docs.prefect.io/api/latest/utilities/context.html) : Implements the Prefect context that is available when tasks run.

**Flow version**
> Each call to flow.register() will bump the version of the flow in the backend. If you are registering flows using automation, you may want to pass an idempotency_key which will only create a new version when the key changes.



## Code Of interest
### Flow Reference Tasks
It's possible to define which tasks are gonna be used to determine the final state of the flow.

```python
flow.set_reference_tasks([task_1, task_2, task_3])
```

### Retries
```python
@task(max_retries=3, retry_delay=timedelta(seconds=10))
def extract_reference_data():
    # same as before ...
```

### [State handlers](https://docs.prefect.io/core/concepts/states.html#state-handlers-callbacks)
Flows and Tasks may have one or more state handler functions that are called whenever the task's state changes.
```python
def notify_on_retry(task, old_state, new_state):
    if isinstance(new_state, state.Retrying):
        send_notification() # function that sends a notification
    return new_state

task_that_notifies = Task(state_handlers=[notify_on_retry])
```

### [Callback_factory](https://docs.prefect.io/core/concepts/notifications.html#higher-level-api)
```python
from prefect.utilities.notifications import callback_factory
import requests

def send_post(task, state):
    msg = f"Task {task} failed and is retrying at {state.start_time}"
    requests.post("https://XXXXX", json={"text": msg})

post_to_slack = callback_factory(send_post, lambda s: s.is_retrying())
task_that_notifies = Task(state_handlers=[post_to_slack])
```


## Commands of Interest

Configures Prefect for local orchestration, and saves the configuration in your local `~/.prefect` directory
```shell script
prefect backend server
```

Starts the Server UI at [localhost:8080](http://localhost:8080).
````shell script
prefect server start
````

Starts a Prefect Agent
```shell script
prefect agent local start
```

Create Project

```shell script
prefect create project 'Hello, World!'
```

## Kubernetes
Use DaskExecutor with [dask_kubernetes.KubeCluster](https://kubernetes.dask.org/) as cluster class.
Setup the [Helm Dask](https://helm.dask.org/) to be able to have Dask in K8s.

- [Static Dask Cluster on Kubernetes](https://docs.prefect.io/orchestration/recipes/k8s_dask.html)
- [Kubernetes Agent](https://docs.prefect.io/orchestration/agents/kubernetes.html#kubernetes-agent)

## Issues of Interest
- Kubernetes Cluster AutoScaler can result in failed Flow Runs [#3058](https://github.com/PrefectHQ/prefect/issues/3058)
```shell script
# Temporal solution by adding --safe-to-evict annotation to the agents
prefect agent install/start kubernetes --safe-to-evict=False
```

## Links of Interest
- [Github - Prefect](https://github.com/prefecthq/prefect)
- [Installation](https://docs.prefect.io/core/getting_started/installation.html)
- [First Steps](https://docs.prefect.io/core/getting_started/first-steps.html)
- [Schedules](https://docs.prefect.io/core/concepts/schedules.html)
- [Logging](https://docs.prefect.io/core/concepts/logging.html)
- [Results](https://docs.prefect.io/api/latest/engine/results.html)
- [Config Example](https://github.com/PrefectHQ/prefect/blob/master/src/prefect/config.toml)
