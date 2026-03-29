# -*- coding: utf-8 -*-
import logging
import os

from odoo import models

_logger = logging.getLogger(__name__)

_ARABIC_ENABLED = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas as reportlab_canvas

    # Ensure the path is correct. Assuming this python file is inside 'models/' folder.
    current_dir = os.path.dirname(__file__)
    module_dir = os.path.dirname(current_dir)
    font_path = os.path.join(module_dir, 'static', 'src', 'fonts', 'Amiri-Regular.ttf')

    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Amiri', font_path))
        _logger.info("✅ ARABIC FIX: Amiri font loaded perfectly.")
        _ARABIC_ENABLED = True
    else:
        # If you see this in your Odoo log, you MUST fix the font file location!
        _logger.error(f"❌ ARABIC FIX: Font NOT found! Looked here: {font_path}")

except ImportError:
    _logger.error("❌ ARABIC FIX: Missing libraries! Please run: pip install arabic-reshaper python-bidi")
except Exception as e:
    _logger.error(f"❌ ARABIC FIX: Error during setup: {e}")


# ================================
# 🔥 PATCH REPORTLAB DIRECTLY FOR RTL ARABIC
# ================================
if _ARABIC_ENABLED:
    try:
        original_drawString = reportlab_canvas.Canvas.drawString
        original_drawRightString = reportlab_canvas.Canvas.drawRightString
        original_drawCentredString = reportlab_canvas.Canvas.drawCentredString

        def _process_arabic_text(text):
            if not text or not isinstance(text, str):
                return text, False

            # Detect if text contains Arabic letters
            is_arabic = any('\u0600' <= c <= '\u06FF' for c in text)

            if not is_arabic:
                return text, False

            # 1. Connect the letters properly
            reshaped = arabic_reshaper.reshape(text)
            # 2. Reverse the string so ReportLab (which draws Left-to-Right) prints it correctly RTL
            bidi_text = get_display(reshaped)
            
            return bidi_text, True

        # Patch left-aligned drawString
        def drawString_patched(self, x, y, text, *args, **kwargs):
            text, is_arabic = _process_arabic_text(text)

            if is_arabic:
                # Safely get current font size, default to 12 if not found
                current_size = getattr(self, '_fontsize', 12) or 12
                self.setFont('Amiri', current_size)
                
                # BUG FIX: DO NOT use drawRightString here. 
                # bidi_text is already reversed. Drawing it normally (left to right)
                # will naturally output the Arabic word in the correct visual order!
                return original_drawString(self, x, y, text, *args, **kwargs)

            return original_drawString(self, x, y, text, *args, **kwargs)

        # Patch right-aligned drawRightString
        def drawRightString_patched(self, x, y, text, *args, **kwargs):
            text, is_arabic = _process_arabic_text(text)
            if is_arabic:
                current_size = getattr(self, '_fontsize', 12) or 12
                self.setFont('Amiri', current_size)
            return original_drawRightString(self, x, y, text, *args, **kwargs)

        # Patch centered text
        def drawCentredString_patched(self, x, y, text, *args, **kwargs):
            text, is_arabic = _process_arabic_text(text)
            if is_arabic:
                current_size = getattr(self, '_fontsize', 12) or 12
                self.setFont('Amiri', current_size)
            return original_drawCentredString(self, x, y, text, *args, **kwargs)

        # Apply the patches to Reportlab globally
        reportlab_canvas.Canvas.drawString = drawString_patched
        reportlab_canvas.Canvas.drawRightString = drawRightString_patched
        reportlab_canvas.Canvas.drawCentredString = drawCentredString_patched

        _logger.info("✅ ARABIC FIX: ReportLab canvas patched successfully.")

    except Exception as e:
        _logger.error(f"❌ ARABIC FIX: Failed to patch canvas: {e}")

else:
    _logger.warning("⚠️ ARABIC FIX: Patch skipped because font was not found or libraries are missing.")

# Required dummy model for Odoo (Keep your existing one)
class SignRequestItem(models.Model):
    _inherit = 'sign.request.item'
