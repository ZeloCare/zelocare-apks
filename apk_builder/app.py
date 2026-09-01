import os
import re
import secrets
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, status
from kubernetes import client, config
from pydantic import BaseModel, Field

APP = FastAPI(title="ZeloCare APK Builder", version="1.0.0")
NAMESPACE = os.getenv("POD_NAMESPACE", "zelocare-dev")
IMAGE = os.environ["APK_BUILDER_IMAGE"]
TOKEN = os.environ["APK_BUILDER_API_TOKEN"]
SECRET_NAME = os.getenv("APK_BUILDER_SECRET", "apk-builder-secrets")
REF_RE = re.compile(r"^[A-Za-z0-9._/@-]{1,128}$")


class BuildRequest(BaseModel):
    app: Literal["all", "zelocare-mobile", "zelocare-volunteer"] = "all"
    mobile_ref: str = Field(default="main", max_length=128)
    volunteer_ref: str = Field(default="main", max_length=128)


def authorize(token: str | None) -> None:
    if not token or not secrets.compare_digest(token, TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def batch_api() -> client.BatchV1Api:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
    return client.BatchV1Api()


@APP.get("/health")
def health():
    return {"status": "ok"}


@APP.post("/v1/builds", status_code=status.HTTP_202_ACCEPTED)
def create_build(payload: BuildRequest, x_apk_builder_token: str | None = Header(default=None)):
    authorize(x_apk_builder_token)
    for ref in (payload.mobile_ref, payload.volunteer_ref):
        if not REF_RE.fullmatch(ref):
            raise HTTPException(status_code=422, detail="Invalid source ref")
    build_id = f"apk-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{secrets.token_hex(3)}"
    labels = {"app.kubernetes.io/name": "apk-builder", "zelocare.pt/build-id": build_id}
    env = [
        client.V1EnvVar(name="BUILD_ID", value=build_id),
        client.V1EnvVar(name="BUILD_APP", value=payload.app),
        client.V1EnvVar(name="MOBILE_REF", value=payload.mobile_ref),
        client.V1EnvVar(name="VOLUNTEER_REF", value=payload.volunteer_ref),
    ]
    container = client.V1Container(
        name="builder", image=IMAGE, image_pull_policy="Always", command=["python", "-m", "apk_builder.worker"],
        env=env, env_from=[client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name=SECRET_NAME))],
        resources=client.V1ResourceRequirements(requests={"cpu": "2", "memory": "6Gi"}, limits={"cpu": "4", "memory": "10Gi"}),
    )
    job = client.V1Job(
        metadata=client.V1ObjectMeta(name=build_id, labels=labels),
        spec=client.V1JobSpec(backoff_limit=0, ttl_seconds_after_finished=86400, active_deadline_seconds=7200,
            template=client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels=labels), spec=client.V1PodSpec(restart_policy="Never", image_pull_secrets=[client.V1LocalObjectReference(name="ghcr-pull-secret")], containers=[container]))),
    )
    batch_api().create_namespaced_job(NAMESPACE, job)
    return {"id": build_id, "status": "queued"}


@APP.get("/v1/builds/{build_id}")
def get_build(build_id: str, x_apk_builder_token: str | None = Header(default=None)):
    authorize(x_apk_builder_token)
    job = batch_api().read_namespaced_job(build_id, NAMESPACE)
    state = "failed" if job.status.failed else "succeeded" if job.status.succeeded else "running" if job.status.active else "queued"
    return {"id": build_id, "status": state, "started_at": job.status.start_time, "completed_at": job.status.completion_time}
