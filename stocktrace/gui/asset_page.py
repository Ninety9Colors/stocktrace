from PyQt6.QtWidgets import QWidget, QScrollArea, QLabel, QGridLayout, QApplication, QPushButton, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor

from stocktrace.asset import AssetManager
from stocktrace.logger import Logger as logger
from stocktrace.indicator import IndicatorManager
from stocktrace.utils import DEFAULT_FONT, DARK_STR, NORMAL_STR
from stocktrace.gui.graphs import AssetWidget

class SelectLabel(QLabel):
    def __init__(self, callback, text, *args, **kwargs) -> None:
        super().__init__(text, *args, **kwargs)
        self.__callback = callback
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont(DEFAULT_FONT, 12))
        self.setStyleSheet(f'background-color: rgb{DARK_STR};')

    def highlight(self) -> None:
        self.setStyleSheet(f'background-color: rgb{NORMAL_STR};')
    
    def unhighlight(self) -> None:
        self.setStyleSheet(f'background-color: rgb{DARK_STR};')
    
    def mousePressEvent(self, ev):
        self.__callback(self.text())

class DictSelect(QWidget):
    def __init__(self, items: dict, search_active: bool=False) -> None:
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

        self.set_dict(self.__items)
        self._init_buttons()

        self.setMaximumWidth(600)
        self.setMaximumHeight(200)

    def show(self):
        super().show()
        if self.__selected is not None:
            self.__labels[self.__selected].unhighlight()
        self.__selected = None
    
    def set_dict(self, new_dict) -> None:
        for i in reversed(range(self.__scroll_widget.layout().count())): 
            self.__scroll_widget.layout().itemAt(i).widget().deleteLater()
        self.__items = new_dict
        self.__labels.clear()
        for i, (name, object) in enumerate(self.__items.items()):
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
        logger.info(f'DictSelect.select_callback() {label} selected!')
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

class AssetPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.__initialized = False

        self.__display_widget = QWidget()
        self.__title_widget = QLabel('Nothing selected')
        self.__asset_select = DictSelect(AssetManager.get_assets(), search_active=True)
        self.__indicator_select = DictSelect(IndicatorManager.get_indicators())
        self.__asset_select_button = QPushButton('Select an Asset')
        self.__indicator_select_button = QPushButton('Add Indicators')

        self.__title_widget.setFont(QFont(DEFAULT_FONT, 25))
        self.__asset_select_button.setFont(QFont(DEFAULT_FONT, 12))
        self.__indicator_select_button.setFont(QFont(DEFAULT_FONT, 12))

        self.__asset_select_button.clicked.connect(lambda: self.__asset_select.show())
        self.__indicator_select_button.clicked.connect(lambda: self.__indicator_select.show())

        self.__asset_select.select_button.clicked.connect(self.on_asset_select)
        self.__asset_select.search_button.clicked.connect(self.on_asset_search)
        self.__indicator_select.select_button.clicked.connect(self.on_indicator_select)

        self.__asset_select.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.__indicator_select.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.__layout.addWidget(self.__asset_select_button, 0,0,1,1)
        self.__layout.addWidget(self.__indicator_select_button, 0,1,1,1)
        self.__layout.addWidget(self.__title_widget,1,0,1,1)
        self.__layout.addWidget(self.__display_widget,2,0,1,2)

        self.layout().setRowStretch(2, 8)

    def on_indicator_select(self) -> None:
        selection = self.__indicator_select.get_selected()
        if selection is None:
            self.__title_widget.setText('Please select an indicator')
            return
        elif self.__initialized and selection in self.__display_widget.indicators.keys():
            self.__display_widget.remove_indicator(selection)
            return
        
        if not self.__initialized:
            self.__title_widget.setText('Please select an asset first')
            return
        else:
            self.__display_widget.add_indicator(selection)


    def on_asset_select(self) -> None:
        selection = self.__asset_select.get_selected()
        if selection is None:
            self.__title_widget.setText('Please select an asset')
            return
        elif self.__initialized and selection == self.__display_widget.asset.ticker_symbol:
            return
        
        asset = AssetManager.get(selection)
        
        if not self.__initialized:
            self.layout().removeWidget(self.__display_widget)
            self.__display_widget = AssetWidget(asset)
            self.layout().addWidget(self.__display_widget,2,0,1,2)
            self.__initialized = True
        else:
            self.__display_widget.set_asset(asset)

        asset.save_data()
        
        self.__asset_select.hide()
    
    def on_asset_search(self) -> None:
        query = self.__asset_select.search_entry.text()
        if query is None or query == '':
            return
        
        asset = AssetManager.get(query)
        if asset is None:
            self.__title_widget.setText('Asset not found')
        else:
            self.__asset_select.set_dict(AssetManager.get_assets())
            self.__asset_select.search_entry.setText('')

app = QApplication([])
window = AssetPage()
window.show()
app.exec()
