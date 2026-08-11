# __init__.py

from .detail_daemon_node import DetailDaemonSamplerNode, DetailDaemonSamplerGUINode, DetailDaemonGraphSigmasNode, MultiplySigmas, LyingSigmaSamplerNode

NODE_CLASS_MAPPINGS = {
    "DetailDaemonSamplerNode": DetailDaemonSamplerNode,
    "DetailDaemonSamplerGUINode": DetailDaemonSamplerGUINode,
    "DetailDaemonGraphSigmasNode": DetailDaemonGraphSigmasNode,
    "MultiplySigmas": MultiplySigmas,
    "LyingSigmaSampler": LyingSigmaSamplerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DetailDaemonSamplerNode": "Detail Daemon Sampler",
    "DetailDaemonSamplerGUINode": "Detail Daemon Sampler GUI",
    "DetailDaemonGraphSigmasNode": "Detail Daemon Graph Sigmas",
    "MultiplySigmas": "Multiply Sigmas (stateless)",
    "LyingSigmaSampler": "Lying Sigma Sampler",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

