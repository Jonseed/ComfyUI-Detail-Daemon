import { app } from "/scripts/app.js";

const NODE_NAME = "DetailDaemonSamplerGUINode";
const GRAPH_HEIGHT = 250;
const MIN_WIDTH = 420;
const PARAMETER_NAMES = [
    "detail_amount",
    "start",
    "end",
    "bias",
    "exponent",
    "start_offset",
    "end_offset",
    "fade",
    "smooth",
];

function isSamplerGUINode(node) {
    return node?.comfyClass === NODE_NAME || node?.type === NODE_NAME;
}

function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
}

function round(value, places = 2) {
    const factor = 10 ** places;
    return Math.round(value * factor) / factor;
}

function formatTooltipValue(value) {
    return Number(value.toFixed(2)).toString();
}

function getHandleTooltip(drag, parameters) {
    const values = {
        start: [
            ["start", parameters.start],
            ["start_offset", parameters.startOffset],
        ],
        exponent_start: [["exponent", parameters.exponent]],
        peak: [
            ["detail_amount", parameters.detailAmount],
            ["bias", parameters.bias],
        ],
        exponent_end: [["exponent", parameters.exponent]],
        end: [
            ["end", parameters.end],
            ["end_offset", parameters.endOffset],
        ],
    }[drag];

    return values?.map(([name, value]) => `${name}:${formatTooltipValue(value)}`).join(" / ") ?? "";
}

function findWidget(node, name) {
    return node.widgets?.find((widget) => widget.name === name);
}

function readParameters(node) {
    const value = (name, fallback) => {
        const current = Number(findWidget(node, name)?.value);
        return Number.isFinite(current) ? current : fallback;
    };

    const end = clamp(value("end", 0.8), 0, 1);
    const start = Math.min(clamp(value("start", 0.2), 0, 1), end);
    return {
        detailAmount: clamp(value("detail_amount", 0.1), -5, 5),
        start,
        end,
        bias: clamp(value("bias", 0.5), 0, 1),
        exponent: clamp(value("exponent", 1), 0, 10),
        startOffset: clamp(value("start_offset", 0), -1, 1),
        endOffset: clamp(value("end_offset", 0), -1, 1),
        fade: clamp(value("fade", 0), 0, 1),
        smooth: Boolean(findWidget(node, "smooth")?.value ?? true),
    };
}

function makeSchedule(parameters, steps = 121) {
    const schedule = new Float64Array(steps);
    const mid = parameters.start + parameters.bias * (parameters.end - parameters.start);
    const startIndex = Math.round(parameters.start * (steps - 1));
    const midIndex = Math.round(mid * (steps - 1));
    const endIndex = Math.round(parameters.end * (steps - 1));

    schedule.fill(parameters.startOffset, 0, startIndex);
    for (let index = startIndex; index <= midIndex; index++) {
        const length = midIndex - startIndex;
        let value = length ? (index - startIndex) / length : 0;
        if (parameters.smooth) value = 0.5 * (1 - Math.cos(value * Math.PI));
        value **= parameters.exponent;
        schedule[index] = value * (parameters.detailAmount - parameters.startOffset) + parameters.startOffset;
    }
    for (let index = midIndex; index <= endIndex; index++) {
        const length = endIndex - midIndex;
        let value = length ? 1 - (index - midIndex) / length : 1;
        if (parameters.smooth) value = 0.5 * (1 - Math.cos(value * Math.PI));
        value **= parameters.exponent;
        schedule[index] = value * (parameters.detailAmount - parameters.endOffset) + parameters.endOffset;
    }
    schedule.fill(parameters.endOffset, endIndex + 1);

    const fadeScale = 1 - parameters.fade;
    for (let index = 0; index < schedule.length; index++) schedule[index] *= fadeScale;
    return schedule;
}

function setWidgetValue(node, name, value) {
    const widget = findWidget(node, name);
    if (!widget || Object.is(widget.value, value)) return;
    widget.value = value;
    widget.callback?.(value, app.canvas, node);
    node.graph?.setDirtyCanvas?.(true, true);
    node.setDirtyCanvas?.(true, true);
}

function chainCallback(object, name, callback) {
    const original = object[name];
    object[name] = function (...args) {
        const result = original?.apply(this, args);
        callback.apply(this, args);
        return result;
    };
}

