from kubernetes import client, config


class K8sTask:
    namespace = ''
    user = ''

    def __init__(self):
        config.load_kube_config()

    def get_user_namespace(self):
        namespace = []
        for ns in client.CoreV1Api().list_namespace().items:
            if ns.metadata.labels is not None:
                if {"user": self.user} == ns.metadata.labels:
                    namespace.append(ns)
        return namespace

    def find_namespace(self):
        namespace = []
        for ns in client.CoreV1Api().list_namespace().items:
            if self.namespace in ns.metadata.name:
                namespace.append(ns)
        return namespace

    def create_namespace(self):
        info = client.V1Namespace(
            api_version="v1",
            kind="Namespace",
            metadata=client.V1ObjectMeta(
                name=self.namespace,
                labels={
                    "user": self.user}))
        return client.CoreV1Api().create_namespace(body=info)

    def delete_namespace(self):
        return client.CoreV1Api().delete_namespace(self.namespace)

    def list_namespace(self):
        return client.CoreV1Api().read_namespace(self.namespace)

    def list_job(self):
        return client.BatchV1Api().list_job_for_all_namespaces().items

    def delete_job(self, name):
        return client.BatchV1Api().delete_namespaced_job(
            name=name, namespace=self.namespace)

    def create_job(self, name, image, cmd, path):
        container = client.V1Container(
            name=name,
            image=image,
            env=[client.V1EnvVar(
                name='PYTHONUNBUFFERED',
                value='0'
            )],
            command=cmd,
            volume_mounts=[client.V1VolumeMount(
                name=name + "-volume",
                mount_path="/root",
            )]
        )
        volume = client.V1Volume(
            name=name + "-volume",
            host_path=client.V1HostPathVolumeSource(
                path=path,
            )
        )
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                name=name, labels={"user": self.user}),
            spec=client.V1PodSpec(
                # 重启策略
                restart_policy="Never",
                containers=[container],
                volumes=[volume],
            )
        )
        spec = client.V1JobSpec(
            template=template,
            # 并行数
            parallelism=1,
            # 失败重启数
            backoff_limit=0,
        )
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec
        )
        client.BatchV1Api().create_namespaced_job(
            namespace=self.namespace,
            body=job
        )

    def get_pod_name_with_job(self, job_name):
        job_uid = client.BatchV1Api().read_namespaced_job_status(
            job_name, self.namespace).metadata.uid
        for pod in client.CoreV1Api().list_pod_for_all_namespaces(watch=False).items:
            if pod.metadata.owner_references is not None:
                if job_uid == pod.metadata.owner_references[0].uid:
                    return pod.metadata.name
        return None

    def get_pod_with_job(self, job_name):
        job_uid = client.BatchV1Api().read_namespaced_job_status(
            job_name, self.namespace).metadata.uid
        for pod in client.CoreV1Api().list_pod_for_all_namespaces(watch=False).items:
            if pod.metadata.owner_references is not None:
                if job_uid == pod.metadata.owner_references[0].uid:
                    return pod
        return None

    def log_job(self, name):
        return client.CoreV1Api().read_namespaced_pod_log(
            name=self.get_pod_name_with_job(job_name=name),
            namespace=self.namespace,
        )

    def info_job(self, name):
        return client.BatchV1Api().read_namespaced_job(
            name=name,
            namespace=self.namespace,
        )


class BreadTask:
    group = 'core.run-linux.com'
    version = 'v1alpha1'

    def __init__(self):
        config.load_kube_config()
        self.api = client.CustomObjectsApi()
        self.coreApi = client.CoreV1Api()

    def Creat_Bread(self, name, namespace, gpu, mem, clock,
                    framework, version, task_type, priority, command):
        body = {
            "apiVersion": "core.run-linux.com/v1alpha1",
            "kind": "Bread",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "scv": {
                    "gpu": gpu,
                    "memory": mem,
                    "clock": clock,
                    "priority": priority,
                },
                "framework": {
                    "name": framework,
                    "version": version
                },
                "task": {
                    "type": task_type,
                    "command": command
                }
            }
        }
        self.api.create_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=namespace,
            plural="breads",
            body=body,
        )

    def Get_Bread(self, name, namespace):
        return self.api.get_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=namespace,
            plural="breads",
            name=name
        )

    def Get_Bread_Status(self, name, namespace):
        return self.api.get_namespaced_custom_object_status(
            group=self.group,
            version=self.version,
            namespace=namespace,
            plural="breads",
            name=name
        )["status"]

    def Delete_Bread(self, name, namespace):
        self.api.delete_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=namespace,
            plural="breads",
            name=name,
            body=client.V1DeleteOptions(),
        )

    def List_Bread(self, namespace):
        return self.api.list_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=namespace,
            plural="breads",
        )['items']

    def Get_Pod_Logs(self, name, namespace):
        return self.coreApi.read_namespaced_pod_log(
            name=name,
            namespace=namespace,
        )

    def Get_Pod_Info(self, name, namespace):
        return self.coreApi.read_namespaced_pod(
            name=name,
            namespace=namespace,
        )


if __name__ == '__main__':
    # k = K8sTask()
    # k.user = 'root'
    # k.namespace = 'test'
    # k.create_namespace()
    # b = BreadTask()

    print(BreadTask().List_Bread("root"))
    # try:
    #     api_response = k.log_job('test')
    #     pprint(api_response)
    # except ApiException as e:
    #     print("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)

    # for ns in k.get_user_namespace():
    #     print(ns.metadata.name)
