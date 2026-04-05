/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillUpdateProps, onWillUnmount, useRef, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class SketchPadWidget extends Component {
    static template = "engineering_project.SketchPadWidget";
    static props = {
        ...standardFieldProps,
        widget: { type: String, optional: true },
    };

    setup() {
        this.canvasContainerRef = useRef("canvasContainer"); 
        
        // Tool Controllers
        this.colorRef = useRef("colorPicker");        // Stroke / Text / Pen Color
        this.fillColorRef = useRef("fillColorPicker");// Shape inside color (NEW)
        this.sizeRef = useRef("sizePicker");          // Stroke width / Brush size / Font size
        this.textInputRef = useRef("textInput");

        this.fabricCanvas = null;
        this.notification = useService("notification");
        this.currentMode = useState({ mode: 'pen' });

        this.loadedValue = null;
        
        // Shape drawing state tracking
        this.isDrawingShape = false;
        this.origX = 0;
        this.origY = 0;
        this.currentShape = null;

        onMounted(() => {
            requestAnimationFrame(() => this.initializeCanvas());
            // Add keyboard event listener to delete selected items easily
            window.addEventListener('keydown', this.handleKeyDown.bind(this));
        });

        onWillUpdateProps((nextProps) => {
            const nextValue = nextProps.record.data[nextProps.name];
            if (nextValue && nextValue !== this.loadedValue && this.fabricCanvas) {
                this.loadImageFromValue(nextValue);
            }
        });

        onWillUnmount(() => {
            window.removeEventListener('keydown', this.handleKeyDown.bind(this));
            if (this.fabricCanvas) {
                this.fabricCanvas.dispose();
                this.fabricCanvas = null;
            }
        });
    }

    initializeCanvas() {
        const container = this.canvasContainerRef.el;
        if (!container) return;

        container.innerHTML = "";
        const canvasEl = document.createElement("canvas");
        container.appendChild(canvasEl);

        this.fabricCanvas = new window.fabric.Canvas(canvasEl, {
            isDrawingMode: false,
            backgroundColor: "#ffffff",
            width: container.clientWidth - 2, 
            height: 500,
        });

        this.setPenMode();

        const initialValue = this.props.record.data[this.props.name];
        this.loadImageFromValue(initialValue);

        // Core Event Listeners
        this.fabricCanvas.on('selection:created', (e) => this.handleSelection(e));
        this.fabricCanvas.on('selection:updated', (e) => this.handleSelection(e));
        
        // Mouse Listeners for Drag & Draw (Shapes & Text)
        this.fabricCanvas.on('mouse:down', this.onMouseDown.bind(this));
        this.fabricCanvas.on('mouse:move', this.onMouseMove.bind(this));
        this.fabricCanvas.on('mouse:up', this.onMouseUp.bind(this));
    }

    handleKeyDown(e) {
        // Pressing "Delete" or "Backspace" removes the currently selected object
        if ((e.key === 'Delete' || e.key === 'Backspace') && this.fabricCanvas) {
            const activeObjects = this.fabricCanvas.getActiveObjects();
            if (activeObjects.length > 0 && this.currentMode.mode === 'select') {
                e.preventDefault();
                activeObjects.forEach((obj) => this.fabricCanvas.remove(obj));
                this.fabricCanvas.discardActiveObject();
                this.fabricCanvas.renderAll();
            }
        }
    }

    handleSelection(e) {
        if (!e.selected || e.selected.length === 0) return;
        const target = e.selected[0];

        // Auto-switch to select mode when touching elements, to prevent accidental drawing
        if (['rect', 'circle', 'triangle', 'line', 'text'].includes(this.currentMode.mode)) {
            this.setSelectMode();
        }

        // Update pickers to match the clicked item's styles
        if (target.type === 'i-text') {
            if (this.colorRef.el) this.colorRef.el.value = target.fill || "#000000";
            if (this.sizeRef.el) this.sizeRef.el.value = Math.max(1, target.fontSize - 10);
        } else {
            if (this.colorRef.el) this.colorRef.el.value = target.stroke || "#000000";
            if (this.fillColorRef.el && target.fill) this.fillColorRef.el.value = target.fill !== 'transparent' ? target.fill : "#ffffff";
            if (this.sizeRef.el) this.sizeRef.el.value = target.strokeWidth || 5;
        }
    }

    // =============================
    //       MODE CONTROLLERS
    // =============================

    setSelectMode() {
        if (!this.fabricCanvas) return;
        this.currentMode.mode = 'select';
        this.fabricCanvas.isDrawingMode = false;
        this.fabricCanvas.selection = true;
        this.fabricCanvas.forEachObject(obj => obj.set({ selectable: true, evented: true }));
    }

    setPenMode() {
        if (!this.fabricCanvas) return;
        this.currentMode.mode = 'pen';
        this.fabricCanvas.isDrawingMode = true;
        this.fabricCanvas.freeDrawingBrush = new window.fabric.PencilBrush(this.fabricCanvas);
        this.fabricCanvas.selection = true;
        this.fabricCanvas.forEachObject(obj => obj.set({ selectable: true, evented: true }));
        
        const color = this.colorRef.el ? this.colorRef.el.value : "#000000";
        const size = this.sizeRef.el ? parseInt(this.sizeRef.el.value, 10) : 5;

        this.fabricCanvas.freeDrawingBrush.color = color;
        this.fabricCanvas.freeDrawingBrush.width = size;
        this.fabricCanvas.renderAll();
    }

    setEraserMode() {
        if (!this.fabricCanvas) return;
        this.currentMode.mode = 'eraser';
        this.fabricCanvas.isDrawingMode = true;
        this.fabricCanvas.selection = false;
        this.fabricCanvas.forEachObject(obj => obj.set({ selectable: false, evented: false }));
        
        this.fabricCanvas.freeDrawingBrush = new window.fabric.PencilBrush(this.fabricCanvas);
        this.fabricCanvas.freeDrawingBrush.color = "#ffffff"; // Assuming white canvas
        const size = this.sizeRef.el ? parseInt(this.sizeRef.el.value, 10) : 15;
        this.fabricCanvas.freeDrawingBrush.width = size + 10;
        this.fabricCanvas.renderAll();
    }

    setTextMode() {
        if (!this.fabricCanvas) return;
        this.currentMode.mode = 'text';
        this.fabricCanvas.isDrawingMode = false;
        this.fabricCanvas.selection = false;
        this.fabricCanvas.forEachObject(obj => obj.set({ selectable: false, evented: false }));
        this.fabricCanvas.discardActiveObject();
        this.fabricCanvas.renderAll();
    }

    setShapeMode(shapeType) {
        if (!this.fabricCanvas) return;
        this.currentMode.mode = shapeType; // 'rect', 'circle', 'triangle', 'line'
        this.fabricCanvas.isDrawingMode = false;
        this.fabricCanvas.selection = false;
        this.fabricCanvas.forEachObject(obj => obj.set({ selectable: false, evented: false }));
        this.fabricCanvas.discardActiveObject();
        this.fabricCanvas.renderAll();
    }

    // =============================
    //       MOUSE LISTENERS
    // =============================

    onMouseDown(options) {
        if (!this.fabricCanvas) return;
        const mode = this.currentMode.mode;
        
        // 1. TEXT MODE LOGIC
        if (mode === 'text') {
            if (options.target && options.target.selectable) return;
            const pointer = this.fabricCanvas.getPointer(options.e);
            const textValue = this.textInputRef.el && this.textInputRef.el.value ? this.textInputRef.el.value : _t("Enter Text");
            const textColor = this.colorRef.el ? this.colorRef.el.value : "#000000";
            const textSize = this.sizeRef.el ? parseInt(this.sizeRef.el.value, 10) + 10 : 20;

            const iText = new window.fabric.IText(textValue, {
                left: pointer.x,
                top: pointer.y,
                fontFamily: 'arial',
                fill: textColor,
                fontSize: textSize,
                editable: true,
                selectable: true,
                evented: true,
            });
            this.fabricCanvas.add(iText);
            this.fabricCanvas.setActiveObject(iText);
            this.setSelectMode(); // Return to select mode immediately after placing
            if (this.textInputRef.el) this.textInputRef.el.value = "";
            return;
        }

        // 2. SHAPE MODE LOGIC
        if (['rect', 'circle', 'triangle', 'line'].includes(mode)) {
            const pointer = this.fabricCanvas.getPointer(options.e);
            this.isDrawingShape = true;
            this.origX = pointer.x;
            this.origY = pointer.y;

            const strokeColor = this.colorRef.el ? this.colorRef.el.value : "#000000";
            const strokeWidth = this.sizeRef.el ? parseInt(this.sizeRef.el.value, 10) : 5;
            const fillColor = this.fillColorRef.el && this.fillColorRef.el.value ? this.fillColorRef.el.value : "transparent";

            if (mode === 'rect') {
                this.currentShape = new window.fabric.Rect({
                    left: this.origX, top: this.origY,
                    originX: 'left', originY: 'top',
                    width: 0, height: 0,
                    fill: fillColor, stroke: strokeColor, strokeWidth: strokeWidth,
                    transparentCorners: false
                });
            } else if (mode === 'circle') {
                this.currentShape = new window.fabric.Circle({
                    left: this.origX, top: this.origY,
                    originX: 'center', originY: 'center',
                    radius: 0,
                    fill: fillColor, stroke: strokeColor, strokeWidth: strokeWidth
                });
            } else if (mode === 'triangle') {
                this.currentShape = new window.fabric.Triangle({
                    left: this.origX, top: this.origY,
                    originX: 'left', originY: 'top',
                    width: 0, height: 0,
                    fill: fillColor, stroke: strokeColor, strokeWidth: strokeWidth
                });
            } else if (mode === 'line') {
                this.currentShape = new window.fabric.Line([this.origX, this.origY, this.origX, this.origY], {
                    stroke: strokeColor, strokeWidth: strokeWidth
                });
            }
            this.fabricCanvas.add(this.currentShape);
        }
    }

    onMouseMove(options) {
        if (!this.isDrawingShape || !this.currentShape) return;
        const pointer = this.fabricCanvas.getPointer(options.e);
        const mode = this.currentMode.mode;

        if (mode === 'rect' || mode === 'triangle') {
            this.currentShape.set({
                left: Math.min(pointer.x, this.origX),
                top: Math.min(pointer.y, this.origY),
                width: Math.abs(this.origX - pointer.x),
                height: Math.abs(this.origY - pointer.y)
            });
        } else if (mode === 'circle') {
            const radius = Math.sqrt(Math.pow(pointer.x - this.origX, 2) + Math.pow(pointer.y - this.origY, 2));
            this.currentShape.set({ radius: radius });
        } else if (mode === 'line') {
            this.currentShape.set({ x2: pointer.x, y2: pointer.y });
        }
        this.fabricCanvas.renderAll();
    }

    onMouseUp() {
        if (this.isDrawingShape && this.currentShape) {
            this.isDrawingShape = false;
            this.currentShape.setCoords();
            this.fabricCanvas.setActiveObject(this.currentShape);
            this.currentShape = null;
            this.setSelectMode(); // Switch back to select mode right after finishing drawing
        }
    }

    // =============================
    //       PROPERTY CHANGERS
    // =============================

    changeColor(ev) {
        if (!this.fabricCanvas) return;
        const color = ev.target.value;
        if (this.currentMode.mode === 'pen' && this.fabricCanvas.isDrawingMode) {
            this.fabricCanvas.freeDrawingBrush.color = color;
        } else {
            const activeObject = this.fabricCanvas.getActiveObject();
            if (activeObject) {
                if (activeObject.type === 'i-text') {
                    activeObject.set({ fill: color });
                } else if (activeObject.type === 'path') {
                    activeObject.set({ stroke: color });
                } else {
                    activeObject.set({ stroke: color });
                }
                this.fabricCanvas.renderAll();
            }
        }
    }

    changeFillColor(ev) {
        if (!this.fabricCanvas) return;
        const color = ev.target.value;
        const activeObject = this.fabricCanvas.getActiveObject();
        if (activeObject && ['rect', 'circle', 'triangle'].includes(activeObject.type)) {
            activeObject.set({ fill: color === '#ffffff' ? 'transparent' : color }); // If white is picked, assume transparent for shapes or use pure white.
            this.fabricCanvas.renderAll();
        }
    }

    changeBrushSize(ev) {
        if (!this.fabricCanvas) return;
        const size = parseInt(ev.target.value, 10);
        if (this.currentMode.mode === 'pen' && this.fabricCanvas.isDrawingMode) {
            this.fabricCanvas.freeDrawingBrush.width = size;
        } else if (this.currentMode.mode === 'eraser' && this.fabricCanvas.isDrawingMode) {
            this.fabricCanvas.freeDrawingBrush.width = size + 10;
        } else {
            const activeObject = this.fabricCanvas.getActiveObject();
            if (activeObject) {
                if (activeObject.type === 'i-text') {
                    activeObject.set({ fontSize: size + 10 });
                } else {
                    activeObject.set({ strokeWidth: size });
                }
                this.fabricCanvas.renderAll();
            }
        }
    }

    // =============================
    //       FILE MANAGERS
    // =============================

    loadImageFromValue(value) {
        if (!this.fabricCanvas) return;

        this.fabricCanvas.clear();
        this.fabricCanvas.backgroundColor = "#ffffff";
        this.loadedValue = value;

        if (value) {
            window.fabric.Image.fromURL("data:image/png;base64," + value, (img) => {
                if (img.width > 0 && img.height > 0) {
                    this.fabricCanvas.setBackgroundImage(
                        img,
                        this.fabricCanvas.renderAll.bind(this.fabricCanvas),
                        {
                            originX: 'center',
                            originY: 'center',
                            left: this.fabricCanvas.width / 2,
                            top: this.fabricCanvas.height / 2,
                            scaleX: this.fabricCanvas.width / img.width,
                            scaleY: this.fabricCanvas.height / img.height,
                        }
                    );
                }
            }, { crossOrigin: 'anonymous' });
        }
        this.fabricCanvas.renderAll();
    }

    clearCanvas() {
        if (!this.fabricCanvas) return;
        this.fabricCanvas.clear();
        this.fabricCanvas.backgroundColor = "#ffffff";
        this.fabricCanvas.renderAll();
        this.notification.add(_t("Canvas Cleared!"), { type: "info" });
    }

    deleteSelected() {
        if (!this.fabricCanvas) return;
        const activeObjects = this.fabricCanvas.getActiveObjects();
        if (activeObjects.length) {
            activeObjects.forEach((obj) => this.fabricCanvas.remove(obj));
            this.fabricCanvas.discardActiveObject();
            this.fabricCanvas.renderAll();
        }
    }

    async saveCanvas() {
        if (!this.fabricCanvas) return;
        if (this.fabricCanvas.getActiveObject() && this.fabricCanvas.getActiveObject().isEditing) {
            this.fabricCanvas.getActiveObject().exitEditing();
        }
        this.fabricCanvas.discardActiveObject();
        this.fabricCanvas.renderAll();

        const dataURL = this.fabricCanvas.toDataURL({ format: "png", multiplier: 1 });
        const base64Data = dataURL.replace(/^data:image\/(png|jpg);base64,/, "");

        this.loadedValue = base64Data;

        await this.props.record.update({ [this.props.name]: base64Data });
        this.notification.add(_t("Sketch Saved Successfully!"), { type: "success" });
    }

    downloadCanvas() {
        if (!this.fabricCanvas) return;
        if (this.fabricCanvas.getActiveObject() && this.fabricCanvas.getActiveObject().isEditing) {
            this.fabricCanvas.getActiveObject().exitEditing();
        }
        this.fabricCanvas.discardActiveObject();
        this.fabricCanvas.renderAll();

        const link = document.createElement("a");
        link.download = `${this.props.record.data.name || "sketch"}.png`;
        link.href = this.fabricCanvas.toDataURL({ format: "png", multiplier: 2 });
        link.click();
    }
}

export const sketchPadField = {
    component: SketchPadWidget,
    supportedTypes: ["binary"],
};

registry.category("fields").add("sketch_pad_editor", sketchPadField);