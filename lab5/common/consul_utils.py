import consul
import logging
import atexit
import socket
import uuid

logger = logging.getLogger(__name__)

CONSUL_HOST = "localhost"
CONSUL_PORT = 8500

try:
    consul_client = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
except Exception as e:
    logger.error(f"Failed to initialize Consul client: {e}")
    consul_client = None


def get_service_id(service_name, port):
    return f"{service_name}-{port}-{str(uuid.uuid4())[:8]}"


def register_service(service_name, service_port, health_check_path="/health", is_http_service=True):
    if not consul_client:
        logger.error("Consul client not available. Cannot register service.")
        return None

    # host_ip = socket.gethostbyname(socket.gethostname())
    host_ip = "host.docker.internal"
    service_id = get_service_id(service_name, service_port)

    check_definition = {
        "name": f"{service_name} Check",
        "interval": "10s",
        "timeout": "5s",
        "deregistercriticalserviceafter": "30s"
    }

    if is_http_service and health_check_path:
        check_definition["http"] = f"http://{host_ip}:{service_port}{health_check_path}"
    else:
        check_definition["tcp"] = f"{host_ip}:{service_port}"

    try:
        consul_client.agent.service.register(
            name=service_name,
            service_id=service_id,
            address=host_ip,
            port=service_port,
            check=check_definition,
            tags=[service_name, "python"]
        )
        logger.info(f"Service '{service_name}' registered with Consul. ID: {service_id}")
        atexit.register(deregister_service, service_id)
        return service_id
    except Exception as e:
        logger.error(f"Failed to register service {service_name} with Consul: {e}")
        return None


def deregister_service(service_id):
    if not consul_client:
        return
    try:
        consul_client.agent.service.deregister(service_id)
        logger.info(f"Service ID '{service_id}' deregistered from Consul.")
    except Exception as e:
        logger.error(f"Failed to deregister service {service_id}: {e}")


def get_config_from_kv(key, default=None):
    if not consul_client:
        return default
    try:
        index, data = consul_client.kv.get(key)
        if data and data['Value']:
            return data['Value'].decode('utf-8')
        return default
    except Exception as e:
        logger.error(f"Error fetching key '{key}' from Consul: {e}")
        return default


def discover_services(service_name):
    if not consul_client:
        return []
    try:
        index, data = consul_client.health.service(service_name, passing=True)
        return [f"{entry['Service']['Address']}:{entry['Service']['Port']}" for entry in data]
    except Exception as e:
        logger.error(f"Error discovering services for {service_name}: {e}")
        return []


# Configuration keys
KAFKA_BROKERS_KV_KEY = "config/kafka/brokers"
KAFKA_TOPIC_KV_KEY = "config/kafka/topic"
HAZELCAST_MEMBERS_KV_KEY = "config/hazelcast/members"
HAZELCAST_CLUSTER_NAME_KV_KEY = "config/hazelcast/cluster_name"