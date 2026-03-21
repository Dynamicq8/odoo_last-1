# -*- coding: utf-8 -*-
import logging
import os
from odoo import models
from odoo.addons.sign.models.sign_request import SignRequestItemValue # Import the class we need to patch

_logger = logging.getLogger(__name__)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    _logger.warning("Could not import arabic_reshaper or python-bidi. Arabic text in Sign will not work.")

# --- Correctly load the bundled font ---
try:
    # Build the path to the font file inside our module's static directory
    font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'src', 'fonts', 'Amiri-Regular.ttf')
    
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Amiri', font_path))
        _logger.info("Successfully registered bundled Amiri font with reportlab.")
    else:
        _logger.error(f"FATAL: Amiri font file not found at expected path: {font_path}")
        ARABIC_SUPPORT = False # Disable Arabic support if font not found
        
except Exception as e:
    _logger.error(f"FATAL: Could not register bundled Amiri font. Error: {e}")
    ARABIC_SUPPORT = False # Disable Arabic support if font registration fails


# --- MONKEY PATCHING THE `font_name` PROPERTY AND `_get_resampled_value` METHOD ---

# 1. Patch the `font_name` property
# We need to get the original getter function for the 'font_name' property.
original_font_name_getter = SignRequestItemValue.font_name.fget

def _get_font_name_arabic(self):
    """
    Overrides the font_name property to force 'Amiri' if Arabic characters are detected.
    """
    if ARABIC_SUPPORT and isinstance(self.value, str):
        is_arabic = any('\u0600' <= char <= '\u06FF' for char in self.value)
        if is_arabic:
            _logger.info(f"Arabic detected for value '{self.value}', forcing font_name to 'Amiri'.")
            return 'Amiri'
    # If not Arabic, or if ARABIC_SUPPORT is False, use the original Odoo getter
    return original_font_name_getter(self)

# Replace the original 'font_name' property with our new getter
SignRequestItemValue.font_name = property(_get_font_name_arabic)


# 2. Patch the `_get_resampled_value` method
# Save the original method from Odoo's code.
original_get_resampled_value = SignRequestItemValue._get_resampled_value

def _get_resampled_value_arabic(self):
    """
    Overrides _get_resampled_value to reshape Arabic text before it's rendered.
    """
    # Get the value first using the original Odoo method
    value = original_get_resampled_value(self)
    
    if ARABIC_SUPPORT and isinstance(value, str):
        is_arabic = any('\u0600' <= char <= '\u06FF' for char in value)
        if is_arabic:
            _logger.info(f"Reshaping Arabic value: '{value}'")
            reshaped_text = arabic_reshaper.reshape(value)
            bidi_text = get_display(reshaped_text)
            _logger.info(f"Reshaped to: '{bidi_text}'")
            return bidi_text
    
    return value

# Replace the original '_get_resampled_value' method with our new patched version
SignRequestItemValue._get_resampled_value = _get_resampled_value_arabic


# We still need this empty class definition for the Odoo framework.
# This prevents an error like "ValueError: The _name attribute SignRequestItemValue is not valid."
class SignRequestItem(models.Model):
    _inherit = 'sign.request.item'
    pass
