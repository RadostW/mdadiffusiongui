import os, re
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QPen,
    QDoubleValidator,
    QKeySequence,
)

class SimpleYamlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mapping = {}
        
        brace_format = QTextCharFormat()
        brace_format.setBackground(QColor(os.environ.get("QTMATERIAL_PRIMARYCOLOR")))
        brace_format.setForeground(QColor(os.environ.get("QTMATERIAL_SECONDARYCOLOR")))
        brace_pattern = r"(\[[A-Z]*\])"
        self.add_mapping(brace_pattern, brace_format)

        illegal_char_format = QTextCharFormat()
        illegal_char_format.setBackground(QColor("#dc3545"))        
        illegal_char_format.setForeground(QColor(os.environ.get("QTMATERIAL_SECONDARYCOLOR")))
        illegal_char_pattern = r"AnnotatedSequence:[A-Z\s[\]]*([^A-Z\s[\]]*)"
        self.add_mapping(illegal_char_pattern, illegal_char_format)
        
        yaml_key_format = QTextCharFormat()
        yaml_key_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)            
        yaml_key_format.setFontItalic(True)            
        yaml_key_pattern = r"^\s*([\w_()]*:)(?:$|\s)"
        self.add_mapping(yaml_key_pattern, yaml_key_format)

    def add_mapping(self, pattern, pattern_format):
        self._mapping[pattern] = pattern_format

    def highlightBlock(self, text_block):
        for pattern, fmt in self._mapping.items():
            for match in re.finditer(pattern, text_block, flags=re.MULTILINE):
                start, end = match.span(1)
                self.setFormat(start, end - start, fmt)

