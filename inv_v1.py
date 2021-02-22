from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QIntValidator

from inv import Ui_MainWindow
from second_window import Ui_Dialog as second_window
import pyodbc
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTableWidgetItem, QShortcut, QTableWidgetSelectionRange, QAbstractItemView, QWidget, \
    QVBoxLayout, QLabel, QDialog, QApplication, QMainWindow, QMessageBox
import sql_querys
import getpass
import sys
from PyQt5.QtGui import QKeySequence

GLOBAL_LIST_TO_ADD_ONE_PART = []


class MainLogic:
    def __init__(self):
        self.server = 'HOST'
        self.database = 'DB'
        self.username = 'sa'
        self.password = 'PW'
        self.driver = '{SQL Server}'  # Driver you need to connect to the database
        self.numpad_mod = ""
        self.cnn = pyodbc.connect(
            'DRIVER=' + self.driver + ';PORT=port;SERVER=' + self.server + ';PORT=1443;DATABASE=' + self.database +
            ';UID=' + self.username +
            ';PWD=' + self.password)
        self.cursor = self.cnn.cursor()
        self.res_LIST = list()

    def add_table_row(self, table, row_data):
        row = table.rowCount()
        table.setRowCount(row + 1)
        col = 0
        for item in row_data:
            cell = QTableWidgetItem(str(item))
            table.setItem(row, col, cell)
            col += 1

    def print_method(self, x):
        print(x)


