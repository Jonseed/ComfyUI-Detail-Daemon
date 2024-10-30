# Based on the concept from https://github.com/muerrilla/sd-webui-detail-daemon

from __future__ import annotations

import io

import matplotlib.pyplot as plt
import numpy as np
import torch
from comfy.samplers import KSAMPLER
from PIL import Image
import folder_paths
import random
import os


# Schedule creation function from https://github.com/muerrilla/sd-webui-detail-daemon
def make_detail_daemon_schedule(
    steps,
    start,
    end,
    bias,
    amount,
    exponent,
    start_offset,
    end_offset,
    fade,
    smooth,
):
    start = min(start, end)
    mid = start + bias * (end - start)
    multipliers = np.zeros(steps)

    start_idx, mid_idx, end_idx = [
        int(round(x * (steps - 1))) for x in [start, mid, end]
    ]

    start_values = np.linspace(0, 1, mid_idx - start_idx + 1)
    if smooth:
        start_values = 0.5 * (1 - np.cos(start_values * np.pi))
    start_values = start_values**exponent
    if start_values.any():
        start_values *= amount - start_offset
        start_values += start_offset

    end_values = np.linspace(1, 0, end_idx - mid_idx + 1)
    if smooth:
        end_values = 0.5 * (1 - np.cos(end_values * np.pi))
    end_values = end_values**exponent
    if end_values.any():
        end_values *= amount - end_offset
        end_values += end_offset

    multipliers[start_idx : mid_idx + 1] = start_values
    multipliers[mid_idx : end_idx + 1] = end_values
    multipliers[:start_idx] = start_offset
    multipliers[end_idx + 1 :] = end_offset
    multipliers *= 1 - fade

    return multipliers


class DetailDaemonGraphSigmasNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "sigmas": ("SIGMAS", {"forceInput": True}),
                "detail_amount": (
                    "FLOAT",
                    {"default": 0.1, "min": -5.0, "max": 5.0, "step": 0.01},
                ),
                "start": (
                    "FLOAT",
                    {"default": 0.2, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "end": (
                    "FLOAT",
                    {"default": 0.8, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "bias": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "exponent": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.05},
                ),
                "start_offset": (
                    "FLOAT",
                    {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01},
                ),
                "end_offset": (
                    "FLOAT",
                    {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01},
                ),
                "fade": (
                    "FLOAT",
                    {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                "smooth": ("BOOLEAN", {"default": True}),
                "cfg_scale": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 100.0,
                        "step": 0.5,
                        "round": 0.01,
                    },
                ),
            },
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    CATEGORY = "sampling/custom_sampling/sigmas"
    FUNCTION = "make_graph"

    def make_graph(
        self,
        sigmas,
        detail_amount,
        start,
        end,
        bias,
        exponent,
        start_offset,
        end_offset,
        fade,
        smooth,
        cfg_scale,
    ):
        # Create a copy of the input sigmas using clone() for tensors to avoid modifying the original
        sigmas = sigmas.clone()

        # Derive the number of steps from the length of sigmas minus 1 (ignore the final sigma)
        steps = len(sigmas) - 1  # 21 sigmas, 20 steps
        actual_steps = steps

        # Create the schedule using the number of steps
        schedule = make_detail_daemon_schedule(
            actual_steps,
            start,
            end,
            bias,
            detail_amount,
            exponent,
            start_offset,
            end_offset,
            fade,
            smooth,
        )

        # Debugging: print schedule and sigmas lengths to verify alignment
        print(
            f"Number of sigmas: {len(sigmas)}, Number of schedule steps: {len(schedule)}",
        )

        # Iterate over the sigmas, except for the last one (which we assume is 0 and leave untouched)
        for idx in range(steps):
            multiplier = schedule[idx] * 0.1

            # Debugging: print each index and sigma to track what's being adjusted
            print(f"Adjusting sigma at index {idx} with multiplier {multiplier}")

            sigmas[idx] *= (
                1 - multiplier * cfg_scale
            )  # Adjust each sigma in "both" mode

        # Create the plot for visualization
        image = self.plot_schedule(schedule)
        
        # Save temp image
        output_dir = folder_paths.get_temp_directory()
        prefix_append = "_temp_" + ''.join(random.choice("abcdefghijklmnopqrstupvxyz") for x in range(5))
        
        full_output_folder, filename, counter, subfolder, _ = (
        folder_paths.get_save_image_path(prefix_append, output_dir)
        )
        filename = f"{filename}_{counter:05}_.png"
        file_path = os.path.join(full_output_folder, filename)
        image.save(file_path, compress_level=1)

        return {
            "ui": {
                "images": [
                    {"filename": filename, "subfolder": subfolder, "type": "temp"},
                ],
            }
        }


    @staticmethod
    def plot_schedule(schedule) -> Image:
        plt.figure(figsize=(6, 4))  # Adjusted width
        plt.plot(schedule, label="Sigma Adjustment Curve")
        plt.xlabel("Steps")
        plt.ylabel("Multiplier (*10)")
        plt.title("Detail Adjustment Schedule")
        plt.legend()
        plt.grid(True)
        plt.xticks(range(len(schedule)))
        plt.ylim(-1, 1)

        # Use tight_layout or subplots_adjust
        plt.tight_layout()
        # Or manually adjust if needed:
        # plt.subplots_adjust(left=0.2)

        buf = io.BytesIO()
        plt.savefig(buf, format="PNG")
        plt.close()
        buf.seek(0)
        image = Image.open(buf)
        return image


def get_dd_schedule(
    sigma: float,
    sigmas: torch.Tensor,
    dd_schedule: torch.Tensor,
) -> float:
    sched_len = len(dd_schedule)
    if (
        sched_len < 2
        or len(sigmas) < 2
        or sigma <= 0
        or not (sigmas[-1] <= sigma <= sigmas[0])
    ):
        return 0.0
    # First, we find the index of the closest sigma in the list to what the model was
    # called with.
    deltas = (sigmas[:-1] - sigma).abs()
    idx = int(deltas.argmin())
    if (
        (idx == 0 and sigma >= sigmas[0])
        or (idx == sched_len - 1 and sigma <= sigmas[-2])
        or deltas[idx] == 0
    ):
        # Either exact match or closest to head/tail of the DD schedule so we
        # can't interpolate to another schedule item.
        return dd_schedule[idx].item()
    # If we're here, that means the sigma is in between two sigmas in the
    # list.
    idxlow, idxhigh = (idx, idx - 1) if sigma > sigmas[idx] else (idx + 1, idx)
    # We find the low/high neighbor sigmas - our sigma is somewhere between them.
    nlow, nhigh = sigmas[idxlow], sigmas[idxhigh]
    if nhigh - nlow == 0:
        # Shouldn't be possible, but just in case... Avoid divide by zero.
        return dd_schedule[idxlow]
    # Ratio of how close we are to the high neighbor.
    ratio = ((sigma - nlow) / (nhigh - nlow)).clamp(0, 1)
    # Mix the DD schedule high/low items according to the ratio.
    return torch.lerp(dd_schedule[idxlow], dd_schedule[idxhigh], ratio).item()


def detail_daemon_sampler(
    model: object,
    x: torch.Tensor,
    sigmas: torch.Tensor,
    *,
    dds_wrapped_sampler: object,
    dds_make_schedule: callable,
    dds_cfg_scale_override: float,
    **kwargs: dict,
) -> torch.Tensor:
    if dds_cfg_scale_override > 0:
        cfg_scale = dds_cfg_scale_override
    else:
        maybe_cfg_scale = getattr(model.inner_model, "cfg", None)
        cfg_scale = (
            float(maybe_cfg_scale) if isinstance(maybe_cfg_scale, (int, float)) else 1.0
        )
    dd_schedule = torch.tensor(
        dds_make_schedule(len(sigmas) - 1),
        dtype=torch.float32,
        device="cpu",
    )
    sigmas_cpu = sigmas.detach().clone().cpu()
    sigma_max, sigma_min = float(sigmas_cpu[0]), float(sigmas_cpu[-1]) + 1e-05

    def model_wrapper(x: torch.Tensor, sigma: torch.Tensor, **extra_args: dict):
        sigma_float = float(sigma.max().detach().cpu())
        if not (sigma_min <= sigma_float <= sigma_max):
            return model(x, sigma, **extra_args)
        dd_adjustment = get_dd_schedule(sigma_float, sigmas_cpu, dd_schedule) * 0.1
        adjusted_sigma = sigma * max(1e-06, 1.0 - dd_adjustment * cfg_scale)
        return model(x, adjusted_sigma, **extra_args)

    for k in (
        "inner_model",
        "sigmas",
    ):
        if hasattr(model, k):
            setattr(model_wrapper, k, getattr(model, k))
    return dds_wrapped_sampler.sampler_function(
        model_wrapper,
        x,
        sigmas,
        **kwargs,
        **dds_wrapped_sampler.extra_options,
    )


class DetailDaemonSamplerNode:
    DESCRIPTION = "This sampler wrapper works by adjusting the sigma passed to the model, while the rest of sampling stays the same."
    CATEGORY = "sampling/custom_sampling/samplers"
    RETURN_TYPES = ("SAMPLER",)
    FUNCTION = "go"

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "sampler": ("SAMPLER",),
                "detail_amount": (
                    "FLOAT",
                    {"default": 0.1, "min": -5.0, "max": 5.0, "step": 0.01},
                ),
                "start": (
                    "FLOAT",
                    {"default": 0.2, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "end": (
                    "FLOAT",
                    {"default": 0.8, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "bias": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                "exponent": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.05},
                ),
                "start_offset": (
                    "FLOAT",
                    {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01},
                ),
                "end_offset": (
                    "FLOAT",
                    {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01},
                ),
                "fade": (
                    "FLOAT",
                    {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                "smooth": ("BOOLEAN", {"default": True}),
                "cfg_scale_override": (
                    "FLOAT",
                    {
                        "default": 0,
                        "min": 0.0,
                        "max": 100.0,
                        "step": 0.5,
                        "round": 0.01,
                        "tooltip": "If set to 0, the sampler will automatically determine the CFG scale (if possible). Set to some other value to override.",
                    },
                ),
            },
        }

    @classmethod
    def go(
        cls,
        sampler: object,
        *,
        detail_amount,
        start,
        end,
        bias,
        exponent,
        start_offset,
        end_offset,
        fade,
        smooth,
        cfg_scale_override,
    ) -> tuple:
        def dds_make_schedule(steps):
            return make_detail_daemon_schedule(
                steps,
                start,
                end,
                bias,
                detail_amount,
                exponent,
                start_offset,
                end_offset,
                fade,
                smooth,
            )

        return (
            KSAMPLER(
                detail_daemon_sampler,
                extra_options={
                    "dds_wrapped_sampler": sampler,
                    "dds_make_schedule": dds_make_schedule,
                    "dds_cfg_scale_override": cfg_scale_override,
                },
            ),
        )

#MultiplySigmas Node
class MultiplySigmas:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sigmas": ("SIGMAS", {"forceInput": True}),
                "factor": ("FLOAT", {"default": 1, "min": 0, "max": 100, "step": 0.001})
            }
        }

    FUNCTION = "simple_output"
    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/sigmas"

    def simple_output(self, sigmas, factor):
        # Clone the sigmas to ensure the input is not modified (stateless)
        sigmas = sigmas.clone()
        return (sigmas * factor,)

#advanced_lying_sigma_sampler
def advanced_lying_sigma_sampler(
    model: object,
    x: torch.Tensor,
    sigmas: torch.Tensor,
    *,
    sampler: object,
    dishonesty_factor: float,
    start_percent: float,
    end_percent: float,
    smooth_factor: float = 0.5,
    **kwargs: dict,
) -> torch.Tensor:
    start_sigma = round(model.inner_model.inner_model.model_sampling.percent_to_sigma(start_percent), 4)
    end_sigma = round(model.inner_model.inner_model.model_sampling.percent_to_sigma(end_percent), 4)

    def model_wrapper(x: torch.Tensor, sigma: torch.Tensor, **extra_args: dict):
        sigma_float = float(sigma.max().detach().cpu())
        if end_sigma <= sigma_float <= start_sigma:
            adjustment = dishonesty_factor * (0.5 * (1 - np.cos(smooth_factor * np.pi)))
            sigma = sigma * (1.0 + adjustment)
        return model(x, sigma, **extra_args)

    for k in (
        "inner_model",
        "sigmas",
    ):
        if hasattr(model, k):
            setattr(model_wrapper, k, getattr(model, k))

    # Check if denoise_mask is supported by the sampler function
    if 'denoise_mask' in inspect.signature(sampler.sampler_function).parameters:
        return sampler.sampler_function(
            model_wrapper,
            x,
            sigmas,
            denoise_mask=kwargs.get('denoise_mask'),
            **kwargs,
            **sampler.extra_options,
        )
    else:
        return sampler.sampler_function(
            model_wrapper,
            x,
            sigmas,
            **kwargs,
            **sampler.extra_options,
        )

class AdvancedLyingSigmaSamplerNode:
    DESCRIPTION = "高级sigma控制器，使用前最好关闭float rounding并重启comfui,以达到最佳控制效果|For advanced sigma controllers, it is best to turn off float rounding and restart comfui before use for optimal control."
    CATEGORY = "sampling/custom_sampling/advanced_samplers"
    RETURN_TYPES = ("SAMPLER",)
    FUNCTION = "initialize"

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "sampler": ("SAMPLER",),
                "dishonesty_factor": (
                    "FLOAT",
                    {
                        "default": -0.1,
                        "min": -1.0,
                        "max": 1.0,
                        "step": 0.001,
                        "tooltip": "Default value -0.1, which is generally a larger value|Multiplier for sigmas passed to the model. -0.1 means we reduce the sigma by 10%."
                    }
                ),
                "start_percent": (
                    "FLOAT",
                    {
                        "default": 0.1,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "If you're not sure what you're doing, leave it at default, a reminder from tatookan."
                    }
                ),
                "end_percent": (
                    "FLOAT",
                    {
                        "default": 0.9,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "If you're not sure what you're doing, leave it at default, a reminder from tatookan."
                    }
                ),
                "smooth_factor": (
                    "FLOAT",
                    {
                        "default": 0.5,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "If you're not sure what you're doing, leave it at default, a reminder from tatookan."
                    }
                ),
            }
        }

    @classmethod
    def initialize(
        cls,
        sampler: object,
        dishonesty_factor: float,
        start_percent: float,
        end_percent: float,
        smooth_factor: float,
    ) -> tuple:
        return (
            KSAMPLER(
                advanced_lying_sigma_sampler,
                extra_options={
                    "sampler": sampler,
                    "dishonesty_factor": dishonesty_factor,
                    "start_percent": start_percent,
                    "end_percent": end_percent,
                    "smooth_factor": smooth_factor,
                },
            ),
        )

