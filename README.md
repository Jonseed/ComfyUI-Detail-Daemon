![DetailDaemon-example](https://github.com/user-attachments/assets/8f336c94-a4c6-426e-abe1-6a4c80a37cbb)
# ComfyUI-Detail-Daemon

A port of muerrilla's [sd-webui-Detail-Daemon](https://github.com/muerrilla/sd-webui-detail-daemon/) as a node for ComfyUI, to adjust sigmas that generally enhance details, and possibly remove unwanted bokeh or background blurring, particularly with Flux models (but also works with SDXL, SD1.5, and likely other models). If the values are taken too far it results in an oversharpened and/or HDR effect. There are four nodes here. Multiply Sigmas and Lying Sigma Sampler are also included as alternative methods of generally enhancing details.

- **Detail Daemon Sampler**
- **Detail Daemon Graph Sigmas** (to graph the sigmas adjustment visually)
- **Multiply Sigmas** (stateless)
- **Lying Sigma Sampler**

## Demonstration
### T2M
FLUX: GGUF-Q6K  
Sampler: euler  
Scheduler: beta  
Steps: 20  
Denoise: 1  

| ON | OFF |
|---|---|
| <img src="https://github.com/tatookan/comfuinoda-Navyblue/blob/main/demo/NO.png" alt="Sampler Example" width="500"> | <img src="https://github.com/tatookan/comfuinoda-Navyblue/blob/main/demo/OFF.png" alt="Sampler Example" width="500"> |

### M2M
FLUX: GGUF-Q6K  
Sampler: euler  
Scheduler: beta  
Steps: 20  
Denoise: 0.5  

| Import Image | Output Image |
|---|---|
| <img src="https://github.com/tatookan/comfuinoda-Navyblue/blob/main/demo/IMAGE.png" alt="Sampler Example" width="500"> | <img src="https://github.com/tatookan/comfuinoda-Navyblue/blob/main/demo/M2M%26NO.png" alt="Sampler Example" width="500"> |

## Nodes

### Detail Daemon Sampler

![Screenshot 2024-10-29 124741](https://github.com/user-attachments/assets/c11bd716-1fa1-43b6-8d64-ab20642bceb5)

Allows sampling with the Detail Daemon schedule adjustment, which keeps the noise levels injected the same while lowering the amount of noise removed at each step, which effectively adds detail. Detail_amounts between 0 and 1.0 work best. See muerrilla's [Detail Daemon](https://github.com/muerrilla/sd-webui-detail-daemon/) repo for full explanation of inputs and methodology.

### Detail Daemon Graph Sigmas

![Screenshot 2024-10-29 131939](https://github.com/user-attachments/assets/d0a3f895-5f6d-4b94-b4d1-aa86e7acb5d7)

Allows graphing adjusted sigmas to visually see the effects of different parameters on a graphed curve. This had to be a separate node from the Detail Daemon Sampler node in order to function properly. Just set the values the same as that node, or set inputs on separate primitive nodes that input into both the Detail Daemon Sampler and this Graph Sigmas node. You'll need to run the queue in order to see the graph on the node. *Please note: this node doesn't actually change the sigmas used when generating, it only graphs them*.

### Multiply Sigmas

![Screenshot 2024-10-29 124833](https://github.com/user-attachments/assets/25efbad7-8df2-4c21-a7b5-989d2954df48)

Simple node to multiply all sigmas by the supplied factor (multiplies both the noise levels added and denoised by the factor, which somehow adds detail with a factor less than 1). Factor values of 0.95-0.99 work best (default without this node is 1.0). It is stateless, meaning it calculates the sigmas fresh on every queue (other multiply sigmas nodes seem to calculate on prior run sigmas). Because this multiplies sigmas of all steps (without start or end values), it tends to change the overall composition of the image too.

### Advanced Lying Sigma Sampler

![Screenshot 2024-10-29 124803](https://github.com/tatookan/comfuinoda-Navyblue/blob/main/demo/%E5%BE%AE%E4%BF%A1%E6%88%AA%E5%9B%BE_20241030163715.png))

A simpler version of Detail Daemon Sampler, with only amount adjustment (-0.1 dishonesty_factor is equivalent of 0.1 in detail_amount of Detail Daemon), start and end values. Dishonesty values between -0.1 and -0.01 work best.

## Example and testing workflow

[![Screenshot 2024-10-29 134541](https://github.com/user-attachments/assets/a3d2849d-4ed0-4b5b-adca-48dcd07132ca)](https://github.com/Jonseed/ComfyUI-Detail-Daemon/blob/main/Comparing%20Detailers.json)

The [Comparing Detailers.json](https://github.com/Jonseed/ComfyUI-Detail-Daemon/blob/main/Comparing%20Detailers.json) workflow will allow you to compare these various detailer nodes on the same prompt and seed.

## Precautions
Before using this node, ensure that floating point rounding is disabled and comfui is restarted. The value of the adjustment factor dishonesty_factor has a significant impact on the results. It is recommended to start with the default value and gradually adjust it.
![Screenshot 2024-10-29 124833](https://github.com/tatookan/comfuinoda-Navyblue/blob/main/demo/%E5%BE%AE%E4%BF%A1%E6%88%AA%E5%9B%BE_20241030164321.png)
## Credits

- Detail Daemon concept and schedule generation function from muerrilla: https://github.com/muerrilla/sd-webui-detail-daemon/
- ComfyUI sampler implementation and schedule interpolation, as well as Lying Sigma Sampler, by https://github.com/blepping/
- Multiply Sigmas node based on the one included here: https://github.com/Extraltodeus/sigmas_tools_and_the_golden_scheduler
