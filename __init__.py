# __init__.py

from .detail_daemon_node import DetailDaemonSamplerNode, DetailDaemonGraphSigmasNode, MultiplySigmas, LyingSigmaSamplerNode

NODE_CLASS_MAPPINGS = {
    "DetailDaemonSamplerNode": DetailDaemonSamplerNode,
    "DetailDaemonGraphSigmasNode": DetailDaemonGraphSigmasNode,
    "MultiplySigmas": MultiplySigmas,
    "AdvancedLyingSigmaSample": AdvancedLyingSigmaSamplerNode，
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DetailDaemonSamplerNode": "Detail Daemon Sampler",
    "DetailDaemonGraphSigmasNode": "Detail Daemon Graph Sigmas",
    "MultiplySigmas": "Multiply Sigmas (stateless)",
    "LyingSigmaSampler": "Advanced Lying Sigma Sampler",
}

__all__ = ["NODE_CLASS_MAPPINGS"]

