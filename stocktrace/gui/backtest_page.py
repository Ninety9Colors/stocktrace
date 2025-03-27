from PyQt6.QtWidgets import QWidget, QScrollArea, QLabel, QGridLayout, QApplication, QPushButton, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QDateEdit
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
import pandas as pd
import datetime as dt

from stocktrace.algorithm import AlgorithmManager
from stocktrace.asset import AssetManager
from stocktrace.backtest import Backtest
from stocktrace.statistics import generate_statistics
from stocktrace.trade_system import Broker
from stocktrace.logger import Logger as logger
from stocktrace.utils import DEFAULT_FONT, BULLISH_STR, BEARISH_STR, TIMEZONE
from stocktrace.gui.graphs import AssetWidget, BacktestAssetWidget, EquityWidget
from stocktrace.gui.generic import ListSelect, SelectLabel

class BacktestSelect(ListSelect):
    def __init__(self) -> None:
        super().__init__([])
        self.__selected = []

    def show(self):
        super().show()
        if len(self.__selected) > 0:
            for name in self.__selected:
                self.labels[name].unhighlight()
        self.__selected: list[str] = []
        self.info_box.setText(None)
    
    def set_list(self, new_list) -> None:
        for i in reversed(range(self.scroll_widget.layout().count())): 
            self.scroll_widget.layout().itemAt(i).widget().deleteLater()
        self.items = new_list
        self.labels.clear()
        for i, name in enumerate(self.items):
            w = SelectLabel(self._select_callback, name)
            self.labels[name] = w
            self.scroll_widget.layout().addWidget(w,i,0)
            
    def get_selected(self) -> list:
        return self.__selected
    
    def _select_callback(self, label: str) -> None:
        if label in self.__selected:
            self.labels[label].unhighlight()
            self.__selected.remove(label)
            return
        self.__selected.append(label)
        self.labels[label].highlight()
        pass

    def _init_buttons(self) -> None:
        super()._init_buttons()

        self.__new_backtest_button = QPushButton('New Backtest')
        self.__new_backtest_button.setFont(QFont(DEFAULT_FONT, 12))
        self.layout().addWidget(self.__new_backtest_button, 3, 0)
    
    @property
    def new_backtest_button(self) -> QPushButton:
        return self.__new_backtest_button

class StatisticWidget(QWidget):
    def __init__(self, stats: pd.Series) -> None:
        super().__init__()
        self.setLayout(QGridLayout())
        self.__scroll_area = QScrollArea()
        self.__widget = QWidget()
        self.__widget.setLayout(QGridLayout())

        self.__statistics: pd.Series = stats
        self.__labels: dict[str, tuple[QLabel]] = {}
        for i,key in enumerate(self.__statistics.index):
            name = QLabel(f'{key}:')
            name.setFont(QFont(DEFAULT_FONT, 8))
            value = QLabel(f'{self.__statistics.loc[key]}')
            value.setFont(QFont(DEFAULT_FONT, 8))
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            self.__widget.layout().addWidget(name,i,0)
            self.__widget.layout().addWidget(value,i,1)

            self.__labels[key] = (name, value)
        
        self.__scroll_area.setWidget(self.__widget)
        self.layout().addWidget(self.__scroll_area)
    
    def highlight(self, label: str, positive=True):
        assert label in self.__labels
        self.__labels[label].setStyleSheet(f'color: rgb{BULLISH_STR if positive else BEARISH_STR};')
    
    def reset_highlights(self) -> None:
        for name, value in self.__labels.values():
            name.setStyleSheet('')
            value.setStyleSheet('')

class BacktestPanel(QWidget):
    def __init__(self, backtest: Backtest, stats, plot_indicators: bool=False) -> None:
        super().__init__()
        self.setLayout(QGridLayout())
        self.__toggle_button = QPushButton(f'Backtest using {backtest.algorithm} ({backtest.start_date} - {backtest.end_date})')
        self.__main_widget = QWidget()
        self.__main_widget.setLayout(QGridLayout())
        self.__toggle_button.clicked.connect(self.toggle)
        self.layout().addWidget(self.__toggle_button)
        self.layout().addWidget(self.__main_widget)
        self.__main_widget.hide()

        self.__backtest = backtest
        self.__statistics = stats

        self.__statistic_widget = StatisticWidget(self.__statistics)
        self.__backtest_asset_widget = BacktestAssetWidget(self.__backtest,plot_indicators=plot_indicators)
        self.__equity_widget = EquityWidget(self.__backtest, self.__statistics)
        self.__equity_widget.plot_widget.plotItem.vb.setXLink(self.__backtest_asset_widget.plot_item.vb)

        self.__asset_select_button = QPushButton('Select a traded Asset')
        self.__asset_select_button.clicked.connect(lambda: self.__asset_select.show())
        self.__asset_select_button.setFont(QFont(DEFAULT_FONT, 8))

        self.__asset_select = ListSelect(self.__backtest.broker.get_traded_tickers())
        self.__asset_select.select_button.clicked.connect(self.on_asset_select)
        self.__asset_select.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.__main_widget.layout().addWidget(self.__asset_select_button, 0, 0, 1, 1)
        self.__main_widget.layout().addWidget(self.__equity_widget, 1, 0, 1, 2)
        self.__main_widget.layout().addWidget(self.__backtest_asset_widget, 2, 0, 1, 2)
        self.__main_widget.layout().addWidget(self.__statistic_widget, 1, 3, 2, 1)
        self.__main_widget.layout().setColumnStretch(0,2)
        self.__main_widget.layout().setColumnStretch(1,2)
        self.__main_widget.layout().setRowStretch(1,3)
        self.__main_widget.layout().setRowStretch(2,5)

        self.setMinimumHeight(50)
        self.setMinimumWidth(800)
    
    def toggle(self) -> None:
        if self.__main_widget.isVisible():
            self.setMinimumHeight(50)
        else:
            self.setMinimumHeight(400)
        self.__main_widget.setVisible(not self.__main_widget.isVisible())
    
    def on_asset_select(self) -> None:
        selection = self.__asset_select.get_selected()
        if selection is None:
            self.__asset_select.info_box.setText('Please select an asset')
            return
        elif selection == self.__backtest_asset_widget.asset.ticker_symbol:
            return
        
        asset = AssetManager.get(selection)
        self.__backtest_asset_widget.set_asset(asset)
        self.__asset_select.hide()

class BacktestPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setLayout(QGridLayout())
        self.__backtests = {}
        self.__panels = []

        self.__dialog = QWidget()
        self.__dialog.setLayout(QGridLayout())
        self.__dialog.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.__backtest_select_button = QPushButton('Select or run backtests')
        self.__backtest_select = BacktestSelect()
        self.__backtest_select.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.__backtest_select.new_backtest_button.clicked.connect(self.__dialog.show)
        self.__backtest_select.select_button.clicked.connect(self.on_backtest_select)
        self.__backtest_select_button.clicked.connect(self.__backtest_select.show)

        self.__display_scroll_area = QScrollArea()
        self.__display_widget = QWidget()
        self.__display_widget.setLayout(QGridLayout())
        self.__display_scroll_area.setWidget(self.__display_widget)
        self.__display_scroll_area.setWidgetResizable(True)

        self._init_new_backtest_dialog()
        self.layout().addWidget(self.__backtest_select_button)
        self.layout().addWidget(self.__display_scroll_area)
    
    def on_backtest_select(self) -> None:
        selected = self.__backtest_select.get_selected()
        for panel in list(self.__panels):
            self.__display_widget.layout().removeWidget(panel)
            panel.deleteLater()
            print(f'removing {panel}')
        self.__panels.clear()
        for i,backtest_name in enumerate(selected):
            bt, stats = self.__backtests[backtest_name]
            panel = BacktestPanel(bt,stats)
            self.__display_widget.layout().addWidget(panel,i,0)
            print(f'adding {panel}')
            self.__panels.append(panel)


    def new_backtest(self) -> None:
        if self.__start_date_edit.date() >= self.__end_date_edit.date():
            return
        start_qdate = self.__start_date_edit.date()
        start = dt.datetime(start_qdate.year(), start_qdate.month(), start_qdate.day(), tzinfo=TIMEZONE)
        end_qdate = self.__end_date_edit.date()
        end = dt.datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), tzinfo=TIMEZONE)

        broker = Broker(self.__cash_edit.value(), self.__toc_button.isChecked(), self.__spread_edit.value()/100)
        backtest = Backtest(AlgorithmManager.get_algorithm(self.__algorithm_combo.currentText()),
                            broker,
                            start,
                            end)
        backtest.run()
        stats = generate_statistics(backtest.broker.closed_trades,
                                    backtest.equity,
                                    backtest.algorithm,
                                    backtest.start_date,
                                    backtest.end_date)
        self.__backtests[backtest.__repr__()] = (backtest, stats)
        self.__backtest_select.set_list(self.__backtests.keys())
    # algo, cash, spread, trade on close, start date, end date

    def _init_new_backtest_dialog(self) -> None:
        self.__algorithm_label = QLabel('Algorithm')
        self.__algorithm_combo = QComboBox()
        self.__algorithm_combo.addItems(AlgorithmManager.get_algorithms())

        self.__cash_label = QLabel('Starting cents')
        self.__cash_edit = QSpinBox()
        self.__cash_edit.setRange(1, 2147483647)
        self.__cash_edit.setValue(1000)

        self.__spread_label = QLabel('Spread %')
        self.__spread_edit = QDoubleSpinBox()
        self.__spread_edit.setRange(0, 100)
        self.__spread_edit.setValue(5)

        self.__toc_label = QLabel('Trade on Close?')
        self.__toc_button = QCheckBox()

        self.__start_date_label = QLabel('Start Date')
        self.__start_date_edit = QDateEdit()
        self.__start_date_edit.setCalendarPopup(True)
        self.__start_date_edit.setDateRange(QDate(1900,1,1),QDate.currentDate())

        self.__end_date_label = QLabel('End Date')
        self.__end_date_edit = QDateEdit()
        self.__end_date_edit.setCalendarPopup(True)
        self.__end_date_edit.setDate(QDate.currentDate())
        self.__end_date_edit.setDateRange(QDate(1900,1,1),QDate.currentDate())

        self.__submit = QPushButton('Submit')
        self.__submit.clicked.connect(self.new_backtest)

        self.__dialog.layout().addWidget(self.__algorithm_label,0,0)
        self.__dialog.layout().addWidget(self.__algorithm_combo,0,1)
        self.__dialog.layout().addWidget(self.__cash_label,1,0)
        self.__dialog.layout().addWidget(self.__cash_edit,1,1)
        self.__dialog.layout().addWidget(self.__spread_label,2,0)
        self.__dialog.layout().addWidget(self.__spread_edit,2,1)
        self.__dialog.layout().addWidget(self.__toc_label,3,0)
        self.__dialog.layout().addWidget(self.__toc_button,3,1)
        self.__dialog.layout().addWidget(self.__start_date_label,4,0)
        self.__dialog.layout().addWidget(self.__start_date_edit,4,1)
        self.__dialog.layout().addWidget(self.__end_date_label,5,0)
        self.__dialog.layout().addWidget(self.__end_date_edit,5,1)
        self.__dialog.layout().addWidget(self.__submit,6,0,1,2)

logger.init(2)

app = QApplication([])
page = BacktestPage()
page.show()
app.exec()
    
    
