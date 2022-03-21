from nornir import InitNornir
from nornir.core.filter import F
from nornir.core.task import Task, Result
from nornir_utils.plugins.functions import print_result
from nornir_jinja2.plugins.tasks import template_string, template_file
from nornir_utils.plugins.tasks.files import write_file
from nornir_napalm.plugins.tasks import napalm_configure


def render_configs(task: Task) -> Result:
    template_path = f"templates/"
    template = "infrastructure_base_config.j2"

    result = task.run(
        task=template_file,
        template=template,
        path=template_path,
        **task.host,
        # **task.host unpacks the host name so you don't have to do "host.interfaces.items()"
        # in jinja template. It allows you to just do "interfaces.items()".
        # Its just a personal preference.
    )

    rendered_config = result[0].result

    # This adds information to the host data field. We are storing rendered config in
    # data field of host object
    task.host['rendered_config'] = rendered_config

    return Result(
        host=task.host,
    )


def write_configs(task: Task, rendered_config) -> Result:
    cfg_path = f"configlets/"
    filename = f"{cfg_path}{task.host.name}.txt"
    content = task.host['rendered_config']

    task.run(
        task=write_file,
        filename=filename,
        content=content,
    )

    return Result(
        host=task.host
    )


def deploy_configs(task: Task) -> Result:
    filename = f"configlets/{task.host.name}.txt"
    with open(filename, "r") as f:
        cfg = f.read()

    task.run(
        task=napalm_configure,
        configuration=cfg,
        replace=True,
    )

    return Result(
        host=task.host,
    )


def main():
    nr = InitNornir()
    nr = nr.filter(F(groups__contains="eos"))
    # nr = nr.filter(name="leaf1")
    render_result = nr.run(
        task=render_configs,
    )
    print_result(render_result)

    write_result = nr.run(
        task=write_configs,
        rendered_config="test"
    )
    print_result(write_result)
    deploy_result = nr.run(
        task=deploy_configs,
    )
    print_result(deploy_result)
    print()


if __name__ == "__main__":
    main()
