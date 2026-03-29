/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ImageField } from "@web/views/fields/image/image_field";
import { onMounted, onWillUpdateProps, onWillUnmount, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { fabric } from "fabric";

export class SketchPadWidget extends ImageField {
    static template = "engineering_project.SketchPadWidget";

    setup() {
        super.setup();

        this.canvasRef = useRef("canvas");
        this.colorRef = useRef("colorPicker");
        this.sizeRef = useRef("sizePicker");

        this.fabricCanvas = null;
        this.notification = useService("notification");

        onMounted(() => {
            requestAnimationFrame(() => this.initializeCanvas());
        });

        onWillUpdateProps((nextProps) => {
            if (nextProps.value && nextProps.value !== this.props.value && this.fabricCanvas) {
                this.loadImageFromValue(nextProps.value);
            }
        });

        onWillUnmount(() => {
            if (this.fabricCanvas) {
                this.fabricCanvas.dispose();
                this.fabricCanvas = null;
            }
        });
    }

    initializeCanvas() {
        if (!this.canvasRef.el || !this.canvasRef.el.parentElement) return;

        this.fabricCanvas = new fabric.Canvas(this.canvasRef.el, {
            isDrawingMode: true,
            backgroundColor: "#ffffff",
            width: this.canvasRef.el.parentElement.clientWidth - 2,
            height: 500,
        });

        this.setPenMode();
        this.loadImageFromValue(this.props.value);
    }

    loadImageFromValue(value) {
        if (!this.fabricCanvas) return;

        this.fabricCanvas.clear();
        this.fabricCanvas.backgroundColor = "#ffffff";

        if (value) {
            fabric.Image.fromURL("data:image/png;base64," + value, (img) => {
                if (img.width > 0 && img.height > 0) {
                    const canvasWidth = this.fabricCanvas.width;
                    const canvasHeight = this.fabricCanvas.height;

                    const scale = Math.min(
                        canvasWidth / img.width,
                        canvasHeight / img.height
                    );

                    img.scale(scale);

                    this.fabricCanvas.setBackgroundImage(
                        img,
                        this.fabricCanvas.renderAll.bind(this.fabricCanvas)
                    );
                }
            });
        }

        this.fabricCanvas.renderAll();
    }

    setPenMode() {
        if (!this.fabricCanvas) return;

        this.fabricCanvas.isDrawingMode = true;
        this.fabricCanvas.freeDrawingBrush = new fabric.PencilBrush(this.fabricCanvas);

        const color = this.colorRef.el ? this.colorRef.el.value : "#000000";
        const size = this.sizeRef.el ? parseInt(this.sizeRef.el.value, 10) : 5;

        this.fabricCanvas.freeDrawingBrush.color = color;
        this.fabricCanvas.freeDrawingBrush.width = size;
    }

    setEraserMode() {
        if (!this.fabricCanvas) return;

        this.fabricCanvas.isDrawingMode = true;

        // Fallback if EraserBrush is not available
        if (fabric.EraserBrush) {
            this.fabricCanvas.freeDrawingBrush = new fabric.EraserBrush(this.fabricCanvas);
        } else {
            this.fabricCanvas.freeDrawingBrush = new fabric.PencilBrush(this.fabricCanvas);
            this.fabricCanvas.freeDrawingBrush.color = "#ffffff";
        }

        const size = this.sizeRef.el ? parseInt(this.sizeRef.el.value, 10) : 5;
        this.fabricCanvas.freeDrawingBrush.width = size + 10;
    }

    changeColor(ev) {
        if (!this.fabricCanvas || !this.fabricCanvas.isDrawingMode) return;
        this.fabricCanvas.freeDrawingBrush.color = ev.target.value;
    }

    changeBrushSize(ev) {
        if (!this.fabricCanvas || !this.fabricCanvas.isDrawingMode) return;
        this.fabricCanvas.freeDrawingBrush.width = parseInt(ev.target.value, 10);
    }

    clearCanvas() {
        if (!this.fabricCanvas) return;

        this.fabricCanvas.clear();
        this.fabricCanvas.backgroundColor = "#ffffff";
        this.fabricCanvas.renderAll();
    }

    async saveCanvas() {
        if (!this.fabricCanvas) return;

        const dataURL = this.fabricCanvas.toDataURL({ format: "png" });
        const base64Data = dataURL.replace(/^data:image\/(png|jpg);base64,/, "");

        await this.props.update(base64Data);

        this.notification.add(_t("Sketch Saved!"), { type: "success" });
    }

    downloadCanvas() {
        if (!this.fabricCanvas) return;

        const link = document.createElement("a");
        link.download = `${this.props.record.data.display_name || "sketch"}.png`;
        link.href = this.fabricCanvas.toDataURL({ format: "png" });
        link.click();
    }
}

registry.category("fields").add("sketch_pad_widget", SketchPadWidget);