class Inventory(QtWidgets.QMainWindow, MainLogic):

    def __init__(self):
        self.win_user = getpass.getuser()
        self.ui = Ui_MainWindow()
        super().__init__()
        self.ui.setupUi(self)
        self.column_number = self.ui.tableWidget.columnCount() - 3
        self.row_number = 0
        self.w = None  # No external window yet.
        # self.ui.add_part.clicked.connect(self.test)
        ######
        #        self.ui.add_part.clicked.connect(self.show_new_window)
        self.add_one_part_status = True
        self.status_list = ""
        self.code_list = list()
        self.provider_list = list()
        self.setWindowIcon(QtGui.QIcon('app.png'))
        self.closing = pyqtSignal()
        self.incoming_latter_text = ""
        self.code_list_search = list()

        self.ui.search_btn.clicked.connect(lambda x: self.search_in_code_column())
        self.ui.search_sheet.clicked.connect(lambda x: self.get_data())
        self.ui.EXIT.clicked.connect(lambda x: self.del_from_listblock())
        self.ui.save.clicked.connect(lambda x: self.update_data_inventory_table())
        self.ui.CloseEdit_3.clicked.connect(lambda x: self.apply_close())
        self.curent_cell_text = list()
        self.current_cell_text_is_bad = False

        # self.column = range(0)
        self.table_used = False
        self.foresight = [self.ui.another_sheet1, self.ui.another_sheet2, self.ui.another_sheet3,
                          self.ui.another_sheet4, self.ui.another_sheet5, self.ui.another_sheet6,
                          self.ui.another_sheet1_2, self.ui.another_sheet2_2, self.ui.another_sheet3_2,
                          self.ui.another_sheet4_2, self.ui.another_sheet5_2, self.ui.another_sheet6_2]
        self.table_item = self.ui.tableWidget
        self.table_item.itemSelectionChanged.connect(self.print_row)
        self.shortcut_del_from_listblock = QShortcut(QKeySequence("ctrl+shift+alt+z"), self)
        self.unblock_latter = QShortcut(QKeySequence("ctrl+shift+alt+q"), self)
        self.shortcut_del_from_listblock.activated.connect(lambda: self.secret_function())
        self.unblock_latter.activated.connect(lambda: self.unclose_edit())
        # self.count_scanner_spares_btn = QShortcut(QKeySequence("f11"), self)
        # self.count_scanner_spares_btn.activated.connect(lambda: self.count_scanner_spares())
        self.who_open = ""
        self.click_mouse = 0
        header = self.table_item.horizontalHeader()
        self.ui.tableWidget.setColumnWidth(0, 160)
        self.ui.tableWidget.setColumnWidth(1, 160)
        self.ui.tableWidget.setColumnWidth(2, 420)
        self.ui.tableWidget.setColumnWidth(3, 50)
        self.ui.tableWidget.setColumnWidth(4, 90)
        self.ui.tableWidget.setColumnWidth(5, 150)
        self.ui.tableWidget.setColumnWidth(6, 350)
        self.ui.incoming_later.textChanged.connect(lambda: self.test())

        self.incoming_latter_backup = ""
        # # self.ui.tableWidget.setColumnWidth(6, 150)
        # self.ui.tableWidget.setColumnWidth(6, 300)

        # for column in range(self.table_item.columnCount()):
        #     header.setSectionResizeMode(column, QtWidgets.QHeaderView.Stretch)

    def apply_close(self):
        ret = QMessageBox.question(self, 'Закриваємо редагування!',
                                   f"Закриваємо редагування листа №{self.incoming_latter_backup}",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.lock_latter()

    def count_scanner_spares(self):
        """работа сканера"""
        self.ui.tableWidget.clearSelection()
        self.ui.incoming_code.selectAll()
        self.ui.incoming_code.setFocus()

    def show_new_window(self, checked):
        self.w = AnotherWindow()
        self.w.exec_()
        self.add_one_part_status = False
        self.add_one_part()
        self.add_one_part_status = True

    def test(self):
        """Удаляет буквы с входящего листа """
        if not self.check_float(self.ui.incoming_later.text()):
            self.ui.incoming_later.setText(self.ui.incoming_later.text()[:-1])

    def clear_table(self):
        while self.table_item.rowCount() > 0:
            self.table_item.removeRow(0)

        self.ui.active_sheet.setText("")
        self.table_used = False
        self.ui.active_sheet.setText("")
        res = self.cursor.execute(sql_querys.del_from_listblock(self.incoming_latter_backup, self.win_user))
        self.cnn.commit()

    def lock_latter(self):
        """зарытиее доступа к листу"""
        if len(self.incoming_latter_backup) != 0:
            self.cursor.execute(sql_querys.close_edit(self.incoming_latter_backup, True))
            self.cnn.commit()
            self.ui.res_label.setText(f"Доступ до листа №{self.incoming_latter_backup} зачинено")
            self.ui.res_label.setStyleSheet("color: red")
            self.clear_table()
        else:
            self.ui.res_label.setText("Спочатку відкрийте листа")
            self.ui.res_label.setStyleSheet("color: red")

    def add_row(self, itemno, suplno):

        for row in self.cursor.execute(sql_querys.add_to_first_window(itemno, suplno)):
            self.add_table_row(self.ui.tableWidget, row)

        self.ui.incoming_code.setText(itemno)
        self.createtable()
        self.select_Fucking_cell(self.ui.tableWidget.rowCount() - 1, self.column_number)
        self.cursor.execute(sql_querys.add_new_row_for_latter(self.ui.incoming_later.text(), itemno, suplno))
        self.cursor.commit()
        self.ui.res_label.setText(f"Запчастину {itemno} додано")
        self.ui.res_label.setStyleSheet("color: green")

    def clear_all_list(self):
        GLOBAL_LIST_TO_ADD_ONE_PART.clear()
        self.code_list.clear()
        self.code_list_search.clear()
        self.clear_foresight()

    def add_one_part(self):
        self.grouping()
        self.clear_foresight()

        if GLOBAL_LIST_TO_ADD_ONE_PART:

            if len(list(self.cursor.execute(
                    sql_querys.chack_part_in_invtno(self.ui.incoming_later.text(), GLOBAL_LIST_TO_ADD_ONE_PART[0],
                                                    GLOBAL_LIST_TO_ADD_ONE_PART[3])))) == 0:
                self.add_row(GLOBAL_LIST_TO_ADD_ONE_PART[0], GLOBAL_LIST_TO_ADD_ONE_PART[3])
                self.clear_all_list()
            else:
                self.ui.res_label.setText("така запчастина вже є у цьому листі!")
                self.ui.res_label.setStyleSheet("color: red")
                self.clear_all_list()

    def secret_function(self):
        """серетная функция"""
        sql_querys.secret(self.ui.incoming_later.text(), self.who_open)
        self.cursor.execute(sql_querys.secret(self.ui.incoming_later.text(), self.who_open))
        self.cnn.commit()
        self.ui.res_label.setText("Лист звільненно")
        self.ui.res_label.setStyleSheet("color : blue")

    def indices(self, lst, element):
        result = []
        offset = -1
        while True:
            try:
                offset = lst.index(element, offset + 1)
            except ValueError:
                return result
            result.append(offset)

    def when_changed_change_color(self):
        if not self.table_item.currentItem() == None and self.add_one_part_status:
            if self.check_float(self.table_item.currentItem().text()):
                if self.table_item.currentItem().text() != self.curent_cell_text[0]:
                    self.ui.res_label.setText("")
                    self.table_item.item(self.table_item.currentRow(), 4).setBackground(QBrush(QColor(66, 221, 245)))
                    self.count_scanner_spares()

            else:
                # print(self.curent_cell_text[0])
                # print(self.table_item.currentRow())
                self.table_item.item(self.table_item.currentRow(), 4).setText(f"{self.curent_cell_text[0]}")
                self.ui.res_label.setText("Колонка приймає тільки числа.")
                self.ui.res_label.setStyleSheet("color:red")
                self.table_item.item(self.table_item.currentRow(), 4).setBackground(QBrush(QColor(147, 110, 111)))
                self.current_cell_text_is_bad = True
                self.count_scanner_spares()

    def check_float(self, potential_float):
        try:
            float(potential_float)
            return True
        except ValueError:
            return False

    def closeEvent(self, event):

        self.del_from_listblock()

    def update_data_inventory_table(self):

        try:
            l1 = list()
            for i in range(self.table_item.rowCount()):
                for row in range(6):
                    l1.append(self.table_item.item(i, row).text())
            invfig = 4
            itemno = 0
            STOCKID = 3

            for i in range(self.table_item.rowCount()):
                res = list(self.cursor.execute(sql_querys.check_sum(self.incoming_latter_backup, l1[itemno])))

                def sent_to_server(infig):

                    self.cursor.execute(
                        sql_querys.update_invt(invtno=self.incoming_latter_backup, INVFIG=infig,
                                               ITEMNO=l1[itemno],
                                               SUPLNO=res[COUNTS][1], STOCKID=l1[STOCKID]))
                    self.cnn.commit()

                # print(sql_querys.check_sum(self.incoming_later_backup, l1[itemno]))
                # print(list(self.cursor.execute(sql_querys.check_sum(self.incoming_later_backup, l1[itemno]))))
                if len(list(self.cursor.execute(sql_querys.check_sum(self.incoming_latter_backup, l1[itemno])))) >= 2:
                    counter = float(l1[invfig])
                    if 0 < counter <= res[0][3]:
                        for COUNTS in range(len(res)):

                            if counter >= res[0][3]:
                                sent_to_server(res[COUNTS][4])
                            if counter <= 0:
                                sent_to_server(0)

                            if counter < res[0][3]:
                                if counter >= res[COUNTS][4]:
                                    sent_to_server(res[COUNTS][4])
                                elif counter >= 0:
                                    sent_to_server(counter)
                                else:
                                    break

                            counter = counter - res[COUNTS][4]

                    elif counter >= res[0][3] and counter != 0:
                        res[-1][-1] = res[-1][-1] + (counter - res[0][3])
                        for COUNTS in range(len(res)):
                            sent_to_server(res[COUNTS][4])
                    elif counter == 0:
                        for COUNTS in range(len(res)):
                            sent_to_server(0)
                else:
                    self.cursor.execute(
                        sql_querys.update_invt(invtno=self.incoming_latter_backup, INVFIG=l1[invfig],
                                               ITEMNO=l1[itemno],
                                               SUPLNO=res[0][1], STOCKID=l1[STOCKID]))

                    self.cnn.commit()

                invfig += 6
                itemno += 6
                STOCKID += 6
            self.ui.res_label.setText("Інформація по листу збережена")
            self.ui.res_label.setStyleSheet("color: green")
        except Exception as err:
            print(err)

    def createtable(self):
        rows = self.table_item.rowCount()
        columns = self.table_item.columnCount() - 3

        for r in range(rows):
            for col in range(columns):
                if self.table_item.item(r, col) != None:
                    self.table_item.item(r, col).setFlags(QtCore.Qt.ItemIsEnabled)
        columns = self.table_item.columnCount() - 2

        for r in range(rows):
            if self.table_item.item(r, columns) != None:
                self.table_item.item(r, columns).setFlags(QtCore.Qt.ItemIsEnabled)
                self.table_item.item(r, columns + 1).setFlags(QtCore.Qt.ItemIsEnabled)

    def del_from_listblock(self):
        self.ui.active_sheet.setText("")
        res = self.cursor.execute(sql_querys.del_from_listblock(self.incoming_latter_backup, self.win_user))
        self.cnn.commit()
        print("дел фром листблок")
        if res.rowcount == 1:
            self.ui.res_label.setText("Лист звільнено!")
            self.ui.res_label.setStyleSheet('color: green')
        self.table_used = False
        self.clear_table()

    def grouping(self):
        nrows = self.ui.tableWidget.rowCount()
        self.code_list.clear()
        for row in range(0, nrows):
            item = self.ui.tableWidget.item(row, 0)
            self.code_list.append(item.text())
        for row in range(0, nrows):
            item = self.ui.tableWidget.item(row, 1)
            self.code_list_search.append(item.text())
        for row in range(0, nrows):
            item = self.ui.tableWidget.item(row, 3)
            self.provider_list.append(item.text())

    def clear_foresight(self):
        for i in self.foresight:
            i.setText("")

    def print_row(self):
        """добавляет в временный список последнею изм. ячейку"""
        self.curent_cell_text.clear()
        self.curent_cell_text.append(self.table_item.currentItem().text())

    def select_Fucking_cell(self, x, y):
        self.table_item.editItem(self.table_item.item(x, y))
        self.table_item.setCurrentCell(x, y)

        # print(f"x ={x} , y={y}")

    def search_in_code_column(self):
        try:
            self.clear_foresight()
            if self.ui.radioButton_code.isChecked():
                self.column = range(self.table_item.columnCount() - 6)

            elif self.ui.radioButton_2_code_search:
                self.column = range(1, self.table_item.columnCount() - 5)
            rows = self.table_item.rowCount()
            tmp = []
            for r in range(rows):
                for col in self.column:
                    if self.ui.incoming_code.text().lower() in self.table_item.item(r, col).text().lower():
                        tmp.append(r)
            if tmp:
                if self.click_mouse >= len(tmp) or len(tmp) == 1:
                    self.click_mouse = 0
                self.ui.tableWidget.selectRow(tmp[self.click_mouse])
                # print(tmp)
                self.row_number = tmp[self.click_mouse]
                self.select_Fucking_cell(self.row_number, self.column_number)

                # print(self.ui.tableWidget.currentItem().text())

                self.ui.res_label.setText(f"Знайдено в {tmp[self.click_mouse] + 1} рядку")
                self.ui.res_label.setStyleSheet('color: green')
                self.click_mouse += 1

            if len(tmp) == 0 and not self.ui.another_sheet_checkBox.isChecked():
                self.clear_foresight()
                self.ui.res_label.setText("Код товару відсутній!")
                self.ui.res_label.setStyleSheet('color: red')
                self.count_scanner_spares()

            if self.ui.another_sheet_checkBox.isChecked():
                self.ui.res_label.setText("")
                self.clear_foresight()
                self.name = self.cursor.execute(sql_querys.get_name_from_block_latter(self.incoming_latter_backup))
                # print(
                #     sql_querys.check_in_another_sheets(self.ui.incoming_code.text(), intvno=self.incoming_latter_backup))
                self.cursor.execute(
                    sql_querys.check_in_another_sheets(self.ui.incoming_code.text(),
                                                       intvno=self.incoming_latter_backup))
                temp_list_result = []
                # print(sql_querys.check_in_another_sheets(ITEMNO=self.ui.incoming_code.text(),
                #                                                                   intvno=self.incoming_later_backup))
                for row in self.cursor.execute(sql_querys.check_in_another_sheets(ITEMNO=self.ui.incoming_code.text(),
                                                                                  intvno=self.incoming_latter_backup)):
                    temp_list_result.append(row)
                    # print(temp_list_result)
                if len(temp_list_result) < 12:  # колонки заполения
                    len_index_ = len(temp_list_result)
                else:
                    len_index_ = 12
                l2 = []
                if self.ui.incoming_code.text() == "":
                    self.ui.res_label.setText("Введіть код пошуку ")
                    self.ui.res_label.setStyleSheet('color: red')
                if self.ui.incoming_code.text() != "":
                    if len(list(
                            self.cursor.execute(sql_querys.get_name_from_block_latter(temp_list_result[0][1])))) == 1:
                        for ind in range(len_index_):
                            l2.append(
                                f"Код товару: {temp_list_result[ind][0]}, " +
                                f"лист: {temp_list_result[ind][1]} відкрив {list(self.cursor.execute(sql_querys.get_name_from_block_latter(temp_list_result[ind][1])))[0][0]} полиця: {temp_list_result[ind][2]}")
                    else:
                        for ind in range(len_index_):
                            l2.append(
                                f"Код товару: {temp_list_result[ind][0]}, "
                                + f"лист: {temp_list_result[ind][1]},  полиця: {temp_list_result[ind][2]}")

                    for item in l2:
                        self.foresight[l2.index(item)].setText(item)
                        self.foresight[l2.index(item)].setStyleSheet('color: green')
                    if len(l2) == 0:
                        self.ui.another_sheet1.setText("код товару не знайдено в жодному листі")
                        self.ui.another_sheet1.setStyleSheet('color: red')
        except IndexError:
            self.ui.res_label.setText("код товару не знайдено в жодному листі")
            self.ui.res_label.setStyleSheet('color: red')

    def keyPressEvent(self, event):
        numpad_mod = int(event.modifiers()) & QtCore.Qt.KeypadModifier
        if event.key() == QtCore.Qt.Key_Enter and numpad_mod \
                and self.ui.incoming_later.text() and not self.ui.incoming_code.text():
            self.get_data()
            self.count_scanner_spares()
        if event.key() == QtCore.Qt.Key_Enter and numpad_mod \
                and self.ui.incoming_later.text() and self.ui.incoming_code.text():
            self.search_in_code_column()

        if event.key() == QtCore.Qt.Key_Escape:
            pass
            # if self.table_used and self.ui.incoming_later.text() != "":
            #     self.del_from_listblock()
            #     self.close()
        if event.key() == QtCore.Qt.Key_Return and self.ui.incoming_later.text() and not self.ui.incoming_code.text():
            self.get_data()
            self.count_scanner_spares()

        if event.key() == QtCore.Qt.Key_Return and self.ui.incoming_later.text() and self.ui.incoming_code.text():
            self.search_in_code_column()

    def unclose_edit(self):
        self.cursor.execute(sql_querys.unclose(self.incoming_latter_backup))
        self.cnn.commit()

    def get_data(self):
        # print("nazhata")
        self.incoming_latter_backup = self.ui.incoming_later.text()
        r1 = self.cursor.execute(sql_querys.may_i_coming(self.incoming_latter_backup))
        len_r1 = len(list(r1))
        if len_r1 == 0:
            print("PRAVDA")
            # print(len(list(r1)))
            self.status_list = \
                list(self.cursor.execute(sql_querys.check_later_for_exist(self.ui.incoming_later.text())))[0][0]
            # print(self.status_list)
            if self.status_list == "1":
                if not self.table_used and self.ui.incoming_later.text() != "":
                    self.incoming_latter_text = self.ui.incoming_later.text()
                    self.check_float(self.incoming_latter_text)
                    check = self.cursor.execute(sql_querys.check_in_base(self.ui.incoming_later.text()))
                    for i in check:
                        if i[0] != "0":
                            self.who_open = i[0]
                            self.ui.res_label.setText(f"Лист відкрито користувачем {i[0]}")
                            self.ui.res_label.setStyleSheet('color: red')

                        else:

                            self.ui.res_label.setText("")
                            self.cursor.execute(sql_querys.listblock(self.incoming_latter_text, self.win_user))
                            self.cnn.commit()
                            res = self.cursor.execute(sql_querys.get_data(self.incoming_latter_text))
                            for row in res:
                                self.add_table_row(self.ui.tableWidget, row)
                            if self.add_one_part_status:
                                self.table_item.cellChanged.connect(self.when_changed_change_color)
                                self.ui.active_sheet.setText(
                                    f"Зараз використовується {self.ui.incoming_later.text()} лист")
                                # self.ui.active_sheet.setStyleSheet("font: bold 14px ")
                                self.ui.active_sheet.setStyleSheet("color: Blue; font: bold 12px ")
                                self.createtable()
                                self.table_used = True
                    self.count_scanner_spares()
                elif self.ui.incoming_later.text() == "":
                    self.ui.res_label.setText(f"Спочатку оберіть лист")
                    self.ui.res_label.setStyleSheet('color: red')
                elif self.ui.res_label.text() != "" and self.table_used:
                    self.ui.res_label.setText(f"Спочатку звільніть листа  {self.incoming_latter_text}")
                    self.ui.res_label.setStyleSheet('color: red')
            if self.status_list == "0":
                self.status_list = ""
                self.table_used = False
                self.ui.res_label.setText(f"Лист не знайдено")
                self.ui.res_label.setStyleSheet('color: red')
        else:
            self.ui.res_label.setText(f"Доступ до листа зачинено!")
            self.ui.res_label.setStyleSheet('color: red')

    def __del__(self):
        self.del_from_listblock()


class AnotherWindow(QDialog, MainLogic):
    """
   NEW WINDOW FOR SERCH IN OSFI
    """

    def __init__(self):
        super().__init__()
        self.ui2 = second_window()
        self.ui2.setupUi(self)
        self.ui2.search_btn.clicked.connect(self.get_parts_from_OSFI)
        header = self.ui2.tableWidget.horizontalHeader()
        for column in range(self.ui2.tableWidget.columnCount()):
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.Stretch)
        self.ui2.tableWidget.itemDoubleClicked.connect(self.test)

    def clear_qtable(self):

        self.ui2.tableWidget.setRowCount(0)

    def get_parts_from_OSFI(self):
        self.clear_qtable()
        res = self.cursor.execute(sql_querys.get_parts_from_OSFI(self.ui2.incoming_code.text()))
        for row in res:
            self.add_table_row(self.ui2.tableWidget, row)
            self.ui2.res_label.setText("Оберіть запчастину")
            self.ui2.res_label.setStyleSheet("color: green")
        if self.ui2.tableWidget.rowCount() == 0:
            self.ui2.res_label.setText("Код товару відсутній!")
            self.ui2.res_label.setStyleSheet('color: red')

    def test(self):
        row = self.ui2.tableWidget.currentItem().row()
        for item in range(self.ui2.tableWidget.columnCount()):
            GLOBAL_LIST_TO_ADD_ONE_PART.append(self.ui2.tableWidget.item(row, item).text())
        print(GLOBAL_LIST_TO_ADD_ONE_PART)

        self.close()


def main():
    app = QApplication(sys.argv)
    w = Inventory()
    w.show()
    app.exec_()


if __name__ == '__main__':
    main()
