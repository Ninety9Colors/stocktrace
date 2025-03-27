from PyQt6.QtWidgets import QWidget, QScrollArea, QLabel, QGridLayout, QPushButton, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from stocktrace.logger import Logger as logger
from stocktrace.utils import DEFAULT_FONT, DARK_STR, NORMAL_STR

class SelectLabel(QLabel):
    def __init__(self, callback, text, *args, **kwargs) -> None:
        super().__init__(text, *args, **kwargs)
        self.__callback = callback
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont(DEFAULT_FONT, 8))
        self.setStyleSheet(f'background-color: rgb{DARK_STR};')

    def highlight(self) -> None:
        self.setStyleSheet(f'background-color: rgb{NORMAL_STR};')
    
    def unhighlight(self) -> None:
        self.setStyleSheet(f'background-color: rgb{DARK_STR};')
    
    def mousePressEvent(self, ev):
        self.__callback(self.text())

class ListSelect(QWidget):
    def __init__(self, items: list, search_active: bool=False) -> None:
        super().__init__()
        self.__items = items
        self.__labels: dict[str, SelectLabel] = {}
        self.__selected = None
        self.__scroll_area = QScrollArea()
        self.__search_active = search_active
        self.setLayout(QGridLayout())
        self.layout().addWidget(self.__scroll_area,0,0,1,3 if search_active else 2)

        self.__scroll_widget = QWidget()
        self.__scroll_widget.setLayout(QGridLayout())
        self.__scroll_area.setWidget(self.__scroll_widget)
        self.__scroll_area.setWidgetResizable(True)

        self.__info_box = QLabel()
        self.__info_box.setFont(QFont(DEFAULT_FONT,12))
        self.layout().addWidget(self.__info_box,2,0)

        self.set_list(self.__items)
        self._init_buttons()

        self.setMaximumWidth(600)
        self.setMaximumHeight(200)

    def show(self):
        super().show()
        if self.__selected is not None:
            self.__labels[self.__selected].unhighlight()
        self.__selected = None
        self.__info_box.setText(None)
    
    def set_list(self, new_list) -> None:
        for i in reversed(range(self.__scroll_widget.layout().count())): 
            self.__scroll_widget.layout().itemAt(i).widget().deleteLater()
        self.__items = new_list
        self.__labels.clear()
        for i, name in enumerate(self.__items):
            w = SelectLabel(self._select_callback, name)
            self.__labels[name] = w
            self.__scroll_widget.layout().addWidget(w,i,0)
            
    def get_selected(self) -> str:
        return self.__selected
    
    def _select_callback(self, label: str) -> None:
        if self.__selected is not None:
            self.__labels[self.__selected].unhighlight()
        self.__selected = label
        self.__labels[self.__selected].highlight()
        pass

    def _init_buttons(self) -> None:
        self.__cancel = QPushButton('Cancel')
        self.__select_button = QPushButton('Select')

        self.__cancel.setFont(QFont(DEFAULT_FONT, 12))
        self.__select_button.setFont(QFont(DEFAULT_FONT, 12))

        self.__cancel.clicked.connect(self.hide)

        self.layout().addWidget(self.__cancel, 1, 1 if self.__search_active else 0)
        self.layout().addWidget(self.__select_button, 1, 2 if self.__search_active else 1)

        if self.__search_active:
            self.__search_box = QWidget()
            self.__search_entry = QLineEdit()
            self.__search_button = QPushButton('Add')

            self.__search_entry.setFont(QFont(DEFAULT_FONT, 13))
            self.__search_button.setFont(QFont(DEFAULT_FONT, 13))

            self.__search_box.setLayout(QGridLayout())
            self.__search_box.layout().addWidget(self.__search_entry, 0, 0)
            self.__search_box.layout().addWidget(self.__search_button, 0, 1)
            self.__search_box.layout().setColumnStretch(0, 2)
            self.__search_box.layout().setColumnStretch(1, 1)

            self.layout().addWidget(self.__search_box, 1, 0)
            self.layout().setColumnStretch(0,2)
    
    @property
    def labels(self) -> dict[str, SelectLabel]:
        return self.__labels
    
    @property
    def items(self) -> list:
        return self.__items
    
    @items.setter
    def items(self, new_items) -> None:
        self.__items = new_items
    
    @property
    def scroll_widget(self) -> QWidget:
        return self.__scroll_widget

    @property
    def info_box(self) -> QLabel:
        return self.__info_box
        
    @property
    def search_entry(self) -> QLineEdit:
        assert self.__search_active
        return self.__search_entry

    @property
    def select_button(self) -> QPushButton:
        return self.__select_button

    @property
    def search_button(self) -> QPushButton:
        if self.__search_active:
            return self.__search_button
        return None