function createGraph(node) {
    if (node._detailDaemonGraph) return;

    const root = document.createElement("div");
    root.style.cssText = 'width:100%;min-height:200px;box-sizing:border-box;padding:6px 0;overflow:hidden;'

    const canvas = document.createElement("canvas");
    canvas.style.cssText =
      'display:block;width:100%;height:100%;border:1px solid rgba(255,255,255,.16);border-radius:6px;background:#17191c;touch-action:none;cursor:default;'
    canvas.title = "Drag the start, exponent handles, peak, and end. Double-click the graph to restore the default curve.";
    root.appendChild(canvas);

    const state = {
        drag: null,
        dragStartY: 0,
        dragStartExponent: 1,
        dragYMax: 1,
        frame: 0,
        layout: null,
        removed: false,
    };
    node._detailDaemonGraph = state;

    const requestDraw = (force = false) => {
        if (state.removed) return;
        if (state.frame) {
            if (!force) return;
            cancelAnimationFrame(state.frame);
            state.frame = 0;
        }
        state.frame = requestAnimationFrame(() => {
            state.frame = 0;
            draw();
        });
    };
    node._detailDaemonRequestDraw = requestDraw;

    const draw = () => {
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        if (width < 1 || height < 1) return;

        const dpr = window.devicePixelRatio || 1;
        const pixelWidth = Math.round(width * dpr);
        const pixelHeight = Math.round(height * dpr);
        if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
            canvas.width = pixelWidth;
            canvas.height = pixelHeight;
        }

        const context = canvas.getContext("2d");
        context.setTransform(dpr, 0, 0, dpr, 0, 0);
        context.clearRect(0, 0, width, height);

        const parameters = readParameters(node);
        const schedule = makeSchedule(parameters);
        const fadeScale = 1 - parameters.fade;
        const peakX = parameters.start + parameters.bias * (parameters.end - parameters.start);
        const exponentStrength = 0.5 ** parameters.exponent;
        const exponentStartY = (parameters.startOffset + (parameters.detailAmount - parameters.startOffset) * exponentStrength) * fadeScale;
        const exponentEndY = (parameters.endOffset + (parameters.detailAmount - parameters.endOffset) * exponentStrength) * fadeScale;
        const handles = [
            { name: "start", x: parameters.start, y: parameters.startOffset * fadeScale, color: "#5ac8fa" },
            { name: "exponent_start", x: (parameters.start + peakX) / 2, y: exponentStartY, color: "#bf5af2", label: "E" },
            { name: "peak", x: peakX, y: parameters.detailAmount * fadeScale, color: "#ffcc00" },
            { name: "exponent_end", x: (peakX + parameters.end) / 2, y: exponentEndY, color: "#bf5af2", label: "E" },
            { name: "end", x: parameters.end, y: parameters.endOffset * fadeScale, color: "#ff6b6b" },
        ];
        const largest = Math.max(1, ...schedule.map(Math.abs), ...handles.map((handle) => Math.abs(handle.y)));
        const yMax = state.drag ? state.dragYMax : Math.min(5.5, Math.max(1, largest * 1.2));
        const padding = { left: 42, right: 12, top: 25, bottom: 27 };
        const plotWidth = Math.max(1, width - padding.left - padding.right);
        const plotHeight = Math.max(1, height - padding.top - padding.bottom);
        const pointX = (value) => padding.left + value * plotWidth;
        const pointY = (value) => padding.top + (1 - (value + yMax) / (2 * yMax)) * plotHeight;
        state.layout = { padding, plotWidth, plotHeight, yMax, handles };

        context.fillStyle = "#17191c";
        context.fillRect(0, 0, width, height);
        context.font = "11px sans-serif";
        context.lineWidth = 1;

        for (let tick = 0; tick <= 4; tick++) {
            const ratio = tick / 4;
            const x = pointX(ratio);
            context.strokeStyle = "rgba(255,255,255,.09)";
            context.beginPath();
            context.moveTo(x, padding.top);
            context.lineTo(x, padding.top + plotHeight);
            context.stroke();
            context.fillStyle = "rgba(255,255,255,.55)";
            context.textAlign = "center";
            context.fillText(`${Math.round(ratio * 100)}%`, x, height - 8);
        }

        for (let tick = -2; tick <= 2; tick++) {
            const value = tick * yMax / 2;
            const y = pointY(value);
            context.strokeStyle = tick === 0 ? "rgba(255,255,255,.28)" : "rgba(255,255,255,.09)";
            context.beginPath();
            context.moveTo(padding.left, y);
            context.lineTo(padding.left + plotWidth, y);
            context.stroke();
            context.fillStyle = "rgba(255,255,255,.55)";
            context.textAlign = "right";
            context.fillText(value.toFixed(yMax < 1 ? 2 : 1), padding.left - 6, y + 4);
        }

        const gradient = context.createLinearGradient(padding.left, 0, padding.left + plotWidth, 0);
        gradient.addColorStop(0, "#5ac8fa");
        gradient.addColorStop(0.5, "#ffcc00");
        gradient.addColorStop(1, "#ff6b6b");
        context.strokeStyle = gradient;
        context.lineWidth = 2.5;
        context.beginPath();
        schedule.forEach((value, index) => {
            const x = pointX(index / (schedule.length - 1));
            const y = pointY(value);
            if (index === 0) context.moveTo(x, y);
            else context.lineTo(x, y);
        });
        context.stroke();

        for (const handle of handles) {
            const x = pointX(handle.x);
            const y = pointY(handle.y);
            handle.canvasX = x;
            handle.canvasY = y;
            context.fillStyle = handle.color;
            context.strokeStyle = "#101214";
            context.lineWidth = 2;
            context.beginPath();
            context.arc(x, y, state.drag === handle.name ? 7 : 6, 0, Math.PI * 2);
            context.fill();
            context.stroke();
            if (handle.label) {
                context.fillStyle = "#fff";
                context.font = "bold 9px sans-serif";
                context.textAlign = "center";
                context.fillText(handle.label, x, y + 3);
            }
        }

        if (state.drag) {
            const activeHandle = handles.find((handle) => handle.name === state.drag);
            const tooltip = getHandleTooltip(state.drag, parameters);
            if (activeHandle && tooltip) {
                context.font = "bold 11px sans-serif";
                const tooltipPadding = 8;
                const tooltipHeight = 24;
                const tooltipWidth = context.measureText(tooltip).width + tooltipPadding * 2;
                const tooltipGap = 12;
                const tooltipX = clamp(activeHandle.canvasX - tooltipWidth / 2, 4, width - tooltipWidth - 4);
                let tooltipY = activeHandle.canvasY - tooltipHeight - tooltipGap;
                if (tooltipY < 4) tooltipY = activeHandle.canvasY + tooltipGap;
                tooltipY = clamp(tooltipY, 4, height - tooltipHeight - 4);

                context.fillStyle = "rgba(8,10,12,.94)";
                context.strokeStyle = activeHandle.color;
                context.lineWidth = 1;
                context.beginPath();
                if (typeof context.roundRect === "function") context.roundRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight, 5);
                else context.rect(tooltipX, tooltipY, tooltipWidth, tooltipHeight);
                context.fill();
                context.stroke();

                context.fillStyle = "rgba(255,255,255,.92)";
                context.textAlign = "center";
                context.textBaseline = "middle";
                context.fillText(tooltip, tooltipX + tooltipWidth / 2, tooltipY + tooltipHeight / 2);
                context.textBaseline = "alphabetic";
            }
        }

        context.fillStyle = "rgba(255,255,255,.78)";
        context.textAlign = "left";
        context.font = "12px sans-serif";
        context.fillText("Detail adjustment schedule", padding.left, 16);
        context.textAlign = "right";
        context.fillStyle = "rgba(255,255,255,.48)";
        context.font = "10px sans-serif";
        context.fillText("drag handles", width - padding.right, 16);
    };

    const pointerPosition = (event) => {
        const bounds = canvas.getBoundingClientRect();
        const scaleX = bounds.width ? canvas.clientWidth / bounds.width : 1;
        const scaleY = bounds.height ? canvas.clientHeight / bounds.height : 1;
        return {
            x: (event.clientX - bounds.left) * scaleX,
            y: (event.clientY - bounds.top) * scaleY,
        };
    };

    const updateFromPointer = (event) => {
        if (!state.drag || !state.layout) return;
        const position = pointerPosition(event);
        const { padding, plotWidth, plotHeight, yMax } = state.layout;
        const x = clamp((position.x - padding.left) / plotWidth, 0, 1);
        const displayedY = clamp((1 - (position.y - padding.top) / plotHeight) * 2 * yMax - yMax, -yMax, yMax);
        const parameters = readParameters(node);
        const fadeScale = Math.max(0.01, 1 - parameters.fade);

        if (state.drag.startsWith("exponent_")) {
            const delta = (position.y - state.dragStartY) / plotHeight * 10;
            const exponent = Math.round(clamp(state.dragStartExponent + delta, 0, 10) / 0.05) * 0.05;
            setWidgetValue(node, "exponent", round(exponent));
        } else if (state.drag === "start") {
            setWidgetValue(node, "start", round(clamp(x, 0, parameters.end)));
            setWidgetValue(node, "start_offset", round(clamp(displayedY / fadeScale, -1, 1)));
        } else if (state.drag === "peak") {
            const span = parameters.end - parameters.start;
            const bias = span > 0 ? (x - parameters.start) / span : 0;
            setWidgetValue(node, "bias", round(clamp(bias, 0, 1)));
            setWidgetValue(node, "detail_amount", round(clamp(displayedY / fadeScale, -5, 5)));
        } else if (state.drag === "end") {
            setWidgetValue(node, "end", round(clamp(x, parameters.start, 1)));
            setWidgetValue(node, "end_offset", round(clamp(displayedY / fadeScale, -1, 1)));
        }
        requestDraw();
    };

    canvas.addEventListener("pointerdown", (event) => {
        if (event.button !== 0 || !state.layout) return;
        const position = pointerPosition(event);
        let closest = null;
        let distance = 14;
        for (const handle of state.layout.handles) {
            const current = Math.hypot(position.x - handle.canvasX, position.y - handle.canvasY);
            if (current < distance) {
                closest = handle;
                distance = current;
            }
        }
        if (!closest) return;
        node.graph?.beforeChange?.();
        state.drag = closest.name;
        state.dragStartY = position.y;
        state.dragStartExponent = readParameters(node).exponent;
        state.dragYMax = state.layout.yMax;
        canvas.setPointerCapture(event.pointerId);
        canvas.style.cursor = "grabbing";
        requestDraw();
        event.preventDefault();
        event.stopPropagation();
    });
    canvas.addEventListener("pointermove", (event) => {
        if (state.drag) {
            updateFromPointer(event);
            event.preventDefault();
            return;
        }
        if (!state.layout) return;
        const position = pointerPosition(event);
        canvas.style.cursor = state.layout.handles.some((handle) => Math.hypot(position.x - handle.canvasX, position.y - handle.canvasY) < 14) ? "grab" : "default";
    });
    const endDrag = (event) => {
        if (!state.drag) return;
        state.drag = null;
        canvas.style.cursor = "default";
        try {
            canvas.releasePointerCapture(event.pointerId);
        } catch (_) {
        }
        node.graph?.afterChange?.();
        node.graph?.change?.();
        requestDraw();
    };
    canvas.addEventListener("pointerup", endDrag);
    canvas.addEventListener("pointercancel", endDrag);
    canvas.addEventListener("dblclick", (event) => {
        node.graph?.beforeChange?.();
        setWidgetValue(node, "detail_amount", 0.1);
        setWidgetValue(node, "start", 0.2);
        setWidgetValue(node, "end", 0.8);
        setWidgetValue(node, "bias", 0.5);
        setWidgetValue(node, "exponent", 1);
        setWidgetValue(node, "start_offset", 0);
        setWidgetValue(node, "end_offset", 0);
        setWidgetValue(node, "fade", 0);
        setWidgetValue(node, "smooth", true);
        node.graph?.afterChange?.();
        node.graph?.change?.();
        requestDraw();
        event.preventDefault();
        event.stopPropagation();
    });

    for (const name of PARAMETER_NAMES) {
        const widget = findWidget(node, name);
        if (widget) chainCallback(widget, "callback", requestDraw);
    }

    const resizeObserver = new ResizeObserver(requestDraw);
    resizeObserver.observe(root);
    const graphWidget = node.addDOMWidget("detail_daemon_schedule", "detail_daemon_schedule", root, {
        serialize: false,
        getMinHeight: () => GRAPH_HEIGHT,
        getMaxHeight: () => GRAPH_HEIGHT,
    });
    graphWidget.serialize = false;
    graphWidget.options.serialize = false;

    chainCallback(node, "onConfigure", () => requestDraw(true));
    chainCallback(node, "onRemoved", () => {
        state.removed = true;
        resizeObserver.disconnect();
        if (state.frame) cancelAnimationFrame(state.frame);
        node._detailDaemonGraph = null;
        node._detailDaemonRequestDraw = null;
    });

    if (!app.configuringGraph && node.size?.[0] < MIN_WIDTH) {
        const computed = node.computeSize?.() ?? node.size;
        node.setSize?.([MIN_WIDTH, Math.max(node.size[1], computed?.[1] ?? 0)]);
    }
    requestDraw();
}

app.registerExtension({
    name: "DetailDaemon.SamplerGUI",

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_NAME) return;

        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalCreated?.apply(this, arguments);
            createGraph(this);
            return result;
        };
    },

    loadedGraphNode(node) {
        if (!isSamplerGUINode(node)) return;
        setTimeout(() => node._detailDaemonRequestDraw?.(true), 0);
    },
});
