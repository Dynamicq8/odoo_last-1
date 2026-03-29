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

    # Ensure this path points exactly to your new Arial or Tahoma font!
    current_dir = os.path.dirname(__file__)
    module_dir = os.path.dirname(current_dir)
    font_path = os.path.join(module_dir, 'static', 'src', 'fonts', 'arial.ttf')

    if os.path.exists(font_path):
        # We register it as 'ArabicFont' to make it universal
        pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
        _logger.info("✅ ARABIC FIX: Arial/Tahoma font loaded perfectly.")
        _ARABIC_ENABLED = True
    else:
        _logger.error(f"❌ ARABIC FIX: Font NOT found! Looked here: {font_path}")

except Exception as e:
    _logger.error(f"❌ ARABIC FIX: Error during setup: {e}")


# ================================
# 🔥 PATCH REPORTLAB DIRECTLY FOR RTL ARABIC
# ================================
if _ARABIC_ENABLED:
    # We configure the reshaper explicitly to FORCE ligatures (connected letters)
    reshaper_config = {
        'delete_harakat': True,
        'support_ligatures': True,
        'use_unshaped_instead_of_isolated': False,
    }
    reshaper = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)

    try:
        original_drawString = reportlab_canvas.Canvas.drawString
        original_drawRightString = reportlab_canvas.Canvas.drawRightString
        original_drawCentredString = reportlab_canvas.Canvas.drawCentredString

        def _process_arabic_text(text):
            if not text or not isinstance(text, str):
                return text, False

            # Detect Arabic letters
            is_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
            if not is_arabic:
                return text, False

            # 1. Clean hidden formatting characters Odoo might inject
            clean_text = text.replace('\u200e', '').replace('\u200f', '').replace('\u202a', '').replace('\u202b', '').replace('\u202c', '')

            # 2. Reshape to connect the letters physically
            reshaped = reshaper.reshape(clean_text)

            # 3. Apply Bidi to reverse for ReportLab's Left-To-Right drawing
            bidi_text = get_display(reshaped)
            
            return bidi_text, True

        # Patch left-aligned drawString
        def drawString_patched(self, x, y, text, *args, **kwargs):
            text_to_draw, is_arabic = _process_arabic_text(text)
            if is_arabic:
                current_size = getattr(self, '_fontsize', 12) or 12
                self.setFont('ArabicFont', current_size)
                return original_drawString(self, x, y, text_to_draw, *args, **kwargs)
            return original_drawString(self, x, y, text, *args, **kwargs)

        # Patch right-aligned drawRightString
        def drawRightString_patched(self, x, y, text, *args, **kwargs):
            text_to_draw, is_arabic = _process_arabic_text(text)
            if is_arabic:
                current_size = getattr(self, '_fontsize', 12) or 12
                self.setFont('ArabicFont', current_size)
                return original_drawRightString(self, x, y, text_to_draw, *args, **kwargs)
            return original_drawRightString(self, x, y, text, *args, **kwargs)

        # Patch centered text
        def drawCentredString_patched(self, x, y, text, *args, **kwargs):
            text_to_draw, is_arabic = _process_arabic_text(text)
            if is_arabic:
                current_size = getattr(self, '_fontsize', 12) or 12
                self.setFont('ArabicFont', current_size)
                return original_drawCentredString(self, x, y, text_to_draw, *args, **kwargs)
            return original_drawCentredString(self, x, y, text, *args, **kwargs)

        # Apply the patches
        reportlab_canvas.Canvas.drawString = drawString_patched
        reportlab_canvas.Canvas.drawRightString = drawRightString_patched
        reportlab_canvas.Canvas.drawCentredString = drawCentredString_patched

        _logger.info("✅ ARABIC FIX: ReportLab canvas patched successfully.")

    except Exception as e:
        _logger.error(f"❌ ARABIC FIX: Failed to patch canvas: {e}")

# Required dummy model for Odoo
class SignRequestItem(models.Model):
    _inherit = 'sign.request.item'