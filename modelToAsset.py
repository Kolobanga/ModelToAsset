import os
import sys
try:
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except:
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *


class ModelToAsset(QWidget):
    def __init__(self):
        super(ModelToAsset, self).__init__(None, Qt.WindowStaysOnTopHint)

        self.setWindowTitle('Create HDA')
        self.resize(200, 250)

        self.projectNameLabel = QLabel('Chose Project Name:')
        self.project = QComboBox()
        self.project.addItems(['Kolobanga', 'Netski'])

        self.typeLabel = QLabel('Chose Project Type:')
        self.type = QComboBox()
        self.type.addItems(['Object', 'Scene'])

        self.assetName = QLineEdit()
        self.assetName.setPlaceholderText('Asset name')

        self.assetLabel = QLineEdit()
        self.assetLabel.setPlaceholderText('Asset label')

        self.assetClass = QComboBox()
        self.assetClass.addItems(('Accessory',
                                 'Animal',
                                 'Building',
                                 'Character',
                                 'Clothes',
                                 'Device',
                                 'Food',
                                 'Furniture',
                                 'Object',
                                 'Plant',
                                 'Prop',
                                 'Tool',
                                  'Vehicle',
                                  'Weapon'))



        self.oldPath = os.path.splitext(hou.hipFile.path())[0] + '.hda'
        self.pathLine = QLineEdit(self.oldPath)
        self.changePathButton = QPushButton('...')
        self.changePathButton.clicked.connect(self.changePath)

        self.createButton = QPushButton('Create')
        self.createButton.clicked.connect(self.createAsset)

        QVBoxLayout(self)
        self.pathLayout = QHBoxLayout()
        self.pathLayout.addWidget(self.pathLine)
        self.pathLayout.addWidget(self.changePathButton)

        self.layout().addWidget(self.projectNameLabel)
        self.layout().addWidget(self.project)
        self.layout().addWidget(self.typeLabel)
        self.layout().addWidget(self.type)
        self.layout().addWidget(self.assetName)
        self.layout().addWidget(self.assetLabel)
        self.layout().addWidget(self.assetClass)
        self.layout().addLayout(self.pathLayout)
        self.layout().addWidget(self.createButton)

    def changePath(self):
        self.pathLine.setText(hou.ui.selectFile(start_directory=self.oldPath, chooser_mode=hou.fileChooserMode.Write))

    def createAsset(self):
        nodes = hou.selectedNodes()
        if len(nodes) == 1 and nodes[0].canCreateDigitalAsset():
            subnet = nodes[0]
            parmTemplateGroup = subnet.parmTemplateGroup()
            asset = subnet.createDigitalAsset('{project}_{type}::{assetName}::1.0'.format(project=self.project.currentText(), type=self.type.currentText(), assetName=self.assetName.text()),
                                              self.pathLine.text(), self.assetLabel.text(), 0, 1, True, '', ignore_external_references=True)
            asset.type().definition().setParmTemplateGroup(parmTemplateGroup)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModelToAsset()
    window.show()
    sys.exit(app.exec_())
