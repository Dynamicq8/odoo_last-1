# -*- coding: utf-8 -*-
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
    _logger.info("Successfully imported arabic_reshaper and python-bidi.")
except ImportError:
    ARABIC_SUPPORT = False
    _logger.warning("Could not import arabic_reshaper or python-bidi. Arabic text in Sign will not work.")

class SignRequestItem(models.Model):
    _inherit = 'sign.request.item'

    def _get_pdf_item_value(self):
        """
        This is a common method for getting the value to be stamped.
        We will process it for Arabic here.
        """
        value = super(SignRequestItem, self)._get_pdf_item_value()
        
        if ARABIC_SUPPORT and isinstance(value, str):
            try:
                # Check if the string contains any Arabic characters
                is_arabic = any('\u0600' <= char <= '\u06FF' for char in value)
                if is_arabic:
                    _logger.info(f"Processing Arabic value: {value}")
                    reshaped_text = arabic_reshaper.reshape(value)
                    bidi_text = get_display(reshaped_text)
                    _logger.info(f"Reshaped value: {bidi_text}")
                    return bidi_text
            except Exception as e:
                _logger.error(f"Error processing Arabic text in Sign: {e}")
        
        return value

    def _get_font_name(self):
        """
        Force the PDF engine to use an Arabic-compatible font.
        This assumes 'Amiri' font was installed via apt_packages.txt.
        """
        # We check the value of the field being rendered
        value = self.value or ''
        is_arabic = any('\u0600' <= char <= '\u06FF' for char in value)
        
        if is_arabic:
            _logger.info("Setting font to Amiri for Arabic text.")
            return 'Amiri' # This must match a system-installed font name
            
        # If not Arabic, let Odoo use its default font
        return super(SignRequestItem, self)._get_font_name()
