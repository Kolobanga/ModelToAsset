import sys

from PyQt5.QtWidgets import *


class Main(QWidget):
    def __init__(self):
        super(Main, self).__init__()
        self.setWindowTitle('Create HDA')
        self.resize(200, 300)

        QVBoxLayout(self)

        self.firstName = QLineEdit()
        self.firstName.setPlaceholderText('First name')

        self.secondName = QLineEdit()
        self.secondName.setPlaceholderText('Second name')

        self.assetName = QLineEdit()
        self.assetName.setPlaceholderText('Asset name')

        self.assetLabel = QLineEdit()
        self.assetLabel.setPlaceholderText('Asset label')

        self.assetType = QComboBox()
        self.assetType.addItems(('Accessory',
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

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Ignored, QSizePolicy.Expanding)

        self.create = QPushButton('Create')
        self.create.clicked.connect(self.createAsset)

        self.layout().addWidget(self.firstName)
        self.layout().addWidget(self.secondName)
        self.layout().addWidget(self.assetName)
        self.layout().addWidget(self.assetLabel)
        self.layout().addWidget(self.assetType)
        self.layout().addSpacerItem(self.spacer)
        self.layout().addWidget(self.create)

    def createAsset(self):
        #subnet.createDigitalAsset('name_sname::my_house::1.0', r'd:/my_house.hda', 'My House', 0, 1, True, '', ignore_external_references=True)
        raise NotImplementedError


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())
