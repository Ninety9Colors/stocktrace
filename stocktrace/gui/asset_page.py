from PyQt6.QtWidgets import QWidget, QScrollArea, QLabel, QGridLayout, QApplication, QPushButton, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from stocktrace.asset import AssetManager
from stocktrace.logger import Logger as logger
from stocktrace.indicator import IndicatorManager
from stocktrace.utils import DEFAULT_FONT, DARK_STR, NORMAL_STR
from stocktrace.gui.graphs import AssetWidget
from stocktrace.gui.generic import ListSelect

class AssetPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.__initialized = False

        self.__display_widget = QWidget()
        self.__title_widget = QLabel('Nothing selected')
        self.__asset_select = ListSelect(AssetManager.get_assets().keys(), search_active=True)
        self.__indicator_select = ListSelect(IndicatorManager.get_indicators().keys())
        self.__asset_select_button = QPushButton('Select an Asset')
        self.__indicator_select_button = QPushButton('Add Indicators')

        self.__title_widget.setFont(QFont(DEFAULT_FONT, 15))
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
            self.__indicator_select.info_box.setText('Please select an indicator')
            return
        elif self.__initialized and selection in self.__display_widget.indicators.keys():
            self.__display_widget.remove_indicator(selection)
            return
        
        if not self.__initialized:
            self.__indicator_select.info_box.setText('Please select an asset first')
            return
        else:
            self.__display_widget.add_indicator(selection)


    def on_asset_select(self) -> None:
        selection = self.__asset_select.get_selected()
        if selection is None:
            self.__asset_select.info_box.setText('Please select an asset')
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
        self.__title_widget.setText(f'Displaying ticker: {asset.ticker_symbol}')
        self.__asset_select.hide()
    
    def on_asset_search(self) -> None:
        query = self.__asset_select.search_entry.text()
        if query is None or query == '':
            self.__asset_select.info_box.setText('Please provide a ticker symbol')
            return
        
        asset = AssetManager.get(query)
        if asset is None:
            self.__asset_select.info_box.setText('Asset not found')
        else:
            self.__asset_select.set_list(AssetManager.get_assets())
            self.__asset_select.search_entry.setText('')

app = QApplication([])
window = AssetPage()
window.show()
app.exec()
