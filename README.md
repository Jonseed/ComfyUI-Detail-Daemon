![DetailDaemon-example](https://github.com/user-attachments/assets/8f336c94-a4c6-426e-abe1-6a4c80a37cbb)
# ComfyUI-Detail-Daemon

A port of muerrilla's [sd-webui-Detail-Daemon](https://github.com/muerrilla/sd-webui-detail-daemon/) as a node for ComfyUI, to adjust sigmas that generally enhance details, and possibly remove unwanted bokeh or background blurring, particularly with Flux models (but also works with SDXL, SD1.5, Qwen, Z-Image, and likely other models). If the values are taken too far it results in an oversharpened and/or HDR effect. There are four nodes here. Multiply Sigmas and Lying Sigma Sampler are also included as alternative methods of generally enhancing details.

- [**Detail Daemon Sampler**](#detail-daemon-sampler)
- [**Detail Daemon Graph Sigmas**](#detail-daemon-graph-sigmas) (to graph the sigmas adjustment visually)
- [**Multiply Sigmas**](#multiply-sigmas) (stateless)
- [**Lying Sigma Sampler**](#lying-sigma-sampler)

Note that Detail Daemon and Lying Sigma Sampler nodes work by default with custom sampler nodes such as `SamplerCustomAdvanced`. If you want to use them with non-custom sampler nodes such as `KSampler` or `KSamplerAdvanced`, then you'll need to make a custom sampler preset using the [`BlehSetSamplerPreset`](https://github.com/blepping/ComfyUI-bleh#blehsetsamplerpreset) node, so you can select the preset from the list in the sampler node, [as discussed here](https://github.com/Jonseed/ComfyUI-Detail-Daemon/discussions/4#discussioncomment-11134965).

[Example and testing workflows](#example-and-testing-workflows) are also available.

## Nodes

### Detail Daemon Sampler

![Screenshot 2024-10-29 124741](https://github.com/user-attachments/assets/c11bd716-1fa1-43b6-8d64-ab20642bceb5)

Allows sampling with the Detail Daemon schedule adjustment, which keeps the noise levels injected the same while lowering the amount of noise removed at each step, which effectively adds detail. Detail_amounts between 0 and 1.0 work best. See muerrilla's [Detail Daemon](https://github.com/muerrilla/sd-webui-detail-daemon/) repo for full explanation of inputs and methodology. Generally speaking, large features are established in earlier steps and small details take shape in later steps. So adjusting the amount in earlier steps will affect bigger shapes, and adjusting it in later steps will influence smaller fine details. The default adjusts mostly in the middle steps.

Parameters (the graphing node below can help visualize these parameters):
- `detail_amount`: the main value that adjusts the detail in the middle of the generation process. Positive values lower the sigmas, reducing noise removed at each step, which increases detail. For Flux or Z-Image models, you'll probably want between 0.1–1.0 range, or higher. For SDXL models, probably less than 0.25. You can also use negative values if you want to *decrease* detail or simplify the image.
- `start`: when do you want the adjustment to start, in a percent range from 0–1.0, 0 being the first step, 1.0 being the last step. Recommended: 0.1–0.5
- `end`: when do you want the adjustment to end, in a percent range from 0–1.0, 0 being the first step, 1.0 being the last step. Recommended: 0.5–0.9
- `bias`: shifts the detail_amount in the middle steps forward or back in the generation process.
- `exponent`: changes the curvature of the adjustment. 0 is no curvature, 1 is smoothly curved.
- `start_offset`: start the detail_amount at a particular value at the beginning of the generation process. Not recommended.
- `end_offset`: end the detail_amount at a particular value at the end of the generation process.
- `fade`: reduce the entire adjustment curve by a particular value.
- `smooth`: (true/false), do you want the adjustment curve to be smooth or not.
- `cfg_scale_override`: if set to 0 (default), the sampler will automatically determine the CFG scale (if possible). Set to some other value to override (should probably match the CFG used in your workflow).

### Detail Daemon Graph Sigmas

![Screenshot 2024-10-29 131939](https://github.com/user-attachments/assets/d0a3f895-5f6d-4b94-b4d1-aa86e7acb5d7)

Allows graphing adjusted sigmas to visually see the effects of different parameters on a graphed curve. This had to be a separate node from the Detail Daemon Sampler node in order to function properly. Just set the values the same as that node, or set inputs on separate primitive nodes that input into both the Detail Daemon Sampler and this Graph Sigmas node. You'll need to run the queue in order to see the graph on the node. *Please note: this node doesn't actually change the sigmas used when generating, it only graphs them*.

### Multiply Sigmas

![Screenshot 2024-10-29 124833](https://github.com/user-attachments/assets/25efbad7-8df2-4c21-a7b5-989d2954df48)

Simple node to multiply all sigmas (noise levels) by the supplied factor. It multiplies both the noise levels added *and* denoised by the factor, which somehow adds detail with a factor less than 1. It is *stateless*, meaning it calculates the sigmas fresh on every queue (other multiply sigmas nodes seem to calculate on prior run sigmas).

Parameters:
- `factor`: the amount that you want to multiply the sigma (noise level) by at each step. So, for example, if the first step has a sigma of 1, then using a factor of 0.95 would make this sigma 0.95. If a step has a sigma of 0.7, then a factor of 0.95 would make it 0.665. You probably want to keep this factor between 0.95–0.99. Lower values increase detail, but might also increasingly change the composition of the image, or introduce noisy grain. Setting it to 1.0 effectively disables the node. 
- `start`: when do you want the adjustment to start, in a percent range from 0–1.0, 0 being the first step, 1.0 being the last step.
- `end`: when do you want the adjustment to end, in a percent range from 0–1.0, 0 being the first step, 1.0 being the last step.

### Lying Sigma Sampler

![Screenshot 2024-10-29 124803](https://github.com/user-attachments/assets/11c24b49-96e1-4f50-9b82-1d6778c2a8ea)

A simpler version of Detail Daemon Sampler, with only amount adjustment and start and end values.

Parameters:
- `dishonesty_factor`: similar to `detail_amount` in the Detail Daemon node, this adjusts the amount of detail. It is on a different scale though, for example, -0.05 `dishonesty_factor` is the equivalent of 0.5 in `detail_amount` of Detail Daemon (or 0.95 of Multiply Sigmas). Negative values adjust the sigmas down, increasing detail. You probably want to stay between -0.1 and -0.01. Positive values would increase the sigmas, *decreasing* detail.
- `start_percent`: when do you want the adjustment to start, in a percent range from 0–1.0, 0 being the first step, 1.0 being the last step. Recommended: 0.1–0.5
- `end_percent`: when do you want the adjustment to end, in a percent range from 0–1.0, 0 being the first step, 1.0 being the last step. Recommended: 0.5–0.9

## Example and testing workflows

[![Screenshot 2024-10-29 134541](https://github.com/user-attachments/assets/a3d2849d-4ed0-4b5b-adca-48dcd07132ca)](https://github.com/Jonseed/ComfyUI-Detail-Daemon/blob/main/Comparing%20Detailers.json)

- **Z-Image-Turbo**: the [Z-Image txt2image-DetailDaemon.json](https://github.com/Jonseed/ComfyUI-Detail-Daemon/blob/main/example_workflows/Z-Image%20txt2img-DetailDaemon.json) is an example of using Detail Daemon in a Z-Image txt2img workflow.
- **Flux**: the [Comparing Detailers.json](https://github.com/Jonseed/ComfyUI-Detail-Daemon/blob/main/example_workflows/Comparing%20Detailers.json) workflow will allow you to compare all these various detailer nodes on the same prompt and seed.
- **Flux img2img**: the [Flux img2img-DetailDaemon.json](https://github.com/Jonseed/ComfyUI-Detail-Daemon/blob/main/example_workflows/Flux%20img2img-DetailDaemon.json) is an example of using Detail Daemon in a Flux img2img workflow.
- **Flux upscale**: the [Flux upscale-DetailDaemon.json](https://github.com/Jonseed/ComfyUI-Detail-Daemon/blob/main/example_workflows/Flux%20upscale-Detail%20Daemon.json) is an example of using Detail Daemon in a Flux upscale workflow.
- **Flux inpainting**: the [Flux inpainting-DetailDaemon.json](https://github.com/Jonseed/ComfyUI-Detail-Daemon/blob/main/example_workflows/Flux%20inpainting-Detail%20Daemon.json) is an example of using Detail Daemon in a Flux inpainting workflow.
- **SDXL**: the [SDXL txt2img-DetailDaemon.json](https://github.com/Jonseed/ComfyUI-Detail-Daemon/blob/main/example_workflows/SDXL%20txt2img-DetailDaemon.json) is an example of using Detail Daemon in a SDXL workflow.

## Credits

- Detail Daemon concept and schedule generation function from muerrilla: https://github.com/muerrilla/sd-webui-detail-daemon/
- ComfyUI sampler implementation and schedule interpolation, as well as Lying Sigma Sampler, by https://github.com/blepping/
- Multiply Sigmas node based on the one included here: https://github.com/Extraltodeus/sigmas_tools_and_the_golden_scheduler
