# __init__.py

from .detail_daemon_node import DetailDaemonSamplerNode, DetailDaemonGraphSigmasNode, MultiplySigmas, AdvancedLyingSigmaSamplerNode

NODE_CLASS_MAPPINGS = {
    "DetailDaemonSamplerNode": DetailDaemonSamplerNode,
    "DetailDaemonGraphSigmasNode": DetailDaemonGraphSigmasNode,
    "MultiplySigmas": MultiplySigmas,
    "AdvancedLyingSigmaSamplerNode": AdvancedLyingSigmaSamplerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DetailDaemonSamplerNode": "Detail Daemon Sampler",
    "DetailDaemonGraphSigmasNode": "Detail Daemon Graph Sigmas",
    "MultiplySigmas": "Multiply Sigmas (stateless)",
    "AdvancedLyingSigmaSamplerNode": "Advanced Lying Sigma Sampler",
}

__all__ = ["NODE_CLASS_MAPPINGS"]
