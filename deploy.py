import datetime
import io
import json
import os
import subprocess
import time
import config
import pyautogui

import logs

logger = logs.get_logger(__name__)


def execute_and_log(command, log_fn=logger.debug):
    """
    Execute the given command and log stdout and stderr.
    """
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    ) as process:

        def line_error(line):
            """
            `True` if the line looks like an error. This is a heuristic built for
            processes that use stderr for both normal and erronious output.
            """
            return any([p in line.upper() for p in ['ERROR', 'INVALID']])

        mixed_stream_result = ''

        # stream stdout
        for line in process.stdout:
            mixed_stream_result += line
            if stripped_line := line.strip('\n'):
                log_fn(stripped_line)

        # stream stderr
        for line in process.stderr:
            mixed_stream_result += line
            if line_error(line):
                logger.error(line)
                exit(1)
            elif stripped_line := line.strip('\n'):
                log_fn(stripped_line)

        return io.StringIO(mixed_stream_result)


def service_state(service_name, readable_obj):
    """
    The current state of the service.
    """
    for service in json.load(readable_obj)["containerServices"]:
        if service["containerServiceName"] == service_name:
            return service["state"]
    logger.error(f"Couldn't find service state for service: {service_name}!")


def create_temp_deployment_files(image_ref):
    """
    Create temporary deployment json configuration files and return their local paths.
    TODO: Perhaps include some global configuration for the container port?
    """
    os.makedirs("/tmp", exist_ok=True)
    containers_path = "/tmp/containers.json"
    with open(containers_path, "w") as file:
        json.dump({"flask": {"image": image_ref, "ports": {"5000": "HTTP"}}}, file, indent=4)
    public_endpoint_path = "/tmp/public-endpoint.json"
    with open(public_endpoint_path, "w") as file:
        json.dump({"containerName": "flask", "containerPort": 5000}, file, indent=4)

    return containers_path, public_endpoint_path


def _deploy_container_service(service_name, ecr_image_uri, poll_freq_seconds=5):
    logger.info("Creating temp deployment files...")
    containers_config, endpoint_config = create_temp_deployment_files(ecr_image_uri)
    args = f"--service-name {service_name} "
    args += f"--containers file://{containers_config} "
    args += f"--public-endpoint file://{endpoint_config}"
    logger.info("Deploying to AWS lightsail...")
    execute_and_log(f"aws lightsail create-container-service-deployment {args}")
    current_state = None
    while "RUNNING" != current_state:
        current_state = service_state(
            service_name, execute_and_log("aws lightsail get-container-services")
        )
        logger.info(f"AWS lightsail service {service_name} -- {current_state}")
        time.sleep(poll_freq_seconds)
    logger.info("Removing temp deployment files...")
    os.remove(containers_config)
    os.remove(endpoint_config)
    logger.green("Deployed!")


def deploy():
    image_name = "sambot-flask-image"
    image_tag = "image-" + datetime.datetime.now().strftime("%Y-%d-%H-%M-%S")
    aws_account_id = "381492305823"
    aws_region = "us-east-1"
    repository_name = "sams-repo"
    service_name = "sambot-flask-service"
    # TODO: Make these constants configurable in the config.py file

    # Build the Docker image
    logger.info("Building docker image...")
    execute_and_log(f"docker build -t {image_name}:{image_tag} .", log_fn=logger.blue)

    # Authenticate Docker to the ECR repository
    logger.info('Authenticating docker to the AWS ERC repository...')
    os.environ['AWS_ACCESS_KEY_ID'] = config.AWS_ACCESS_KEY_ID
    os.environ['AWS_SECRET_ACCESS_KEY'] = config.AWS_SECRET_ACCESS_KEY
    os.environ['AWS_DEFAULT_REGION'] = aws_region
    execute_and_log('aws configure')
    # Simulate pressing 'Enter'
    pyautogui.press('enter')
    login_command = f"aws ecr get-login-password --region {aws_region} | docker login --username AWS --password-stdin {aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com"
    execute_and_log(login_command)
    logger.info('Authenticated!')

    # Tag the Docker image for the Amazon ECR repository
    logger.info("Tagging docker image...")
    ecr_image_uri = (
        f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/{repository_name}:{image_tag}"
    )
    execute_and_log(f"docker tag {image_name}:{image_tag} {ecr_image_uri}")
    logger.info("Tagged!")

    # Push the Docker image to the ECR repository
    logger.info("Pushing docker image...")
    execute_and_log(f"docker push {ecr_image_uri}", log_fn=logger.blue)

    # deploy!
    _deploy_container_service(service_name, ecr_image_uri)


if __name__ == "__main__":
    deploy()
