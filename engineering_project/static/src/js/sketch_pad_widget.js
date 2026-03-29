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
        // Make sure 'widget' is included if it's used for styling or behavior differentiation
        widget: { type: String, optional: true },
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.colorRef = useRef("colorPicker");
        this.sizeRef = useRef("sizePicker");
        this.textInputRef = useRef("textInput"); // Reference for text input

        this.fabricCanvas = null;
        this.notification = useService("notification");
        this.currentMode = useState({ mode: 'pen' }); // 'pen', 'eraser', 'text'

        onMounted(() => {
            requestAnimationFrame(() => this.initializeCanvas());
        });

        onWillUpdateProps((nextProps) => {
            const currentValue = this.props.record.data[this.props.name];
            const nextValue = nextProps.record.data[nextProps.name];

            if (nextValue && nextValue !== currentValue && this.fabricCanvas) {
                this.loadImageFromValue(nextValue);
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

        this.fabricCanvas = new window.fabric.Canvas(this.canvasRef.el, {
            isDrawingMode: false, // Start with drawing mode off, controlled by buttons
            backgroundColor: "#ffffff",
            width: this.canvasRef.el.parentElement.clientWidth - 2,
            height: 500,
        });

        // Set initial mode to pen
        this.setPenMode(); 
        
        const initialValue = this.props.record.data[this.props.name];
        this.loadImageFromValue(initialValue);

        // Event listener for object selection to enable text editing
        this.fabricCanvas.on('selection:created', (e) => this.handleSelection(e));
        this.fabricCanvas.on('selection:updated', (e) => this.handleSelection(e));
        this.fabricCanvas.on('selection:cleared', (e) => this.handleSelection(e));
    }

    handleSelection(e) {
        if (e.target && e.target.type === 'i-text') {
            this.currentMode.mode = 'text_edit'; // Indicate text editing mode
        } else {
            if (this.currentMode.mode === 'text_edit') {
                this.setPenMode(); // Revert to pen mode if text object is deselected
            }
        }
    }

    loadImageFromValue(value) {
        if (!this.fabricCanvas) return;

        this.fabricCanvas.clear();
        this.fabricCanvas.backgroundColor = "#ffffff";

        if (value) {
            // Fabric loadFromJSON expects a string, not base64 directly
            // If the saved value is an image, we need to handle it as an image.
            // If it's a JSON string, Fabric can load it directly.
            // For simplicity, let's assume `value` is a base64 string of a PNG,
            // or modify the save to store Fabric JSON if more complex objects are expected.
            // Given the existing `toDataURL({ format: "png" })`, we'll treat it as a background image.

            window.fabric.Image.fromURL("data:image/png;base64," + value, (img) => {
                if (img.width > 0 && img.height > 0) {
                    const canvasWidth = this.fabricCanvas.width;
                    const canvasHeight = this.fabricCanvas.height;

                    const scale = Math.min(
                        canvasWidth / img.width,
                        canvasHeight / img.height,
                        1 // Do not scale up beyond original size
                    );
                    img.scale(scale);
                    img.set({
                        left: (canvasWidth - img.getScaledWidth()) / 2,
                        top: (canvasHeight - img.getScaledHeight()) / 2,
                        selectable: false, // Make background image not selectable
                        evented: false, // Do not react to mouse events
                    });

                    this.fabricCanvas.setBackgroundImage(
                        img,
                        this.fabricCanvas.renderAll.bind(this.fabricCanvas),
                        {
                            originX: 'left',
                            originY: 'top',
                            scaleX: img.scaleX,
                            scaleY: img.scaleY
                        }
                    );
                }
            }, { crossOrigin: 'anonymous' }); // Add crossOrigin for base64 images
        }
        this.fabricCanvas.renderAll();
    }

    setPenMode() {
        if (!this.fabricCanvas) return;
        this.currentMode.mode = 'pen';
        this.fabricCanvas.isDrawingMode = true;
        this.fabricCanvas.freeDrawingBrush = new window.fabric.PencilBrush(this.fabricCanvas);
        this.fabricCanvas.selection = true; // Allow selection in pen mode too
        this.fabricCanvas.forEachObject(obj => obj.set({ selectable: true, evented: true })); // Make existing objects selectable
        
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
        this.fabricCanvas.selection = false; // Disable selection in eraser mode
        this.fabricCanvas.forEachObject(obj => obj.set({ selectable: false, evented: false })); // Make objects unselectable during erase
        
        this.fabricCanvas.freeDrawingBrush = new window.fabric.PencilBrush(this.fabricCanvas);
        this.fabricCanvas.freeDrawingBrush.color = "#ffffff"; // Eraser is a white brush
        const size = this.sizeRef.el ? parseInt(this.sizeRef.el.value, 10) : 15; // Larger default for eraser
        this.fabricCanvas.freeDrawingBrush.width = size + 10;
        this.fabricCanvas.renderAll();
    }

    setTextMode() {
        if (!this.fabricCanvas) return;
        this.currentMode.mode = 'text';
        this.fabricCanvas.isDrawingMode = false; // Disable drawing mode for text
        this.fabricCanvas.selection = true; // Enable selection for text objects
        this.fabricCanvas.forEachObject(obj => obj.set({ selectable: true, evented: true })); // Make all objects selectable

        this.fabricCanvas.off('mouse:down', this.addTextOnClick); // Remove previous listener if any
        this.fabricCanvas.on('mouse:down', this.addTextOnClick.bind(this)); // Add click listener for text
        this.fabricCanvas.renderAll();
    }

    addTextOnClick(options) {
        if (this.currentMode.mode !== 'text' || !this.fabricCanvas) return;

        const pointer = this.fabricCanvas.getPointer(options.e);
        const textValue = this.textInputRef.el ? this.textInputRef.el.value : _t("Enter Text");
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
        this.fabricCanvas.renderAll();
        // After adding text, switch to text_edit mode or stay in text mode
        this.currentMode.mode = 'text_edit';
        this.textInputRef.el.value = ""; // Clear input after adding
    }

    changeColor(ev) {
        if (!this.fabricCanvas) return;
        if (this.currentMode.mode === 'pen' && this.fabricCanvas.isDrawingMode) {
            this.fabricCanvas.freeDrawingBrush.color = ev.target.value;
        } else if (this.currentMode.mode === 'text_edit') {
            const activeObject = this.fabricCanvas.getActiveObject();
            if (activeObject && activeObject.type === 'i-text') {
                activeObject.set({ fill: ev.target.value });
                this.fabricCanvas.renderAll();
            }
        }
    }

    changeBrushSize(ev) {
        if (!this.fabricCanvas) return;
        if (this.currentMode.mode === 'pen' && this.fabricCanvas.isDrawingMode) {
            this.fabricCanvas.freeDrawingBrush.width = parseInt(ev.target.value, 10);
        } else if (this.currentMode.mode === 'eraser' && this.fabricCanvas.isDrawingMode) {
            this.fabricCanvas.freeDrawingBrush.width = parseInt(ev.target.value, 10) + 10; // Eraser is larger
        } else if (this.currentMode.mode === 'text_edit') {
            const activeObject = this.fabricCanvas.getActiveObject();
            if (activeObject && activeObject.type === 'i-text') {
                activeObject.set({ fontSize: parseInt(ev.target.value, 10) + 10 });
                this.fabricCanvas.renderAll();
            }
        }
    }

    clearCanvas() {
        if (!this.fabricCanvas) return;

        // Clear all objects and reset background
        this.fabricCanvas.clear();
        this.fabricCanvas.backgroundColor = "#ffffff";
        this.fabricCanvas.renderAll();
        this.notification.add(_t("Canvas Cleared!"), { type: "info" });
    }

    async saveCanvas() {
        if (!this.fabricCanvas) return;

        // Ensure no text object is in edit mode
        if (this.fabricCanvas.getActiveObject() && this.fabricCanvas.getActiveObject().isEditing) {
            this.fabricCanvas.getActiveObject().exitEditing();
        }
        this.fabricCanvas.discardActiveObject(); // Deselect any active object
        this.fabricCanvas.renderAll();

        // Convert the entire canvas (including objects) to Data URL
        const dataURL = this.fabricCanvas.toDataURL({
            format: "png",
            multiplier: 2, // Increase resolution for better quality
        });
        const base64Data = dataURL.replace(/^data:image\/(png|jpg);base64,/, "");

        // Find the record for the specific sketch, not the task
        const sketchRecordId = this.props.record.data.id;
        if (sketchRecordId) {
            try {
                await this.env.model.orm.write(
                    "project.task.sketch", 
                    [sketchRecordId], 
                    { sketch_image: base64Data }
                );
                this.notification.add(_t("Sketch Saved Successfully!"), { type: "success" });
                // Force a reload of the parent view to show the updated image in the form
                this.env.model.load(); 
            } catch (error) {
                console.error("Error saving sketch:", error);
                this.notification.add(_t("Failed to save sketch."), { type: "danger" });
            }
        } else {
            this.notification.add(_t("Cannot save unsaved sketch. Create a new sketch first."), { type: "warning" });
        }
    }

    downloadCanvas() {
        if (!this.fabricCanvas) return;

        // Ensure no text object is in edit mode
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
    // Add default options if needed for the field itself
    // Example: options: { custom_option: true }
};

registry.category("fields").add("sketch_pad_editor", sketchPadField);