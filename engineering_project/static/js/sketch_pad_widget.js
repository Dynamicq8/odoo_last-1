/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { CharField } from "@web/views/fields/char/char_field"; // For inheritance
import { onMounted, onWillUpdateProps, useRef } from "@odoo/owl";

export class SketchPadWidget extends CharField {
    static template = "engineering_project.SketchPadWidget";

    setup() {
        super.setup();
        this.canvasRef = useRef("canvas");
        this.fabricCanvas = null;
        this.notification = useService("notification");
        
        onMounted(() => {
            this.initializeCanvas();
        });

        onWillUpdateProps((nextProps) => {
            // Re-load image if the field value changes from outside
            if (this.props.value !== nextProps.value && this.fabricCanvas) {
                this.loadImageFromValue(nextProps.value);
            }
        });
    }

    initializeCanvas() {
        if (!this.canvasRef.el) return;
        
        this.fabricCanvas = new fabric.Canvas(this.canvasRef.el, {
            isDrawingMode: true,
            backgroundColor: '#ffffff',
            width: this.canvasRef.el.parentElement.clientWidth - 2, // Fit width to parent
            height: 500,
        });
        
        this.fabricCanvas.freeDrawingBrush.color = '#000000';
        this.fabricCanvas.freeDrawingBrush.width = 5;

        // Load existing image if any
        this.loadImageFromValue(this.props.value);
    }
    
    loadImageFromValue(value) {
        this.fabricCanvas.clear();
        this.fabricCanvas.backgroundColor = '#ffffff'; // Ensure background is white on load
        if (value) {
            fabric.Image.fromURL('data:image/png;base64,' + value, (img) => {
                this.fabricCanvas.setBackgroundImage(img, this.fabricCanvas.renderAll.bind(this.fabricCanvas), {
                    scaleX: this.fabricCanvas.width / img.width,
                    scaleY: this.fabricCanvas.height / img.height
                });
            });
        }
    }

    setPenMode() {
        this.fabricCanvas.isDrawingMode = true;
        this.fabricCanvas.freeDrawingBrush = new fabric.PencilBrush(this.fabricCanvas);
        this.fabricCanvas.freeDrawingBrush.color = document.getElementById('colorPicker' + this.props.id).value;
        this.fabricCanvas.freeDrawingBrush.width = parseInt(document.getElementById('sizePicker' + this.props.id).value, 10);
    }
    
    setEraserMode() {
        this.fabricCanvas.isDrawingMode = true;
        this.fabricCanvas.freeDrawingBrush = new fabric.EraserBrush(this.fabricCanvas);
        this.fabricCanvas.freeDrawingBrush.width = parseInt(document.getElementById('sizePicker' + this.props.id).value, 10) + 10; // Eraser is bigger
    }
    
    changeColor(ev) {
        if (this.fabricCanvas.isDrawingMode) {
            this.fabricCanvas.freeDrawingBrush.color = ev.target.value;
        }
    }
    
    changeBrushSize(ev) {
        if (this.fabricCanvas.isDrawingMode) {
            this.fabricCanvas.freeDrawingBrush.width = parseInt(ev.target.value, 10);
        }
    }
    
    clearCanvas() {
        this.fabricCanvas.clear();
        this.fabricCanvas.backgroundColor = '#ffffff';
    }

    async saveCanvas() {
        const dataURL = this.fabricCanvas.toDataURL({ format: 'png' });
        // Strip the data URL prefix to get the pure base64 string
        const base64Data = dataURL.replace(/^data:image\/(png|jpg);base64,/, "");
        await this.props.update(base64Data);
        this.notification.add(_t("Sketch Saved!"), { type: 'success' });
    }

    downloadCanvas() {
        const link = document.createElement('a');
        link.download = `${this.props.record.data.display_name || 'sketch'}.png`;
        link.href = this.fabricCanvas.toDataURL({ format: 'png' });
        link.click();
    }
}

registry.category("fields").add("sketch_pad_widget", SketchPadWidget);