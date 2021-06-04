# -*- coding: utf-8 -*-
"""
Created on Sun May  9 17:33:55 2021

@author: anvlad
"""

# ------------------------------------------------- ----- 
# ---------------------- main.py ------------------- ---- 
# --------------------------------------------- --------- 
from  PyQt5.QtWidgets  import QMainWindow, QApplication, QTreeWidgetItem, QFileDialog
from  PyQt5.uic  import  loadUi
from PyQt5.QtCore import Qt, QAbstractTableModel
import h5py
from functools import reduce

class TableModel(QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)
        #return self._data.shape[0]

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])
        #return self._data.shape[1]
            
class HdfViewer(QMainWindow):
    
    def  __init__(self):
        QMainWindow.__init__(self)
        loadUi("hdfviewer.ui" , self)
        self.btnOpen.clicked.connect(self.open)
        
    
    def open(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Load HDF file", "",
                                                  "HDF files (*.hdf, *.hdf5);;All files (*.*)", options=options)
        if fileName:
            try:
                f = h5py.File(fileName, "r")
                self.lblFileName.setText(fileName.split('/')[-1])
                self.lblFileName.setStyleSheet("color:#377eb8;")
                self.f = f
                self.s = HdfViewer.hdfanalyse(f)
                self.treeWidget.clear()
                self.treeWidget.setColumnCount(2)
                self.treeWidget.setHeaderLabels(['key', 'shape'])
                self.addRow(self.s, self.treeWidget)
                self.treeWidget.itemClicked.connect(self.showData)
            except OSError:
                self.lblFileName.setText("Not a valid HDF5 file")
                self.lblFileName.setStyleSheet("color:#e41a1c;")
    
    def addRow(self, x, parent):
        if self.cboxLimit.isChecked():
            keys = list(x.keys())[:100]
        else:
            keys = list(x.keys())
        for key in keys:
            w = QTreeWidgetItem(parent)
            w.setText(0, key)
            if not type(x[key]) is tuple:
                w.setText(1, str(len(x[key].keys())))
                self.addRow(x[key], w)
                w.setExpanded(False)
            else:
                w.setText(1, str(x[key]))    
            self.treeWidget.setCurrentItem(w)
   
    def showData(self):
        w = self.treeWidget.currentItem()
        if w.childCount() == 0:
            # Get hierarchy of keys for clicked element
            keys = []
            while not w is None:
                keys.append(w.data(0,0))
                w = w.parent()
            # Get the element following the list of keys in the reverse order
            try:
                data = reduce(lambda x, y: x[y], keys[::-1], self.f)[()]
                if data.ndim == 1:
                    data = data[:, None]
                elif data.ndim == 0:
                    data = data[None, None]
                self.model = TableModel(data.tolist())
                self.tableView.setModel(self.model)
            except AttributeError:
                pass
            
    @staticmethod
    def hdfanalyse(file):
        keys = file.keys()
        s = {}
        for key in keys:
            if isinstance(file[key], h5py.Dataset):
                if file[key].ndim == 0:
                    s[key] = (1, )
                else:
                    s[key] = file[key].shape
            elif isinstance(file[key], h5py.Group):
                s[key] = HdfViewer.hdfanalyse(file[key])
        return s

    def closeEvent(self, event):
        # then stop the app
        event.accept()
        
app = QApplication([]) 
window = HdfViewer() 


window.show() 
app.exec_()